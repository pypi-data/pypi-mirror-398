#  SPDX-FileCopyrightText: © 2024 Josef Hahn
#  SPDX-License-Identifier: AGPL-3.0-only
"""
Additional terminal support, incl. text layout and styling.
"""
import abc
import copy
import functools
import math
import os
import sys
import typing as t
import xml.etree.ElementTree
import xml.sax.saxutils


class Color:

    def __init__(self):
        self.__rgb256 = None
        self.__bare_ansi_terminal_code = None
        self.__xterm256_terminal_code = None

    def by_html(self, html_color: str) -> "Color":
        def parse(channel):
            part_len = 1 if len(html_color) == 4 else 2
            return int(html_color[1 + channel * part_len :][:part_len], 16)

        return self.by_rgb256(parse(0), parse(1), parse(2))

    def by_rgb256(self, r: float, g: float, b: float) -> "Color":
        result = copy.copy(self)
        result.__rgb256 = (min(max(0, r), 255), min(max(0, g), 255), min(max(0, b), 255))
        return result

    def by_rgb_normed(self, r: float, g: float, b: float) -> "Color":
        return self.by_rgb256(r * 255, g * 255, b * 255)

    def by_bare_ansi_terminal_code(self, code):
        result = copy.copy(self)
        result.__bare_ansi_terminal_code = code
        return result

    def by_xterm256_terminal_code(self, code):
        result = copy.copy(self)
        result.__xterm256_terminal_code = code
        return result

    @functools.lru_cache(maxsize=100)
    def as_rgb256(self) -> tuple[float, float, float]:
        if self.__rgb256:
            return self.__rgb256
        if self.__xterm256_terminal_code is not None:
            return _xterm256_colorspace.index_to_color(self.__xterm256_terminal_code)
        if self.__bare_ansi_terminal_code is not None:
            return _bare_ansi_colorspace.index_to_color(self.__bare_ansi_terminal_code)
        raise ValueError("invalid color")

    def as_rgb_normed(self) -> tuple[float, float, float]:
        r, g, b = self.as_rgb256()
        return r / 255, g / 255, b / 255

    @functools.lru_cache(maxsize=100)
    def as_bare_ansi_terminal_code(self) -> int:
        return (
            _bare_ansi_colorspace.color_to_index(*self.as_rgb256())
            if (self.__bare_ansi_terminal_code is None)
            else self.__bare_ansi_terminal_code
        )

    @functools.lru_cache(maxsize=100)
    def as_xterm256_terminal_code(self) -> int:
        return (
            _xterm256_colorspace.color_to_index(*self.as_rgb256())
            if (self.__xterm256_terminal_code is None)
            else self.__xterm256_terminal_code
        )

    def as_html(self) -> str:
        return "#" + "".join([f"{int(value):02x}" for value in self.as_rgb256()])

    def __str__(self):
        return self.as_html()


class Style:

    def has_key(self, key: str) -> bool:
        return hasattr(self, key)

    def value(self, key) -> t.Any:
        return getattr(self, key)


class _DefaultStyle(Style):
    # TODO https://stackoverflow.com/questions/2507337/how-to-determine-a-terminals-background-color

    def __init__(self):
        self.welcome_text__fg = Color().by_html("#5f87ff")

        self.announcement__fg = Color().by_html("#808080")
        self.announcement_important__fg = Color().by_html("#ff5f00")

        self.section_user__fg = Color().by_html("#b2b2b2")
        self.section_user__bg = Color().by_html("#5f5fff")
        self.user_name__fg = Color().by_html("#bcbcbc")
        self.user_root_name__fg = Color().by_html("#ff005f")
        self.user_hostname__fg = Color().by_html("#b2b2b2")

        self.section_avatar__fg = Color().by_html("#5f5faf")
        self.section_avatar__bg = Color().by_html("#8787ff")

        self.section_cwd__fg = Color().by_html("#333377")
        self.section_cwd__bg = Color().by_html("#afafff")
        self.cwd_prefix__fg = Color().by_html("#5f5f87")

        self.prompt_char__fg = Color().by_html("#afafff")

        self.bar_window_list__fg = Color().by_html("#444444")
        self.bar_window_list__bg = Color().by_html("#b2b2b2")
        self.bar_window_list_active__fg = Color().by_html("#d0d0d0")
        self.bar_window_list_active__bg = Color().by_html("#303030")
        self.bar_info_panel__fg = Color().by_html("#c6c6c6")
        self.bar_info_panel__bg = Color().by_html("#4e4e4e")

        self.command_hint__fg = Color().by_html("#5f8787")


