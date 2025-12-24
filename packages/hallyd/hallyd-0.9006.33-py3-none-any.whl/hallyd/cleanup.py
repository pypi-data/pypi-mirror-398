#  SPDX-FileCopyrightText: © 2022 Josef Hahn
#  SPDX-License-Identifier: AGPL-3.0-only
"""
Cleanup tasks can do arbitrary things after your process is terminated, like removing temporary files or other system
resources that are not cleaned up automatically by the operating system.
"""
import datetime
import importlib
import json
import os
import signal
import time
import traceback
import typing as t

import hallyd.fs as _fs
import hallyd.lang as _lang
import hallyd.bindle as _bindle
import hallyd.subprocess as _subprocess
import hallyd.typing as _typing


_VAR_LIB_PATH = _fs.Path("/var/lib")
_CLEANUP_DIR_BASE_PATH = _VAR_LIB_PATH("hallyd/cleanup")

try:  # TODO nicer, stricter, ...
    _CLEANUP_DIR_BASE_PATH.make_dir(until=_VAR_LIB_PATH, readable_by_all=True)
except IOError:
    pass

_CLEANUP_DIR_PATH = _CLEANUP_DIR_BASE_PATH("tasks")

_CLEANUP_SCOPE_ENV_VAR_NAME = "_HALLYD_CLEANUP_SCOPE"

_is_started = False
_lock = _lang.lock(_CLEANUP_DIR_BASE_PATH("lock"), is_reentrant=True)


def add_cleanup_task(func: _typing.CallableWithQualifiedName, *args, **kwargs) -> "_CleanupTask":
    """
    Add a cleanup task to be executed when the current process is terminated, and return a task controller object that
    allows early execution and other things.
    This will run in a separate process, once the current process is fully terminated.

    :param func: The function to call. Must not be a (non-static) method of some object.
    :param args: The function call args.
    :param kwargs: The function call kwargs.
    """
    return _add_cleanup_task(func, args, kwargs)


def cleanup_task_by_id(task_id: "_CleanupTask.Id") -> "_CleanupTask":
    """
    Return the task controller object by task id.

    :param task_id: The task id.
    """
    return _CleanupTask(task_id)


def mark_current_process_as_cleanup_scope() -> None:
    """
    Mark the current process as cleanup scope, so even for child processes, cleanup will not happen before this process
    is terminated.
    """
    if _CLEANUP_SCOPE_ENV_VAR_NAME not in os.environ:
        os.environ[_CLEANUP_SCOPE_ENV_VAR_NAME] = _subprocess.process_permanent_id_for_pid(os.getpid())


def cleanup_after_exit():
    """
    Make sure that cleanup will take place once the current process is terminated.

    You usually do not need to call it manually!
    """
    global _is_started
    with _lock:
        if not _is_started:
            _is_started = True
            if _have_same_fs_root(_current_cleanup_scope(), _subprocess.process_permanent_id_for_pid(os.getpid())):
                _CLEANUP_DIR_PATH.make_dir(until=_fs.Path("/"), exist_ok=True, readable_by_all=True)
                _subprocess.start_function_in_new_process(_guarded_cleanup, args=(_current_cleanup_scope(),))


def _current_cleanup_scope() -> str:
    return os.environ.get(_CLEANUP_SCOPE_ENV_VAR_NAME, _subprocess.process_permanent_id_for_pid(os.getpid()))


def _have_same_fs_root(p1: str, p2: str) -> bool:
    pid1 = _subprocess.pid_for_process_permanent_id(p1)
    pid2 = _subprocess.pid_for_process_permanent_id(p2)
    stat1 = _fs.Path(f"/proc/{pid1}/root/.").stat()
    stat2 = _fs.Path(f"/proc/{pid2}/root/.").stat()
    return stat1.st_ino == stat2.st_ino and stat1.st_dev == stat2.st_dev


