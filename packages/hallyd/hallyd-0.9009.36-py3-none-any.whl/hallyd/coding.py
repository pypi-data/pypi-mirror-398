#  SPDX-FileCopyrightText: © 2021 Josef Hahn
#  SPDX-License-Identifier: AGPL-3.0-only
"""
Automated editing of Python code.
"""
import abc
import ast
import re
import typing as t

import hallyd.fs as _fs


TBD_TAG = "TO" "DO"


class Editor:

    class _Handle(abc.ABC):

        def __init__(self, editor):
            super().__init__()
            self.__editor = editor

        @property
        def _editor(self):
            return self.__editor

        @property
        @abc.abstractmethod
        def _ast(self) -> ast.AST | None:
            pass

    # noinspection PyUnresolvedReferences
    class _WithCodePositionsHandleMixin:

        @property
        def starts_at_position(self):
            return len("\n".join(self._editor.code.split("\n")[: self._ast.lineno - 1])) + 1

        @property
        def ends_at_position(self):
            return len("\n".join(self._editor.code.split("\n")[: self._ast.end_lineno])) + 1

    # noinspection PyUnresolvedReferences
    class _WithDecorationSupportHandleMixin:

        def add_decoration(self, code: str):
            i = self._editor.code.rfind("\n", 0, self.starts_at_position)
            self._editor.code = (
                self._editor.code[:i] + "\n" + self._editor.indentation + code.strip() + self._editor.code[i:]
            )

        def remove_decoration(self, idx):
            i, j = self.__decoration_ast_to_code_indexes(self._ast.decorator_list[idx])
            self._editor.code = self._editor.code[:i] + self._editor.code[j:]

        @property
        def decorations(self):
            result = []
            for decoration_ast in self._ast.decorator_list:
                i, j = self.__decoration_ast_to_code_indexes(decoration_ast)
                result.append(self._editor.code[i : j + 1].strip())
            return result

        def __decoration_ast_to_code_indexes(self, decoration_ast):
            i = len("\n".join(self._editor.code.split("\n")[: decoration_ast.lineno - 1]))
            # TODO dedup split&indexing stuff for lineno
            j = len("\n".join(self._editor.code.split("\n")[: decoration_ast.end_lineno]))
            return i, j

    # noinspection PyUnresolvedReferences
    class _RemovableHandleMixin:

        def remove(self):
            self._editor.code = (
                self._editor.code[: self.starts_at_position].rstrip()
                + "\n"
                + self._editor.code[self.ends_at_position :]
            )

    class _ClassHandle(
        _Handle, _WithCodePositionsHandleMixin, _WithDecorationSupportHandleMixin, _RemovableHandleMixin
    ):

        def __init__(self, editor, class_name):
            super().__init__(editor)
            self.__name = class_name

        @property
        def _ast(self) -> ast.ClassDef | None:
            # noinspection PyProtectedMember
            for child_ast in self._editor._ast.body:
                if isinstance(child_ast, ast.ClassDef) and child_ast.name == self.name:
                    return child_ast

        @property
        def name(self) -> str:
            return self.__name

        def add_method(self, body: str):
            code = self._editor.code
            ends_at_position = self.ends_at_position
            # noinspection PyProtectedMember
            indented_body = "\n".join(
                [self._editor.indentation + line for line in self._editor._fix_body(body).split("\n")]
            )
            self._editor.code = code[:ends_at_position] + "\n" + indented_body + "\n\n" + code[ends_at_position:]
            return self.method_by_name(Editor._function_name_from_body(body))

        def method_by_name(self, method_name):
            return Editor._FunctionHandle(self._editor, method_name, self)

        @property
        def methods(self):
            result = []
            for child_ast in self._ast.body:
                if isinstance(child_ast, ast.FunctionDef):
                    result.append(self.method_by_name(child_ast.name))
            return result

    class _FunctionHandle(
        _Handle, _WithCodePositionsHandleMixin, _WithDecorationSupportHandleMixin, _RemovableHandleMixin
    ):

        def __init__(self, editor: "Editor", function_name: str, class_handle=None):
            super().__init__(editor)
            self.__name = function_name
            self.__class_handle = class_handle

        @property
        def name(self) -> str:
            return self.__name

        @property
        def _ast(self) -> ast.FunctionDef | None:
            # noinspection PyProtectedMember
            base_ast = self.__class_handle._ast if self.__class_handle else self._editor._ast
            for child_ast in base_ast.body:
                if isinstance(child_ast, ast.FunctionDef) and child_ast.name == self.name:
                    return child_ast

    def __init__(self, srcfile: _fs.Path):
        self.__srcfile = srcfile
        self.__code = None

    def class_by_name(self, class_name: str) -> _ClassHandle:
        return Editor._ClassHandle(self, class_name)

    @property
    def path(self) -> _fs.Path:
        return self.__srcfile

    @property
    def code(self) -> str:
        return self.__code

    @code.setter
    def code(self, code):
        self.__code = code.rstrip() + "\n"

    @property
    def indentation(self) -> str:
        return self.__indentation_for_code_fragment(self.code)

    def __enter__(self):
        self.code = self.__srcfile.read_text() if self.__srcfile.exists() else ""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.__srcfile.parent.make_dir(until=_fs.Path("/TODO/.."), exist_ok=True, readable_by_all=True)
            self.__srcfile.set_data(self.code, readable_by_all=True)
        self.__code = None

    @property
    def _ast(self) -> ast.AST:
        return ast.parse(self.code)

    @staticmethod
    def _function_name_from_body(body):
        # noinspection PyUnresolvedReferences
        return ast.parse(body).body[0].name

    def add_import(self, module_name: str):
        self.code = f"import {module_name}\n" + self.code

    def add_class(self, class_name, *, derived_from=None, docstring=f"{TBD_TAG} add some documentation here"):
        derived_from_str = f"({derived_from})" if derived_from else ""
        docstring_code = f'"""{repr(docstring)[1:-1]}"""'
        self.code += f"\n\nclass {class_name}{derived_from_str}:\n{self.indentation}{docstring_code}"
        return Editor._ClassHandle(self, class_name)

    def add_function(self, body):
        self.code += "\n\n" + self._fix_body(body)
        return Editor._FunctionHandle(self, self._function_name_from_body(body))

    def _fix_body(self, body: str) -> str:
        body_indentation = self.__indentation_for_code_fragment(body)
        result = []
        indent_by_base = 0
        line = body  # TODO odd
        while line.startswith(body_indentation):
            indent_by_base += 1
            line = line[len(body_indentation) :]
        for line in body.strip().split("\n"):
            indent_by = -indent_by_base
            while line.startswith(body_indentation):
                indent_by += 1
                line = line[len(body_indentation) :]
            if indent_by < 0:
                raise ValueError("invalid indentation in body")
            result.append((indent_by * self.indentation) + line)
        return "\n".join(result)

    @staticmethod
    def __indentation_for_code_fragment(code: str) -> str:
        for line in code.split("\n"):
            match = re.match(r"(\s+)\S+", line)
            if match:
                return match.group(1)
        return 4 * " "
