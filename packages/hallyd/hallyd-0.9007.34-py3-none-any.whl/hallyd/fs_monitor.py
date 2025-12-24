#  SPDX-FileCopyrightText: © 2023 Josef Hahn
#  SPDX-License-Identifier: AGPL-3.0-only
"""
Watching for files/directories for changes.
"""
import abc
import logging
import math
import os
import stat
import threading
import time
import traceback
import typing as t

import hallyd.fs as _fs


_logger = logging.getLogger(__name__)


class Watcher(abc.ABC):

    @abc.abstractmethod
    def wait_changed(self, *, timeout: float | None = None) -> bool:
        pass


class _Watcher(Watcher):

    class WatchThread(threading.Thread, abc.ABC):

        def __init__(self, watcher: "_Watcher"):
            super().__init__(daemon=True, name=f"{type(self).__name__} for {watcher}")
            self.__watcher = watcher
            self.__stopped = False

        @classmethod
        def try_create(cls, watcher: "_Watcher") -> "_Watcher.WatchThread | None":
            try:
                return cls(watcher)
            except Exception:
                return

        def stop(self):
            self.__stopped = True

        @property
        def _watcher(self) -> "_Watcher":
            return self.__watcher

        def _setup(self):
            pass

        def _wait_event(self) -> bool:
            time.sleep(10)
            return False

        def _teardown(self):
            pass

        def run(self):
            try:
                self._setup()
                while not self.__stopped:
                    try:
                        was_triggered = self._wait_event()
                    except Exception:
                        _logger.warning(traceback.format_exc())
                        was_triggered = False
                        time.sleep(10)
                    if was_triggered:
                        self.__watcher._check_if_changed()
                self._teardown()
            except Exception:
                _logger.warning(traceback.format_exc())

    class PollingWatchThread(WatchThread):

        def _wait_event(self):
            time.sleep(10)
            return True

    class WatchdogWatchThread(WatchThread):

        def __init__(self, watcher: "_Watcher"):
            super().__init__(watcher)
            import watchdog  # just for testing if it is supported

            self.__observer = None

        def _setup(self):
            import watchdog.observers
            import watchdog.events

            class MyEventHandler(watchdog.events.FileSystemEventHandler):
                def on_any_event(self_, event):  # TODO only write events?! (see parzzley?!)
                    self._watcher._force_changed()

            event_handler = MyEventHandler()
            self.__observer = watchdog.observers.Observer()
            for path in self._watcher.paths:
                self.__observer.schedule(event_handler, str(path))
            self.__observer.start()

        def _teardown(self):
            self.__observer.stop()
            self.__observer.join()

    _WatchThreadTypes = (PollingWatchThread, WatchdogWatchThread)

    def __init__(self, paths: t.Iterable["_fs.TInputPath"], trigger_initially: bool):
        self.__paths = tuple([_fs.Path(path) for path in paths])
        self.__cookie = self.__compute_cookie()
        self.__was_changed = []
        if trigger_initially:
            self.__was_changed.append(object())
        self.__was_maybe_changed = []
        self.__is_change_handling = []
        self.__lock = threading.Lock()
        self.__was_changed_condition = threading.Condition(self.__lock)
        self.__watch_threads = None
        self.__entered_count = 0

    @property
    def paths(self) -> t.Iterable["_fs.Path"]:
        return self.__paths

    def _force_changed(self, *, wait_until_handled: bool = False) -> None:
        with self.__lock:
            token = object()
            self.__was_changed.append(token)
            self.__was_changed_condition.notify_all()
            self.__wait_handled(token, wait_until_handled)

    def _check_if_changed(self, *, wait_until_handled: bool = False) -> None:
        with self.__lock:
            token = object()
            self.__was_maybe_changed.append(token)
            self.__was_changed_condition.notify_all()
            self.__wait_handled(token, wait_until_handled)

    def __wait_handled(self, token: object, do_wait: bool) -> None:
        while do_wait:
            if token not in (*self.__was_changed, *self.__was_maybe_changed, *self.__is_change_handling):
                return
            self.__was_changed_condition.wait()

    def __compute_cookie(self):
        return tuple([self.__compute_cookie__single_item(path) for path in self.__paths])

    def __compute_cookie__single_item(self, path: "_fs.Path", *, flat: bool = False):
        try:
            path_stat = os.stat(path)
            children = None
            if not flat and stat.S_ISDIR(path_stat.st_mode):
                children = tuple(
                    [self.__compute_cookie__single_item(child_path, flat=True) for child_path in sorted(path.iterdir())]
                )
            return path.name, path_stat.st_ctime, path_stat.st_mtime, path_stat.st_size, path_stat.st_mode, children
        except IOError:
            return path.name

    def wait_changed(self, *, timeout=None):
        wait_until = math.inf if (timeout is None) else (time.time() + timeout)
        with self.__lock:
            self.__is_change_handling = []
            self.__was_changed_condition.notify_all()
        while True:
            with self.__lock:
                while not (self.__was_changed or self.__was_maybe_changed):
                    self.__was_changed_condition.wait(timeout=min(max(0.0, wait_until - time.time()), 2**30))
                    if time.time() > wait_until:
                        return False
                if self.__was_changed:
                    self.__cookie = object()
                self.__is_change_handling = self.__was_changed + self.__was_maybe_changed
                self.__was_changed = []
                self.__was_maybe_changed = []
                self.__was_changed_condition.notify_all()
            last_cookie = self.__cookie
            self.__cookie = self.__compute_cookie()
            if self.__cookie != last_cookie:
                return True
            with self.__lock:
                self.__is_change_handling = []
                self.__was_changed_condition.notify_all()

    def __enter__(self):
        if self.__entered_count == 0:
            self.__watch_threads = []
            for watch_thread_type in self._WatchThreadTypes:
                watch_thread = watch_thread_type.try_create(self)
                if watch_thread:
                    watch_thread.start()
                    self.__watch_threads.append(watch_thread)
        self.__entered_count += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__entered_count -= 1
        if self.__entered_count == 0:
            for watch_thread in self.__watch_threads:
                watch_thread.stop()
            self.__watch_threads = None


