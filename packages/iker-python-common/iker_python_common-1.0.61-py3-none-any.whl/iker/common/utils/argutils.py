import argparse
import dataclasses
import inspect
import typing
from collections.abc import Sequence
from typing import Any

from iker.common.utils.typeutils import is_identical_type

__all__ = [
    "ParserTreeNode",
    "ParserTree",
    "ArgParseSpec",
    "argparse_spec",
    "make_argparse"
]

import sys


class ParserTreeNode(object):
    """
    Represents a node in the parser tree, holding a command, its parser, and any child nodes. Each node may have
    subparsers and a list of child nodes representing subcommands.

    :param command: The command string for this node.
    :param parser: The ``ArgumentParser`` associated with this node.
    """

    def __init__(self, command: str, parser: argparse.ArgumentParser):
        self.command = command
        self.parser = parser
        self.subparsers = None
        self.child_nodes: list[ParserTreeNode] = []


def construct_parser_tree(
    root_node: ParserTreeNode,
    command_chain: list[str],
    command_key_prefix: str,
    **kwargs,
) -> list[ParserTreeNode]:
    """
    Constructs a parser tree by traversing or creating nodes for each command in the command chain. Returns the path
    from the ``root_node`` to the last node in the chain.

    :param root_node: The root node of the parser tree.
    :param command_chain: A list of command strings representing the path.
    :param command_key_prefix: Prefix for command keys in the parser.
    :param kwargs: Additional keyword arguments for parser creation.
    :return: A list of ``ParserTreeNode`` objects representing the path from root to the last command.
    """
    node_path = [root_node]
    if len(command_chain) == 0:
        return node_path

    node = root_node
    for depth, command in enumerate(command_chain):
        if node.subparsers is None:
            node.subparsers = node.parser.add_subparsers(dest=f"{command_key_prefix}:{depth}")
        for child_node in node.child_nodes:
            if child_node.command == command:
                node = child_node
                break
        else:
            if depth == len(command_chain) - 1:
                child_parser = node.subparsers.add_parser(command, **kwargs)
            else:
                child_parser = node.subparsers.add_parser(command)
            child_node = ParserTreeNode(command, child_parser)
            node.child_nodes.append(child_node)
            node = child_node
        node_path.append(node)

    return node_path


class ParserTree(object):
    """
    Represents a tree structure for managing ``argparse`` parsers and subcommands. Provides methods to add subcommand
    parsers and parse arguments, returning the command chain and parsed namespace.

    :param root_parser: The root ``ArgumentParser``.
    :param command_key_prefix: Prefix for command keys in the parser tree.
    """

    def __init__(self, root_parser: argparse.ArgumentParser, command_key_prefix: str = "command"):
        self.root_node = ParserTreeNode("", root_parser)
        self.command_key_prefix = command_key_prefix

    def add_subcommand_parser(self, command_chain: list[str], **kwargs) -> argparse.ArgumentParser:
        """
        Adds a subcommand parser for the specified command chain, creating intermediate nodes as needed.

        :param command_chain: A list of command strings representing the subcommand path.
        :param kwargs: Additional keyword arguments for parser creation.
        :return: The ``ArgumentParser`` for the last command in the chain.
        """
        *_, last_node = construct_parser_tree(self.root_node, command_chain, self.command_key_prefix, **kwargs)
        return last_node.parser

    def parse_args(self, args: list[str] | None = None) -> tuple[list[str], argparse.Namespace]:
        """
        Parses the provided argument list, returning the command chain and the parsed namespace.

        :param args: The list of arguments to parse. If ``None``, parses ``sys.argv``.
        :return: A tuple containing the list of command strings and the parsed ``Namespace``.
        """
        # Before Python 3.12 the ``exit_on_error`` attribute does not take effect properly
        # if unknown arguments encountered. We have to employ this workaround
        if sys.version_info < (3, 12):
            if self.root_node.parser.exit_on_error:
                known_args_namespace = self.root_node.parser.parse_args(args)
            else:
                known_args_namespace, unknown_args = self.root_node.parser.parse_known_args(args)
                if len(unknown_args or []) > 0:
                    raise argparse.ArgumentError(None, f"unrecognized arguments '{unknown_args}'")
        else:
            known_args_namespace = self.root_node.parser.parse_args(args)

        command_pairs = []
        namespace = argparse.Namespace()
        for key, value in dict(vars(known_args_namespace)).items():
            if key.startswith(self.command_key_prefix) and value is not None:
                command_pairs.append((key, value))
            else:
                setattr(namespace, key, value)

        return list(command for _, command in sorted(command_pairs)), namespace


