#  SPDX-FileCopyrightText: © 2024 Josef Hahn
#  SPDX-License-Identifier: AGPL-3.0-only
"""
Services.
"""
import abc
import base64
import contextlib
import dataclasses
import functools
import inspect
import json
import pathlib
import random
import shlex
import subprocess
import sys
import typing as t

import hallyd.asset as _asset
import hallyd.fs as _fs
import hallyd.lang as _lang
import hallyd.bindle as _bindle


def create_service(name: str | None, runnable: "TRunnable") -> t.ContextManager["ServiceSetup"]:
    return _create_setup_context(name, runnable, ServiceSetup, _service_backend.create_service)


def service(runnable: "TServiceKey") -> "Service":
    return _service_backend.service(runnable) if isinstance(runnable, str) else runnable


def remove_service(runnable: "TServiceKey") -> None:
    _service_backend.remove_service(runnable if isinstance(runnable, str) else runnable.name)


def create_interval_task(name: str | None, runnable: "TRunnable") -> t.ContextManager["IntervalTaskSetup"]:
    return _create_setup_context(name, runnable, IntervalTaskSetup, _interval_task_backend.create_interval_task)


def interval_task(runnable: "TIntervalTaskKey") -> "IntervalTask":
    return _interval_task_backend.interval_task(runnable) if isinstance(runnable, str) else runnable


def remove_interval_task(runnable: "TIntervalTaskKey") -> None:
    _interval_task_backend.remove_interval_task(runnable if isinstance(runnable, str) else runnable.name)


def create_calendar_task(name: str | None, runnable: "TRunnable") -> t.ContextManager["CalendarTaskSetup"]:
    return _create_setup_context(name, runnable, CalendarTaskSetup, _calendar_task_backend.create_calendar_task)


def calendar_task(runnable: "TCalendarTaskKey") -> "CalendarTask":
    return _calendar_task_backend.calendar_task(runnable) if isinstance(runnable, str) else runnable


def remove_calendar_task(runnable: "TCalendarTaskKey") -> None:
    _calendar_task_backend.remove_calendar_task(runnable if isinstance(runnable, str) else runnable.name)


def create_next_boot_task(name: str | None, runnable: "TRunnable") -> t.ContextManager["NextBootTaskSetup"]:
    return _create_setup_context(name, runnable, NextBootTaskSetup, _next_boot_task_backend.create_next_boot_task)


def next_boot_task(runnable: "TNextBootTaskKey") -> "NextBootTask":
    return _next_boot_task_backend.next_boot_task(runnable) if isinstance(runnable, str) else runnable


def remove_next_boot_action(runnable: "TNextBootTaskKey") -> None:
    _next_boot_task_backend.remove_next_boot_action(runnable if isinstance(runnable, str) else runnable.name)


@dataclasses.dataclass
class _TaskSetup:

    _name: str | None = None
    _runnable: "TRunnable | None" = None
    _description: str | None = None
    _user: str | int | None = None
    _group: str | int | None = None
    _discard_output: bool = False
    _working_dir: _fs.Path = _fs.Path("/")
    _umask: int = 0o022
    _private_tmp: bool = False

    def run_in_working_dir(self, working_dir: _fs.TInputPath) -> None:
        self._working_dir = _fs.Path(working_dir)

    def description(self, description: str) -> None:
        self._description = description

    def discard_output(self, discard_output: bool = True) -> None:
        self._discard_output = discard_output

    def run_as_user(self, user: str | int, group: str | int | None = None) -> None:
        self._user = user
        self._group = group

    def with_umask(self, _: int) -> None:
        self._umask = _

    def with_private_tmp(self, _: bool = True) -> None:
        self._private_tmp = _

    def _before_create(self) -> None:
        self._name = self._name or f"hld-{_lang.unique_id()}"

    def _after_create(self) -> None:
        pass

    @dataclasses.dataclass
    class _WithDependencies:

        @dataclasses.dataclass
        class Dependency:
            name: str
            afterwards: bool
            success_required: bool
            optional: bool

        _dependencies: t.Iterable[Dependency] = ()

        def add_dependency(
            self, unit_name: str, *, afterwards: bool = False, success_required: bool = False, optional: bool = False
        ):
            self._dependencies = tuple(
                [*self._dependencies, self.Dependency(unit_name, afterwards, success_required, optional)]
            )


