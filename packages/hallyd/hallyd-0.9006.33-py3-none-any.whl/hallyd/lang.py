#  SPDX-FileCopyrightText: © 2022 Josef Hahn
#  SPDX-License-Identifier: AGPL-3.0-only
"""
Various low-level features.
"""
import abc
import datetime
import fcntl
import functools
import json
import logging
import math
import os
import re
import string
import threading
import time
import traceback
import typing as t
import weakref
import xml.etree.ElementTree

import hallyd.bindle as _bindle
import hallyd.fs as _fs


_logger = logging.getLogger(__name__)

_T = t.TypeVar("_T", bound=object)


def call_now_with_retry(
    *,
    tries: int = 8,
    interval: float = 30,
    interval_fact: float = 1,
    retry_on: t.Iterable[type[Exception]] | None = None,
) -> t.Callable:  # TODO use
    def decorator(fct, *args, **kwargs):
        return with_retry(tries=tries, interval=interval, interval_fact=interval_fact, retry_on=retry_on)(fct)(
            *args, **kwargs
        )

    return decorator


def with_retry(
    *,
    tries: int = 8,
    interval: float = 30,
    interval_fact: float = 1,
    retry_on: t.Iterable[type[Exception]] | None = None,
) -> t.Callable:
    if retry_on is None:
        retry_on = [Exception]

    def decorator(fct):
        @functools.wraps(fct)
        def func(*a, **b):
            nwi = interval
            for itr in reversed(range(tries)):
                try:
                    return fct(*a, **b)
                except Exception as e:
                    if (itr > 0) and any((issubclass(type(e), x) for x in retry_on)):
                        #    import krrezzeedtest.log
                        #   krrezzeedtest.log.debug(traceback.format_exc(), tag="grayerror")
                        time.sleep(nwi)
                        nwi *= interval_fact
                    else:
                        raise

        return func

    return decorator


def with_friendly_repr_implementation(*, skip: t.Iterable[str] = ()):
    #  TODO test (for all classes that use it);   more reliable (cycles?!)
    return functools.partial(_with_friendly_repr_implementation__decorator, tuple(skip))


def _with_friendly_repr_implementation__decorator(skip_, cls_):
    def friendly_repr(self):
        objdict = json.loads(_bindle.dumps(self))
        module_name, type_name = objdict.pop(_bindle._TYPE_KEY)
        objdict = _bindle._filter_unneeded_dict_entries(type(self), objdict)
        objdict = {key: value for key, value in objdict.items() if key not in skip_}
        params_pieces = []
        for key, value in objdict.items():
            params_pieces.append(f"{key}={repr(value)}")
        full_type_name = (f"{module_name}." if module_name else "") + type_name
        return f"{full_type_name}({', '.join(params_pieces)})"

    cls_.__repr__ = friendly_repr
    return cls_


class Counter:

    def __init__(self):
        self.__current = 0
        self.__lock = threading.Lock()

    def next(self):
        with self.__lock:
            self.__current += 1
            return self.__current


_unique_id_counter = Counter()

_unique_id_sources = [
    (time.time_ns, datetime.datetime(9999, 1, 1, 0, 0, 0).timestamp() * 1000**3),
    (_unique_id_counter.next, 99999),
    (threading.get_native_id, 2**32 - 1),
    (functools.partial(os.getpgid, 0), 2**32 - 1),
]


def unique_id(*, numeric_only: bool = False) -> str:
    alphabet = string.digits if numeric_only else f"{string.digits}{string.ascii_uppercase}{string.ascii_lowercase}"
    alphabet_len = len(alphabet)
    result = ""
    for source, range_max in _unique_id_sources:
        number = source()
        result_piece = ""
        while number > 0:
            result_piece = alphabet[number % alphabet_len] + result_piece
            number = number // alphabet_len
        length = math.floor(math.log(range_max, alphabet_len)) + 1
        result += result_piece[-length:].rjust(length, alphabet[0])
    return result


def execute_in_parallel(funcs: list[t.Callable[[], None]]) -> None:
    threads = [_ExecuteParallelThread(func) for func in funcs]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    errors = [thread.error for thread in threads if thread.error]
    if errors:
        errors_text = ", ".join([str(e) for e in errors])
        raise Exception(f"TODO Error(s) in parallel execution: {errors_text}")


class _ExecuteParallelThread(threading.Thread):

    def __init__(self, fct: t.Callable[[], None]):
        super().__init__(daemon=True)
        self.__fct = fct
        self.error = None

    def run(self):
        #            with self.__logsection:
        try:
            self.__fct()
        except Exception as e:
            self.error = e


