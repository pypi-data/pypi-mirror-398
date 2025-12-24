from enum import Enum, auto
from typing import Union

__all__ = [
    'DshellTokenType',
    'Token',
    'MASK_CHARACTER'
]

MASK_CHARACTER = '§'


class DshellTokenType(Enum):
    INT = auto()
    FLOAT = auto()
    STR = auto()
    BOOL = auto(),
    NONE = auto(),
    LIST = auto()
    DICT = auto()
    MENTION = auto()
    IDENT = auto()  # nom de variable, fonction
    KEYWORD = auto()  # if, let, end, etc.
    DISCORD_KEYWORD = auto()  # embed, #embed...
    COMMAND = auto()
    PARAMETER = auto()  # --
    PARAMETERS = auto(),  # --*
    STR_PARAMETER = auto(),  # --"
    SUB_SEPARATOR = auto(),  # ~~
    MATHS_OPERATOR = auto()  # ==, +, -, *, etc.
    LOGIC_OPERATOR = auto(),
    LOGIC_WORD_OPERATOR = auto()  # and, or, not
    EVAL_GROUP = auto()  # `code`
    COMMENT = auto()  # lignes commençant par ##


class Token:
    def __init__(self, type_: "DTT", value: Union[str, list], position: tuple[int, int]):
        self.type = type_
        self.value = value
        self.position = position

    def __repr__(self):
        return f"<{self.type.name} '{self.value}'>"

    def to_dict(self):
        def serialize_value(value):
            if isinstance(value, list):
                return [serialize_value(v) for v in value]
            elif isinstance(value, Token):
                return value.to_dict()
            return value

        return {
            "type": self.type.name,
            "value": serialize_value(self.value),
            "position": self.position
        }