@dataclasses.dataclass
class ServiceSetup(_TaskSetup._WithDependencies, _TaskSetup):
    __DEFAULT_RESTART_DELAY = 2
    _start_instantly: bool = True
    _enabled: bool = True
    _restart_delay: int | None = __DEFAULT_RESTART_DELAY
    _as_oneshot: bool = False
    _startup_context: t.Iterable[str] | None = None
    _post_stop: "TCmdLineRunnable | None" = None
    _options: t.Iterable[t.Callable[[str], None]] = ()

    def do_not_start_instantly(
        self, do_not_start_instantly: bool = True, *, not_even_enable: bool | None = None
    ) -> None:
        self._start_instantly = not do_not_start_instantly
        if not_even_enable is not None:
            self._enabled = not not_even_enable

    def do_not_restart(self, do_not_restart: bool = True) -> None:
        self._restart_delay = None if do_not_restart else ServiceSetup.__DEFAULT_RESTART_DELAY

    def with_startup_context(self, startup_context: str) -> None:
        self._startup_context = tuple([*(self._startup_context or ()), startup_context])

    def with_restart_delay(self, restart_delay: int | None) -> None:
        self._restart_delay = restart_delay

    def with_post_stop_command(self, post_stop_command: str) -> None:
        self._post_stop = post_stop_command if not self._post_stop else f"({self._post_stop});({post_stop_command})"

    def with_option(self, option: t.Callable[[str], None]) -> None:
        self._options = tuple([*self._options, option])

    def as_oneshot(self, as_oneshot: bool = True) -> None:
        self._as_oneshot = as_oneshot

    def _after_create(self):
        super()._after_create()
        new_service = _service_backend.service(self._name)
        for option in self._options:
            option(self._name)
        if self._enabled:
            new_service.enable()
        if self._start_instantly:
            new_service.start()


class _TimedTaskSetup(_TaskSetup):
    _start_instantly: bool = False

    def start_instantly(self, start_instantly: bool = True) -> None:
        self._start_instantly = start_instantly


@dataclasses.dataclass
class IntervalTaskSetup(_TimedTaskSetup):
    _intervals: t.Iterable[float] = ()

    def schedule_by_interval(self, seconds: float = 0, *, minutes: float = 0, hours: float = 0) -> None:
        self._intervals = tuple([*self._intervals, seconds + (minutes + (hours * 60)) * 60])


@dataclasses.dataclass
class CalendarTaskSetup(_TimedTaskSetup):
    _calendars: t.Iterable["_Calendar"] = ()

    def schedule_daily(self, *, time: str | None = None) -> None:
        self._calendars = tuple([*self._calendars, self._DailyCalendar(time)])

    def schedule_weekly(self, *, time: str | None = None, day_of_week: int = 7) -> None:
        self._calendars = tuple([*self._calendars, self._WeeklyCalendar(time, min(max(1, day_of_week), 7))])

    def schedule_monthly(self, *, time: str | None = None, day: int = 1) -> None:
        self._calendars = tuple([*self._calendars, self._MonthlyCalendar(time, day)])

    def schedule_yearly(self, *, time: str | None = None, day: int = 1, month: int = 1) -> None:
        self._calendars = tuple([*self._calendars, self._YearlyCalendar(time, day, month)])

    class _Calendar:
        pass

    @dataclasses.dataclass
    class _DailyCalendar(_Calendar):
        time: str | None

    @dataclasses.dataclass
    class _WeeklyCalendar(_Calendar):
        time: str | None
        day_of_week: int

    @dataclasses.dataclass
    class _MonthlyCalendar(_Calendar):
        time: str | None
        day: int

    @dataclasses.dataclass
    class _YearlyCalendar(_Calendar):
        time: str | None
        day: int
        month: int


