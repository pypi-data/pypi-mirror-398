from typing import Any, Union
from .._DshellTokenizer.dshell_token_type import DshellTokenType as DTT

class DshellArgumentsData:
    """
    Data structure for Dshell argument.
    """

    def __init__(self,value: Any, obligatory: bool, type_: DTT):
        self.value = value
        self.type = type_
        self.obligatory = obligatory

    def __repr__(self):
        return f"DshellArgumentsData(value={self.value}, obligatory={self.obligatory})"

class DshellArguments:
    """
    Manage Dhsell parameters and arguments passed to a command call.
    Example : !ban @user reason for ban
    """

    def __init__(self):
        self.parameters: dict[str, DshellArgumentsData] = {'*': DshellArgumentsData([], False, DTT.LIST)}  # Non-specified parameters

    def set_parameter(self, name: str, value: Any, type_: DTT,  obligatory: bool = False):
        """
        Set data parameter with its type and value.
        :param name: Name of the parameter
        :param value: Value of the parameter
        """
        self.parameters[name] = DshellArgumentsData(value, obligatory, type_)

    def get_parameter(self, name: str) -> DshellArgumentsData:
        """
        Get data parameter by its name.
        :param name:
        :return:
        """
        return self.parameters.get(name, DshellArgumentsData(None, False, DTT.NONE))

    def update_parameter(self, name: str, value: DshellArgumentsData):
        """
        Update parameter value.
        :param name: Name of the parameter
        :param value: New value of the parameter
        """
        if name in self.parameters and self.get_parameter(name).type == value.type:
            self.parameters[name] = value

    def get_dict_parameters(self) -> dict[str, Union[Any, None]]:
        """
        Get all parameters as a dictionary.
        :return: Dictionary of parameters with their values.
        """
        return {name: data.value for name, data in self.parameters.items()}

    def get_non_specified_parameters(self) -> list[Any]:
        """
        Get all non-specified parameters (i.e., those stored under the '*' key).
        :return: List of non-specified parameter values.
        """
        return self.parameters['*'].value

    def add_non_specified_parameters(self, values: list[Any]):
        """
        add non-specified parameters.
        :param values: New list of non-specified parameter values.
        """
        self.parameters['*'].value.append(values)


    def __repr__(self):
        return str(self.parameters)