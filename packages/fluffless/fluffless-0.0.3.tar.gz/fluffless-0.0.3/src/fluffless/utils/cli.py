""" Runner module to provide entrypoint decorator functions for CLI interface.

Example usage of CLI entrypoints:

    PARSER = _BASE_PARSER.add_parser("awoo")

    @entrypoint(PARSER)
    def awoo() -> None:
        print("Awoo!")

    cli.run(parse_args(), Config())
"""
import argparse
import importlib
import pkgutil
from types import ModuleType
from typing import Any, Callable

from rich_argparse import _lazy_rich, RichHelpFormatter

from fluffless.models.base_model import BaseModel


class CustomRichHelpFormatter(RichHelpFormatter):
    """ Custom argparse formatter class to use Rich colouring, add default values, and preserve raw formatting. """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Extend the formatter styles and highlights with custom values.
        self.styles |= {
            "argparse.todo": "red",
            "argparse.quote": "green",
            "argparse.menu_item": "cyan",
            "argparse.default": "italic dark_cyan",
        }

        self.highlights.extend([
            r"(?P<todo>todo|TODO)",
            r"(?P<quote>'.*?')",
            r"\n\s+(?P<menu_item>\w+):",
        ])

    def _rich_split_lines(self, text: _lazy_rich.Text, width: int) -> _lazy_rich.Lines:
        """ Define a custom line split method to preserve raw text formatting when displaying help strings. """
        text = text.copy()
        text.expand_tabs(8)  # Textwrap expands tabs first.
        return text.wrap(self.console, width)

    def _get_help_string(self, action: argparse.Action) -> str | None:
        """ Add default help string arguments for actions which require them. """
        # Do not add default argument strings for specific argparse actions.
        if tuple(action.option_strings) in (
            ("-v", "--verbose"),  # Standard verbosity flag.
        ):
            return super()._get_help_string(action)

        if (
            "%(default)" not in (action.help or "")  # Do not add default strings if they were already present.
            and action.default != "==SUPPRESS=="     # Default value for the `--help` argument.
            and action.default is not None           # Do not add default strings for null defaults.
            # Argparse `nargs` may take the values ("?", "*", "+"). The value "+" requires one or more value
            # as input, and as such does not take a default. Both "?" and "*" permit no input, and thus are
            # able to take default arguments, and should have their help strings modified.
            and (action.option_strings or action.nargs in ("?", "*"))
        ):
            # Do not add a leading space if the default is intentionally on a new line.
            padding = " " if not (help_str := action.help or "").endswith("\n") else ""
            action.help = f"{help_str}{padding}Defaults to %(default)s."

        return super()._get_help_string(action)


RunnerFunction = Callable[[argparse.Namespace, BaseModel], None]

ROOT_PARSER = argparse.ArgumentParser(formatter_class=RichHelpFormatter, add_help=False)
ROOT_PARSER.add_argument(
    "-h", "--help", action="help", default=argparse.SUPPRESS, help="Show this help message and exit.",
)
ROOT_SUBPARSERS = ROOT_PARSER.add_subparsers(required=True)
ROOT_PARSER.set_defaults(_entry_func=None)  # Defaults to None, until overridden by the chosen runner function.


def base_parser(
    is_leaf: bool, formatter_class: type[argparse.HelpFormatter] = CustomRichHelpFormatter,
) -> argparse.ArgumentParser:
    """ Baseline parser to provide standard arguments to all parsers using it as a parent.

    For non-leaf parsers, only the `--help` action is added, as they are not intended to be invoked directly.

    Args:
        is_leaf (bool): If the parser should be invoked directly or not, and thus have the appropriate arguments added.
        formatter_class (type[argparse.HelpFormatter], optional): Formatter class to use for help blocks. \
                                                                  Defaults to `CustomRichHelpFormatter`.

    Returns:
        argparse.ArgumentParser: Argument parser to be used as a parent, providing standardised arguments.
    """
    # Do not add a default help string, defer to the specific runner to define it.
    parser = argparse.ArgumentParser(formatter_class=formatter_class, add_help=False)
    parser.add_argument(
        "-h", "--help", action="help", default=argparse.SUPPRESS, help="Show this help message and exit.",
    )
    if is_leaf:
        parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity of logger output.")

    return parser


def add_parser(
    name: str,
    subparsers: argparse._SubParsersAction | None = None,
    parents: list[argparse.ArgumentParser] | None = None,
    is_leaf: bool = True,
    formatter_class: type[argparse.HelpFormatter] = CustomRichHelpFormatter,
    **kwargs,
) -> argparse.ArgumentParser:
    """ Create a parser under a given subparsers group, or the root subparsers group if one is not provided.

    If a description was not provided for the subparser, uses the help string as a description.

    Args:
        name (str): The name of the command to use when invoking the parser.
        subparsers (argparse._SubParsersAction | None, optional): Subparsers group to add the new parser to. \
                                                                  Defaults to None, where the root subparser \
                                                                  group will be used by default.
        parents (list[argparse.ArgumentParser] | None, optional): List of parent parsers to inherit from. \
                                                                  Defaults to None, where `base_parser` will be used.
        is_leaf (bool): If the parser should be invoked directly or not, and thus have the appropriate arguments added.
        formatter_class (type[argparse.HelpFormatter], optional): Formatter class to use for help blocks. \
                                                                  Defaults to `CustomRichHelpFormatter`.
        **kwargs: Additional keyword arguments to pass to `subparser.add_parser()`.


    Returns:
        argparse.ArgumentParser: The created parser from the given arguments.
    """
    add_parser_kwargs: dict[str, Any] = {
        "name": name,
        "parents": parents or [base_parser(is_leaf, formatter_class)],
        "formatter_class": formatter_class,
        "description": kwargs.get("description") or kwargs.get("help"),
        "add_help": False,
    }
    add_parser_kwargs.update(kwargs)
    return (subparsers or ROOT_SUBPARSERS).add_parser(**add_parser_kwargs)  # type: ignore[invalid-argument-type]


def parse_args(*args, **kwargs) -> argparse.Namespace:
    """ Parse the full set of command line arguments through the root parser. """
    return ROOT_PARSER.parse_args(*args, **kwargs)


def run(args: argparse.Namespace, config: BaseModel) -> None:
    """ Execute the runner function with arguments and config, or print help if it was provided. """
    if args._entry_func:
        args._entry_func(args, config)
    else:
        ROOT_PARSER.print_help()


def entrypoint(parser: argparse.ArgumentParser) -> Callable:
    """ Decorate a function as the main runner function for a given parser. """
    def entrypoint_decorator(runner_function: RunnerFunction) -> RunnerFunction:
        """ Set default entry function for the parser. """
        parser.set_defaults(_entry_func=runner_function)
        return runner_function

    return entrypoint_decorator


def import_package_modules(package: ModuleType) -> None:
    """ Recursively import all modules of a given package.

    Used with the runner entrypoint paradigm, as all individual runner files are
    required to be imported to be parsed appropriately. Forcing a recursive import
    on `myproject.runners` before parsing arguments ensures the load order is valid.
    """
    for _, name, is_pkg in pkgutil.walk_packages(package.__path__):
        # Resolve the full name of the module and import it.
        module = importlib.import_module(f"{package.__name__}.{name}")

        # If the module itself is a package, call the import function recursively.
        if is_pkg:
            import_package_modules(module)
