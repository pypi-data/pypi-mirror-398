from asyncio import sleep
from re import findall, sub, escape
from typing import TypeVar, Union, Any, Optional, Callable
from copy import deepcopy
from pycordViews import EasyModifiedViews
from pycordViews.views.errors import CustomIDNotFound

from discord import AutoShardedBot, Embed, Colour, PermissionOverwrite, Permissions, Guild, Member, Role, Message, Interaction, ButtonStyle
from discord.ui import Button
from discord.abc import PrivateChannel

from .errors import *
from .._DshellParser.ast_nodes import *
from ..DISCORD_COMMANDS.utils.utils_permissions import DshellPermissions
from .._DshellParser.dshell_parser import parse
from .._DshellParser.dshell_parser import to_postfix, print_ast
from .._DshellTokenizer.dshell_keywords import *
from .._DshellTokenizer.dshell_token_type import DshellTokenType as DTT
from .._DshellTokenizer.dshell_token_type import Token
from .._DshellTokenizer.dshell_tokenizer import DshellTokenizer
from .cached_messages import dshell_cached_messages
from .dshell_arguments import DshellArguments

All_nodes = TypeVar('All_nodes', IfNode, LoopNode, ElseNode, ElifNode, ArgsCommandNode, VarNode)
context = TypeVar('context', AutoShardedBot, Message, PrivateChannel, Interaction)
ButtonStyleValues: tuple = tuple(i.name for i in ButtonStyle)

