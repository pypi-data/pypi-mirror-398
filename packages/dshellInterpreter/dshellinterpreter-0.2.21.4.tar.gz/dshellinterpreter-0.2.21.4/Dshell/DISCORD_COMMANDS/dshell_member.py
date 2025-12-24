from datetime import timedelta, datetime, UTC

from discord import MISSING, Message, Member, Permissions, Role, Embed

__all__ = [
    "dshell_send_private_message",
    "dshell_ban_member",
    "dshell_unban_member",
    "dshell_kick_member",
    "dshell_rename_member",
    "dshell_add_roles",
    "dshell_remove_roles",
    "dshell_check_permissions",
    "dshell_timeout_member",
    "dshell_move_member",
    "dshell_give_member_roles",
    "dshell_remove_member_roles"
]

async def dshell_send_private_message(ctx: Message, message: str = None, member: int = None, delete: int = None, embeds = None, ):
    """
    Sends a private message to a member.
    If member is None, sends the message to the author of the command.
    If delete is specified, deletes the message after the specified time in seconds.
    """
    if delete is not None and not isinstance(delete, (int, float)):
        raise Exception(f'Delete parameter must be a number (seconds) or None, not {type(delete)} !')

    member_to_send = ctx.author if member is None else ctx.channel.guild.get_member(member)

    if member_to_send is None:
        raise Exception(f'Member {member} not found!')

    from .._DshellParser.ast_nodes import ListNode

    if embeds is None:
        embeds = ListNode([])

    elif isinstance(embeds, Embed):
        embeds = ListNode([embeds])

    else:
        raise Exception(f'Embeds must be a list of Embed objects or a single Embed object, not {type(embeds)} !')

    sended_message = await member_to_send.send(message, delete_after=delete, embeds=embeds)

    return sended_message.id


async def dshell_ban_member(ctx: Message, member: int, reason: str = MISSING):
    """
    Bans a member from the server.
    """
    banned_member = ctx.channel.guild.get_member(member)

    if not banned_member:
        raise Exception(f'Member {member} not found in the server !')

    await ctx.channel.guild.ban(banned_member, reason=reason)

    return banned_member.id


async def dshell_unban_member(ctx: Message, user: int, reason: str = MISSING):
    """
    Unbans a user from the server.
    """
    banned_users = ctx.channel.guild.bans()
    user_to_unban = None

    async for ban_entry in banned_users:
        if ban_entry.user.id == user:
            user_to_unban = ban_entry.user
            break

    if not user_to_unban:
        raise Exception(f'User {user} not found in the banned list')

    await ctx.channel.guild.unban(user_to_unban, reason=reason)

    return user_to_unban.id


async def dshell_kick_member(ctx: Message, member: int, reason: str = MISSING):
    """
    Kicks a member from the server.
    """
    kicked_member = ctx.channel.guild.get_member(member)

    if not kicked_member:
        raise Exception(f'Member {member} not found in the server !')

    await ctx.channel.guild.kick(kicked_member, reason=reason)

    return kicked_member.id


async def dshell_timeout_member(ctx: Message, duration: int, member=None, reason: str = MISSING):
    """
    Timeouts a member in the server for a specified duration.
    """
    target_member = ctx.author if member is None else ctx.channel.guild.get_member(member)

    if not target_member:
        raise Exception(f'Member {member} not found in the server !')

    if not isinstance(duration, int):
        raise TypeError("Duration must be an integer representing seconds.")

    if duration < 0:
        raise ValueError("Duration must be a non-negative integer.")

    await target_member.timeout(until=datetime.now(UTC) + timedelta(seconds=duration), reason=reason)

    return target_member.id


async def dshell_rename_member(ctx: Message, new_name, member=None):
    """
    Renames a member in the server.
    """
    renamed_member = ctx.channel.guild.get_member(member)

    if not renamed_member:
        raise Exception(f'Member {member} not found in the server !')

    await renamed_member.edit(nick=new_name)

    return renamed_member.id


