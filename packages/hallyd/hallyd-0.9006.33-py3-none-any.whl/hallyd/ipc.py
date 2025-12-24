#  SPDX-FileCopyrightText: © 2021 Josef Hahn
#  SPDX-License-Identifier: AGPL-3.0-only
"""
Simple IPC mechanism (based on file sockets).

Allows to create a server for an object (running as a separate thread as long as needed) and to call methods on it
from any process. Input and output data must both be :py:mod:`hallyd.bindle` serializable.

See :py:func:`threaded_server` and :py:func:`client`.
"""
import abc
import base64
import errno
import logging
import shlex
import socket
import threading
import time
import traceback
import typing as t

import hallyd.fs as _fs
import hallyd.net as _net
import hallyd.bindle as _bindle


_logger = logging.getLogger(__name__)


class Server(abc.ABC):

    @property
    @abc.abstractmethod
    def is_enabled(self) -> bool:
        """
        Whether this server is currently enabled (i.e. running).
        """

    @abc.abstractmethod
    def enable(self) -> None:
        """
        Enable this server.
        """

    @abc.abstractmethod
    def disable(self) -> None:
        """
        Disable this server.
        """


def threaded_server(object_: t.Any, *, path: _fs.Path) -> Server:
    """
    Create an IPC server (to be running in a separate background thread once enabled) for the given object at the given
    filesystem path and return it.

    :param object_: The object to create a server for.
    :param path: The path where to start the server. It must not exist yet. The filesystem must support sockets.
                 This path will be accessible by everyone. Make sure to restrict access properly by the permissions
                 of its super-directories!
    """
    return _ThreadedServer(object_, path=path)


def client(path: _fs.Path, *, connection: "_net.Connection | None" = None) -> t.Any:
    """
    Return an IPC client object for a running IPC server. It allows to call methods on the server object with common
    Python syntax (i.e. as if it would be a plain local object).

    :param path: The path where the server was started.
    :param connection: Network connection to use (only for remote calls).
    """
    return (_NetworkClient(connection, path) if connection else _LocalClient(path)).object


class _ThreadedServer(Server):

    class _Request:

        def __init__(
            self,
            connection,
            method_name: str,
            args: list[t.Any],
            kwargs: dict[str, list[t.Any]],
        ):
            self.__connection = connection
            self.method_name = method_name
            self.args = args
            self.kwargs = kwargs

        def answer(self, *, result=None, error=None):
            for char in (base64.b64encode(_bindle.dumps([result, error]).encode()) + b"\n").decode():
                while True:
                    try:
                        self.__connection.send(char.encode())
                        break
                    except IOError as ex:
                        if ex.errno not in [errno.EWOULDBLOCK, errno.EAGAIN]:
                            raise

    class _MainThread(threading.Thread):

        def __init__(self, server: "_ThreadedServer"):
            super().__init__(name=f"IPC Server Main Thread for {server}", daemon=True)
            self.__server = server
            self.__stopped = False

        def run(self):
            while not self.__stopped:
                self.__server._try_process_request()

        def stop(self):
            self.__stopped = True

    # noinspection PyShadowingBuiltins
    def __init__(self, object: t.Any, *, path: _fs.Path):
        super().__init__()
        self.__object = object
        self.__path = path
        self.__sock = None
        self.__thread = None
        self.__start_stop_lock = threading.RLock()

    def _try_process_request(self) -> None:
        try:
            connection, client_address = self.__sock.accept()
            request = self.__get_request(connection)
            threading.Thread(
                target=self.__worker,
                args=(request, connection),
                name=f"IPC Server Worker Thread for {self}",
                daemon=True,
            ).start()
        except OSError as ex:
            if ex.errno not in [errno.EWOULDBLOCK, errno.EAGAIN]:
                raise
            time.sleep(0.01)

    def __worker(self, request, connection):
        if request:
            # noinspection PyBroadException
            try:
                if request.args is None:
                    if type(getattr(type(self.__object), request.method_name, None)).__name__ == "function":
                        result = 1, None
                    else:
                        request_method = getattr(self.__object, request.method_name)
                        result = 2, request_method
                else:
                    request_method = getattr(self.__object, request.method_name)
                    result = request_method(*request.args, **request.kwargs)
                request.answer(result=result)
            except Exception:
                try:
                    request.answer(error=traceback.format_exc())
                except IOError:
                    _logger.warning(traceback.format_exc())
        connection.close()

    def __get_request(self, connection) -> "_ThreadedServer._Request | None":
        data = b""
        while not data.endswith(b"\n"):
            new_data = connection.recv(4096)
            if not new_data:
                return
            data += new_data
        request_data = _bindle.loads(base64.b64decode(data))
        return self._Request(connection, *request_data)

    @property
    def is_enabled(self):
        with self.__start_stop_lock:
            return self.__sock is not None

    def enable(self):
        with self.__start_stop_lock:
            if self.is_enabled:
                return

            try:
                self.__path.make_dir(readable_by_all=True)
            except FileExistsError:
                raise IPCServerPathAlreadyExistsError(self.__path) from None
            socket_path = _socket_path(self.__path)
            self.__sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                self.__sock.bind(str(socket_path))
            except IOError as ex:
                if ex.errno == errno.EADDRINUSE:
                    raise IPCServerPathAlreadyExistsError(self.__path) from None
                raise
            socket_path.change_access(0o777)
            self.__sock.listen(1)
            self.__sock.setblocking(False)
            self.__thread = self._MainThread(self)
            self.__thread.start()

    def disable(self):
        with self.__start_stop_lock:
            if not self.is_enabled:
                return
            self.__thread.stop()
            self.__sock.close()
            self.__sock = None
            self.__thread = None