class _AllAbstractMethodsProvidedByTrickMeta(abc.ABCMeta, t.Generic[_T]):

    def __new__(mcs, name, bases, namespace):
        x = type.__new__(mcs, name, bases, namespace)
        for foo in [xx for xx in dir(_T) if not xx.startswith("_")]:
            setattr(x, foo, None)
        return x


class AllAbstractMethodsProvidedByTrick(t.Generic[_T], metaclass=_AllAbstractMethodsProvidedByTrickMeta[_T]):
    pass


_locks = {}
_locks_lock = threading.Lock()


def _check_lock_alive(lock_file: "_fs.Path") -> None:
    with _locks_lock:
        lock_weakref = _locks.get(lock_file)
        if lock_weakref and not lock_weakref():
            _locks.pop(lock_file)


def lock(lock_file: "_fs.TInputPath", *, is_reentrant: bool = True, peek_interval: float = 0.25) -> "Lock":
    lock_file = _fs.Path(lock_file).resolve()
    with _locks_lock:
        result_weakref = _locks.get(lock_file)
        result = result_weakref() if result_weakref else None
        if not result:
            result = lock_ = _Lock(lock_file, is_reentrant, peek_interval)
            _locks[lock_file] = weakref.ref(lock_)
            weakref.finalize(lock_, lambda: _check_lock_alive(lock_file))
        return result


class Lock(abc.ABC):

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    @abc.abstractmethod
    def acquire(self, blocking: bool = True, timeout: float = -1) -> bool:
        pass

    @abc.abstractmethod
    def release(self) -> None:
        pass

    @abc.abstractmethod
    def locked(self) -> bool:
        pass


class _Lock(Lock):

    def __init__(self, lock_path: "_fs.Path", is_reentrant: bool, peek_interval: float):
        self.__lock_path = lock_path
        self.__is_reentrant = is_reentrant
        self.__peek_interval = peek_interval
        self.__inner_lock = threading.RLock() if is_reentrant else threading.Lock()
        self.__lock_fd = None
        self.__locked_count = 0

    def acquire(self, blocking=True, timeout=-1):
        self.__lock_path.touch()

        timeout_ = timeout if blocking else 0
        timeout_at = None if (timeout_ < 0) else (time.monotonic() + timeout_)

        if not self.__inner_lock.acquire(blocking=blocking, timeout=timeout):
            return False

        try:
            self.__lock_fd = self.__lock_fd or open(self.__lock_path, "w")
            while True:
                try:
                    fcntl.lockf(self.__lock_fd, fcntl.LOCK_EX | (0 if timeout_at is None else fcntl.LOCK_NB))
                    self.__locked_count += 1
                    return True
                except BlockingIOError:
                    if time.monotonic() >= timeout_at:
                        self.__release()
                        return False
                    time.sleep(self.__peek_interval)

        except:
            self.__release()
            raise

    def release(self):
        if not self.locked():
            raise RuntimeError("releasing an unlocked Lock is forbidden")
        self.__locked_count -= 1
        self.__release(fd=self.__locked_count == 0)

    def locked(self):
        return self.__locked_count > 0

    def __release(self, *, fd: bool = True, inner_lock: bool = True) -> None:
        if fd and self.__lock_fd:
            try:
                self.__lock_fd.close()
            except Exception:
                _logger.warning(traceback.format_exc())
            self.__lock_fd = None

        if inner_lock:
            self.__inner_lock.release()


def match_format_string(pattern: str, string: str) -> dict[str, str]:
    def unescape_double_braces(s):
        return s.replace("{{", "{").replace("}}", "}")

    pattern_re = ""
    i = 0
    for expression_match in re.finditer(r"(?:[^{]|^)\{([^{}]+)\}(?:[^}]|$)", pattern):
        pattern_re += re.escape(unescape_double_braces(pattern[i : expression_match.start(1) - 1]))
        pattern_re += f"(?P<{expression_match.group(1)}>.*)"
        i = expression_match.end(1) + 1
    pattern_re += re.escape(unescape_double_braces(pattern[i:])) + "$"
    result_match = re.match(pattern_re, string)
    return result_match.groupdict() if result_match else None


def pretty_print_xml(input_xml: str) -> str:  # TODO broken
    xtree = xml.etree.ElementTree.fromstring(input_xml)
    ytree = xml.etree.ElementTree.ElementTree(xtree)
    xml.etree.ElementTree.indent(ytree, space=4 * " ")
    result = ""
    for line in xml.etree.ElementTree.tostring(xtree, encoding="unicode").split("\n"):
        if line.strip():
            result += line + "\n"
    return result
