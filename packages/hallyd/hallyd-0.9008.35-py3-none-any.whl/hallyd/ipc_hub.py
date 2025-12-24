#  SPDX-FileCopyrightText: © 2021 Josef Hahn
#  SPDX-License-Identifier: AGPL-3.0-only
"""
Distributed computing mechanism.

Basic usage is to create and run a :py:class:`Hub`. Clients can (via :py:mod:`hallyd.ipc` clients) make requests to that
hub and get answers. Then to subclass :py:class:`HubWorker` and plug it into the hub.
"""
import abc
import threading
import time
import typing as t

import hallyd.fs as _fs
import hallyd.ipc as _ipc
import hallyd.lang as _lang
import hallyd.net as _net


_RequestT = t.TypeVar("_RequestT", bound=object)
_ResponseT = t.TypeVar("_ResponseT", bound=object)


class HubWorker(t.Generic[_RequestT, _ResponseT]):
    """
    Hub workers can be plugged into :py:class:`Hub` instances in order to implement a routine that processes requests.

    Plug a worker into a hub using :py:meth:`plug_into_hub`.
    """

    def __init__(self, ipc_dialog_hub_object: "_HubIpcObject", *, poll_interval: float = 0.5):
        self.__poll_interval = poll_interval
        self.__ipc_hub_object = ipc_dialog_hub_object
        self.__pending_request_ids = {}
        self.__stopped = True

    @classmethod
    def plug_into_hub(cls, path: "_fs.Path", connection: "_net.Connection | None" = None, **kwargs) -> "t.Self":
        """
        Create a new instance of this hub worker type and connect it to a hub while active.

        You must use it for a with-block (it is only plugged in inside it).

        :param path: The path to the hub. See :py:attr:`Hub.path`.
        :param connection: Network connection to use (only for remote hubs).
        :param kwargs: Additional kwargs for worker instantiation.
        """
        return cls(_ipc.client(path, connection=connection), **kwargs)

    def __enter__(self):
        self.__stopped = False
        self.__thread = threading.Thread(target=self.__run_worker_thread, daemon=True)
        self.__thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__stopped = True
        self.__thread.join()
        self.__thread = None

    def __run_worker_thread(self):
        while not self.__stopped:
            try:
                pending_request_ids = self.__ipc_hub_object.pending_request_ids()
            except _ipc.BadConnectionError:
                pass
            for old_request_id in list(
                filter(lambda i: i not in pending_request_ids, self.__pending_request_ids.keys())
            ):
                request = self.__pending_request_ids.pop(old_request_id)
                self.request_disappeared(request)
            for new_request_id in list(filter(lambda i: i not in self.__pending_request_ids, pending_request_ids)):
                request = self.__ipc_hub_object.request_by_id(new_request_id)
                if request:
                    self.__pending_request_ids[new_request_id] = request
                    self.request_arrived(request)
            time.sleep(1)

    @abc.abstractmethod
    def request_arrived(self, request: _RequestT) -> None:
        pass

    def request_disappeared(self, request: _RequestT) -> None:
        pass

    def answer_request(self, request_id: int, response: _ResponseT) -> bool:
        return self.__ipc_hub_object.add_answer(request_id, response)

    def try_lock_request(self, request: _RequestT) -> bool:
        pass


class Hub(t.Generic[_RequestT, _ResponseT]):
    """
    Hubs provide one way of distributed computing via :py:mod:`hallyd.ipc`.

    Clients of a hub can put requests on a hub, and eventually get answer data.

    A hub contains an IPC server for an internal hub controller, which provides a pluggable interface.
    Connect :py:class:`HubWorker` instances to the hub for request processing.

    You must use it for a with-block (it will only run inside it).
    """

    def __init__(self, path: _fs.Path):
        """
        :param path: The path where to start the server. It must not exist yet. The filesystem must support sockets.
                     This path will be accessible by everyone. Make sure to restrict access properly by the permissions
                     of its super-directories!
        """
        self.__path = path
        self.__ipc_hub_object = _HubIpcObject()
        self.__ipc_hub_server = _ipc.threaded_server(self.__ipc_hub_object, path=path)
        self.__entered = False

    @property
    def path(self):
        """
        The IPC path where hub workers can be plugged into by means of :py:meth:`HubWorker.plug_into_hub`.
        """
        return self.__path

    def put_request(self, request: _RequestT) -> int:
        """
        Make a request to the hub and return the request id for further actions.
        """
        self.__verify_entered()
        return self.__ipc_hub_object.add_request(request)

    def get_answer(self, request_id: int) -> _ResponseT:
        """
        Return the answer for a request made in the past.

        This can only be called for each request.

        :param request_id: The request id.
        """
        self.__verify_entered()
        return self.__ipc_hub_object.pop_answer(request_id)

    def __verify_entered(self):
        if not self.__entered:
            raise RuntimeError("this is only allowed inside the with-context of this object")

    def __enter__(self):
        if not self.__entered:
            self.__entered = True
            self.__ipc_hub_server.enable()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__entered:
            self.__entered = False
            self.__ipc_hub_server.disable()


class _HubRequest(t.Generic[_RequestT]):
    """
    One request that was made to the hub.
    """

    def __init__(self, request_id, payload):
        self.__id = request_id
        self.__request_payload = payload

    @property
    def id(self):
        return self.__id

    @property
    def request_id(self):
        return self.__id

    @property
    def request_payload(self):
        return self.__request_payload

    @property
    def payload(self):
        return self.__request_payload


class _HubIpcObject(t.Generic[_RequestT, _ResponseT]):
    """
    The internal controller used by each hubs in order to provide pluggability.
    """

    def __init__(self):
        self.__requests: dict[int, _HubRequest[_RequestT]] = {}
        self.__answers: dict[int, _ResponseT] = {}
        self.__request_id_counter = _lang.Counter()
        self.__lock = threading.Lock()
        self.__request_answered_condition = threading.Condition(self.__lock)

    def pending_request_ids(self):
        """
        Return request ids for all requests that a currently open.
        """
        with self.__lock:
            return list(self.__requests.keys())

    def request_by_id(self, request_id: int) -> _HubRequest[_RequestT] | None:
        """
        Return the request by request id.

        :param request_id:
        """
        with self.__lock:
            return self.__requests.get(request_id, None)

    def add_request(self, request: _RequestT) -> int:
        """
        Add a new request to the hub.

        :param request:
        """
        with self.__lock:
            request_id = self.__request_id_counter.next()
            self.__requests[request_id] = _HubRequest(request_id, request)
            return request_id

    def pop_answer(self, request_id: int) -> _ResponseT:
        """
        Return and delete the answer for a request.

        :param request_id:
        """
        with self.__lock:
            while request_id not in self.__answers:
                self.__request_answered_condition.wait()
            return self.__answers.pop(request_id)

    def add_answer(self, request_id: int, response: _ResponseT) -> bool:
        """
        Store the answer for a request.

        :param request_id:
        :param response:
        """
        with self.__lock:
            if request_id not in self.__requests:
                return False
            self.__requests.pop(request_id)
            self.__answers[request_id] = response
            self.__request_answered_condition.notify_all()
