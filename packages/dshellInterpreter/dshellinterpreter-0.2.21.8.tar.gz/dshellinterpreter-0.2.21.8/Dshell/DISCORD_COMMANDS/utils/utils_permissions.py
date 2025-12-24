from typing import Union
from discord import Guild, Member, Role, Permissions, PermissionOverwrite, Message

from .utils_global import utils_what_discord_type_is, DiscordType

async def utils_update_permissions(ctx: Message,
                                   permission1: dict[Union[Member, Role, None], PermissionOverwrite],
                                   permission2: dict[Union[Member, Role, None], PermissionOverwrite]) -> dict:

    if not isinstance(permission1, dict):
        raise ValueError(f"permission1 must be a permission block, not {type(permission1).__name__}")

    if not isinstance(permission2, dict):
        raise ValueError(f"permission2 must be a permission block, not {type(permission2).__name__}")

    permission1.update(permission2)

    return permission1


class DshellPermissions:
    def __init__(self, target: dict[str, list[int]]):
        """
        Creates a Dshell permissions object.
        :param target: A dictionary containing parameters and their values.
        Expected parameters: “allow”, “deny”, ‘members’, “roles”.
        For “members” and “roles”, values must be ID ListNodes.
        """
        self.target: dict[str, Union["ListNode", int]] = target

    @staticmethod
    def get_member(guild, member_id: int) -> Member:
        """
        Return a Member object from a member ID.
        :param member_id:
        :return:
        """
        discord_type, instance = utils_what_discord_type_is(guild, member_id)
        if discord_type == DiscordType.MEMBER:
            return instance
        raise ValueError(f"No member found with ID {member_id} in perm command.")

    @staticmethod
    def get_role(guild, role_id: int) -> Role:
        """
        Return a Role object from a role ID.
        :param role_id:
        :return:
        """
        discord_type, instance = utils_what_discord_type_is(guild, role_id)
        if discord_type == DiscordType.ROLE:
            return instance
        raise ValueError(f"No role found with ID {role_id} in perm command.")

    def get_permission_overwrite(self, guild: Guild) -> dict[Union[Member, Role, None], PermissionOverwrite]:
        """
        Returns a PermissionOverwrite object with member and role permissions.
        If no members or roles are specified, it returns a PermissionOverwrite with None key.
        :param guild: The Discord server
        :return: A dictionary of PermissionOverwrite objects with members and roles as keys
        """
        from ..._DshellParser.ast_nodes import ListNode
        permissions: dict[Union[Member, Role, None], PermissionOverwrite] = {}
        target_keys = self.target.keys()

        if 'members' in target_keys:
            for member_id in (
                    self.target['members'] if isinstance(self.target['members'], ListNode) else [
                        self.target['members']]):  # allow a single ID
                member = self.get_member(guild, member_id)
                permissions[member] = PermissionOverwrite.from_pair(
                    allow=Permissions(permissions=self.target.get('allow', 0)),
                    deny=Permissions(permissions=self.target.get('deny', 0))
                )

        elif 'roles' in target_keys:
            for role_id in (
                    self.target['roles'] if isinstance(self.target['roles'], ListNode) else [
                        self.target['roles']]):  # allow a single ID
                if role_id == guild.id:  # @everyone role
                    role = guild.default_role
                else:
                    role = self.get_role(guild, role_id)
                permissions[role] = PermissionOverwrite.from_pair(
                    allow=Permissions(permissions=self.target.get('allow', 0)),
                    deny=Permissions(permissions=self.target.get('deny', 0))
                )
        else:
            permissions[None] = PermissionOverwrite.from_pair(
                allow=Permissions(permissions=self.target.get('allow', 0)),
                deny=Permissions(permissions=self.target.get('deny', 0))
            )

        return permissions