def _add_cleanup_task(func: _typing.CallableWithQualifiedName, args: tuple, kwargs: dict) -> "_CleanupTask":
    cleanup_after_exit()
    task_path = _CLEANUP_DIR_PATH(_lang.unique_id())  # file names must be in clock order
    task_temp_path = _fs.Path(f"{task_path}~")
    task_temp_path.write_text(
        _bindle.dumps(
            {
                "module": func.__module__,
                "func": func.__qualname__,
                "args": args,
                "kwargs": kwargs,
                "process_permanent_id": _current_cleanup_scope(),
                "try_after": [
                    x.total_seconds()
                    for x in [
                        datetime.timedelta(seconds=0),
                        datetime.timedelta(seconds=0),
                        datetime.timedelta(seconds=0),
                        datetime.timedelta(seconds=20),
                        datetime.timedelta(minutes=2),
                        datetime.timedelta(minutes=30),
                        datetime.timedelta(hours=3),
                        datetime.timedelta(hours=12),
                        datetime.timedelta(days=5),
                        datetime.timedelta(days=60),
                        datetime.timedelta(days=365 * 2),
                    ]
                ],
            }
        )
    )
    task_temp_path.rename(task_path)
    return cleanup_task_by_id(task_path)


def _do_cleanup() -> None:
    tries_to_make = 3
    while tries_to_make > 0:
        tries_to_make -= 1

        task_paths = sorted(_fs.Path(_CLEANUP_DIR_PATH).iterdir())
        if len(task_paths) == 0:
            break

        for task_path in task_paths:
            if task_path.name.endswith("~"):
                continue

            time.sleep(0)
            with _lock:
                try:
                    task_data = json.loads(task_path.read_text())
                except Exception:
                    task_path.remove(not_exist_ok=True)
                    continue

                try_after = task_data["try_after"]
                if len(try_after) > 0:
                    process_permanent_id = task_data["process_permanent_id"]
                    gone_since = task_data.get("gone_since", None)

                    if not gone_since:
                        is_process_running = _subprocess.is_process_running(process_permanent_id)
                        if is_process_running is None:
                            return
                        if not is_process_running:
                            gone_since = task_data["gone_since"] = time.time()

                    if gone_since:
                        next_try = try_after[0] + gone_since
                        if next_try < time.time():
                            task_data["try_after"] = try_after[1:]
                            successful = False
                            # noinspection PyBroadException
                            try:
                                _CleanupTask(task_path)()
                                successful = True
                            except Exception:
                                task_data["errors"] = [*task_data.get("errors", []), traceback.format_exc()]
                            if not successful:
                                task_path.write_text(json.dumps(task_data))

        time.sleep(1)


def _guarded_cleanup(process_permanent_id: str) -> None:
    check_every = 100

    def prepare_stop(signum, frame):
        nonlocal check_every
        check_every = 1

    signal.signal(signal.SIGHUP, prepare_stop)
    signal.signal(signal.SIGTERM, prepare_stop)

    _do_cleanup()
    i = 0
    while True:
        i = (i + 1) % check_every
        if (i == 0) and _subprocess.is_process_running(process_permanent_id) is not True:
            break
        time.sleep(1)
    _do_cleanup()


class _CleanupTask:

    Id = str

    def __init__(self, task_id: Id | _fs.Path):
        self.__task_id = _CleanupTask.Id(task_id)
        self.__task_path = _fs.Path(task_id)

    def remove(self) -> None:
        with _lock:
            self.__task_path.unlink(missing_ok=True)

    @property
    def task_id(self) -> Id:
        return self.__task_id

    def __call__(self) -> None:
        with _lock:
            if not self.__task_path.exists():
                return
            task_data = _bindle.loads(self.__task_path.read_text())
            func = self.__module_item(importlib.import_module(task_data["module"]), task_data["func"])
            func(*task_data["args"], **task_data["kwargs"])
            self.remove()

    def __module_item(self, module, item_name) -> t.Any:
        x = module
        for segment in item_name.split("."):
            x = getattr(x, segment)
        return x
