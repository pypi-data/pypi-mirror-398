__all__ = [
    "utils_len",
    "utils_random",
    "utils_get_name",
    "utils_get_id",
    "utils_get_roles",
]

from discord import Message, Role, TextChannel, VoiceChannel, CategoryChannel, ForumChannel, Thread, Member, Guild
from discord.utils import get
from typing import Union, Optional
from enum import StrEnum
from random import random, choice


class DiscordType(StrEnum):
    MEMBER = "member"
    ROLE = "role"
    TEXT_CHANNEL = "text_channel"
    VOICE_CHANNEL = "voice_channel"
    CATEGORY_CHANNEL = "category_channel"
    FORUM_CHANNEL = "forum_channel"
    THREAD = "thread"
    UNKNOWN = "unknown"

def utils_what_discord_type_is(ctx: Union[Message, Guild], value: int) -> tuple[str, Union[Member, Role, TextChannel, VoiceChannel, CategoryChannel, ForumChannel, Thread, None]]:
    """
    Return an enum of what the value is (str, int, list, Member, Role, Channel, etc.)
    :param ctx:
    :param value:
    :return:
    """
    guild = ctx if isinstance(ctx, Guild) else ctx.guild

    if member := guild.get_member(value):
        return DiscordType.MEMBER, member

    elif role := guild.get_role(value):
        return DiscordType.ROLE, role

    elif (channel := guild.get_channel(value)) and isinstance(channel, TextChannel):
        return DiscordType.TEXT_CHANNEL, channel

    elif (channel := guild.get_channel(value)) and isinstance(channel, VoiceChannel):
        return DiscordType.VOICE_CHANNEL, channel

    elif (channel := guild.get_channel(value)) and isinstance(channel, CategoryChannel):
        return DiscordType.CATEGORY_CHANNEL, channel

    elif (channel := guild.get_channel(value)) and isinstance(channel, ForumChannel):
        return DiscordType.FORUM_CHANNEL, channel

    elif (channel := guild.get_channel(value)) and isinstance(channel, Thread):
        return DiscordType.THREAD, channel
    else:
        return DiscordType.UNKNOWN, None

async def utils_len(ctx: Message, value):
    """
    Return the length of a list, or a string
    :param value:
    :return:
    """
    from ..._DshellParser.ast_nodes import ListNode
    if not isinstance(value, (str, ListNode)):
        raise TypeError(f"value must be a list or a string in len command, not {type(value)}")

    return len(value)

async def utils_random(ctx: Message, value: Optional["ListNode"] = None):
    """
    Return a random element from a list, or a random integer between 0 and value
    :param value:
    :return:
    """
    from ..._DshellParser.ast_nodes import ListNode
    if value is not None and not isinstance(value, ListNode):
        raise TypeError(f"value must be a list in random command, not {type(value)}")

    if value is None:
        return random()
    return choice(value)

async def utils_get_name(ctx : Message, value: int) -> Union[str, None]:
    """
    Return the name of a role, member, or channel.
    If not found, return None.
    :param value:
    :return:
    """

    if not isinstance(value, int):
        raise TypeError(f"value must be an int in name command, not {type(value)}")

    guild = ctx.guild
    result = None

    if role := guild.get_role(value):
        result = role.name

    elif member := guild.get_member(value):
        result = member.name

    if channel := guild.get_channel(value) :
        result = channel.name

    return result

async def utils_get_id(ctx : Message, value: str) -> Union[int, None]:
    """
    Return the id of a role, member, or channel.
    If not found, return None.
    :param value:
    :return:
    """

    if not isinstance(value, str):
        raise TypeError(f"value must be a str in id command, not {type(value)}")

    guild = ctx.guild
    result = None

    if role := get(guild.roles, name=value):
        result = role.id

    elif member := get(guild.members, name=value):
        result = member.id

    if channel := get(guild.channels, name=value) :
        result = channel.id

    return result

async def utils_get_roles(ctx: Message, value: int):
    """
    Return the roles of a member.
    :param value:
    :return:
    """

    if not isinstance(value, int):
        raise TypeError(f"value must be an int in roles command, not {type(value)}")

    guild = ctx.guild

    what_is, member = utils_what_discord_type_is(ctx, value)

    if what_is == DiscordType.UNKNOWN:
        raise ValueError(f"{value} member not found in guild {guild.name}")

    if what_is != DiscordType.MEMBER:
        raise TypeError(f"value must be a member id in roles command, not {what_is}")

    from ..._DshellParser.ast_nodes import ListNode
    return ListNode([i.id for i in member.roles])