@dataclasses.dataclass
class NextBootTaskSetup(_TaskSetup._WithDependencies, _TaskSetup):
    _interactive: bool = False

    def run_interactively(self, run_interactively: bool = True) -> None:
        self._interactive = run_interactively

    def _after_create(self):
        super()._after_create()
        _next_boot_task_backend.next_boot_task(self._name).enable()


@contextlib.contextmanager
def _create_setup_context(
    name: str | None, runnable: "TRunnable", setup_type: type["_TTaskSetup"], create_func
) -> t.ContextManager["_TTaskSetup"]:
    yield (setup := setup_type(name, runnable))
    setup._before_create()
    create_func(setup)
    setup._after_create()


class _Task(abc.ABC):

    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def is_enabled(self) -> bool:
        pass

    @abc.abstractmethod
    def enable(self) -> None:
        pass

    @abc.abstractmethod
    def disable(self) -> None:
        pass


class Service(_Task, abc.ABC):

    @abc.abstractmethod
    def start(self) -> None:
        pass

    @abc.abstractmethod
    def stop(self) -> None:
        pass

    @abc.abstractmethod
    def is_active(self) -> None:
        pass

    @abc.abstractmethod
    def restart(self) -> None:
        pass

    @abc.abstractmethod
    def reload(self) -> None:
        pass


class IntervalTask(_Task, abc.ABC):
    pass


class CalendarTask(_Task, abc.ABC):
    pass


class NextBootTask(_Task, abc.ABC):
    pass


class _ServiceBackend(abc.ABC):

    @abc.abstractmethod
    def create_service(self, setup: ServiceSetup) -> None:
        pass

    @abc.abstractmethod
    def service(self, name: str) -> "Service":
        pass

    @abc.abstractmethod
    def remove_service(self, name: str) -> None:
        pass


class _CalendarTaskBackend(abc.ABC):

    @abc.abstractmethod
    def create_calendar_task(self, setup: CalendarTaskSetup) -> None:
        pass

    @abc.abstractmethod
    def calendar_task(self, name: str) -> "CalendarTask":
        pass

    @abc.abstractmethod
    def remove_calendar_task(self, name: str) -> None:
        pass


class _IntervalTaskBackend(abc.ABC):

    @abc.abstractmethod
    def create_interval_task(self, setup: IntervalTaskSetup) -> None:
        pass

    @abc.abstractmethod
    def interval_task(self, name: str) -> "IntervalTask":
        pass

    @abc.abstractmethod
    def remove_interval_task(self, name: str) -> None:
        pass


class _NextBootTaskBackend(abc.ABC):

    @abc.abstractmethod
    def create_next_boot_task(self, setup: NextBootTaskSetup) -> None:
        pass

    @abc.abstractmethod
    def next_boot_task(self, name: str) -> "NextBootTask":
        pass

    @abc.abstractmethod
    def remove_next_boot_action(self, name: str) -> None:
        pass


class Runnable(abc.ABC):

    class _FinishAndReboot(BaseException):
        pass

    def __init__(self):
        self.__reboot_afterwards = False

    @abc.abstractmethod
    def run(self) -> None:
        pass

    def reboot(self) -> None:
        raise Runnable._FinishAndReboot()


class _FunctionRunnable(Runnable):

    def __init__(self, func: "TCallableRunnable"):
        super().__init__()
        self.func = func

    def run(self):
        self.func(*(() if (len(inspect.signature(self.func).parameters.keys()) == 0) else (self,)))


