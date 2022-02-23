"""
The module provides an interface for creating OpenSCAD objects.
"""

import itertools
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Tuple

from scad.scad import Command

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
    def to_command(self) -> Command:
        """
        Create SCAD command from the object.
        """
        raise NotImplementedError()

    def named(self, name: str, hidden_names: Iterable[str] = None) -> "ScadObject":
        """
        A new object with given name.
        """
        return NamedWrapper(self, name, hidden_names)

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

    def to_command(self) -> Command:
        return self._child.to_command()


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

    def to_command(self) -> Command:
        return Command(
            name=self._name,
            arguments=self._arguments,
            children=[child.to_command() for child in self._children],
        )


class Minkowski(ScadObject):
    """
    Minkowski sum of shild objects.
    """

    def __init__(self, objects: Iterable[ScadObject] = None) -> None:
        super().__init__()

        self._objects = list(objects or []) if objects is not None else []

    def iter_children(self) -> Iterable["ScadObject"]:
        return self._objects

    def add(self, scad_object) -> "Minkowski":
        """
        Add child object.
        """
        self._objects.append(scad_object)
        return self

    def to_command(self) -> Command:
        return Command(
            name="minkowski",
            arguments={},
            children=[child.to_command() for child in self._objects],
        )


class Hull(ScadObject):
    """
    Convex hull of child objects.
    """

    def __init__(self, objects: Iterable[ScadObject] = None) -> None:
        super().__init__()

        self._objects = list(objects or []) if objects is not None else []

    def iter_children(self) -> Iterable["ScadObject"]:
        return self._objects

    def add(self, scad_object) -> "Hull":
        """
        Add child object.
        """
        self._objects.append(scad_object)
        return self

    def to_command(self) -> Command:
        return Command(
            name="hull",
            arguments={},
            children=[child.to_command() for child in self._objects],
        )


class IDUObject(ScadObject):
    """
    Intersection, Difference, Union object.

    Represents the following structure:
    intersection {
        difference {
            union { positive_obects }
            negative_objcts
        }
        intersection_objects
    }

    Objects are processed regardless of the order in which they were added.
    """

    def __init__(
        self,
        positive_objects: Iterable[ScadObject] = None,
        negative_objects: Iterable[ScadObject] = None,
        intersection_objects: Iterable[ScadObject] = None,
    ) -> None:
        super().__init__()

        self._positive_objects = list(positive_objects) if positive_objects is not None else []
        self._negative_objects = list(negative_objects) if negative_objects is not None else []
        self._intersection_objects = list(intersection_objects) if intersection_objects is not None else []

    def iter_children(self) -> Iterable["ScadObject"]:
        return itertools.chain(self._positive_objects, self._negative_objects, self._intersection_objects)

    def add_positive(self, scad_object: ScadObject) -> "IDUObject":
        """
        Add object to union.
        """
        self._positive_objects.append(scad_object)
        return self

    def add_negative(self, scad_object: ScadObject) -> "IDUObject":
        """
        Add object to difference.
        It will be subtracted from the union of all positive objects.
        """
        self._negative_objects.append(scad_object)
        return self

    def intersect(self, scad_object: ScadObject) -> "IDUObject":
        """
        Add object to intersection.
        """
        self._intersection_objects.append(scad_object)
        return self

    def __iadd__(self, scad_object: ScadObject) -> "IDUObject":
        return self.add_positive(scad_object)

    def __isub__(self, scad_object: ScadObject) -> "IDUObject":
        return self.add_negative(scad_object)

    def __imul__(self, scad_object: ScadObject) -> "IDUObject":
        return self.intersect(scad_object)

    def to_command(self) -> Command:
        positive_commands = [child.to_command() for child in self._positive_objects]
        negative_commands = [child.to_command() for child in self._negative_objects]
        intersection_commands = [child.to_command() for child in self._intersection_objects]

        return Command(
            name="intersection",
            arguments={},
            children=[
                Command(
                    name="difference",
                    arguments={},
                    children=[
                        Command(
                            name="union",
                            arguments={},
                            children=positive_commands,
                        )
                    ]
                    + negative_commands,
                )
            ]
            + intersection_commands,
        )
