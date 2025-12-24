#  SPDX-FileCopyrightText: © 2022 Josef Hahn
#  SPDX-License-Identifier: AGPL-3.0-only
"""
Running subprocesses. Some shortcuts based on Python :code:`subprocess`.
"""
import json
import os
import subprocess
import sys
import typing as t

import hallyd.asset as _asset
import hallyd.fs as _fs
import hallyd.lang as _lang
import hallyd.bindle as _bindle
import hallyd.typing as _typing


def check_call_with_stdin_string(cmd: t.Iterable, *, stdin: t.AnyStr, **kwargs) -> None:
    """
    Call a process with a given string piped to its stdin. Raise an exception if it fails.

    See Python :code:`subprocess.check_call`.

    :param cmd: The command to call.
    :param stdin: The string to pipe to the process' stdin.
    :param kwargs: Additional arguments.
    """
    cmd = tuple(cmd)
    stdin = stdin.encode() if isinstance(stdin, str) else stdin
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, **kwargs)
    stdout_result, stderr_result = p.communicate(stdin)
    if p.returncode:
        raise subprocess.CalledProcessError(p.returncode, cmd, stdout_result, stderr_result)
    return stdout_result


def check_output_with_stdin_string(cmd: t.Iterable, *, stdin: t.AnyStr, **kwargs) -> bytes:
    """
    Call a process with a given string piped to its stdin and return its stdout answer. Raise an exception if it fails.

    See Python :code:`subprocess.check_output`.

    :param cmd: The command to call.
    :param stdin: The string to pipe to the process' stdin.
    :param kwargs: Additional arguments.
    """
    return check_call_with_stdin_string(cmd, stdin=stdin, stdout=subprocess.PIPE, **kwargs)


def start_function_in_new_process(
    func: _typing.CallableWithQualifiedName,
    args=None,
    kwargs=None,
    *,
    interactive=False,
    capture_output=False,
    command_line_prefix=(),
) -> subprocess.Popen:
    """
    Start a function in a new process and return the process object.

    :param func: The function to start in a new process.
    :param args: The args to pass to this function.
    :param kwargs: The kwargs to pass to this function.
    :param interactive: Whether to execute the function in an interactive way, potentially accessing the terminal.
    :param capture_output: Whether to capture stdout (and stderr redirected to it) in a pipe for further processing.
                           Only for non-interactive calls.
    :param command_line_prefix: An optional command line prefix. Usually not needed.
    """
    return subprocess.Popen(
        [*command_line_prefix, sys.executable, _asset.data.helpers_dir("call_function.py"), _lang.unique_id()],
        start_new_session=True,
        env={
            **os.environb,
            b"HALLYD_SUBPROCESS_DATA": _bindle.dumps(
                {
                    "MODULE_NAME": func.__module__,
                    "FUNCTION_NAME": func.__qualname__,
                    "ARGS": args or (),
                    "KWARGS": kwargs or {},
                }
            ),
            b"HALLYD_SUBPROCESS_SYS_PATH": json.dumps(list(sys.path)),
        },
        stdin=None if interactive else subprocess.DEVNULL,
        stderr=None if interactive else subprocess.STDOUT,
        stdout=None if interactive else (subprocess.PIPE if capture_output else subprocess.DEVNULL),
    )


def process_permanent_id_for_pid(pid: int) -> str:
    """
    Return a permanent id for a running process.

    This id is better than just a pid in order to monitor a process lifetime, as the latter one has a higher risk of
    being re-used by other processes after the original process dies. It is even perfect if the command line is unique.

    See also :py:meth:`pid_for_process_permanent_id`.

    :param pid: The pid of the process to return permanent id for.
    """
    try:
        cmdline = _fs.Path(f"/proc/{pid}/cmdline").read_text()
        return _bindle.dumps({"PID": pid, "CMDLINE": cmdline})
    except FileNotFoundError:
        if _fs.Path("/proc/version").exists():
            raise ProcessNotRunningError() from None
        raise ProcessInfoUnavailableError() from None


def pid_for_process_permanent_id(process_permanent_id: str) -> int:
    """
    Return the pid of a permanent id. See :py:meth:`process_permanent_id_for_pid`.

    :param process_permanent_id: The process permanent id.
    """
    return _bindle.loads(process_permanent_id)["PID"]


def is_process_running(process_id: str | int) -> bool | None:
    """
    Check whether a process is currently running (:code:`None` means this info is unavailable).

    :param process_id: Can be either a pid or a process permanent id (see :py:meth:`process_permanent_id_for_pid`).
    """
    if isinstance(process_id, int):
        try:
            process_permanent_id_for_pid(process_id)
            return True
        except ProcessInfoUnavailableError:
            return None
        except ProcessNotRunningError:
            return False

    pid = pid_for_process_permanent_id(process_id)
    try:
        return process_permanent_id_for_pid(pid) == process_id
    except ProcessInfoUnavailableError:
        return None
    except ProcessNotRunningError:
        return False


def verify_tool_available(tool: str) -> None:  # TODO use more
    """
    Check whether a given tool is installed (by calling it). Raises an exception if not.

    :param tool: The tool to check for.
    """
    try:
        subprocess.check_output([tool, "--help"], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        pass
    except IOError:
        raise RuntimeError(f"'{tool}' is not available") from None


class ProcessNotRunningError(Exception):
    pass


class ProcessInfoUnavailableError(Exception):
    pass
