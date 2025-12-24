#  SPDX-FileCopyrightText: © 2021 Josef Hahn
#  SPDX-License-Identifier: AGPL-3.0-only
"""
Shell connections; potentially over the network.
"""
import abc
import shlex
import subprocess

import hallyd.fs as _fs
import hallyd.lang as _lang
import hallyd.subprocess as _subprocess


@_lang.with_friendly_repr_implementation()
class Connection:

    class ExecutionResult:

        def __init__(self, returncode: int, output: str, error_output: str):
            self.__returncode = returncode
            self.__output = output
            self.__error_output = error_output

        @property
        def returncode(self):
            return self.__returncode

        @property
        def output(self) -> str:
            return self.__output

        @property
        def error_output(self) -> str:
            return self.__error_output

    def is_alive(self) -> bool:
        try:
            self.exec(["true"])
            return True
        except CouldNotConnectError:
            return False

    @abc.abstractmethod
    def exec(self, command: list[str]) -> ExecutionResult:
        pass

    @abc.abstractmethod
    def mount(self, remote_path: _fs.Path, local_path: _fs.Path) -> None:
        pass

    @abc.abstractmethod
    def umount(self, local_path: _fs.Path) -> None:
        pass


class SshConnection(Connection):

    def __init__(self, host: str, *, port: int, user: str, password: str, connect_timeout: float = 60):
        super().__init__()
        self.__host = host
        self.__port = port
        self.__user = user
        self.__password = password
        self.__connect_timeout = connect_timeout

    def exec(self, command):
        import fabric
        import paramiko

        try:
            with fabric.Connection(
                self.__host,
                port=self.__port,
                user=self.__user,
                connect_timeout=int(self.__connect_timeout),
                connect_kwargs=dict(password=self.__password),
            ) as fabric_conn:
                # TODO how to handle that its host_key is different from the known one?
                fabric_result = fabric_conn.run(" ".join([shlex.quote(x) for x in command]), hide=True, warn=True)
        except paramiko.ssh_exception.AuthenticationException as ex:
            raise AccessDeniedError("authentication failed") from ex
        except IOError as ex:
            raise CouldNotConnectError(f"could not connect to {self.__host} via ssh") from ex
        return Connection.ExecutionResult(fabric_result.exited, fabric_result.stdout, fabric_result.stderr)

    def mount(self, remote_path, local_path):  # TODO mitm attacks due to disabled host key check
        _subprocess.check_call_with_stdin_string(
            [
                "sshfs",
                f"-p{self.__port}",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-o",
                "GlobalKnownHostsFile=/dev/null",
                "-o",
                f"ConnectTimeout={self.__connect_timeout},ServerAliveInterval=20,ServerAliveCountMax=4",
                "-o",
                "password_stdin",
                f"{self.__user}@{self.__host}:{remote_path}",
                local_path,
            ],
            stdin=self.__password,
        )

    def umount(self, local_path):
        subprocess.check_call(["fusermount", "-u", local_path])


class CouldNotConnectError(IOError):
    pass


class AccessDeniedError(IOError):
    pass
