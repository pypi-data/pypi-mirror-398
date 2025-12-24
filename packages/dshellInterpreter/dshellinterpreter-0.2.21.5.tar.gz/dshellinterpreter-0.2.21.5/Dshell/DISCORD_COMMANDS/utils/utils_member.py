__all__ = [
    "utils_has_permissions",
]
from discord import Message, PermissionOverwrite

from .utils_global import utils_what_discord_type_is, DiscordType

async def utils_has_permissions(ctx: Message, member: int, permission: dict[None, PermissionOverwrite]) -> bool:
    """
    Return True if the member has the specified permissions.
    :param member:
    :param permission:
    :return:
    """

    if not isinstance(member, int):
        raise TypeError(f"member must be an int in has_perms command, not {type(member)}")

    if not isinstance(permission, dict):
        raise TypeError(f"permissions must be a permission bloc in has_perms command, not {type(permission)}")

    if None not in permission:
        raise ValueError(f"permissions must have simple 'allow' permission in has_perms command, not {permission.keys()}")

    discord_type, member = utils_what_discord_type_is(ctx, member)

    if discord_type != DiscordType.MEMBER:
        raise ValueError(f"No member found with ID {member} in has_perms command.")

    return (member.guild_permissions & permission[None].pair()[0]) == permission[None].pair()[0]
