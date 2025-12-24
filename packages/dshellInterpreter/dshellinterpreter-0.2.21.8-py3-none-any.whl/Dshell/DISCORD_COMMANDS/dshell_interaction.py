__all__ = [
    'dshell_respond_interaction',
    'dshell_defer_interaction',
    'dshell_delete_original_message'
]

from types import NoneType
from discord import Interaction, Embed, AllowedMentions
from pycordViews import EasyModifiedViews

from .utils.utils_message import utils_autorised_mentions

async def dshell_respond_interaction(ctx: Interaction,
                                     content: str = None,
                                     delete=None,
                                     global_mentions: bool = None,
                                     everyone_mention: bool = True,
                                     roles_mentions: bool = True,
                                     users_mentions: bool = True,
                                     reply_mention: bool = False,
                                     hide: bool = False,
                                     embeds=None,
                                     view=None) -> int:
    """
    Responds to a message interaction on Discord
    """

    if not isinstance(ctx, Interaction):
        raise Exception(f'Respond to an interaction must be used in an interaction context, not {type(ctx)} !')

    if delete is not None and not isinstance(delete, (int, float)):
        raise Exception(f'Delete parameter must be a number (seconds) or None, not {type(delete)} !')

    if not isinstance(hide, bool):
        raise Exception(f'Hide parameter must be a boolean, not {type(hide)} !')

    allowed_mentions = utils_autorised_mentions(global_mentions,
                                                everyone_mention,
                                                roles_mentions,
                                                users_mentions,
                                                reply_mention)

    from .._DshellParser.ast_nodes import ListNode

    if not isinstance(embeds, (ListNode, Embed, NoneType)):
        raise Exception(f'Embeds must be a list of Embed objects or a single Embed object, not {type(embeds)} !')

    if embeds is None:
        embeds = ListNode([])

    elif isinstance(embeds, Embed):
        embeds = ListNode([embeds])

    if not isinstance(view, (EasyModifiedViews, NoneType)):
        raise Exception(f'View must be an UI bloc or None, not {type(view)} !')

    sended_message = await ctx.response.send_message(
                                     content=str(content),
                                     ephemeral=hide,
                                     allowed_mentions=allowed_mentions,
                                     delete_after=delete,
                                     embeds=embeds,
                                     view=view)

    return sended_message.id

async def dshell_defer_interaction(ctx: Interaction) -> bool:
    """
    Defer a message interaction on Discord
    """

    if not isinstance(ctx, Interaction):
        raise Exception(f'Respond to an interaction must be used in an interaction context, not {type(ctx)} !')

    await ctx.response.defer()

    return True

async def dshell_delete_original_message(ctx: Interaction) -> int:
    """
    Delete the original message of an interaction on Discord
    """

    if not isinstance(ctx, Interaction):
        raise Exception(f'Respond to an interaction must be used in an interaction context, not {type(ctx)} !')

    await ctx.delete_original_message()

    return ctx.message.id