default_style = _DefaultStyle()


class TextFormatter(abc.ABC):

    @abc.abstractmethod
    def escape(self, s: str) -> str:
        pass

    @abc.abstractmethod
    def control_for_fg_color(self, color: "Color") -> str:
        pass

    @abc.abstractmethod
    def control_for_bg_color(self, color: "Color") -> str:
        pass

    @abc.abstractmethod
    def control_for_reset(self) -> str:
        pass


class AnsiEscapedTextFormatter(TextFormatter):

    def __init__(self, *, with_rgb256: bool):
        self.__with_rgb256 = with_rgb256

    def escape(self, s):
        return s

    def control_for_fg_color(self, color):
        return self.__control_for_color(color, 30, 90, 38)

    def control_for_bg_color(self, color):
        return self.__control_for_color(color, 40, 100, 48)

    def control_for_reset(self):
        return "\033[0m"

    def __control_for_color(self, color, bare_block1_begin: int, bare_block2_begin: int, rgb256_code: int):
        if self.__with_rgb256:
            index = _xterm256_colorspace.color_to_index(*color.as_rgb256())
            return f"\033[{rgb256_code};5;{index}m"
        else:
            index = _bare_ansi_colorspace.color_to_index(*color.as_rgb256())
            code = (index + bare_block1_begin) if (index < 8) else (index - 8 + bare_block2_begin)
            return f"\033[{code}m"


class PlainTextFormatter(TextFormatter):

    def escape(self, s):
        return s

    def control_for_fg_color(self, color):
        return ""

    def control_for_bg_color(self, color):
        return ""

    def control_for_reset(self):
        return ""