def watch(*paths: "_fs.TInputPath", trigger_initially: bool = True) -> Watcher:
    return _Watcher(paths, trigger_initially)


class FilesystemMonitor(abc.ABC):

    def __init__(self, *paths: "_fs.TInputPath", trigger_initially: bool = True):
        self.__paths = tuple([_fs.Path(path) for path in paths])
        self.__trigger_initially = trigger_initially
        self.__entered_count = 0
        self.__thread = None
        self.__lock = threading.RLock()

    @property
    def paths(self) -> t.Iterable["_fs.Path"]:
        return self.__paths

    @abc.abstractmethod
    def _changed(self) -> None:
        pass

    def force_changed(self, *, wait_until_handled: bool = True) -> None:
        with self.__lock:
            with self:
                self.__thread.force_changed(wait_until_handled)

    def check_if_changed(self, *, wait_until_handled: bool = True) -> None:
        with self.__lock:
            with self:
                self.__thread.check_if_changed(wait_until_handled)

    def __enter__(self):
        with self.__lock:
            if self.__entered_count == 0:
                self.__thread = FilesystemMonitor._Thread(self.__paths, self.__trigger_initially, self)
                self.__thread.start()
            self.__entered_count += 1
            return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self.__lock:
            self.__entered_count -= 1
            if self.__entered_count == 0:
                self.__thread.stop()
                self.__thread = None

    class _Thread(threading.Thread):

        def __init__(self, paths: t.Iterable["_fs.Path"], trigger_initially: bool, monitor: "FilesystemMonitor"):
            super().__init__(daemon=True, name=f"monitoring for {monitor}")
            self.__stopped = False
            self.__stopped_lock = threading.Lock()
            self.__watcher_lock = threading.Lock()
            self.__watcher_set_condition = threading.Condition(self.__watcher_lock)
            self.__paths = tuple(paths)
            self.__trigger_initially = trigger_initially
            self.__monitor = monitor
            self.__watcher_ = None

        def stop(self):
            with self.__stopped_lock:
                self.__stopped = True

        def force_changed(self, wait_until_handled: bool) -> None:
            self.__watcher._force_changed(wait_until_handled=wait_until_handled)

        def check_if_changed(self, wait_until_handled: bool) -> None:
            self.__watcher._check_if_changed(wait_until_handled=wait_until_handled)

        @property
        def __watcher(self) -> _Watcher:
            with self.__watcher_lock:
                while not self.__watcher_:
                    self.__watcher_set_condition.wait()
                return self.__watcher_

        def run(self):
            with watch(*self.__paths, trigger_initially=self.__trigger_initially) as watcher:
                with self.__watcher_lock:
                    self.__watcher_ = watcher
                    self.__watcher_set_condition.notify_all()
                while True:
                    was_changed = watcher.wait_changed(timeout=10)
                    with self.__stopped_lock:
                        if self.__stopped:
                            break
                    if was_changed:
                        self.__monitor._changed()
