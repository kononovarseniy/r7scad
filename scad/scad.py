"""
The module provides tools for creating .scad files.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence


def format_value(value: Any) -> str:
    """
    Convert Python object to OpenSCAD representation.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple)):
        return f"[{', '.join(str(item) for item in value)}]"
    if isinstance(value, str):
        # TODO: Excape string.
        return f'"{value}"'

    raise ValueError("Unsupported type")


def format_argument(name: str, value: Any) -> str:
    """
    Format named argument.
    """
    return f"{name}={format_value(value)}"


def format_command_arguments(arguments: Dict[str, Any]) -> str:
    """
    Format command arguments.
    """
    return ", ".join(format_argument(name, value) for name, value in arguments.items() if value is not None)


def indent(indentation: int, line: str) -> str:
    """
    Add indentation to the line.
    """
    return " " * indentation + line


debug_commands = set("%#|*")

commands_to_skip_if_less_than_two_children = {
    "union",
    "difference",
    "intersection",
    "minkowski",
    "hull",
}

commands_to_skip_if_no_children = (
    commands_to_skip_if_less_than_two_children
    | debug_commands
    | {
        "render",
    }
)


class Module(ABC):
    """
    OpenSCAD base class.
    """

    @abstractmethod
    def to_scad(self) -> List[str]:
        """
        Convert the object to OpenSCAD representation.
        """
        raise NotImplementedError()

    def write_to(self, file: Path) -> None:
        """
        Write the object ot .scad file.
        """
        file.write_text("\n".join(self.to_scad()))


@dataclass
class Command(Module):
    """
    OpenSCAD command.
    """

    name: str
    arguments: Dict[str, Any]
    children: Sequence[Module]

    def to_scad(self) -> List[str]:
        """
        Convert the object to OpenSCAD representation.
        """
        if self.name in debug_commands:
            header = self.name
        else:
            header = f"{self.name}({format_command_arguments(self.arguments)})"

        if len(self.children) == 0:
            if self.name in commands_to_skip_if_no_children:
                lines = []
            else:
                lines = [header + ";"]
        elif len(self.children) == 1:
            if self.name in commands_to_skip_if_less_than_two_children:
                lines = []
            else:
                lines = [header]
            lines.extend(self.children[0].to_scad())
        else:
            lines = [header + " {"]
            for child in self.children:
                lines.extend(indent(4, line) for line in child.to_scad())
            lines.append("}")

        return lines
