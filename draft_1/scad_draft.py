from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple


ScadType = bool | int | float | List["ScadType"] | Tuple["ScadType", ...]


def format_value(value: ScadType) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, (list, tuple)):
        return f"[{', '.join(str(item) for item in value)}]"
    else:
        raise ValueError("Unsupported type")


def format_command(name: str, arguments: Dict[str, ScadType]) -> str:
    argument_strings = (f"{argument}={format_value(value)}" for argument, value in arguments.items())
    return f"{name}({argument_strings})"


@dataclass
class Command:
    name: str
    arguments: Dict[str, ScadType]

    def to_scad(self, indent: int) -> List[str]:
        return [indent(indent, format_command(self.name, self.arguments))]

    def __mul__(self, modifier: "Modifier"):
        return modifier.apply(self)


@dataclass
class ModifierBlock(Command):
    children: List[Command]

    def to_scad(self, indent: int) -> List[str]:
        command_str = indent(indent, format_command(self.name, self.arguments))
        if len(self.children) == 1:
            result = [command_str + " {"]
            for child in self.children:
                result.extend(child.to_scad(indent + 4))
            result.append("}")
        else:
            result = [command_str]
            result.extend(self.children[0].to_scad(indent))
            result.append("}")
        return result


def cube(size: float | Tuple[float, float, float], center: bool = False) -> Command:
    return Command("cube", {"size": size, "center": center})


class Modifier(ABC):
    @abstractmethod
    def apply(self, command: Command) -> Command:
        raise NotImplementedError


@dataclass
class Translate(Modifier):
    vector: Tuple[float, float, float]

    def apply(self, command: Command) -> Command:
        return ModifierBlock("translate", {"v": self.vector}, [command])
