#  SPDX-FileCopyrightText: © 2024 Josef Hahn
#  SPDX-License-Identifier: AGPL-3.0-only
"""
Additional features around Python modules.
"""
import importlib.machinery
import importlib.util
import sys
import types as tt
import typing as t

import hallyd.fs as _fs


def import_from_file(
    module_file: "_fs.TInputPath",
    *,
    module_name_left: str = "+hallyd..",
    module_name_right: str | None = None,
    using_sys_modules: bool = False
) -> tt.ModuleType:
    """
    Import a Python module from a Python source file and return it.

    :param module_file: The module file to import.
    :param module_name_left: The left part of the name the module gets.
    :param module_name_right: The right part of the name the module gets. Default: The file name without '.py'.
    :param using_sys_modules: Whether to use Python sys.modules as cache.
    """
    module_file = _fs.Path(module_file)
    module_name = module_name_left + (
        _file_name_to_module_name(module_file.name) if module_name_right is None else module_name_right
    )

    if using_sys_modules:
        module = sys.modules.get(module_name, import_from_file)
        if module is not import_from_file:
            return module

    loader = importlib.machinery.SourceFileLoader(module_name, str(module_file))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(module_name, loader))
    loader.exec_module(module)

    if using_sys_modules:
        sys.modules[module_name] = module

    return module


_T = t.TypeVar("_T", bound=object)


def types_from_module(base_type: type[_T], module: tt.ModuleType) -> t.Iterable[type[_T]]:
    """
    Return a list of types defined in a given module.

    This only includes types that are really defined in this module and not only an assignment from a foreign type.

    :param base_type: The base type to filter results for.
    :param module: The module to search.
    """
    for attr_name in sorted(dir(module)):
        attr = getattr(module, attr_name)
        if isinstance(attr, type) and issubclass(attr, base_type):
            if attr.__module__ == module.__name__ and attr.__name__ == attr_name:
                yield attr


def import_types_from_module_dir(
    base_type: type[_T],
    module_dir: "_fs.TInputPath",
    *,
    file_name_glob_pattern: str = "*.[Pp][Yy]",
    module_name_left: str = "+hallyd..",
    using_sys_modules: bool = False
) -> t.Iterable[type[_T]]:
    """
    Return a list of types defined in a given directory of modules.

    :param base_type: The base type to filter results for.
    :param module_dir: The directory of modules to search.
    :param file_name_glob_pattern: Pattern of files to consider as modules.
    :param module_name_left: The left part of the name the module gets. The right part is the file name without '.py'.
    :param using_sys_modules: Whether to use Python sys.modules as cache.
    """
    module_dir = _fs.Path(module_dir)
    for module_file in sorted(module_dir.glob(file_name_glob_pattern)):
        if module_file.is_file():
            for type_from_module in types_from_module(
                base_type,
                import_from_file(module_file, module_name_left=module_name_left, using_sys_modules=using_sys_modules),
            ):
                yield type_from_module


def _file_name_to_module_name(file_name: str) -> str:
    if file_name.lower().endswith(".py"):
        file_name = file_name[:-3]
    return file_name