class DshellInterpreteur:
    """
    Discord Dshell interpreter.
    Make what you want with Dshell code to interact with Discord !
    """

    def __init__(self, code: str, ctx: context,
                 debug: bool = False,
                 vars: Optional[str] = None,
                 vars_env: Optional[dict[str, Any]] = None):
        """
        Interpreter Dshell code
        :param code: The code to interpret. Each line must end with a newline character, except SEPARATOR and SUB_SEPARATOR tokens.
        :param ctx: The context in which the code is executed. It can be a Discord bot, a message, or a channel.
        :param debug: If True, prints the AST of the code and put the ctx to None.
        :param vars: Optional dictionary of variables to initialize in the interpreter's environment.
        :param vars_env: Optional dictionary of additional environment variables to add to the interpreter's environment.

        Note: __message_before__ (message content before edit) can be overwritten by vars_env parameter.
        """
        self.ast: list[ASTNode] = parse(DshellTokenizer(code).start(), StartNode([]))[0]
        message = ctx.message if isinstance(ctx, Interaction) else ctx
        self.env: dict[str, Any] = {
            '__ret__': None,  # environment variables, '__ret__' is used to store the return value of commands

            '__author__': message.author.id,
            '__author_name__': message.author.name,
            '__author_display_name__': message.author.display_name,
            '__author_avatar__': message.author.display_avatar.url if message.author.display_avatar else None,
            '__author_discriminator__': message.author.discriminator,
            '__author_bot__': message.author.bot,
            '__author_nick__': message.author.nick if hasattr(message.author, 'nick') else None,
            '__author_id__': message.author.id,
            '__author_add_reaction__': None, # Can be overwritten by add vars_env parameter to get the author on message add event reaction
            '__author_remove_reaction__': None, # Can be overwritten by add vars_env parameter to get the author on message remove event reaction

            '__message__': message.content,
            '__message_content__': message.content,
            '__message_id__': message.id,
            '__message_author__': message.author.id,
            '__message_before__': message.content,  # same as __message__, but before edit. Can be overwritten by add vars_env parameter
            '__message_created_at__': str(message.created_at),
            '__message_edited_at__': str(message.edited_at),
            '__message_reactions__': ListNode([str(reaction.emoji) for reaction in message.reactions]),
            '__message_add_reaction__': None, # Can be overwritten by add vars_env parameter to get the reaction added on message add event reaction
            '__message_remove_reaction__': None, # Can be overwritten by add vars_env parameter to get the reaction removed on message remove event reaction
            '__message_url__': message.jump_url if hasattr(message, 'jump_url') else None,
            '__last_message__': message.channel.last_message_id,

            '__channel__': message.channel.id,
            '__channel_name__': message.channel.name,
            '__channel_type__': message.channel.type.name if hasattr(message.channel, 'type') else None,
            '__channel_id__': message.channel.id,
            '__private_channel__': isinstance(message.channel, PrivateChannel),

            '__guild__': message.channel.guild.id,
            '__guild_name__': message.channel.guild.name,
            '__guild_id__': message.channel.guild.id,
            '__guild_members__': ListNode([member.id for member in message.channel.guild.members]),
            '__guild_member_count__': message.channel.guild.member_count,
            '__guild_icon__': message.channel.guild.icon.url if message.channel.guild.icon else None,
            '__guild_owner_id__': message.channel.guild.owner_id,
            '__guild_description__': message.channel.guild.description,
            '__guild_roles__': ListNode([role.id for role in message.channel.guild.roles]),
            '__guild_roles_count__': len(message.channel.guild.roles),
            '__guild_emojis__': ListNode([emoji.id for emoji in message.channel.guild.emojis]),
            '__guild_emojis_count__': len(message.channel.guild.emojis),
            '__guild_channels__': ListNode([channel.id for channel in message.channel.guild.channels]),
            '__guild_text_channels__': ListNode([channel.id for channel in message.channel.guild.text_channels]),
            '__guild_voice_channels__': ListNode([channel.id for channel in message.channel.guild.voice_channels]),
            '__guild_categories__': ListNode([channel.id for channel in message.channel.guild.categories]),
            '__guild_stage_channels__': ListNode([channel.id for channel in message.channel.guild.stage_channels]),
            '__guild_forum_channels__': ListNode([channel.id for channel in message.channel.guild.forum_channels]),
            '__guild_channels_count__': len(message.channel.guild.channels),

        } if message is not None and not debug else {'__ret__': None} # {} is used in debug mode, when ctx is None
        if vars_env is not None: # add the variables to the environment
            self.env.update(vars_env)
        self.vars = vars or ''
        self.ctx: context = ctx
        dshell_cached_messages.set(dict()) # save all messages view in the current scoop
        if debug:
            print_ast(self.ast)

    async def execute(self, ast: Optional[list[All_nodes]] = None):
        """
        Executes the abstract syntax tree (AST) generated from the Dshell code.

        This asynchronous method traverses and interprets each node in the AST, executing commands,
        handling control flow structures (such as if, elif, else, and loops), managing variables,
        and interacting with Discord through the provided context. It supports command execution,
        variable assignment, sleep operations, and permission handling, among other features.

        :param ast: Optional list of AST nodes to execute. If None, uses the interpreter's main AST.
        :raises RuntimeError: If an EndNode is encountered, indicating execution should be stopped.
        :raises Exception: If sleep duration is out of allowed bounds.
        """
        if ast is None:
            ast = self.ast

        for node in ast:

            if isinstance(node, StartNode):
                await self.execute(node.body)

            if isinstance(node, CommandNode):
                result = await call_function(dshell_commands[node.name], node.body, self)
                self.env[f'__{node.name}__'] = result # return value of the command
                self.env['__ret__'] = result  # global return variable for all commands

            elif isinstance(node, ParamNode):
                params = await get_params(node, self)
                self.env.update(params)  # update the environment

            elif isinstance(node, IfNode):
                elif_valid = False
                if await eval_expression(node.condition, self):
                    await self.execute(node.body)
                    continue
                elif node.elif_nodes:

                    for i in node.elif_nodes:
                        if await eval_expression(i.condition, self):
                            await self.execute(i.body)
                            elif_valid = True
                            break

                if not elif_valid and node.else_body is not None:
                    await self.execute(node.else_body.body)

            elif isinstance(node, LoopNode):
                self.env[node.variable.name.value] = 0
                for i in DshellIterator(await eval_expression(node.variable.body, self)):
                    self.env[node.variable.name.value] = i
                    c = deepcopy(node.body)
                    await self.execute(c)
                    del c

            elif isinstance(node, VarNode):

                first_node = node.body[0]
                if isinstance(first_node, IfNode):
                    self.env[node.name.value] = await eval_expression_inline(first_node, self)

                elif isinstance(first_node, EmbedNode):
                    # rebuild the embed if it already exists
                    if node.name.value in self.env and isinstance(self.env[node.name.value], Embed):
                        self.env[node.name.value] = await rebuild_embed(self.env[node.name.value], first_node.body, first_node.fields, self)
                    else:
                        self.env[node.name.value] = await build_embed(first_node.body, first_node.fields, self)

                elif isinstance(first_node, PermissionNode):
                    # rebuild the permissions if it already exists
                    if node.name.value in self.env and isinstance(self.env[node.name.value], dict):
                        self.env[node.name.value].update(await build_permission(first_node.body, self))
                    else:
                        self.env[node.name.value] = await build_permission(first_node.body, self)

                elif isinstance(first_node, UiNode):
                    # rebuild the UI if it already exists
                    if node.name.value in self.env and isinstance(self.env[node.name.value], EasyModifiedViews):
                        self.env[node.name.value] = await rebuild_ui(first_node, self.env[node.name.value], self)
                    else:
                        self.env[node.name.value] = await build_ui(first_node, self)

                else:
                    self.env[node.name.value] = await eval_expression(node.body, self)

            elif isinstance(node, SleepNode):
                sleep_time = await eval_expression(node.body, self)
                if sleep_time > 3600:
                    raise Exception(f"Sleep time is too long! ({sleep_time} seconds) - maximum is 3600 seconds)")
                elif sleep_time < 1:
                    raise Exception(f"Sleep time is too short! ({sleep_time} seconds) - minimum is 1 second)")

                await sleep(sleep_time)


            elif isinstance(node, EndNode):
                if await self.eval_data_token(node.error_message):
                    raise RuntimeError("Execution stopped - EndNode encountered")
                else:
                    raise DshellInterpreterStopExecution()

    async def eval_data_token(self, token: Token):
        """
        Eval a data token and returns its value in Python.
        :param token: The token to evaluate.
        """

        if not hasattr(token, 'type'):
            return token

        if token.type in (DTT.INT, DTT.MENTION):
            return int(token.value)
        elif token.type == DTT.FLOAT:
            return float(token.value)
        elif token.type == DTT.BOOL:
            return token.value.lower() == "true"
        elif token.type == DTT.NONE:
            return None
        elif token.type == DTT.LIST:
            return ListNode(
                [await self.eval_data_token(tok) for tok in token.value])  # token.value contient déjà une liste de Token
        elif token.type == DTT.IDENT:
            if token.value in self.env.keys():
                return self.env[token.value]
            return token.value
        elif token.type == DTT.EVAL_GROUP:
            await self.execute(parse([token.value], StartNode([]))[0]) # obliger de parser car ce il n'est pas dejà un AST
            return self.env['__ret__']
        elif token.type == DTT.STR:
            for match in findall(rf"\$({'|'.join(self.env.keys())})", token.value):
                token.value = token.value.replace('$' + match, str(self.env[match]))
            return token.value
        else:
            return token.value  # fallback


