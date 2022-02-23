"""
The module provides an interface for creating OpenSCAD objects.
"""

from abc import ABC, abstractmethod
import textwrap
from typing import Any, Dict, Iterable, List, Optional, Tuple

from scad.scad import Command, Commented, Module

Vector3 = Tuple[float, float, float]
Vector4 = Tuple[float, float, float, float]


class ScadObject(ABC):
    """
    Base class for all SCAD objects.
    """

    def search(self, name_parts: Tuple[str, ...]) -> List["ScadObject"]:
        """
        Recursively search for all descendants with the given name.
        """
        result = []
        for child in self.iter_children():
            result.extend(child.search(name_parts))
        return result

    def __item__(self, name: str | Tuple[str, ...]) -> "ScadObject":
        name_parts = (name,) if isinstance(name, str) else name
        children = self.search(name_parts)
        if len(children) == 1:
            return children[0]
        if len(children) == 0:
            raise KeyError(str(name))
        raise KeyError(f"Found multiple descendants with the name {name}")

    @abstractmethod
    def iter_children(self) -> Iterable["ScadObject"]:
        """
        Returns an iterable with all child objects.
        """
        raise NotImplementedError()

    @abstractmethod
    def to_command(self) -> Module:
        """
        Create SCAD command from the object.
        """
        raise NotImplementedError()

    def named(self, name: str, hidden_names: Iterable[str] = None) -> "ScadObject":
        """
        A new object with given name.
        """
        return NamedWrapper(self, name, hidden_names)

    def commented(self, comment: str, *, dedent=True) -> "ScadObject":
        """
        A new object that will be commented in .scad file.
        """
        if dedent:
            comment = textwrap.dedent(comment).strip("\n")
        return CommentedWrapper(self, comment)

    def with_hidden_descendants(self, hidden_names: Iterable[str]) -> "ScadObject":
        """
        A new object with given name.
        """
        return NamedWrapper(self, None, hidden_names)

    def colored(self, color: str | Vector3 | Vector4, alpha: float = None) -> "ScadObject":
        """
        A new object of the specified color.
        """
        # TODO: Check values are valid.
        return SimpleModule(name="color", arguments={"c": color, "alpha": alpha}, children=[self])

    def scaled(self, vector: Vector3) -> "ScadObject":
        """
        A new object with scaling applied.
        """
        return SimpleModule(name="scale", arguments={"v": vector}, children=[self])

    def rotated(self, vector: Vector3) -> "ScadObject":
        """
        A new object with rotation applied.
        """
        return SimpleModule(name="rotate", arguments={"a": vector}, children=[self])

    def translated(self, vector: Vector3) -> "ScadObject":
        """
        A new object with translation applied.
        """
        return SimpleModule(name="translate", arguments={"v": vector}, children=[self])

    def mirrored(self, vector: Vector3) -> "ScadObject":
        """
        A new mirrored object.
        """
        return SimpleModule(name="mirror", arguments={"v": vector}, children=[self])

    def rendered(self, convexity: int = None):
        """
        A new object with forced CGAL rendering.
        """
        return SimpleModule(name="render", arguments={"convexity": convexity}, children=[self])

    def background(self) -> "ScadObject":
        """
        A new object that will be treated as a background object by OpenSCAD.
        """
        return SimpleModule(name="%", arguments={}, children=[self])

    def debug(self) -> "ScadObject":
        """
        A new object that will be treated as a debug object by OpenSCAD.
        """
        return SimpleModule(name="#", arguments={}, children=[self])

    def root(self) -> "ScadObject":
        """
        A new object that will be treated as a root object by OpenSCAD.
        """
        return SimpleModule(name="|", arguments={}, children=[self])

    def disable(self) -> "ScadObject":
        """
        A new object that will be ignored by OpenSCAD.
        """
        return SimpleModule(name="*", arguments={}, children=[self])


class NamedWrapper(ScadObject):
    """
    Gives names to objects.
    """

    def __init__(self, child: ScadObject, object_name: str = None, hidden_names: Iterable[str] = None) -> None:
        super().__init__()

        self._child = child
        self._object_name = object_name
        self._hidden_names = {} if hidden_names is None else set(hidden_names)

    @property
    def name(self) -> Optional[str]:
        """
        The name of the object.
        """
        return self._object_name

    @property
    def hidden_names(self) -> Iterable[str]:
        """
        List of names of hidden descendants.
        """
        return self._hidden_names

    def search(self, name_parts: Tuple[str, ...]) -> List["ScadObject"]:
        if name_parts[0] == self.name:
            name_parts = name_parts[1:]
            if len(name_parts) == 0:
                return [self]
        if name_parts[0] in self.hidden_names:
            return []
        result = []
        for child in self.iter_children():
            result.extend(child.search(name_parts))
        return result

    def iter_children(self) -> Iterable["ScadObject"]:
        return [self._child]

    def to_command(self) -> Module:
        if self.name is not None:
            return Commented(self.name, self._child.to_command())
        return self._child.to_command()


class CommentedWrapper(ScadObject):
    """
    Adds comments to objects.
    """

    def __init__(self, child: ScadObject, comment: str) -> None:
        super().__init__()

        self._child = child
        self._comment = comment

    def iter_children(self) -> Iterable["ScadObject"]:
        return [self._child]

    def to_command(self) -> Module:
        return Commented(self._comment, self._child.to_command())


class SimpleModule(ScadObject):
    """
    SCAD object representing a specific SCAD command.
    """

    def __init__(self, name: str, arguments: Dict[str, Any], children: Iterable[ScadObject]) -> None:
        super().__init__()

        self._name = name
        self._arguments = dict(arguments)
        self._children = list(children)

    def iter_children(self) -> Iterable["ScadObject"]:
        return self._children

    def to_command(self) -> Module:
        return Command(
            name=self._name,
            arguments=self._arguments,
            children=[child.to_command() for child in self._children],
        )
