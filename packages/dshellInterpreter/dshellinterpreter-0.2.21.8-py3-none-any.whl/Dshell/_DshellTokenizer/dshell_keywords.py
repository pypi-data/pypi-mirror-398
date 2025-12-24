__all__ = [
    "dshell_keyword",
    "dshell_discord_keyword",
    "dshell_commands",
    "dshell_mathematical_operators",
    "dshell_logical_operators",
    "dshell_operators",
    "dshell_logical_word_operators"
]

from typing import Callable

from ..DISCORD_COMMANDS.dshell_channel import *
from ..DISCORD_COMMANDS.dshell_member import *
from ..DISCORD_COMMANDS.dshell_message import *
from ..DISCORD_COMMANDS.dshell_pastbin import *
from ..DISCORD_COMMANDS.dshell_role import *
from ..DISCORD_COMMANDS.dshell_interaction import *
from ..DISCORD_COMMANDS.utils.utils_global import *
from ..DISCORD_COMMANDS.utils.utils_list import *
from ..DISCORD_COMMANDS.utils.utils_member import *
from ..DISCORD_COMMANDS.utils.utils_string import *
from ..DISCORD_COMMANDS.utils.utils_permissions import utils_update_permissions

dshell_keyword: set[str] = {
    'if', 'else', 'elif', 'loop', '#end', 'var', '#loop', '#if', 'sleep', 'param', '#param'
}

dshell_discord_keyword: set[str] = {
    'embed', '#embed', 'field', 'perm', 'permission', '#perm', '#permission', 'ui', '#ui', 'button', 'select'
}

async def dshell_debug(ctx, x):
    """
    Print all x parameter
    :param ctx:
    :param x:
    :return:
    """
    print(x)
    return x

dshell_commands: dict[str, Callable] = {

    "debug": dshell_debug,
    ## global utils
    'random': utils_random,

    ## List utils
    'length': utils_len,
    'len': utils_len,
    'add': utils_list_add,
    'remove': utils_list_remove,
    'clear': utils_list_clear,
    'pop': utils_list_pop,
    'sort': utils_list_sort,
    'reverse': utils_list_reverse,
    'get': utils_list_get_value,

    ## String utils
    'split': utils_split_string,
    'upper': utils_upper_string,
    'lower': utils_lower_string,
    'title': utils_title_string,
    'strip': utils_strip_string,
    'replace': utils_replace_string,
    'regex_findall': utils_regex_findall,
    'regex_sub': utils_regex_sub,
    'regex': utils_regex_search,

    ## Discord utils
    'name': utils_get_name, # get the name from id (channel, role, member)
    'id': utils_get_id, # get the id from name (channel, role, member)
    'roles': utils_get_roles, # get all roles of a member

    ## Member utils
    'has_perms': utils_has_permissions, # check if a member has the specified permissions

    ## Permission utils
    'update_perms': utils_update_permissions, # update permission dict

    ## Pastbin command
    "gp": dshell_get_pastbin,  # get pastbin

    ## Discord commands
    "sm": dshell_send_message,  # send message
    "spm": dshell_send_private_message,  # send private message
    "srm": dshell_respond_message,  # respond to a message
    "dm": dshell_delete_message,
    "pm": dshell_purge_message,
    "em": dshell_edit_message,  # edit message
    "pinm": dshell_pin_message,  # pin message
    "mh": dshell_get_history_messages,  # get message history
    "gcm": dshell_get_content_message,  # get content of a message
    "gma": dshell_get_author_id_message,  # get author id of a message
    "gml": dshell_get_message_link,  # get message link
    "gmc": dshell_get_message_category_id,  # get message category id
    "gmp": dshell_get_channel_pined_messages,  # get channel pined messages
    "gmat": dshell_get_message_attachments,  # get message attachments
    "ims": dshell_is_message_system,  # is message system

    "sri": dshell_respond_interaction,  # respond to an interaction
    "sdi": dshell_defer_interaction,  # defer an interaction
    "dom": dshell_delete_original_message,  # delete original interaction message

    "cc": dshell_create_text_channel,  # create channel
    "cvc": dshell_create_voice_channel,  # create voice channel
    "cca": dshell_create_category,  # create category
    "dca": dshell_delete_category,  # delete category
    "dc": dshell_delete_channel,  # delete channel
    "dcs": dshell_delete_channels,  # delete several channels by name or regex

    "gc": dshell_get_channel,  # get channel
    "gcs": dshell_get_channels,  # get channels by name or regex
    "gccs": dshell_get_channels_in_category,  # get channels in category
    "gcc": dshell_get_channel_category_id,  # get channel category id
    "gcnsfw": dshell_get_channel_nsfw,  # get channel nsfw status
    "gcsl": dshell_get_channel_slowmode,  # get channel slowmode
    "gct": dshell_get_channel_topic,  # get channel topic
    "gcth": dshell_get_channel_threads,  # get channel threads
    "gvcm": dshell_get_channel_voice_members,  # get voice channel members

    "ct": dshell_create_thread_message,  # create thread
    "dt": dshell_delete_thread,  # delete thread
    "gt": dshell_get_thread,  # get thread
    "et": dshell_edit_thread,  # edit thread

    "bm": dshell_ban_member,  # ban member
    "um": dshell_unban_member,  # unban member
    "km": dshell_kick_member,  # kick member
    "tm": dshell_timeout_member,  # timeout member
    "mm": dshell_move_member,  # move member to another channel
    "rm": dshell_rename_member,  # rename member
    "cp": dshell_check_permissions,  # check permissions
    "gmr": dshell_give_member_roles, # give roles
    "rmr": dshell_remove_member_roles, # remove roles

    "ec": dshell_edit_text_channel,  # edit text channel
    "evc": dshell_edit_voice_channel,  # edit voice channel
    "eca": dshell_edit_category,  # edit category

    "cr": dshell_create_role, # create role
    "dr": dshell_delete_roles, # delete role
    "er": dshell_edit_role, # edit role

    "ar": dshell_add_reactions,  # add reactions to a message
    "rr": dshell_remove_reactions,  # remove reactions from a message
    "cmr": dshell_clear_message_reactions, # clear reactions from a message
    "cor": dshell_clear_one_reactions , # clear one reaction from a message

}