class Text:

    def __init__(self, krz_shl_doc_xml: str):
        self.__xml = krz_shl_doc_xml

    @staticmethod
    def by_xml(krz_shl_doc_xml: str) -> "Text":
        return Text(krz_shl_doc_xml)

    @staticmethod
    def by_plain_text(text: str, *, smart_strip: bool = True) -> "Text":
        return Text.by_xml(xml.sax.saxutils.escape(Text.__smart_strip(text) if smart_strip else text))

    @staticmethod
    def __smart_strip(s: str) -> str:
        lines = s.split("\n")

        while lines and (not lines[0].strip()):
            lines.pop(0)

        if not lines:
            return ""

        first_line = lines[0]
        base_indentation = first_line[: len(first_line) - len(first_line.strip())]
        base_off = len(base_indentation)

        lines = [(x[base_off:].rstrip() if x.startswith(base_indentation) else x) for x in lines]

        compacting = True
        while compacting:
            compacting = False
            for i_line in range(1, len(lines)):
                line_before_i = lines[i_line - 1]
                line_i = lines[i_line]

                if line_i and line_before_i and line_i[0] not in "-*:.#+=%!?\t ":
                    lines[i_line] = line_before_i + " " + line_i
                    lines.pop(i_line - 1)
                    compacting = True
                    break

                if not line_i and not line_before_i:
                    lines.pop(i_line)
                    compacting = True
                    break

        return "\n".join(lines)

    def __add__(self, other):
        if not isinstance(other, Text):
            raise TypeError(f'can only concatenate {Text.__name__} (not "{type(other).__name__}") to {Text.__name__}')
        return Text.by_xml(self.__xml + other.__xml)

    @property
    def as_xml(self) -> str:
        return self.__xml

    def indent(self, width: int, *, char: str = " ") -> "Text":
        result = ""
        for xml_line in self.__xml.split("\n"):
            xml_line_pre = ""
            while xml_line.startswith("<"):
                i_end = xml_line.index(">")
                xml_line_pre += xml_line[: i_end + 1]
                xml_line = xml_line[i_end + 1 :]
            result += f"{xml_line_pre}{width*char}{xml_line}\n"
        return Text.by_xml(result[:-1])

    def __traverse(self, node_start_func, node_stop_func) -> "Text":
        def visit_node(node: xml.etree.ElementTree.Element) -> None:
            node_start_func(node)
            for child_node in node:
                visit_node(child_node)
            node_stop_func(node)

        root_node = xml.etree.ElementTree.fromstring(f"<x>{self.__xml}</x>")
        visit_node(root_node)
        return Text.by_xml(xml.etree.ElementTree.tostring(root_node).decode()[3:-4])

    def line_wrap_at_maximum_width(self, width: int | None) -> "Text":
        if width is None:
            return self
        if width < 1:
            return Text.by_plain_text("")

        plain_line_width = 0

        def insert_linebreaks(attr: str, node: xml.etree.ElementTree.Element) -> None:
            nonlocal plain_line_width
            i = 0
            while i is not None:
                remaining_width = width - plain_line_width
                satt = getattr(node, attr)
                if satt is None:
                    break
                s = satt[i:]

                if len(s) <= remaining_width:
                    plain_line_width += len(s)
                    break
                else:
                    newline_i = s[:remaining_width].rfind("\n")
                    if newline_i != -1:
                        break_i = newline_i
                        cont_i = newline_i + 1
                    else:
                        space_i = s[:remaining_width].rfind(" ")
                        if space_i != -1:
                            break_i = space_i
                            cont_i = space_i + 1
                        else:
                            break_i = remaining_width
                            cont_i = remaining_width
                    setattr(node, attr, f"{satt[:i+break_i]}\n{satt[i+cont_i:]}")
                    i += cont_i + 1
                    plain_line_width = 0

        return self.__traverse(
            functools.partial(insert_linebreaks, "text"), functools.partial(insert_linebreaks, "tail")
        )

    def format(self, formatter: TextFormatter, *, style: Style = default_style) -> str:
        result = ""
        state_stack = [(None, None)]

        def format_node_start_to_result(node: xml.etree.ElementTree.Element):
            nonlocal result, state_stack
            state_stack.append(list(state_stack[-1]))

            if node.tag == "style":
                key = node.get("key")

                fg_attr = f"{key}__fg"
                if style.has_key(fg_attr):
                    state_stack[-1][0] = style.value(fg_attr)

                bg_attr = f"{key}__bg"
                if style.has_key(bg_attr):
                    state_stack[-1][1] = style.value(bg_attr)

            elif node.tag == "color":
                fg = node.get("fg")
                bg = node.get("bg")
                if fg:
                    state_stack[-1][0] = Color().by_html(fg)
                if bg:
                    state_stack[-1][1] = Color().by_html(bg)

            result += formatter.control_for_reset()
            result += formatter.control_for_fg_color(state_stack[-1][0]) if state_stack[-1][0] else ""
            result += formatter.control_for_bg_color(state_stack[-1][1]) if state_stack[-1][1] else ""
            result += formatter.escape(node.text or "")

        def format_node_stop_to_result(node: xml.etree.ElementTree.Element):
            nonlocal result, state_stack

            state_stack.pop()

            result += formatter.control_for_reset()
            result += formatter.control_for_fg_color(state_stack[-1][0]) if state_stack[-1][0] else ""
            result += formatter.control_for_bg_color(state_stack[-1][1]) if state_stack[-1][1] else ""
            result += formatter.escape(node.tail or "")

        self.__traverse(format_node_start_to_result, format_node_stop_to_result)
        return result + formatter.control_for_reset()


_is_interactive_shell = None


def is_interactive_shell() -> bool:
    global _is_interactive_shell
    if _is_interactive_shell is None:
        try:
            _is_interactive_shell = bool(os.ttyname(sys.stdin.fileno()))
        except IOError:
            _is_interactive_shell = False
    return _is_interactive_shell


def is_superuser():
    return os.geteuid() == 0


def terminal_width(*, fallback_to: int = 80) -> int:
    try:
        return os.get_terminal_size().columns
    except Exception:
        return fallback_to


class _TerminalColorSpace(abc.ABC):

    @abc.abstractmethod
    def color_to_index(self, r: float, g: float, b: float) -> int:
        pass

    @abc.abstractmethod
    def index_to_color(self, idx: int) -> tuple[float, float, float]:
        pass


class _BareAnsiTerminalColorSpace(_TerminalColorSpace):

    def color_to_index(self, r, g, b):
        best_i = None
        best_cost = sys.maxsize
        for i, (i_r, i_g, i_b) in enumerate(self._COLORS):
            cost = math.pow(i_r - r, 2) + math.pow(i_g - g, 2) + math.pow(i_b - b, 2)
            if cost < best_cost:
                best_i, best_cost = i, cost
        return best_i

    def index_to_color(self, idx):
        return self._COLORS[idx]

    _COLORS = (
        (0, 0, 0),
        (128, 0, 0),
        (0, 128, 0),
        (128, 128, 0),
        (0, 0, 128),
        (128, 0, 128),
        (0, 128, 128),
        (192, 192, 192),
        (128, 128, 128),
        (255, 0, 0),
        (0, 255, 0),
        (255, 255, 0),
        (0, 0, 255),
        (255, 0, 255),
        (0, 255, 255),
        (255, 255, 255),
    )