@dataclasses.dataclass(frozen=True)
class ArgParseSpec(object):
    """
    Specification for an argument to be added to an ``ArgumentParser``. Allows detailed configuration of argument
    properties such as ``flag``, ``name``, ``type``, ``action``, ``default``, ``choices``, and help text.

    :param flag: The optional flag for the argument (e.g., '-f').
    :param name: The name of the argument (e.g., '--file').
    :param action: The action to be taken by the argument parser.
    :param default: The default value for the argument.
    :param type: The type of the argument value.
    :param choices: A list of valid choices for the argument.
    :param required: Whether the argument is required.
    :param help: The help text for the argument.
    """
    flag: str | None = None
    name: str | None = None
    action: str | None = None
    default: Any = None
    type: typing.Type | None = None
    choices: list[Any] | None = None
    required: bool | None = None
    help: str | None = None

    def make_kwargs(self) -> dict[str, Any]:
        """
        Constructs a dictionary of keyword arguments for ``ArgumentParser.add_argument``, omitting any that are
        ``None``.

        :return: A dictionary of argument properties suitable for ``ArgumentParser.add_argument``.
        """
        kwargs = dict(
            action=self.action,
            default=self.default,
            type=self.type,
            choices=self.choices,
            required=self.required,
            help=self.help,
        )

        return {key: value for key, value in kwargs.items() if value is not None}


argparse_spec = ArgParseSpec


def make_argparse(func, parser: argparse.ArgumentParser = None) -> argparse.ArgumentParser:
    """
    Automatically generates an ``ArgumentParser`` for the given function by inspecting its signature and parameter
    annotations. Supports ``ArgParseSpec`` for detailed argument configuration.

    :param func: The function whose parameters will be used to generate arguments.
    :param parser: An optional ``ArgumentParser`` to add arguments to. If ``None``, a new parser is created.
    :return: The ``ArgumentParser`` with arguments added based on the function signature.
    """
    if parser is None:
        parser = argparse.ArgumentParser()

    def is_type_of(a: Any, *bs) -> bool:
        return any(is_identical_type(a, b, strict_optional=False, covariant=True) for b in bs)

    sig = inspect.signature(func)
    for name, param in sig.parameters.items():

        arg_name = f"--{name.replace('_', '-')}"

        if param.annotation is None:
            arg_type = str
        elif is_type_of(param.annotation, str, Sequence[str]):
            arg_type = str
        elif is_type_of(param.annotation, int, Sequence[int]):
            arg_type = int
        elif is_type_of(param.annotation, float, Sequence[float]):
            arg_type = float
        elif is_type_of(param.annotation, bool, Sequence[bool]):
            arg_type = bool
        else:
            arg_type = str

        arg_action = "append" if typing.get_origin(param.annotation) in {list, Sequence} else None
        arg_default = None if param.default is inspect.Parameter.empty else param.default

        if isinstance(arg_default, ArgParseSpec):
            spec = arg_default
            spec = dataclasses.replace(spec,
                                       name=spec.name or arg_name,
                                       type=spec.type if spec.type is not None else arg_type,
                                       action=spec.action if spec.action is not None else arg_action)

            if spec.flag is None:
                parser.add_argument(spec.name, **spec.make_kwargs())
            else:
                parser.add_argument(spec.flag, spec.name, **spec.make_kwargs())

        else:
            parser.add_argument(arg_name,
                                type=arg_type,
                                action=arg_action,
                                required=arg_default is None,
                                default=arg_default)

    return parser
