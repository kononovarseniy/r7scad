"""
The module provides an interface for creating OpenSCAD objects.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Tuple

from scad.scad import Command

Vector3 = Tuple[float, float, float]
Vector4 = Tuple[float, float, float, float]


class ScadObject(ABC):
    """
    Base class for all SCAD objects.
    """

    @abstractmethod
    def to_command(self) -> Command:
        """
        Create SCAD command from the object.
        """
        raise NotImplementedError()

    def colored(self, color: str | Vector3 | Vector4, alpha: float = None):
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


class SimpleModule(ScadObject):
    """
    SCAD object representing a specific SCAD command.
    """

    def __init__(self, name: str, arguments: Dict[str, Any], children: Iterable[ScadObject]) -> None:
        self._name = name
        self._arguments = dict(arguments)
        self._children = list(children)

    def to_command(self) -> Command:
        return Command(
            name=self._name,
            arguments=self._arguments,
            children=[child.to_command() for child in self._children],
        )


def box(x: float, y: float, z: float, *, center: bool = False) -> ScadObject:
    """
    Creates a box with the specified side lengths.
    """
    return SimpleModule(name="cube", arguments={"size": (x, y, z), "center": center}, children=[])


def cube(size: float, *, center: bool = False) -> ScadObject:
    """
    Creates a cube with the specified side length.
    """
    return SimpleModule(name="cube", arguments={"size": (size, size, size), "center": center}, children=[])


def sphere(radius: float, *, fa: float = None, fs: float = None, fn: float = None) -> ScadObject:
    """
    Creates a sphere of given radius
    """
    return SimpleModule(
        name="sphere",
        arguments={
            "r": radius,
            "$fa": fa,
            "$fs": fs,
            "$fn": fn,
        },
        children=[],
    )


def cylinder(
    height: float,
    r_bottom: float,
    r_top: float = None,
    *,
    center: bool = False,
    fa: float = None,
    fs: float = None,
    fn: float = None,
) -> ScadObject:
    """
    Creates a cylinder with given parameters.
    """
    return SimpleModule(
        name="sphere",
        arguments={
            "h": height,
            "r": r_bottom if r_top is None else None,
            "r1": None if r_top is None else r_bottom,
            "r2": r_top,
            "center": center,
            "$fa": fa,
            "$fs": fs,
            "$fn": fn,
        },
        children=[],
    )


def polyhedron(points: List[Vector3], faces: List[List[int]], convexity: int = 1) -> ScadObject:
    """
    Creates a polyhedron.
    """
    return SimpleModule(
        name="polyhedron",
        arguments={
            "points": points,
            "faces": faces,
            "convexity": convexity,
        },
        children=[],
    )


class Minkowski(ScadObject):
    """
    Minkowski sum of shild objects.
    """

    def __init__(self, objects: Iterable[ScadObject] = None) -> None:
        self._objects = list(objects or []) if objects is not None else []

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
        self._objects = list(objects or []) if objects is not None else []

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
        self._positive_objects = list(positive_objects) if positive_objects is not None else []
        self._negative_objects = list(negative_objects) if negative_objects is not None else []
        self._intersection_objects = list(intersection_objects) if intersection_objects is not None else []

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
