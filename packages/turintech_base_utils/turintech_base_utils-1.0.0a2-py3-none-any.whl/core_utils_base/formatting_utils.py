"""
This module contains useful methods for the representation of different data structures.
"""

# pylint: disable=R0914
#        R0914: Too many local variables (17/15) (too-many-locals)
# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from typing import Dict, List, Optional, Union

from pydantic import BaseModel

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = [
    "DEFAULT_LINE_SIZE",
    "get_start_end",
    "get_list_formatter",
    "get_dict_formatter",
    "get_data_formatter",
    "get_time_formatter",
]

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

DEFAULT_LINE_SIZE: int = 120
DEFAULT_NL_START: bool = True
DEFAULT_NL_END: bool = False


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def get_start_end(
    title: str,
    print_char: str = "-",
    size: int = DEFAULT_LINE_SIZE,
    nl_start: bool = DEFAULT_NL_START,
    nl_end: bool = DEFAULT_NL_END,
):
    """
    :return:
        start: ------------------------------- <title> -------------------------------
          end: -----------------------------------------------------------------------
    """
    title_aux = (f" {title} " if title else "").center(size, print_char)
    start = ("\n" if nl_start else "") + title_aux
    end = print_char * len(title_aux) + ("\n" if nl_end else "")
    return start, end


def get_list_formatter(
    data: list,
    title: Optional[str] = None,
    indent: int = 1,
    print_char: str = "-",
    size: int = DEFAULT_LINE_SIZE,
    nl_start: bool = DEFAULT_NL_START,
    nl_end: bool = DEFAULT_NL_END,
) -> str:
    """
    :return:
            - <value1>
            - <value2>
            ...
            - <valueN>
    """
    start, end = (
        get_start_end(title=title, print_char=print_char, size=size, nl_start=nl_start, nl_end=False)
        if title
        else ("", "")
    )
    union = "\n" + "    " * indent + "- "
    data_str = start
    if data:
        data_str += union + union.join([str(value.dict() if isinstance(value, BaseModel) else value) for value in data])
    return data_str + ("\n" + end if end else "") + ("\n" if nl_end else "")


def get_dict_formatter(
    data: Dict,
    title: Optional[str] = None,
    indent: int = 1,
    print_char: str = "-",
    size: int = DEFAULT_LINE_SIZE,
    nl_start: bool = DEFAULT_NL_START,
    nl_end: bool = DEFAULT_NL_END,
) -> str:
    """
    :return:
        ------------------------------- <title> -------------------------------
            - <key1>                  : <value1>
            - <key3>                  : <value2>
            ...
            - <keyN>                  : <valueN>
        -----------------------------------------------------------------------
    """
    start, end = (
        get_start_end(title=title, print_char=print_char, size=size, nl_start=nl_start, nl_end=nl_end)
        if title
        else ("", "")
    )

    union = "\n" + "    " * indent + "- "
    data_str = start
    if data:
        keys_str = [str(key) for key in data]
        key_size = len(max(keys_str, key=len)) + 1
        data_str += union + union.join(
            [
                f"{key:<{key_size}}: {value.dict() if isinstance(value, BaseModel) else value}"
                for key, value in data.items()
            ]
        )
    return data_str + "\n" + end


def get_data_formatter(
    data: Union[Dict, List],
    title: Optional[str] = None,
    indent: int = 1,
    print_char: str = "-",
    levels: int = 2,
    size: int = DEFAULT_LINE_SIZE,
    nl_start: bool = DEFAULT_NL_START,
    nl_end: bool = True,
) -> str:
    """
    :return:
        ------------------------------- <title> -------------------------------
            - <value1>
                - <key1> : <value1>
                - <key2> : <value2>
            - <value2>
                - <key3> :
                    - <value3>
        -----------------------------------------------------------------------
    """
    args = {"print_char": print_char, "size": size, "nl_start": nl_start, "nl_end": nl_end}
    start, end = get_start_end(title=title, **args) if title else ("", "")  # type: ignore
    args["nl_start"] = args["nl_end"] = False
    union: str = "\n" + "    " * indent + "- "

    data_str: str = start
    if data:
        data_str = _indent_text(indent, levels, data, union, data_str, args)
    elif not isinstance(data, str) and data is not None:
        # In the case of numerical values, we want to display 0 or 0.0
        data_str = str(data)
    return data_str + ("\n" if nl_end else "") + end


def _indent_text(indent: int, levels: int, data: Union[Dict, List], union: str, start: str, args: dict) -> str:
    data_str = start
    if indent > levels or not isinstance(data, (Dict, List)):
        return str(data)
    if isinstance(data, Dict):
        key_size = len(max(data.keys(), key=len)) + 1 if data.keys() else 0
        for key, value in data.items():
            _value = get_data_formatter(data=value, levels=levels, indent=indent + 1, **args)  # type: ignore
            data_str += f"{union}{key:<{key_size}}: {_value}"
    else:
        for value in data:
            if not isinstance(value, (Dict, List)):
                data_str += union
            data_str += get_data_formatter(data=value, levels=levels, indent=indent, **args)  # type: ignore
    return data_str


def get_title(title: Union[str, List[str]], print_char: str = "─", max_len: int = 80, with_end: bool = True):
    """get_title(title="", print_char="-", with_end=False, max_len=70) #

    -------------------------------------------------------------------- # #
    --------------------------------------------------------------------

    get_title(title="This is an example", max_len=70)
        # ────────────────────────────────────────────────────────────────── #
        #                         This is an example                         #
        # ────────────────────────────────────────────────────────────────── #

    """
    init_line = "# "
    end_line = " #" if with_end else ""

    print_char_len = max_len - len(init_line) - len(end_line)
    print_char_line = init_line + print_char * print_char_len + end_line

    title_line = ""
    for _title in [title] if isinstance(title, str) else title:
        _title_line = init_line + _title.center(max_len - len(init_line) - len(end_line), " ") + end_line
        title_line = title_line + ("\n" if title_line else "") + _title_line

    return f"{print_char_line}\n{title_line}\n{print_char_line}"


def get_title_line(title: str, print_char: str = "─", max_len: int = 80, with_end: bool = True):
    """
    get_title_line(title="imports", max_len=70) # ─────────────────────── This is an example ─────────────────────── #
    """
    init_line = "# "
    end_line = " #" if with_end else ""
    title_aux = f" {title} " if title else ""
    return init_line + title_aux.center(max_len - len(init_line) - len(end_line), print_char) + end_line


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def get_time_formatter(total_time: float) -> str:
    return (
        f"{total_time * 1000:.4f} ms"
        if total_time < 1
        else f"{total_time:.4f} s"
        if total_time < 60
        else f"{total_time / 60:.4f} m"
    )
