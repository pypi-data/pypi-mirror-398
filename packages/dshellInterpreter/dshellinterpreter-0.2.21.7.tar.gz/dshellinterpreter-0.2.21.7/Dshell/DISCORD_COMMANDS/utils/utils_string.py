__all__ = [
    "utils_split_string",
    "utils_upper_string",
    "utils_lower_string",
    "utils_title_string",
    "utils_strip_string",
    "utils_replace_string",
    "utils_regex_findall",
    "utils_regex_sub",
    "utils_regex_search"
]

from discord import Message
from re import search, findall, sub

async def utils_split_string(ctx: Message, value: str, separator: str = ' ') -> "ListNode":
    """
    Split a string into a list of strings using the specified separator.
    :param value:
    :param separator:
    :return:
    """

    if not isinstance(value, str):
        raise TypeError(f"value must be a str in split command, not {type(value)}")

    if not isinstance(separator, str):
        raise TypeError(f"separator must be a str in split command, not {type(separator)}")

    from ..._DshellParser.ast_nodes import ListNode

    return ListNode(value.split(separator))

async def utils_upper_string(ctx: Message, value: str) -> str:
    """
    Convert a string to uppercase.
    :param value:
    :return:
    """

    if not isinstance(value, str):
        raise TypeError(f"value must be a str in upper command, not {type(value)}")

    return value.upper()

async def utils_lower_string(ctx: Message, value: str) -> str:
    """
    Convert a string to lowercase.
    :param value:
    :return:
    """

    if not isinstance(value, str):
        raise TypeError(f"value must be a str in lower command, not {type(value)}")

    return value.lower()

async def utils_title_string(ctx: Message, value: str) -> str:
    """
    Convert a string to title case.
    :param value:
    :return:
    """

    if not isinstance(value, str):
        raise TypeError(f"value must be a str in title command, not {type(value)}")

    return value.title()

async def utils_strip_string(ctx: Message, value: str) -> str:
    """
    Strip whitespace from the beginning and end of a string.
    :param value:
    :return:
    """

    if not isinstance(value, str):
        raise TypeError(f"value must be a str in strip command, not {type(value)}")

    return value.strip()

async def utils_replace_string(ctx: Message, value: str, old: str, new: str) -> str:
    """
    Replace all occurrences of old with new in a string.
    :param value:
    :param old:
    :param new:
    :return:
    """

    if not isinstance(value, str):
        raise TypeError(f"value must be a str in replace command, not {type(value)}")

    if not isinstance(old, str):
        raise TypeError(f"old must be a str in replace command, not {type(old)}")

    if not isinstance(new, str):
        raise TypeError(f"new must be a str in replace command, not {type(new)}")

    return value.replace(old, new)

async def utils_regex_findall(ctx: Message, regex: str, content: str = None) -> "ListNode":
    """
    Find all occurrences of a regex in a string.
    :param regex:
    :param content:
    :return:
    """

    if not isinstance(regex, str):
        raise Exception(f"Regex must be a string, not {type(regex)}!")

    if content is not None and not isinstance(content, str):
        raise Exception(f"Content must be a string, not {type(content)}!")

    from ..._DshellParser.ast_nodes import ListNode

    return ListNode(findall(regex, content if content is not None else ctx.content))


async def utils_regex_sub(ctx: Message, regex: str, replace: str, content: str = None) -> str:
    """
    Replace all occurrences of a regex in a string with a replacement string.
    :param regex:
    :param replace:
    :param content:
    :return:
    """

    if not isinstance(regex, str):
        raise Exception(f"Regex must be a string, not {type(regex)}!")

    if not isinstance(replace, str):
        raise Exception(f"Replacement must be a string, not {type(replace)}!")

    if content is not None and not isinstance(content, str):
        raise Exception(f"Content must be a string, not {type(content)}!")

    return sub(regex, replace, content if content is not None else ctx.content)

async def utils_regex_search(ctx: Message, regex: str, content: str = None) -> str:
    """
    Search for a regex in a string.
    :param regex:
    :param content:
    :return:
    """

    if not isinstance(regex, str):
        raise Exception(f"Regex must be a string, not {type(regex)}!")

    if content is not None and not isinstance(content, str):
        raise Exception(f"Content must be a string, not {type(content)}!")

    result = search(regex, content if content is not None else ctx.content)

    return result.group() if result else ''