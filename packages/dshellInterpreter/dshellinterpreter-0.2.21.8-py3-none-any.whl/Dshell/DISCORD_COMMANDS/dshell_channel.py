from asyncio import sleep
from re import search
from typing import Union

from discord import MISSING, PermissionOverwrite, Member, Role, Message, CategoryChannel, PartialMessage, VoiceChannel
from discord.utils import _MissingSentinel

from .utils.utils_message import utils_get_message
from .utils.utils_thread import utils_get_thread

__all__ = [
    'dshell_get_channel',
    'dshell_get_channels',
    'dshell_get_thread',
    'dshell_get_channels_in_category',
    'dshell_create_text_channel',
    'dshell_create_thread_message',
    'dshell_delete_channel',
    'dshell_delete_channels',
    'dshell_delete_thread',
    'dshell_create_voice_channel',
    'dshell_edit_text_channel',
    'dshell_edit_voice_channel',
    'dshell_edit_thread',
    'dshell_create_category',
    'dshell_edit_category',
    'dshell_delete_category',
    'dshell_get_channel_category_id',
    'dshell_get_channel_nsfw',
    'dshell_get_channel_slowmode',
    'dshell_get_channel_topic',
    'dshell_get_channel_threads',
    'dshell_get_channel_position',
    'dshell_get_channel_url',
    'dshell_get_channel_voice_members',
]


async def dshell_get_channel(ctx: Message, name):
    """
    Returns the channel object of the channel where the command was executed or the specified channel.
    """

    if isinstance(name, str):
        return next((c.id for c in ctx.channel.guild.channels if c.name == name), None)

    raise Exception(f"Channel must be an integer or a string, not {type(name)} !")


async def dshell_get_channels(ctx: Message, name=None, regex=None):
    """
    Returns a list of channels with the same name and/or matching the same regex.
    If neither is set, it will return all channels in the server.
    """
    if name is not None and not isinstance(name, str):
        raise Exception(f"Name must be a string, not {type(name)} !")

    if regex is not None and not isinstance(regex, str):
        raise Exception(f"Regex must be a string, not {type(regex)} !")

    from .._DshellParser.ast_nodes import ListNode
    channels = ListNode([])

    for channel in ctx.channel.guild.channels:
        if name is not None and channel.name == str(name):
            channels.add(channel.id)

        elif regex is not None and search(regex, channel.name):
            channels.add(channel.id)

    return channels

async def dshell_get_channels_in_category(ctx: Message, category=None, name=None, regex=None):
    """
    Returns a list of channels in a specific category with the same name and/or matching the same regex.
    If neither is set, it will return all channels in the specified category.
    """

    if category is None and ctx.channel.category is not None:
        category = ctx.channel.category.id

    if category is None:
        raise Exception("Category must be specified !")

    if not isinstance(category, int):
        raise Exception(f"Category must be an integer, not {type(category)} !")

    if name is not None and not isinstance(name, str):
        raise Exception(f"Name must be a string, not {type(name)} !")

    if regex is not None and not isinstance(regex, str):
        raise Exception(f"Regex must be a string, not {type(regex)} !")

    from .._DshellParser.ast_nodes import ListNode
    channels = ListNode([])

    category_channel = ctx.channel.guild.get_channel(category)
    if category_channel is None or not hasattr(category_channel, 'channels'):
        raise Exception(f"Category {category} not found or does not contain channels !")

    for channel in category_channel.channels:
        if name is not None and channel.name == str(name):
            channels.add(channel.id)

        elif regex is not None and search(regex, channel.name):
            channels.add(channel.id)

    return channels

