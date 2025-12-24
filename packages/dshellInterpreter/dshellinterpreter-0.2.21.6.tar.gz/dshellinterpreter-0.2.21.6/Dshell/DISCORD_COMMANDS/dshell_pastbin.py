from discord import Message
from requests import get

__all__ = [
    'dshell_get_pastbin'
]


async def dshell_get_pastbin(ctx: Message, code: str) -> "ListNode":
    """
    Get a pastbin from a code snippet.
    """
    if not isinstance(code, str):
        raise Exception(f'Code must be a string, not {type(code)} !')

    from .._DshellParser.ast_nodes import ListNode

    content = ListNode([])  # Initialize content to an empty string

    with get(f"https://pastebin.com/raw/{code}", stream=True, timeout=10) as response:

        if not response.ok:
            raise Exception(f"Failed to retrieve pastbin with code {code} !")

        for line in response.iter_lines(decode_unicode=True, chunk_size=512):
            content.add(line)

    return content
