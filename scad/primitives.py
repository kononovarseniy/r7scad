"""
The mudule provides functions for creating OpenSCAD primitives.
"""

from typing import List

from scad.core import ScadObject, SimpleModule, Vector3


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