class _SystemdBackend(_ServiceBackend, _CalendarTaskBackend, _IntervalTaskBackend, _NextBootTaskBackend):

    __lock = _lang.lock("/tmp/hld-systemd-lock")  # TODO good location?

    def create_interval_task(self, setup):
        _SystemdBackend.__create(setup)

    def interval_task(self, name):
        return self.__unit(name, type="timer", also_allow_types=["service"])

    def remove_interval_task(self, name):
        _SystemdBackend.__remove(self.service(name))

    def create_calendar_task(self, setup):
        _SystemdBackend.__create(setup)

    def calendar_task(self, name):
        return self.__unit(name, type="timer", also_allow_types=["service"])

    def remove_calendar_task(self, name):
        _SystemdBackend.__remove(self.service(name))

    def create_service(self, setup):
        _SystemdBackend.__create(setup)

    def service(self, name):
        return self.__unit(name, type="service", also_allow_types=["timer"])

    def remove_service(self, name):
        _SystemdBackend.__remove(self.service(name))

    def create_next_boot_task(self, setup):
        _SystemdBackend.__create(setup)

    def next_boot_task(self, name):
        return self.__unit(name, type="service")

    def remove_next_boot_action(self, name):
        _SystemdBackend.__remove(self.service(name))

    @staticmethod
    def _short_name(name: str) -> tuple[str, str | None]:
        for postfix in ("service", "target", "timer"):
            if name.endswith(f".{postfix}"):
                return name[: -len(postfix) - 1], postfix
        return name, None

    @staticmethod
    def __create(setup) -> None:
        name, postfix = _SystemdBackend._short_name(setup._name)

        timer_opts = None
        if isinstance(setup, IntervalTaskSetup):
            timer_opts = [("OnBootSec", 12)]
            for interval in setup._intervals:
                timer_opts.append(("OnUnitActiveSec", max(1, round(interval))))
        if isinstance(setup, CalendarTaskSetup):
            timer_opts = [("Persistent", "true")]
            for calendar in setup._calendars:
                default_time = f"{random.randrange(1,6)}:00"
                if isinstance(calendar, CalendarTaskSetup._DailyCalendar):
                    timer_opts.append(("OnCalendar", calendar.time or default_time))
                elif isinstance(calendar, CalendarTaskSetup._WeeklyCalendar):
                    day = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][calendar.day_of_week - 1]
                    timer_opts.append(("OnCalendar", f"{day}, {calendar.time or default_time}"))
                elif isinstance(calendar, CalendarTaskSetup._MonthlyCalendar):
                    timer_opts.append(("OnCalendar", f"*-*-{calendar.day} {calendar.time or default_time}"))
                elif isinstance(calendar, CalendarTaskSetup._YearlyCalendar):
                    timer_opts.append(
                        ("OnCalendar", f"*-{calendar.month}-{calendar.day} {calendar.time or default_time}")
                    )
                else:
                    raise ValueError(f"invalid calendar {calendar!r}")

        if not ((postfix in (None, "service")) or (postfix == "timer" and timer_opts)):
            raise ValueError(f"invalid name {setup._name!r}")

        with _SystemdBackend.__lock:
            service_spec_path = _fs.Path(f"/etc/systemd/system/{name}.service")
            service_spec_path.set_data(
                str(_SystemdBackend.__setup_to_object_spec(setup, service_spec_path)), readable_by_all=True
            )

            if timer_opts:
                timer_opts_str = "\n".join([f"{k}={v}" for k, v in timer_opts])
                _fs.Path(f"/etc/systemd/system/{name}.timer").set_data(
                    f"[Timer]\n" f"{timer_opts_str}\n" f"[Install]\n" f"WantedBy=timers.target\n", readable_by_all=True
                )
                subprocess.check_call(["systemctl", "enable", f"{name}.timer"])
                if setup._start_instantly:
                    subprocess.check_call(["systemctl", "start", f"{name}.timer"])

    @staticmethod
    def __remove(service: "_Unit") -> None:
        name, postfix = _SystemdBackend._short_name(service.full_name)
        if postfix not in (None, "service", "timer"):
            raise ValueError(f"unable to remove {service.full_name!r}")

        with _SystemdBackend.__lock:
            service.stop()
            service.disable()

            timer_file = _fs.Path(f"/etc/systemd/system/{name}.timer")
            if timer_file.exists():
                subprocess.check_call(["systemctl", "disable", f"{name}.timer"])
                timer_file.remove()

            _fs.Path(f"/etc/systemd/system/{name}.service").remove()
            _fs.Path(f"/etc/systemd/system/{name}.service.d").remove(not_exist_ok=True)

            subprocess.check_call(["systemctl", "daemon-reload"])

    @staticmethod
    def __setup_to_object_spec(setup: _TaskSetup, service_spec_path: _fs.Path | None = None) -> "_UnitSpec":
        def full_name(s):
            short_name, postfix = _SystemdBackend._short_name(s)
            return f"{short_name}.{postfix or "service"}"

        name, postfix = _SystemdBackend._short_name(setup._name)
        if not ((postfix in (None, "service")) or (postfix == "timer" and isinstance(setup, _TimedTaskSetup))):
            raise ValueError(f"invalid name {setup._name!r}")

        unit_spec = _SystemdBackend._UnitSpec()
        service_type = "oneshot"
        interactive = False
        once = False

        unit_spec.service.set_value("User", setup._user or "root")
        if setup._group is not None:
            unit_spec.service.set_value("Group", setup._group)
        if setup._description:
            unit_spec.unit.set_value("Description", setup._description)
        unit_spec.service.set_value("WorkingDirectory", str(setup._working_dir))

        unit_spec.service.set_value("UMask", oct(setup._umask).replace("o", "0"))
        unit_spec.service.set_value("PrivateTmp", "yes" if setup._private_tmp else "no")

        if isinstance(setup, _TaskSetup._WithDependencies):
            for wants in [full_name(d.name) for d in setup._dependencies if not d.optional and not d.success_required]:
                unit_spec.unit.add_value("Wants", wants)
            for requires in [full_name(d.name) for d in setup._dependencies if not d.optional and d.success_required]:
                unit_spec.unit.add_value("Requires", requires)
            for after in [full_name(d.name) for d in setup._dependencies if not d.afterwards]:
                unit_spec.unit.add_value("After", after)
            for before in [full_name(d.name) for d in setup._dependencies if d.afterwards]:
                unit_spec.unit.add_value("Before", before)

        if isinstance(setup, ServiceSetup):
            if setup._restart_delay is not None:
                unit_spec.service.set_value("RestartSec", str(setup._restart_delay))
                unit_spec.service.set_value("Restart", "on-failure" if setup._as_oneshot else "always")
            unit_spec.unit.set_value("StartLimitInterval", "0")

            if setup._post_stop:
                unit_spec.service.add_value(
                    "ExecStopPost",
                    _SystemdBackend.__runnable_to_spec_info(
                        setup._post_stop, unit_spec, service_spec_path, discard_output=setup._discard_output
                    ),
                )

            service_type = "oneshot" if setup._as_oneshot else "simple"
            unit_spec.service.set_value("RemainAfterExit", "yes" if (service_type == "oneshot") else "no")

            for startup_context in setup._startup_context or ["multi-user.target"]:
                unit_spec.install.add_value("WantedBy", full_name(startup_context))

        if isinstance(setup, _TimedTaskSetup):
            unit_spec.unit.add_value("Wants", f"{name}.timer")

        if isinstance(setup, NextBootTaskSetup):
            once = True
            interactive = setup._interactive
            unit_spec.unit.add_value("After", "multi-user.target")
            unit_spec.install.add_value("WantedBy", "multi-user.target")
            unit_spec.unit.add_value("Before", "graphical.target")

        unit_spec.service.set_value("Type", service_type)

        if interactive:
            unit_spec.unit.add_value("After", "getty@tty2.service")
            unit_spec.service.set_value("StandardInput", "tty")
            unit_spec.service.set_value("StandardOutput", "tty")
            unit_spec.service.set_value("StandardError", "tty")
            unit_spec.service.set_value("TTYPath", "/dev/tty2")
            unit_spec.service.set_value("TTYReset", "yes")
            unit_spec.service.set_value("TTYVHangup", "yes")

        unit_spec.service.set_value(
            "ExecStart",
            _SystemdBackend.__runnable_to_spec_info(
                setup._runnable,
                unit_spec,
                service_spec_path,
                discard_output=setup._discard_output,
                interactive=interactive,
                once=once,
            ),
        )

        return unit_spec

    @staticmethod
    def __runnable_to_spec_info(
        runnable: "TRunnable",
        unit_spec: "_UnitSpec",
        service_spec_path: _fs.Path | None,
        *,
        interactive: bool = False,
        once: bool = False,
        discard_output: bool = False,
    ) -> str:
        once, interactive = bool(once), bool(interactive)
        if runnable is None:
            runnable = "true"
        if isinstance(runnable, pathlib.Path):
            runnable = [runnable]
        if not isinstance(runnable, str) and hasattr(runnable, "__iter__"):
            runnable = " ".join([shlex.quote(str(x)) for x in runnable])
        if (interactive or once) and isinstance(runnable, str):
            runnable = functools.partial(subprocess.check_call, ["sh", "-c", runnable])
        if callable(runnable):
            runnable = _FunctionRunnable(runnable)
        if isinstance(runnable, Runnable):
            token = _lang.unique_id()

            # TODO (optionally?) put runnable data into a place where only root can read it? is EnvironmentFile good? - https://serverfault.com/questions/413397/how-to-set-environment-variable-in-systemd-service/910655#910655
            base64_data = base64.b64encode(
                _bindle.dumps(
                    dict(ACTION=runnable, SVC_PATH=service_spec_path, INTERACTIVE=interactive, ONCE=once)
                ).encode()
            ).decode()
            unit_spec.service.add_value("Environment", f"HALLYD_SUBPROCESS_DATA_{token}={base64_data}")

            base64_sys_path = base64.b64encode(json.dumps(list(sys.path)).encode()).decode()
            unit_spec.service.add_value("Environment", f"HALLYD_SUBPROCESS_SYS_PATH_{token}={base64_sys_path}")

            aux_bin = _asset.data.helpers_dir("call_action.py")
            runnable = f"{sys.executable} {aux_bin} {token}"
        if discard_output:
            runnable = "sh -c " + shlex.quote(f"({runnable}) &> /dev/null")
        return runnable

    def __unit(self, name, *, type: str, also_allow_types: t.Iterable[str] = ()) -> "_Unit":
        short_name, postfix = _SystemdBackend._short_name(name)
        if postfix not in (type, None, *also_allow_types):
            raise ValueError(f"invalid name {name!r}")
        return _SystemdBackend._Unit(short_name, type)

    class _UnitSpec:

        class _MultiDict:

            def __init__(self):
                self.__data = {}

            def add_value(self, key: str, value: str):
                if key not in self.__data:
                    self.clear_values(key)
                self.__data[key].append(value)

            def clear_values(self, key: str):
                self.__data[key] = []

            def set_value(self, key: str, value: str):
                self.clear_values(key)
                self.__data[key].append(value)

            def __str__(self):
                result = ""
                for key, values in self.__data.items():
                    for value in values:
                        result += f"{key}={value}\n"
                return result

        def __init__(self):
            self.__unit = _SystemdBackend._UnitSpec._MultiDict()
            self.__service = _SystemdBackend._UnitSpec._MultiDict()
            self.__install = _SystemdBackend._UnitSpec._MultiDict()
            self.__timer = _SystemdBackend._UnitSpec._MultiDict()

        @property
        def unit(self) -> _MultiDict:
            return self.__unit

        @property
        def service(self) -> _MultiDict:
            return self.__service

        @property
        def install(self) -> _MultiDict:
            return self.__install

        @property
        def timer(self) -> _MultiDict:
            return self.__timer

        def __str__(self):
            result = ""

            for section_name, section in [
                ("Unit", self.__unit),
                ("Service", self.__service),
                ("Install", self.__install),
                ("Timer", self.__timer),
            ]:
                section_result = str(section)
                if section_result:
                    result += f"[{section_name}]\n{section_result}\n"

            return result

    class _Unit(Service, IntervalTask, CalendarTask):

        def __init__(self, name: str, unit_type: str):
            super().__init__()
            self.__name = name
            self.__unit_type = unit_type

        @property
        def name(self):
            return self.__name

        @property
        def unit_type(self):
            return self.__unit_type

        @property
        def full_name(self):
            return f"{self.name}.{self.unit_type}"

        def start(self):
            self.__systemctl("start", self.full_name)

        def stop(self):
            self.__systemctl("stop", self.full_name)

        def is_active(self):
            try:
                self.__systemctl("is-active", "--quiet", self.full_name)
                return True
            except subprocess.CalledProcessError:
                return False

        def restart(self):
            self.__systemctl("restart", self.full_name)

        def reload(self):
            self.__systemctl("reload", self.full_name)

        def enable(self):
            self.__systemctl("enable", self.full_name)

        def disable(self):
            self.__systemctl("disable", self.full_name)

        @property
        def is_enabled(self):
            try:
                self.__systemctl("is-enabled", "--quiet", self.full_name)
                return True
            except subprocess.CalledProcessError:
                return False

        def override(
            self,
            wants: list[str] = (),
            requires: list[str] = (),
            after: list[str] = (),
            before: list[str] = (),
            wanted_by: list[str] = (),
            required_by: list[str] = (),
            reset_wants: bool = False,
            reset_requires: bool = False,
            reset_after: bool = False,
            reset_before: bool = False,
            reset_wanted_by: bool = False,
            reset_required_by: bool = False,
        ) -> None:
            def config_string(new_list, do_reset, config_key):
                return (f"{config_key}=\n" if do_reset else "") + f"{config_key}=" + " ".join(new_list) + "\n"

            install_section = "\n".join(
                [
                    config_string(*args)
                    for args in (
                        (wanted_by, reset_wanted_by, "WantedBy"),
                        (required_by, reset_required_by, "RequiredBy"),
                    )
                ]
            )
            unit_section = "\n".join(
                [
                    config_string(*args)
                    for args in (
                        (wants, reset_wants, "Wants"),
                        (requires, reset_requires, "Requires"),
                        (after, reset_after, "After"),
                        (before, reset_before, "Before"),
                    )
                ]
            )
            override_config = ""
            if install_section:
                override_config += f"[Install]\n{install_section}\n"
            if unit_section:
                override_config += f"[Unit]\n{unit_section}\n"
            if not override_config:
                return
            _fs.Path(f"/etc/systemd/system/{self.full_name}.d").make_dir(exist_ok=True, readable_by_all=True)
            override_config_path = _fs.Path(f"/etc/systemd/system/{self.full_name}.d/override.conf")
            if override_config_path.exists():
                raise Exception("TODO goof")
            override_config_path.write_text(override_config)
            if self.is_enabled:
                self.__systemctl("reenable", self.full_name)

        def __systemctl(self, *args) -> None:
            subprocess.check_output(["systemctl", *args], stderr=subprocess.STDOUT)


_service_backend: _ServiceBackend = _SystemdBackend()
_calendar_task_backend: _CalendarTaskBackend = _SystemdBackend()
_interval_task_backend: _IntervalTaskBackend = _SystemdBackend()
_next_boot_task_backend: _NextBootTaskBackend = _SystemdBackend()

_TTaskSetup = t.TypeVar("_TTaskSetup", bound=_TaskSetup)

_TCmdLineRunnablePart = str | _fs.TInputPath
TCmdLineRunnable = t.Iterable[_TCmdLineRunnablePart] | _TCmdLineRunnablePart
TCallableRunnable = t.Callable[[], None] | t.Callable[[Runnable], None]
TRunnable = TCmdLineRunnable | Runnable | TCallableRunnable | None

TServiceKey = Service | str
TIntervalTaskKey = IntervalTask | str
TCalendarTaskKey = CalendarTask | str
TNextBootTaskKey = NextBootTask | str