async def get_params(node: ParamNode, interpreter: DshellInterpreteur) -> dict[str, Any]:
    """
    Get the parameters from a ParamNode.
    :param node: The ParamNode to get the parameters from.
    :param interpreter: The Dshell interpreter instance.
    :return: A dictionary of parameters.
    """
    def remplacer(match) -> str:
        spacial_char = match.group(1)
        if spacial_char:
            return ''
        return match.group(4)

    variables = interpreter.vars
    regrouped_parameters: DshellArguments = await regroupe_commandes(node.body, interpreter)

    _ = DshellTokenizer(variables).start()
    regrouped_variables = await regroupe_commandes(_[0] if _ else tuple(), interpreter)

    already_modified = set()
    variables_non_specified_parameters = regrouped_variables.parameters.pop('*', None).value  # remove non-specified parameters

    for param_name, param_data in regrouped_variables.parameters.items():
        regrouped_parameters.update_parameter(param_name, param_data)
        variables = sub(rf"--([*']?)({escape(param_name)})\s+(.*)\s*?(.*)$", remplacer, variables, count=1)
        already_modified.add(param_name)

    index_variable = 0
    for var in regrouped_parameters.parameters.keys():
        if var not in already_modified:

            parameter_type = regrouped_parameters.get_parameter(var).type

            if parameter_type == DTT.PARAMETER and index_variable < len(variables_non_specified_parameters):
                regrouped_parameters.set_parameter(var, variables_non_specified_parameters[index_variable], parameter_type)  # variables_post_regrouped[index_variable] n'est pas un token donc impossible de l'évaluer ! pose problème dans les commandes qui requière autre chose que des str
                index_variable += 1

            elif parameter_type == DTT.STR_PARAMETER:
                variables_post_regrouped: list[str] = variables.strip().split(' ') if variables else []  # set uniquement pour les paramètres full str
                regrouped_parameters.set_parameter(var, ' '.join(variables_post_regrouped[index_variable:]), parameter_type)
                break

            elif parameter_type == DTT.PARAMETERS:
                regrouped_parameters.set_parameter(var, ListNode(variables_non_specified_parameters[index_variable:]), parameter_type)
                break

    for param_name, param_data in regrouped_parameters.parameters.items():
        if param_data.obligatory and param_data.value == '*':
            raise Exception(f"Parameter '{param_name}' is obligatory but not specified!")

    x = regrouped_parameters.get_dict_parameters()
    x.pop('*', None)
    print(x)
    return x