async def dshell_create_text_channel(ctx: Message,
                                     name,
                                     category=None,
                                     position=MISSING,
                                     slowmode=MISSING,
                                     topic=MISSING,
                                     nsfw=MISSING,
                                     permissions: dict[Union[Member, Role], PermissionOverwrite] = MISSING,
                                     reason=None):
    """
    Creates a text channel on the server
    """

    if not isinstance(position, (_MissingSentinel, int)):
        raise Exception(f"Position must be an integer, not {type(position)} !")

    if not isinstance(slowmode, (_MissingSentinel, int)):
        raise Exception(f"Slowmode must be an integer, not {type(slowmode)} !")

    if not isinstance(topic, (_MissingSentinel, str)):
        raise Exception(f"Topic must be a string, not {type(topic)} !")

    if not isinstance(nsfw, (_MissingSentinel, bool)):
        raise Exception(f"NSFW must be a boolean, not {type(nsfw)} !")

    channel_category = ctx.channel.category if category is None else ctx.channel.guild.get_channel(category)

    created_channel = await ctx.guild.create_text_channel(str(name),
                                                          category=channel_category,
                                                          position=position,
                                                          slowmode_delay=slowmode,
                                                          topic=topic,
                                                          nsfw=nsfw,
                                                          overwrites=permissions,
                                                          reason=reason)

    return created_channel.id


async def dshell_create_voice_channel(ctx: Message,
                                      name,
                                      category=None,
                                      position=MISSING,
                                      bitrate=MISSING,
                                      permissions: dict[Union[Member, Role], PermissionOverwrite] = MISSING,
                                      reason=None):
    """
    Creates a voice channel on the server
    """
    if not isinstance(position, (_MissingSentinel, int)):
        raise Exception(f"Position must be an integer, not {type(position)} !")

    if not isinstance(bitrate, (_MissingSentinel, int)):
        raise Exception(f"Bitrate must be an integer, not {type(bitrate)} !")

    channel_category = ctx.channel.category if category is None else ctx.channel.guild.get_channel(category)

    created_channel = await ctx.guild.create_voice_channel(str(name),
                                                           category=channel_category,
                                                           position=position,
                                                           bitrate=bitrate,
                                                           overwrites=permissions,
                                                           reason=reason)

    return created_channel.id


async def dshell_delete_channel(ctx: Message, channel=None, reason=None, timeout=0):
    """
    Deletes a channel.
    You can add a waiting time before it is deleted (in seconds)
    """
    if not isinstance(timeout, int):
        raise Exception(f'Timeout must be an integer, not {type(timeout)} !')

    channel_to_delete = ctx.channel if channel is None else ctx.channel.guild.get_channel(channel)

    if channel_to_delete is None:
        raise Exception(f"Channel {channel} not found !")

    await sleep(timeout)

    await channel_to_delete.delete(reason=reason)

    return channel_to_delete.id


async def dshell_delete_channels(ctx: Message, name=None, regex=None, reason=None):
    """
    Deletes all channels with the same name and/or matching the same regex.
    If neither is set, it will delete all channels with the same name as the one where the command was executed.
    """
    if name is not None and not isinstance(name, str):
        raise Exception(f"Name must be a string, not {type(name)} !")

    if regex is not None and not isinstance(regex, str):
        raise Exception(f"Regex must be a string, not {type(regex)} !")

    for channel in ctx.channel.guild.channels:

        if name is not None and channel.name == str(name):
            await channel.delete(reason=reason)

        elif regex is not None and search(regex, channel.name):
            await channel.delete(reason=reason)