dshell_mathematical_operators: dict[str, tuple[Callable, int]] = {

    r".": (lambda a, b: a.b, 9),
    r"->": (lambda a: a.at, 10),  # equivalent to calling .at(key)

    r"+": (lambda a, b: a + b, 6),
    r"-": (lambda a, b=None: -a if b is None else a - b, 6),
    # warning: ambiguity between unary and binary to be handled in your parser
    r"**": (lambda a, b: a ** b, 8),
    r"*": (lambda a, b: a * b, 7),
    r"%": (lambda a, b: a % b, 7),
    r"//": (lambda a, b: a // b, 7),
    r"/": (lambda a, b: a / b, 7),
}

dshell_logical_word_operators: dict[str, tuple[Callable, int]] = {
    r"and": (lambda a, b: bool(a and b), 2),
    r"or": (lambda a, b: bool(a or b), 1),
    r"not": (lambda a: not a, 3),
    r"in": (lambda a, b: a in b, 4),
}

dshell_logical_operators: dict[str, tuple[Callable, int]] = {

    r"<": (lambda a, b: a < b, 4),
    r"<=": (lambda a, b: a <= b, 4),
    r"=<": (lambda a, b: a <= b, 4),
    r"=": (lambda a, b: a == b, 4),
    r"!=": (lambda a, b: a != b, 4),
    r"=!": (lambda a, b: a != b, 4),
    r">": (lambda a, b: a > b, 4),
    r">=": (lambda a, b: a >= b, 4),
    r"=>": (lambda a, b: a >= b, 4),
    r"&": (lambda a, b: a & b, 2),
    r"|": (lambda a, b: a | b, 1),

}

dshell_operators: dict[str, tuple[Callable, int]] = dshell_logical_operators.copy()
dshell_operators.update(dshell_logical_word_operators)
dshell_operators.update(dshell_mathematical_operators)