async def eval_expression_inline(if_node: IfNode, interpreter: DshellInterpreteur) -> Token:
    """
    Eval a conditional expression inline.
    :param if_node: The IfNode to evaluate.
    :param interpreter: The Dshell interpreter instance.
    """
    if await eval_expression(if_node.condition, interpreter):
        return await eval_expression(if_node.body, interpreter)
    else:
        return await eval_expression(if_node.else_body.body, interpreter)


async def eval_expression(tokens: list[Token], interpreter: DshellInterpreteur) -> Any:
    """
    Evaluates an arithmetic and logical expression.
    :param tokens: A list of tokens representing the expression.
    :param interpreter: The Dshell interpreter instance.
    """
    postfix = to_postfix(tokens, interpreter)
    stack = []

    for token in postfix:

        if token.type in {DTT.INT, DTT.FLOAT, DTT.BOOL, DTT.STR, DTT.LIST, DTT.IDENT, DTT.EVAL_GROUP}:
            stack.append(await interpreter.eval_data_token(token))

        elif token.type in (DTT.MATHS_OPERATOR, DTT.LOGIC_OPERATOR, DTT.LOGIC_WORD_OPERATOR):
            op = token.value

            if op == "not":
                a = stack.pop()
                result = dshell_operators[op][0](a)

            else:
                b = stack.pop()
                try:
                    a = stack.pop()
                except IndexError:
                    if op == "-":
                        a = 0
                    else:
                        raise SyntaxError(f"Invalid expression: {op} operator requires two operands, but only one was found.")

                result = dshell_operators[op][0](a, b)

            stack.append(result)

        else:
            raise SyntaxError(f"Unexpected token type: {token.type} - {token.value}")

    if len(stack) != 1:
        raise SyntaxError("Invalid expression: stack should contain exactly one element after evaluation.")

    return stack[0]