async def dshell_edit_text_channel(ctx: Message,
                                   channel=None,
                                   name=None,
                                   category=MISSING,
                                   position=MISSING,
                                   slowmode=MISSING,
                                   topic=MISSING,
                                   nsfw=MISSING,
                                   permissions: dict[Union[Member, Role], PermissionOverwrite] = MISSING,
                                   reason=None):
    """
    Edits a text channel on the server
    """
    if name is not None and not isinstance(name, str):
        raise Exception(f"Name must be a string, not {type(name)} !")

    if not isinstance(position, (_MissingSentinel, int)):
        raise Exception(f"Position must be an integer, not {type(position)} !")

    if not isinstance(category, (_MissingSentinel, int)):
        raise Exception(f"Category must be an integer, not {type(category)} !")

    if not isinstance(slowmode, (_MissingSentinel, int)):
        raise Exception(f"Slowmode must be an integer, not {type(slowmode)} !")

    if not isinstance(topic, (_MissingSentinel, str)):
        raise Exception(f"Topic must be a string, not {type(topic)} !")

    if not isinstance(nsfw, (_MissingSentinel, bool)):
        raise Exception(f"NSFW must be a boolean, not {type(nsfw)} !")

    channel_to_edit = ctx.channel if channel is None else ctx.channel.guild.get_channel(channel)
    new_categoy = ctx.channel.category if isinstance(category, _MissingSentinel) else ctx.channel.guild.get_channel(category)

    if channel_to_edit is None:
        raise Exception(f"Channel {channel} not found !")

    await channel_to_edit.edit(name=name if name is not None else channel_to_edit.name,
                               position=position if position is not MISSING else channel_to_edit.position,
                               category=new_categoy,
                               slowmode_delay=slowmode if slowmode is not MISSING else channel_to_edit.slowmode_delay,
                               topic=topic if topic is not MISSING else channel_to_edit.topic,
                               nsfw=nsfw if nsfw is not MISSING else channel_to_edit.nsfw,
                               overwrites=permissions if permissions is not MISSING else channel_to_edit.overwrites,
                               reason=reason)

    return channel_to_edit.id


async def dshell_edit_voice_channel(ctx: Message,
                                    channel=None,
                                    name=None,
                                    category=MISSING,
                                    position=MISSING,
                                    bitrate=MISSING,
                                    permissions: dict[Union[Member, Role], PermissionOverwrite] = MISSING,
                                    reason=None):
    """
    Edits a voice channel on the server
    """
    if not isinstance(position, (_MissingSentinel, int)):
        raise Exception(f"Position must be an integer, not {type(position)} !")

    if not isinstance(category, (_MissingSentinel, int)):
        raise Exception(f"Category must be an integer, not {type(category)} !")

    if not isinstance(bitrate, (_MissingSentinel, int)):
        raise Exception(f"Bitrate must be an integer, not {type(bitrate)} !")

    channel_to_edit = ctx.channel if channel is None else ctx.channel.guild.get_channel(channel)
    new_categoy = ctx.channel.category if isinstance(category, _MissingSentinel) else ctx.channel.guild.get_channel(category)

    if channel_to_edit is None:
        raise Exception(f"Channel {channel} not found !")

    await channel_to_edit.edit(name=name if name is not None else channel_to_edit.name,
                               position=position if position is not MISSING else channel_to_edit.position,
                               category=new_categoy,
                               bitrate=bitrate if bitrate is not MISSING else channel_to_edit.bitrate,
                               overwrites=permissions if permissions is not MISSING else channel_to_edit.overwrites,
                               reason=reason)

    return channel_to_edit.id


async def dshell_create_thread_message(ctx: Message,
                                       name,
                                       message: Union[int, str] = None,
                                       archive=MISSING,
                                       slowmode=MISSING):
    """
    Creates a thread from a message.
    """

    if message is None:
        message = ctx.id

    message = utils_get_message(ctx, message)


    if not isinstance(name, str):
        raise Exception(f"Name must be a string, not {type(name)} !")

    if not isinstance(archive, (_MissingSentinel, int)):
        raise Exception(f"Auto archive duration must be an integer, not {type(archive)} !")

    if not isinstance(archive, _MissingSentinel) and archive not in (60, 1440, 4320, 10080):
        raise Exception("Auto archive duration must be one of the following values: 60, 1440, 4320, 10080 !")

    if not isinstance(slowmode, (_MissingSentinel, int)):
        raise Exception(f"Slowmode delay must be an integer, not {type(slowmode)} !")

    if not isinstance(slowmode, _MissingSentinel) and slowmode < 0:
        raise Exception("Slowmode delay must be a positive integer !")

    if isinstance(message, PartialMessage):
        m = await message.fetch()
    else:
        m = message

    thread = await m.create_thread(name=name,
                    auto_archive_duration=archive,
                    slowmode_delay=slowmode)

    return thread.id

