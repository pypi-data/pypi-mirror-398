from discord import Message, Thread
from discord.errors import NotFound

from typing import Union
from re import search


async def utils_get_thread(ctx: Message, thread: Union[int, str]) -> Thread:
    """
    Returns the thread object of the specified thread ID or link.
    Thread is only available in the same server as the command and in the same channel.
    If the thread is a link, it must be in the format: https://discord.com/channels/{guild_id}/{channel_id}/{message_id}
    """

    if isinstance(thread, int):
        return ctx.channel.get_thread(thread)

    elif isinstance(thread, str):
        match = search(r'https://discord\.com/channels/(\d+)/(\d+)(/\d+)?', thread)
        if not match:
            raise Exception("Invalid thread link format. Use a valid Discord thread link.")
        guild_id = int(match.group(1))
        message_id = int(match.group(2))
        channel_id = ctx.channel.id if len(match.groups()) == 3 else ctx.channel.id

        if guild_id != ctx.guild.id:
            raise Exception("The thread must be from the same server as the command !")

        try:
            c = await ctx.guild.get_channel(channel_id).fetch_message(message_id)
            return c.thread
        except NotFound:
            raise Exception(f"Thread with ID {message_id} not found in channel {channel_id} !")

    raise Exception(f"Thread must be an integer or a string, not {type(thread)} !")