async def call_function(function: Callable, args: ArgsCommandNode, interpreter: DshellInterpreteur):
    """
    Call the function with the given arguments.
    It can be an async function !
    :param function: The function to call.
    :param args: The arguments to pass to the function.
    :param interpreter: The Dshell interpreter instance.
    """
    reformatted = await regroupe_commandes(args.body, interpreter)

    args = reformatted.get_non_specified_parameters()  # remove non-specified parameters from dict parameters
    kwargs = reformatted.get_dict_parameters()
    kwargs.pop('*', None)

    args.insert(0, interpreter.ctx)  # add the context as first argument

    return await function(*args, **kwargs)


async def regroupe_commandes(body: list[Token], interpreter: DshellInterpreteur, normalise: bool = False) -> DshellArguments:
    """
    Groups the command arguments in the form of a python dictionary.
    Note that you can specify the parameter you wish to pass via -- followed by the parameter name. But this is not mandatory!
    Non-mandatory parameters will be stored in a list in the form of tokens with the key \`*\`.
    The others, having been specified via a separator, will be in the form of a list of tokens with the IDENT token as key, following the separator for each argument.
    If two parameters have the same name, the last one will overwrite the previous one.
    To accept duplicates, use the SUB_SEPARATOR (~~) to create a sub-dictionary for parameters with the same name (sub-dictionary is added to the list returned).

    :param body: The list of tokens to group.
    :param interpreter: The Dshell interpreter instance.
    :param normalise: If True, normalises the arguments (make value lowercase).
    """
    # tokens to return

    instance_dhsell_arguments = DshellArguments()
    index = 0
    n = len(body)

    while index < n:

        if normalise and hasattr(body[index], 'value') and isinstance(body[index].value, str):
                body[index].value = body[index].value.lower()

        # If the current token is the last one and is a parameter marker, add it with empty value
        if index == n - 1 and body[index].type in (DTT.PARAMETER, DTT.STR_PARAMETER, DTT.PARAMETERS):
            if body[index].type == DTT.PARAMETER:
                instance_dhsell_arguments.set_parameter(body[index].value, '', DTT.PARAMETER)
            elif body[index].type == DTT.STR_PARAMETER:
                instance_dhsell_arguments.set_parameter(body[index].value, '', DTT.STR_PARAMETER)
            else:  # DTT.PARAMETERS
                instance_dhsell_arguments.set_parameter(body[index].value, ListNode([]), DTT.PARAMETERS)
            index += 1
            continue

        if body[index].type == DTT.PARAMETER:

            value = ''
            current_index = index
            while (index + 1) < n and body[index + 1].type not in (DTT.PARAMETER, DTT.STR_PARAMETER, DTT.PARAMETERS):

                value = await interpreter.eval_data_token(body[index + 1])
                index += 1
                break

            instance_dhsell_arguments.set_parameter(body[current_index].value, value, DTT.PARAMETER, obligatory=value == '*')
            index += 1

        elif body[index].type == DTT.STR_PARAMETER:

            final_argument = ''
            current_index = index

            while (index + 1) < n and body[index + 1].type not in (DTT.PARAMETER, DTT.STR_PARAMETER, DTT.PARAMETERS):

                final_argument += body[index + 1].value + ' '
                index += 1
                instance_dhsell_arguments.set_parameter(body[current_index].value, final_argument, type_=DTT.STR_PARAMETER)

            index += 1

        elif body[index].type == DTT.PARAMETERS:

            list_parameters = []
            current_index = index
            while (index + 1) < n and body[index + 1].type not in (DTT.PARAMETER, DTT.STR_PARAMETER, DTT.PARAMETERS):

                list_parameters.append(await interpreter.eval_data_token(body[index + 1]))
                index += 1
                instance_dhsell_arguments.set_parameter(body[current_index].value, ListNode(list_parameters), type_=DTT.PARAMETERS)

            index += 1

        else:
            instance_dhsell_arguments.add_non_specified_parameters(await interpreter.eval_data_token(body[index]))
            index += 1

    return instance_dhsell_arguments