async def dshell_edit_thread(ctx: Message,
                             thread: Union[int, str] = None,
                             name=None,
                             archive=MISSING,
                             slowmode=MISSING,
                             reason=None):
    """ Edits a thread.
    """
    if thread is None:
        thread = ctx.thread

    if thread is None:
        raise Exception("Thread must be specified !")

    thread = await utils_get_thread(ctx, thread)

    if not isinstance(name, (_MissingSentinel, str)):
        raise Exception(f"Name must be a string, not {type(name)} !")

    if not isinstance(archive, (_MissingSentinel, int)):
        raise Exception(f"Auto archive duration must be an integer, not {type(archive)} !")

    if not isinstance(archive, _MissingSentinel) and archive not in (60, 1440, 4320, 10080):
        raise Exception("Auto archive duration must be one of the following values: 60, 1440, 4320, 10080 !")

    if not isinstance(slowmode, (_MissingSentinel, int)):
        raise Exception(f"Slowmode delay must be an integer, not {type(slowmode)} !")

    if not isinstance(slowmode, _MissingSentinel) and slowmode < 0:
        raise Exception("Slowmode delay must be a positive integer !")

    await thread.edit(name=name if name is not None else thread.name,
                      auto_archive_duration=archive if archive is not MISSING else thread.auto_archive_duration,
                      slowmode_delay=slowmode if slowmode is not MISSING else thread.slowmode_delay,
                      reason=reason)


async def dshell_get_thread(ctx: Message, message: Union[int, str] = None):
    """
    Returns the thread object of the specified thread ID.
    """

    if message is None:
        message = ctx.id

    target_message = utils_get_message(ctx, message)
    if isinstance(target_message, PartialMessage):
        message = await target_message.fetch()
    else:
        message = target_message

    if not hasattr(message, 'thread'):
        return None

    thread = message.thread

    if thread is None:
        return None

    return thread.id


async def dshell_delete_thread(ctx: Message, thread: Union[int, str] = None, reason=None):
    """
    Deletes a thread.
    """

    if thread is None:
        thread = ctx.id

    target_message = utils_get_message(ctx, thread)
    if isinstance(target_message, PartialMessage):
        thread = await target_message.fetch()
    else:
        thread = target_message

    if not hasattr(thread, 'thread'):
        raise Exception("The specified message does not have a thread !")

    if thread.thread is None:
        raise Exception("The specified message does not have a thread !")

    await thread.thread.delete(reason=reason)

    return thread.thread.id

async def dshell_create_category(ctx: Message,
                                   name,
                                   position=MISSING,
                                   permissions: dict[Union[Member, Role], PermissionOverwrite] = MISSING,
                                   reason=None):
    """
    Creates a category on the server
    """

    if not isinstance(position, (_MissingSentinel, int)):
        raise Exception(f"Position must be an integer, not {type(position)} !")

    created_category = await ctx.guild.create_category(str(name),
                                                      position=position,
                                                      overwrites=permissions,
                                                      reason=reason)

    return created_category.id

async def dshell_edit_category(ctx: Message,
                                category,
                                name=None,
                                position=MISSING,
                                permissions: dict[Union[Member, Role], PermissionOverwrite] = MISSING,
                                reason=None):
    """
    Edits a category on the server
    """
    if not isinstance(position, (_MissingSentinel, int)):
        raise Exception(f"Position must be an integer, not {type(position)} !")

    category_to_edit = ctx.channel.guild.get_channel(category)

    if category_to_edit is None or not isinstance(category_to_edit, CategoryChannel):
        raise Exception(f"Category {category} not found or is not a category !")

    await category_to_edit.edit(name=name if name is not None else category_to_edit.name,
                                position=position if position is not MISSING else category_to_edit.position,
                                overwrites=permissions if permissions is not MISSING else category_to_edit.overwrites,
                                reason=reason)

    return category_to_edit.id