async def dshell_add_roles(ctx: Message, roles: list[int] | int, member=None, reason: str = None):
    """
    Adds roles to a member in the server.
    """
    target_member: Member = ctx.author if member is None else ctx.channel.guild.get_member(member)

    if not target_member:
        raise Exception(f'Member {member} not found in the server !')

    if isinstance(roles, int):
        roles = [roles]

    roles_to_add = [ctx.channel.guild.get_role(role_id) for role_id in roles if ctx.channel.guild.get_role(role_id)]

    if not roles_to_add:
        raise Exception(f'No role found !')

    await target_member.add_roles(*roles_to_add, reason=reason)

    return target_member.id


async def dshell_remove_roles(ctx: Message, roles: list[int] | int, member=None, reason: str = None):
    """
    Removes roles from a member in the server.
    """
    target_member: Member = ctx.author if member is None else ctx.channel.guild.get_member(member)

    if not target_member:
        raise Exception(f'Member {member} not found in the server !')

    if isinstance(roles, int):
        roles = [roles]

    roles_to_remove = [ctx.channel.guild.get_role(role_id) for role_id in roles if ctx.channel.guild.get_role(role_id)]

    if not roles_to_remove:
        raise Exception(f'No role found !')

    await target_member.remove_roles(*roles_to_remove, reason=reason)

    return target_member.id


async def dshell_check_permissions(ctx: Message, permissions, member=None):
    """
    Checks if a member has specific permissions in the server.
    """
    target_member: Member = ctx.author if member is None else ctx.channel.guild.get_member(member)

    if not target_member:
        raise Exception(f'Member {member} not found in the server !')

    if not isinstance(permissions, int):
        raise TypeError("Permissions must be an integer representing permissions flags.")

    permissions_to_check = Permissions(permissions)
    member_permissions = target_member.guild_permissions

    if (permissions_to_check.value & member_permissions.value) != 0:
        return True
    return False


async def dshell_move_member(ctx: Message, member=None, channel=None, disconnect: bool = False, reason=None):
    """
    Moves a member to another channel.
    If channel is None, disconnect the member from their current voice channel.
    """
    target_member = ctx.author if member is None else ctx.channel.guild.get_member(member)
    target_channel = ctx.channel if channel is None else ctx.channel.guild.get_channel(channel)

    if not target_member:
        raise Exception(f'Member {member} not found in the server !')

    if target_member.voice.channel is None:
        raise Exception(f'Member {target_member.name} is not in a voice channel !')

    if not target_channel:
        raise Exception(f'Channel {channel} not found in the server !')

    if disconnect:
        await target_member.move_to(None, reason=reason)
    else:
        await target_member.move_to(target_channel, reason=reason)

    return target_member.id


async def dshell_give_member_roles(ctx: Message, roles, member=None, reason=None):
    """
    Give roles to the target member
    """
    target_member = ctx.author if member is None else ctx.guild.get_member(member)

    if target_member is None:
        raise Exception(f'Member {member} not found in the server !')

    if isinstance(roles, int):
        roles = (roles, )

    list_roles: list[Role] = []
    for i in roles:
        role_to_give = ctx.guild.get_role(i)

        if role_to_give is None:
            raise Exception(f'Role {i} not found in the server !')

        list_roles.append(role_to_give)

    list_roles.extend(target_member.roles)

    await target_member.edit(roles=list_roles, reason=str(reason))

    return target_member.id


async def dshell_remove_member_roles(ctx: Message, roles, member=None, reason=None):
    """
    Remove roles to the target member
    """
    target_member = ctx.author if member is None else ctx.guild.get_member(member)

    if target_member is None:
        raise Exception(f'Member {member} not found in the server !')

    if isinstance(roles, int):
        roles = (roles,)

    list_roles: set[Role] = set()
    for i in roles:
        role_to_give = target_member.get_role(i)

        if role_to_give is None:
            raise Exception(f"{target_member.name} member doesn't have {i} role !")

        list_roles.add(role_to_give)

    new_set_role = list(set(target_member.roles) - list_roles)

    await target_member.edit(roles=new_set_role, reason=str(reason))

    return target_member.id