async def build_embed_args(body: list[Token], fields: list[FieldEmbedNode], interpreter: DshellInterpreteur) -> tuple[dict, list[dict]]:
    """
    Builds the arguments for an embed from the command information.
    """
    regrouped_parameters = await regroupe_commandes(body, interpreter)
    args_main_embed: dict[str, list[Any]] = regrouped_parameters.get_dict_parameters()
    args_main_embed.pop('*')  # remove unspecified parameters for the embed
    args_main_embed: dict[str, Token]  # specify what it contains from now on

    args_fields: list[dict[str, Token]] = []
    for field in fields:  # do the same for the fields
        y = await regroupe_commandes(field.body, interpreter)
        args_field = y.get_dict_parameters()
        args_field.pop('*')
        args_field: dict[str, Token]
        args_fields.append(args_field)

    if 'color' in args_main_embed:
        args_main_embed['color'] = build_colour(args_main_embed['color'])  # convert color to Colour object or int

    return args_main_embed, args_fields

async def build_embed(body: list[Token], fields: list[FieldEmbedNode], interpreter: DshellInterpreteur) -> Embed:
    """
    Builds an embed from the command information.
    """

    args_main_embed, args_fields = await build_embed_args(body, fields, interpreter)
    embed = Embed(**args_main_embed)  # build the main embed
    for field in args_fields:
        embed.add_field(**field)  # add all fields

    return embed

async def rebuild_embed(embed: Embed, body: list[Token], fields: list[FieldEmbedNode], interpreter: DshellInterpreteur) -> Embed:
    """
    Rebuilds an embed from an existing embed and the command information.
    """
    args_main_embed, args_fields = await build_embed_args(body, fields, interpreter)

    for key, value in args_main_embed.items():
        if key == 'color':
            embed.colour = value
        else:
            setattr(embed, key, value)

    if args_fields:
        embed.clear_fields()
        for field in args_fields:
            embed.add_field(**field)

    return embed

def build_colour(color: Union[int, ListNode]) -> Union[Colour, int]:
    """
    Builds a Colour object from an integer or a ListNode.
    :param color: The color to build.
    :return: A Colour object.
    """
    if isinstance(color, int):
        return color
    elif isinstance(color, (ListNode, list)):
        if not len(color) == 3:
            raise ValueError(f"Color must be a list of 3 integers, not {len(color)} elements !")
        return Colour.from_rgb(*color)
    else:
        raise TypeError(f"Color must be an integer or a ListNode, not {type(color)} !")

async def build_ui_parameters(ui_node: UiNode, interpreter: DshellInterpreteur):
    """
    Builds the parameters for a UI component from the UiNode.
    Can accept buttons and select menus.
    :param ui_node:
    :param interpreter:
    :return:
    """
    for ident_component in range(len(ui_node.buttons)):
        regrouped_parameters = await regroupe_commandes(ui_node.buttons[ident_component].body, interpreter, normalise=True)
        args_button: dict[str, list[Any]] = regrouped_parameters.get_dict_parameters()

        code = args_button.pop('code', None)
        style = args_button.pop('style', 'primary').lower()
        custom_id = args_button.pop('custom_id', str(ident_component))

        if not isinstance(custom_id, str):
            raise TypeError(f"Button custom_id must be a string, not {type(custom_id)} !")

        if style not in ButtonStyleValues:
            raise ValueError(f"Button style must be one of {', '.join(ButtonStyleValues)}, not '{style}' !")

        args_button['custom_id'] = custom_id
        args_button['style'] = ButtonStyle[style]
        args = args_button.pop('*', ())
        yield args, args_button, code