async def dshell_delete_category(ctx: Message, category=None, reason=None):
    """
    Deletes a category.
    """

    if category is None and ctx.channel.category is None:
        raise Exception("Category must be specified !")

    category_to_delete = ctx.channel.category if category is None else ctx.channel.guild.get_channel(category)

    if category_to_delete is None or not isinstance(category_to_delete, CategoryChannel):
        raise Exception(f"Category {category} not found or is not a category !")

    await category_to_delete.delete(reason=reason)

    return category_to_delete.id

############################# CHANNEL INFO ##############################

async def dshell_get_channel_category_id(ctx: Message, channel=None):
    """
    Returns the category ID of a channel.
    """

    channel_to_check = ctx.channel if channel is None else ctx.channel.guild.get_channel(channel)

    if channel_to_check is None:
        raise Exception(f"Channel {channel} not found !")

    if channel_to_check.category is None:
        return None

    return channel_to_check.category.id if channel_to_check.category is not None else 0

async def dshell_get_channel_nsfw(ctx: Message, channel=None):
    """
    Returns if the channel is NSFW.
    """

    channel_to_check = ctx.channel if channel is None else ctx.channel.guild.get_channel(channel)

    if channel_to_check is None:
        raise Exception(f"Channel {channel} not found !")

    return channel_to_check.nsfw

async def dshell_get_channel_slowmode(ctx: Message, channel=None):
    """
    Returns the slowmode delay of a channel.
    """

    channel_to_check = ctx.channel if channel is None else ctx.channel.guild.get_channel(channel)

    if channel_to_check is None:
        raise Exception(f"Channel {channel} not found !")

    if not hasattr(channel_to_check, 'slowmode_delay'):
        raise Exception(f"Channel {channel} is not a text channel !")

    return channel_to_check.slowmode_delay

async def dshell_get_channel_topic(ctx: Message, channel=None):
    """
    Returns the topic of a channel.
    """

    channel_to_check = ctx.channel if channel is None else ctx.channel.guild.get_channel(channel)

    if channel_to_check is None:
        raise Exception(f"Channel {channel} not found !")

    if not hasattr(channel_to_check, 'topic'):
        raise Exception(f"Channel {channel} is not a text channel !")

    return channel_to_check.topic

async def dshell_get_channel_threads(ctx: Message, channel=None):
    """
    Returns the list of threads in a channel.
    """

    channel_to_check = ctx.channel if channel is None else ctx.channel.guild.get_channel(channel)

    if channel_to_check is None:
        raise Exception(f"Channel {channel} not found !")

    if not hasattr(channel_to_check, 'threads'):
        raise Exception(f"Channel {channel} is not a text channel !")

    from .._DshellParser.ast_nodes import ListNode
    threads = ListNode([])

    for thread in channel_to_check.threads:
        threads.add(thread.id)

    return threads

async def dshell_get_channel_position(ctx: Message, channel=None):
    """
    Returns the position of a channel.
    """

    channel_to_check = ctx.channel if channel is None else ctx.channel.guild.get_channel(channel)

    if channel_to_check is None:
        raise Exception(f"Channel {channel} not found !")

    return channel_to_check.position

async def dshell_get_channel_url(ctx: Message, channel=None):
    """
    Returns the URL of a channel.
    """

    channel_to_check = ctx.channel if channel is None else ctx.channel.guild.get_channel(channel)

    if channel_to_check is None:
        raise Exception(f"Channel {channel} not found !")

    return channel_to_check.jump_url

async def dshell_get_channel_voice_members(ctx: Message, channel=None):
    """
    Returns the list of members in a voice channel.
    """

    channel_to_check = ctx.channel if channel is None else ctx.channel.guild.get_channel(channel)

    if channel_to_check is None:
        raise Exception(f"Channel {channel} not found !")

    if not isinstance(channel_to_check, VoiceChannel):
        raise Exception(f"Channel {channel} is not a voice channel !")

    from .._DshellParser.ast_nodes import ListNode
    members = ListNode([])

    for member in channel_to_check.members:
        members.add(member.id)

    return members