class _XTerm256TerminalColorSpace(_TerminalColorSpace):

    def __color_to_index__colors(self, r, g, b):
        def foo(v):
            if v < self._COLOR_VALUE_BEGIN - self._COLOR_VALUE_STEP / 2:
                return 0
            return (
                self.__color_to_index__helper__channel(
                    v, self._COLOR_SYMBOLS_PER_CHANNEL - 1, self._COLOR_VALUE_BEGIN, self._COLOR_VALUE_STEP
                )
                + 1
            )

        return (
            self._COLOR_INDEX_BEGIN
            + foo(r) * (self._COLOR_SYMBOLS_PER_CHANNEL**2)
            + foo(g) * self._COLOR_SYMBOLS_PER_CHANNEL
            + foo(b)
        )

    def __color_to_index__grayscale(self, r, g, b):
        return (
            self.__color_to_index__helper__channel(
                (r + g + b) / 3,
                self._GRAYSCALE_SYMBOLS_PER_CHANNEL,
                self._GRAYSCALE_VALUE_BEGIN,
                self._GRAYSCALE_VALUE_STEP,
            )
            + self._GRAYSCALE_INDEX_BEGIN
        )

    def __color_to_index__helper__channel(self, val, symbol_count, value_begin, value_step):
        return min(max(0, int((val - value_begin + value_step / 2) / value_step)), symbol_count - 1)

    def __cost(self, c1, c2):
        return sum([d**2 for d in [v1 - v2 for v1, v2 in zip(c1, c2)]])

    def color_to_index(self, r, g, b):
        index_colors = self.__color_to_index__colors(r, g, b)
        index_grayscale = self.__color_to_index__grayscale(r, g, b)

        return (
            index_colors
            if (
                self.__cost(self.index_to_color(index_colors), (r, g, b))
                < self.__cost(self.index_to_color(index_grayscale), (r, g, b))
            )
            else index_grayscale
        )

    def index_to_color(self, idx):

        def color_value(ii, channel, symbols_per_channel, value_begin, value_step):
            val = (ii // symbols_per_channel**channel) % symbols_per_channel
            return 0 if (val == 0) else ((val - 1) * value_step + value_begin)

        i = idx - self._GRAYSCALE_INDEX_BEGIN

        if i >= 0:

            col_val = color_value(i + 1, 0, sys.maxsize, self._GRAYSCALE_VALUE_BEGIN, self._GRAYSCALE_VALUE_STEP)
            return col_val, col_val, col_val

        else:
            i = idx - self._COLOR_INDEX_BEGIN

        if i >= 0:

            return (
                color_value(i, 2, self._COLOR_SYMBOLS_PER_CHANNEL, self._COLOR_VALUE_BEGIN, self._COLOR_VALUE_STEP),
                color_value(i, 1, self._COLOR_SYMBOLS_PER_CHANNEL, self._COLOR_VALUE_BEGIN, self._COLOR_VALUE_STEP),
                color_value(i, 0, self._COLOR_SYMBOLS_PER_CHANNEL, self._COLOR_VALUE_BEGIN, self._COLOR_VALUE_STEP),
            )

        else:
            return _bare_ansi_colorspace.index_to_color(idx)

    _COLOR_INDEX_BEGIN = 16
    _COLOR_VALUE_BEGIN = 95
    _COLOR_VALUE_STEP = 40
    _COLOR_VALUE_END = 255
    _GRAYSCALE_INDEX_BEGIN = 232
    _GRAYSCALE_VALUE_BEGIN = 8
    _GRAYSCALE_VALUE_STEP = 10
    _GRAYSCALE_VALUE_END = 238
    _END_INDEX_BEGIN = 256
    _COLOR_SYMBOLS_PER_CHANNEL = int((_COLOR_VALUE_END - _COLOR_VALUE_BEGIN) / _COLOR_VALUE_STEP) + 1 + 1
    _GRAYSCALE_SYMBOLS_PER_CHANNEL = int((_GRAYSCALE_VALUE_END - _GRAYSCALE_VALUE_BEGIN) / _GRAYSCALE_VALUE_STEP) + 1


_bare_ansi_colorspace = _BareAnsiTerminalColorSpace()
_xterm256_colorspace = _XTerm256TerminalColorSpace()