async def build_ui(ui_node: UiNode, interpreter: DshellInterpreteur) -> EasyModifiedViews:
    """
    Builds a UI component from the UiNode.
    Can accept buttons and select menus.
    :param ui_node:
    :param interpreter:
    :return:
    """
    view = EasyModifiedViews()

    async for args, args_button, code in build_ui_parameters(ui_node, interpreter):
        b = Button(**args_button)

        view.add_items(b)
        view.set_callable(b.custom_id, _callable=ui_button_callback, data={'code': code})

    return view

async def rebuild_ui(ui_node : UiNode, view: EasyModifiedViews, interpreter: DshellInterpreteur) -> EasyModifiedViews:
    """
    Rebuilds a UI component from an existing EasyModifiedViews.
    :param view:
    :param interpreter:
    :return:
    """
    async for args, args_button, code in build_ui_parameters(ui_node, interpreter):
        try:
            ui = view.get_ui(args_button['custom_id'])
        except CustomIDNotFound:
            raise ValueError(f"Button with custom_id '{args_button['custom_id']}' not found in the view !")

        ui.label = args_button.get('label', ui.label)
        ui.style = args_button.get('style', ui.style)
        ui.emoji = args_button.get('emoji', ui.emoji)
        ui.disabled = args_button.get('disabled', ui.disabled)
        ui.url = args_button.get('url', ui.url)
        ui.row = args_button.get('row', ui.row)
        new_code = code if code is not None else view.get_callable_data(args_button['custom_id'])['code']
        view.set_callable(args_button['custom_id'], _callable=ui_button_callback, data={'code': args_button.get('code', code)})

    return view


async def ui_button_callback(button: Button, interaction: Interaction, data: dict[str, Any]):
    """
    Callback for UI buttons.
    Executes the code associated with the button.
    :param button:
    :param interaction:
    :param data:
    :return:
    """
    code = data.pop('code', None)
    if code is not None:
        local_env = {
            '__ret__': None,
            '__guild__': interaction.guild.name if interaction.guild else None,
            '__channel__': interaction.channel.name if interaction.channel else None,
            '__author__': interaction.user.name,
            '__author_display_name__': interaction.user.display_name,
            '__author_avatar__': interaction.user.display_avatar.url if interaction.user.display_avatar else None,
            '__author_discriminator__': interaction.user.discriminator,
            '__author_bot__': interaction.user.bot,
            '__author_nick__': interaction.user.nick if hasattr(interaction.user, 'nick') else None,
            '__author_id__': interaction.user.id,
            '__message__': interaction.message.content if hasattr(interaction.message, 'content') else None,
            '__message_id__': interaction.message.id if hasattr(interaction.message, 'id') else None,
            '__channel_name__': interaction.channel.name if interaction.channel else None,
            '__channel_type__': interaction.channel.type.name if hasattr(interaction.channel, 'type') else None,
            '__channel_id__': interaction.channel.id if interaction.channel else None,
            '__private_channel__': isinstance(interaction.channel, PrivateChannel),
        }
        local_env.update(data)
        x = DshellInterpreteur(code, interaction, debug=False)
        x.env.update(local_env)
        await x.execute()
    else:
        await interaction.response.defer(invisible=True)

    data.update({'code': code})

async def build_permission(body: list[Token], interpreter: DshellInterpreteur) -> dict[
    Union[Member, Role], PermissionOverwrite]:
    """
    Builds a dictionary of PermissionOverwrite objects from the command information.
    """
    args_permissions: DshellArguments = await regroupe_commandes(body, interpreter, normalise=True)

    print(args_permissions)

    x = args_permissions.get_dict_parameters()
    x.pop('*', None)

    return DshellPermissions(x).get_permission_overwrite(interpreter.ctx.channel.guild)



class DshellIterator:
    """
    Used to transform anything into an iterable
    """

    def __init__(self, data):
        self.data = data if isinstance(data, (str, list, ListNode)) else range(int(data))
        self.current = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.current >= len(self.data):
            self.current = 0
            raise StopIteration

        value = self.data[self.current]
        self.current += 1
        return value


