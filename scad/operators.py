"""
The mudule provides functions for combining OpenSCAD primitives.
"""

import itertools
from typing import Iterable

from scad.core import ScadObject
from scad.scad import Command, Module


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

    def to_command(self) -> Module:
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

    def to_command(self) -> Module:
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

    def to_command(self) -> Module:
        union_children = [child.to_command() for child in self._positive_objects]
        difference_children = [child.to_command() for child in self._negative_objects]
        intersection_children = [child.to_command() for child in self._intersection_objects]

        union = Command(name="union", arguments={}, children=union_children)
        difference_children.insert(0, union)

        difference = Command(name="difference", arguments={}, children=difference_children)
        intersection_children.insert(0, difference)

        return Command(name="intersection", arguments={}, children=intersection_children)
