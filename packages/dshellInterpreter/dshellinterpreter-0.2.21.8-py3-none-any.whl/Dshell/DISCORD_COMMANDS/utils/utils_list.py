__all__ = [
    "utils_list_add",
    "utils_list_remove",
    "utils_list_clear",
    "utils_list_pop",
    "utils_list_sort",
    "utils_list_reverse",
    "utils_list_get_value",
]

async def utils_list_add(ctx, value: "ListNode", *elements):
    """
    Add an element to a list
    :param value:
    :param elements:
    :return:
    """
    from ..._DshellParser.ast_nodes import ListNode
    if not isinstance(value, ListNode):
        raise TypeError("value must be a list in add command")

    for elem in elements:
        if isinstance(elem, ListNode):
            value.extend(elem)
        else:
            value.add(elem)
    return value

async def utils_list_remove(ctx, value: "ListNode", element, count: int = 1):
    """
    Remove an element from a list
    :param value:
    :param element:
    :param count:
    :return:
    """
    from ..._DshellParser.ast_nodes import ListNode
    if not isinstance(value, ListNode):
        raise TypeError("value must be a list in remove command")

    value.remove(element, count)
    return value

async def utils_list_clear(ctx, value: "ListNode"):
    """
    Clear a list
    :param value:
    :return:
    """
    from ..._DshellParser.ast_nodes import ListNode
    if not isinstance(value, ListNode):
        raise TypeError("value must be a list in clear command")
    value.clear()
    return value

async def utils_list_pop(ctx, value: "ListNode", index: int = -1):
    """
    Pop an element from a list
    :param value:
    :param index:
    :return:
    """
    from ..._DshellParser.ast_nodes import ListNode
    if not isinstance(value, ListNode):
        raise TypeError("value must be a list in pop command")
    if not isinstance(index, int):
        raise TypeError("index must be an integer in pop command")
    return value.pop(index)

async def utils_list_sort(ctx, value: "ListNode", reverse: bool = False):
    """
    Sort a list
    :param value:
    :param reverse:
    :return:
    """
    from ..._DshellParser.ast_nodes import ListNode
    if not isinstance(value, ListNode):
        raise TypeError("value must be a list in sort command")
    if not isinstance(reverse, bool):
        raise TypeError("reverse must be a boolean in sort command")
    value.sort(reverse=reverse)
    return value

async def utils_list_reverse(ctx, value: "ListNode"):
    """
    Reverse a list
    :param value:
    :return:
    """
    from ..._DshellParser.ast_nodes import ListNode
    if not isinstance(value, ListNode):
        raise TypeError("value must be a list in reverse command")
    value.reverse()
    return value

async def utils_list_get_value(ctx, value: "ListNode", index: int = 0):
    """
    Get a value from a list
    :param value:
    :param index:
    :return:
    """
    from ..._DshellParser.ast_nodes import ListNode
    if not isinstance(value, ListNode):
        raise TypeError("value must be a list in get command")
    if not isinstance(index, int):
        raise TypeError("index must be an integer in get command")
    return value[index]