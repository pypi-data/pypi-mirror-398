"""
ekta_chalk - A simple command-line argument parser like Commander.js

Example usage:
    from ekta_chalk import Program

    program = Program()
    program.name("myapp")
    program.version("1.0.0")
    program.description("My awesome CLI app")

    program.option("-d, --debug", "Enable debug mode")
    program.option("-c, --config <path>", "Path to config file")
    program.argument("<file>", "File to process")

    @program.action
    def main(file, options):
        print(f"Processing {file}")
        if options.debug:
            print("Debug mode enabled")

    program.parse()
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

__version__ = "0.1.0"
__all__ = ["Program", "Command", "Option", "Argument"]


@dataclass
class Option:
    """Represents a command-line option."""

    short: str | None
    long: str | None
    description: str
    required: bool = False
    value_name: str | None = None  # e.g., <path> means it takes a value
    default: Any = None

    @property
    def name(self) -> str:
        """Get the option name (without dashes)."""
        if self.long:
            return self.long.lstrip("-").replace("-", "_")
        if self.short:
            return self.short.lstrip("-")
        return ""

    @property
    def takes_value(self) -> bool:
        """Check if this option takes a value."""
        return self.value_name is not None


@dataclass
class Argument:
    """Represents a positional argument."""

    name: str
    description: str
    required: bool = True
    default: Any = None
    variadic: bool = False  # e.g., <files...>


@dataclass
class Options:
    """Container for parsed options."""

    _data: dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            return object.__getattribute__(self, name)
        return self._data.get(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            self._data[name] = value

    def __repr__(self) -> str:
        return f"Options({self._data})"

    def to_dict(self) -> dict[str, Any]:
        """Convert options to a dictionary."""
        return dict(self._data)


class Command:
    """Represents a command or subcommand."""

    def __init__(self, name: str = "", parent: Command | None = None):
        self._name = name
        self._parent = parent
        self._version: str | None = None
        self._description: str = ""
        self._options: list[Option] = []
        self._arguments: list[Argument] = []
        self._commands: dict[str, Command] = {}
        self._action_handler: Callable[..., Any] | None = None
        self._aliases: list[str] = []

        # Add default help option
        self._options.append(Option(
            short="-h",
            long="--help",
            description="Display help for command"
        ))

    def name(self, name: str) -> Command:
        """Set the command name."""
        self._name = name
        return self

    def version(self, version: str) -> Command:
        """Set the version (adds -V, --version option)."""
        self._version = version
        self._options.append(Option(
            short="-V",
            long="--version",
            description="Output the version number"
        ))
        return self

    def description(self, desc: str) -> Command:
        """Set the command description."""
        self._description = desc
        return self

    def alias(self, alias: str) -> Command:
        """Add an alias for this command."""
        self._aliases.append(alias)
        return self

    def option(
        self,
        flags: str,
        description: str = "",
        default: Any = None
    ) -> Command:
        """
        Add an option.

        Flags format: "-s, --long" or "-s, --long <value>" or "--long <value>"
        Use <value> for required option values, [value] for optional.
        """
        opt = self._parse_option_flags(flags)
        opt.description = description
        opt.default = default
        self._options.append(opt)
        return self

    def required_option(
        self,
        flags: str,
        description: str = "",
        default: Any = None
    ) -> Command:
        """Add a required option."""
        opt = self._parse_option_flags(flags)
        opt.description = description
        opt.default = default
        opt.required = True
        self._options.append(opt)
        return self

    def argument(
        self,
        name: str,
        description: str = "",
        default: Any = None
    ) -> Command:
        """
        Add a positional argument.

        Use <name> for required, [name] for optional, <name...> for variadic.
        """
        arg = self._parse_argument(name)
        arg.description = description
        arg.default = default
        self._arguments.append(arg)
        return self

    def command(self, name: str, description: str = "") -> Command:
        """
        Add a subcommand.

        Returns the new Command object for chaining.
        """
        cmd = Command(name, parent=self)
        cmd._description = description
        self._commands[name] = cmd
        return cmd

    def action(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        """
        Set the action handler (can be used as decorator).

        The handler receives positional arguments followed by an Options object.
        """
        self._action_handler = fn
        return fn

    def _parse_option_flags(self, flags: str) -> Option:
        """Parse option flags string into an Option object."""
        short = None
        long = None
        value_name = None

        # Extract value placeholder if present
        value_match = re.search(r"[<\[]([^>\]]+)[>\]]", flags)
        if value_match:
            value_name = value_match.group(1)
            flags = re.sub(r"\s*[<\[][^>\]]+[>\]]", "", flags)

        parts = [p.strip() for p in flags.split(",")]
        for part in parts:
            part = part.strip()
            if part.startswith("--"):
                long = part
            elif part.startswith("-"):
                short = part

        return Option(
            short=short,
            long=long,
            description="",
            value_name=value_name
        )

    def _parse_argument(self, name: str) -> Argument:
        """Parse argument specification into an Argument object."""
        variadic = "..." in name
        required = name.startswith("<")

        # Extract just the name
        clean_name = re.sub(r"[<>\[\].]", "", name)

        return Argument(
            name=clean_name,
            description="",
            required=required,
            variadic=variadic
        )

    def _find_option(self, flag: str) -> Option | None:
        """Find an option by its short or long flag."""
        for opt in self._options:
            if opt.short == flag or opt.long == flag:
                return opt
        return None

    def help(self) -> str:
        """Generate help text."""
        lines = []

        # Usage line
        usage_parts = ["Usage:"]
        if self._parent:
            usage_parts.append(self._parent._name)
        usage_parts.append(self._name or "program")

        if self._commands:
            usage_parts.append("[command]")
        if self._options:
            usage_parts.append("[options]")
        for arg in self._arguments:
            if arg.variadic:
                usage_parts.append(f"<{arg.name}...>" if arg.required else f"[{arg.name}...]")
            else:
                usage_parts.append(f"<{arg.name}>" if arg.required else f"[{arg.name}]")

        lines.append(" ".join(usage_parts))

        # Description
        if self._description:
            lines.append("")
            lines.append(self._description)

        # Arguments section
        if self._arguments:
            lines.append("")
            lines.append("Arguments:")
            for arg in self._arguments:
                name_display = arg.name
                if arg.variadic:
                    name_display += "..."
                lines.append(f"  {name_display:<20} {arg.description}")

        # Options section
        if self._options:
            lines.append("")
            lines.append("Options:")
            for opt in self._options:
                flags = []
                if opt.short:
                    flags.append(opt.short)
                if opt.long:
                    long_part = opt.long
                    if opt.value_name:
                        long_part += f" <{opt.value_name}>"
                    flags.append(long_part)
                flag_str = ", ".join(flags)
                default_str = f" (default: {opt.default})" if opt.default is not None else ""
                required_str = " (required)" if opt.required else ""
                lines.append(f"  {flag_str:<25} {opt.description}{default_str}{required_str}")

        # Commands section
        if self._commands:
            lines.append("")
            lines.append("Commands:")
            for name, cmd in self._commands.items():
                alias_str = f" ({', '.join(cmd._aliases)})" if cmd._aliases else ""
                lines.append(f"  {name}{alias_str:<20} {cmd._description}")
            lines.append("")
            lines.append(f"Run '{self._name or 'program'} <command> --help' for more information on a command.")

        return "\n".join(lines)

    def parse(self, args: list[str] | None = None) -> tuple[list[Any], Options]:
        """
        Parse command-line arguments.

        Returns tuple of (positional_args, options).
        """
        if args is None:
            args = sys.argv[1:]

        options = Options()
        positional: list[Any] = []

        # Initialize defaults
        for opt in self._options:
            if opt.name and opt.name not in ("help", "version"):
                if opt.default is not None:
                    setattr(options, opt.name, opt.default)
                elif opt.takes_value:
                    setattr(options, opt.name, None)
                else:
                    setattr(options, opt.name, False)

        i = 0
        while i < len(args):
            arg = args[i]

            # Check for subcommand
            if arg in self._commands:
                subcmd = self._commands[arg]
                return subcmd.parse(args[i + 1:])

            # Check for command alias
            for _name, cmd in self._commands.items():
                if arg in cmd._aliases:
                    return cmd.parse(args[i + 1:])

            # Handle options
            if arg.startswith("-"):
                # Handle --option=value format
                if "=" in arg:
                    flag, value = arg.split("=", 1)
                    found_opt = self._find_option(flag)
                    if found_opt and found_opt.takes_value:
                        setattr(options, found_opt.name, value)
                        i += 1
                        continue

                found_opt = self._find_option(arg)

                if found_opt:
                    if found_opt.long == "--help" or found_opt.short == "-h":
                        print(self.help())
                        sys.exit(0)
                    elif found_opt.long == "--version" or found_opt.short == "-V":
                        if self._version:
                            print(self._version)
                        sys.exit(0)
                    elif found_opt.takes_value:
                        if i + 1 < len(args):
                            setattr(options, found_opt.name, args[i + 1])
                            i += 2
                            continue
                        else:
                            print(f"Error: Option {arg} requires a value", file=sys.stderr)
                            sys.exit(1)
                    else:
                        setattr(options, found_opt.name, True)
                else:
                    print(f"Error: Unknown option: {arg}", file=sys.stderr)
                    print("Run with --help for usage information", file=sys.stderr)
                    sys.exit(1)
            else:
                positional.append(arg)

            i += 1

        # Check required options
        for opt in self._options:
            if opt.required and getattr(options, opt.name) is None:
                print(f"Error: Required option {opt.long or opt.short} is missing", file=sys.stderr)
                sys.exit(1)

        # Handle variadic arguments
        arg_values: list[Any] = []
        for idx, arg_spec in enumerate(self._arguments):
            if arg_spec.variadic:
                # Collect remaining positional args
                arg_values.append(positional[idx:] if idx < len(positional) else [])
            elif idx < len(positional):
                arg_values.append(positional[idx])
            elif arg_spec.required:
                print(f"Error: Missing required argument: {arg_spec.name}", file=sys.stderr)
                print(self.help())
                sys.exit(1)
            else:
                arg_values.append(arg_spec.default)

        # Execute action if defined
        if self._action_handler:
            self._action_handler(*arg_values, options)

        return arg_values, options


class Program(Command):
    """
    Main program class - entry point for creating CLI applications.

    Example:
        program = Program()
        program.name("myapp").version("1.0.0")
        program.option("-d, --debug", "Enable debug mode")

        @program.action
        def main(options):
            if options.debug:
                print("Debug enabled!")

        program.parse()
    """

    def __init__(self, name: str = ""):
        super().__init__(name)

    def parse(self, args: list[str] | None = None) -> tuple[list[Any], Options]:
        """Parse arguments and execute the appropriate action."""
        return super().parse(args)


def program(name: str = "") -> Program:
    """Create a new Program instance (convenience function)."""
    return Program(name)
