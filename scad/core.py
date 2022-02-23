from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Tuple

from scad.scad import Command

Vector3 = Tuple[float, float, float]
Vector4 = Tuple[float, float, float, float]


class ScadObject(ABC):
    @abstractmethod
    def to_command(self) -> Command:
        raise NotImplementedError()

    @abstractmethod
    def copy(self) -> "ScadObject":
        raise NotImplementedError()

    def colored(self, color: str | Vector3 | Vector4, alpha: float = None):
        # TODO: Check values are valid.
        return SimpleModule(name="color", arguments={"c": color, "alpha": alpha}, children=[self])

    def scaled(self, vector: Vector3) -> "ScadObject":
        return SimpleModule(name="scale", arguments={"v": vector}, children=[self])

    def rotated(self, vector: Vector3) -> "ScadObject":
        return SimpleModule(name="rotate", arguments={"a": vector}, children=[self])

    def translated(self, vector: Vector3) -> "ScadObject":
        return SimpleModule(name="translate", arguments={"v": vector}, children=[self])

    def mirrored(self, vector: Vector3) -> "ScadObject":
        return SimpleModule(name="mirror", arguments={"v": vector}, children=[self])

    def rendered(self, convexity: int = None):
        return SimpleModule(name="render", arguments={"convexity": convexity}, children=[self])

    def background(self) -> "ScadObject":
        return SimpleModule(name="%", arguments={}, children=[self])

    def debug(self) -> "ScadObject":
        return SimpleModule(name="#", arguments={}, children=[self])

    def root(self) -> "ScadObject":
        return SimpleModule(name="|", arguments={}, children=[self])

    def disable(self) -> "ScadObject":
        return SimpleModule(name="*", arguments={}, children=[self])


class SimpleModule(ScadObject):
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

    def copy(self) -> ScadObject:
        return SimpleModule(self._name, self._arguments, self._children)


def box(x: float, y: float, z: float, *, center: bool = False) -> ScadObject:
    return SimpleModule(name="cube", arguments={"size": (x, y, z), "center": center}, children=[])


def cube(size: float, *, center: bool = False) -> ScadObject:
    return SimpleModule(name="cube", arguments={"size": (size, size, size), "center": center}, children=[])


def sphere(r: float, *, fa: float = None, fs: float = None, fn: float = None) -> ScadObject:
    return SimpleModule(
        name="sphere",
        arguments={
            "r": r,
            "$fa": fa,
            "$fs": fs,
            "$fn": fn,
        },
        children=[],
    )


def cylinder(
    h: float,
    r1: float,
    r2: float = None,
    *,
    center: bool = False,
    fa: float = None,
    fs: float = None,
    fn: float = None,
) -> ScadObject:
    return SimpleModule(
        name="sphere",
        arguments={
            "h": h,
            "r": r1 if r2 is None else None,
            "r1": None if r2 is None else r1,
            "r2": r2,
            "center": center,
            "$fa": fa,
            "$fs": fs,
            "$fn": fn,
        },
        children=[],
    )


def polyhedron(points: List[Vector3], faces: List[List[int]], convexity: int = 1) -> ScadObject:
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
    def __init__(self, objects: Iterable[ScadObject] = None) -> None:
        self._objects = list(objects or []) if objects is not None else []

    def add(self, scad_object) -> "Minkowski":
        self._objects.append(scad_object)
        return self

    def copy(self) -> "Minkowski":
        return Minkowski(self._objects)

    def to_command(self) -> Command:
        return Command(
            name="minkowski",
            arguments={},
            children=[child.to_command() for child in self._objects],
        )


class Hull(ScadObject):
    def __init__(self, objects: Iterable[ScadObject] = None) -> None:
        self._objects = list(objects or []) if objects is not None else []

    def add(self, scad_object) -> "Hull":
        self._objects.append(scad_object)
        return self

    def copy(self) -> "Hull":
        return Hull(self._objects)

    def to_command(self) -> Command:
        return Command(
            name="hull",
            arguments={},
            children=[child.to_command() for child in self._objects],
        )


class IDUObject(ScadObject):
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
        self._positive_objects.append(scad_object)
        return self

    def add_negative(self, scad_object: ScadObject) -> "IDUObject":
        self._negative_objects.append(scad_object)
        return self

    def intersect(self, scad_object: ScadObject) -> "IDUObject":
        self._intersection_objects.append(scad_object)
        return self

    def __iadd__(self, scad_object: ScadObject) -> "IDUObject":
        return self.add_positive(scad_object)

    def __isub__(self, scad_object: ScadObject) -> "IDUObject":
        return self.add_negative(scad_object)

    def __imul__(self, scad_object: ScadObject) -> "IDUObject":
        return self.intersect(scad_object)

    def copy(self) -> "IDUObject":
        return IDUObject(self._positive_objects, self._negative_objects)

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