class _Client:

    class Proxy:

        def __init__(self, request_func):
            self.__request_func = request_func

        def __getattr__(self, item):
            attr_kind, attr_value = self.__request_func(item, None, None)
            if attr_kind == 1:

                def method_proxy(*args, **kwargs):
                    return self.__request_func(item, args, kwargs)

                return method_proxy
            return attr_value

    def __init__(self):
        super().__init__()
        self.__proxy = self.Proxy(self._request)

    @property
    def object(self):
        return self.__proxy

    @abc.abstractmethod
    def _request(self, method_name, args, kwargs):
        pass


class _LocalClient(_Client):

    def __init__(self, path: _fs.Path):
        super().__init__()
        self.__path = path

    def _request(self, method_name, args, kwargs):
        socket_path = _socket_path(self.__path)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(str(socket_path.resolve()))
        except IOError as ex:
            raise IPCServerUnavailableError(self.__path) from ex
        try:
            request_data = method_name, args, kwargs
            sock.sendall(base64.b64encode(_bindle.dumps(request_data).encode()) + b"\n")
            data = b""
            while not data.endswith(b"\n"):
                new_data = sock.recv(4096)
                if not new_data:
                    raise BadConnectionError("the communication stream was malformed")
                data += new_data
            answer_data = _bindle.loads(base64.b64decode(data))
            if answer_data[1]:
                raise MethodCallErroneousError(answer_data[1])
            return answer_data[0]
        finally:
            sock.close()


class _NetworkClient(_Client):

    def __init__(self, connection: "_net.Connection", path: _fs.Path):
        super().__init__()
        self.__path = path
        self.__connection = connection

    def _request(self, method_name, args, kwargs):  # TODO
        py_code = (
            f"import base64\n"
            f"import traceback\n"
            f"import hallyd\n"
            f"answer_data = [None, None]\n"
            f"try:\n"
            f"    client = hallyd.ipc.client(hallyd.fs.Path({repr(str(self.__path))}))\n"
            f"    answer_data[0] = client._request({repr(method_name)}, {repr(args)}, {repr(kwargs)})\n"
            f"except:\n"
            f"    answer_data[1] = traceback.format_exc()\n"
            f"print(base64.b64encode(hallyd.bindle.dumps(answer_data).encode()).decode())"
        )
        exec_result = self.__connection.exec(
            ["sudo", "bash", "-c", f"cd /usr/local/share; echo {shlex.quote(py_code)} | python3"]
        )
        if exec_result.returncode != 0:
            raise IOError(
                f"there was an internal error executing the request:"
                f"\n{exec_result.output}\n{exec_result.error_output}"
            )
        answer_data = _bindle.loads(base64.b64decode(exec_result.output))
        if answer_data[1]:
            raise MethodCallErroneousError(answer_data[1])
        return answer_data[0]


class MethodCallErroneousError(RuntimeError):

    def __init__(self, message: str):
        super().__init__(f"the remote method raised an exception: {message}")


class BadConnectionError(OSError):

    def __init__(self, message: str):
        super().__init__(f"IPC connection problem: {message}")


class IPCServerPathAlreadyExistsError(BadConnectionError):

    def __init__(self, ipc_path: _fs.Path):
        super().__init__(f"there is already another server at {str(ipc_path)!r}")
        self.__ipc_path = ipc_path

    @property
    def ipc_path(self):
        return self.__ipc_path


class IPCServerUnavailableError(BadConnectionError):

    def __init__(self, ipc_path: _fs.Path):
        super().__init__(f"there is no server available at {str(ipc_path)!r}")
        self.__ipc_path = ipc_path

    @property
    def ipc_path(self):
        return self.__ipc_path


def _socket_path(ipc_path: _fs.Path) -> _fs.Path:
    return ipc_path("socket")
