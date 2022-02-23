from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


def format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, (list, tuple)):
        return f"[{', '.join(str(item) for item in value)}]"
    elif isinstance(value, str):
        # TODO: Excape string.
        return f'"{value}"'
    else:
        raise ValueError("Unsupported type")


def format_argument(name: str, value: Any) -> str:
    return f"{name}={format_value(value)}"


def format_command_arguments(arguments: Dict[str, Any]) -> str:
    return ", ".join(format_argument(name, value) for name, value in arguments.items() if value is not None)


def indent(indentation: int, line: str) -> str:
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


@dataclass
class Command:
    name: str
    arguments: Dict[str, Any]
    children: List["Command"]

    def to_scad(self) -> List[str]:
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

    def write_to(self, file: Path) -> None:
        file.write_text("\n".join(self.to_scad()))
