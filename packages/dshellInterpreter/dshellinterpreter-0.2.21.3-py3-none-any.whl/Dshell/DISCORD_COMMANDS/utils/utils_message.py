from discord import Message, PartialMessage, AllowedMentions
from typing import Union
from re import search

from ..._DshellInterpreteur.cached_messages import dshell_cached_messages

def utils_get_message(ctx: Message, message: Union[int, str]) -> Union[PartialMessage, Message]:
    """
    Returns the message object of the specified message ID or link.
    Message is only available in the same server as the command and in the same channel.
    If the message is a link, it must be in the format: https://discord.com/channels/{guild_id}/{channel_id}/{message_id}
    """
    cached_messages = dshell_cached_messages.get()

    if isinstance(message, int):
        if message in cached_messages:
            return cached_messages[message]

        cached_messages[message] = ctx.channel.get_partial_message(message)
        dshell_cached_messages.set(cached_messages)
        return cached_messages[message]

    elif isinstance(message, str):
        match = search(r'https://discord\.com/channels/(\d+)/(\d+)/(\d+)', message)
        if not match:
            raise Exception("Invalid message link format. Use a valid Discord message link.")
        guild_id = int(match.group(1))
        channel_id = int(match.group(2))
        message_id = int(match.group(3))

        if guild_id != ctx.guild.id:
            raise Exception("The message must be from the same server as the command !")

        cached_messages[message_id] = ctx.guild.get_channel(channel_id).get_partial_message(message_id)
        dshell_cached_messages.set(cached_messages)
        return cached_messages[message_id]

    raise Exception(f"Message must be an integer or a string, not {type(message)} !")


def utils_autorised_mentions(global_mentions: bool = None,
                            everyone_mention: bool = True,
                            roles_mentions: bool = True,
                            users_mentions: bool = True,
                            reply_mention: bool = False) -> Union[bool, 'AllowedMentions']:
    """
    Returns the AllowedMentions object based on the provided parameters.
    If global_mentions is set to True or False, it overrides all other parameters.
    """

    from discord import AllowedMentions

    if global_mentions is not None and not isinstance(global_mentions, bool):
        raise Exception(f'Mention parameter must be a boolean or None, not {type(global_mentions)} !')

    if not isinstance(everyone_mention, bool):
        raise Exception(f'Everyone mention parameter must be a boolean, not {type(everyone_mention)} !')

    if not isinstance(roles_mentions, bool):
        raise Exception(f'Roles mention parameter must be a boolean, not {type(roles_mentions)} !')

    if not isinstance(users_mentions, bool):
        raise Exception(f'Users mention parameter must be a boolean, not {type(users_mentions)} !')

    if not isinstance(reply_mention, bool):
        raise Exception(f'Reply mention parameter must be a boolean, not {type(reply_mention)} !')

    if global_mentions is True:
        return AllowedMentions.all()

    elif global_mentions is False:
        return AllowedMentions.none()

    else:
        return AllowedMentions(everyone=everyone_mention,
                               roles=roles_mentions,
                               users=users_mentions,
                               replied_user=reply_mention)
