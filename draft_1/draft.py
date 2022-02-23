from abc import ABC
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Optional


class ScadTree(ABC):
    """Scad module tree. Immutable."""
    pass


@dataclass
class ScadHandle:
    tree: ScadTree


class ScadContext:
    """Manages creation of SCAD objects."""
    def enter_nodule(self, module) -> None:
        """Add module on the top of module stack."""
    def add_object(self, handle: ScadHandle) -> None:
        """Register object that will be wrapped in the currently active modules."""
    def exit_module(self) -> None:
        """Wraps all objects created since the moment of entering current module."""


g_scad_file: Optional[IO] = None

@contextmanager
def open_scad(file: Path):
    global g_scad_file
    prev_scad_file = g_scad_file
    with open(file, 'w') as f:
        yield f
    g_scad_file = prev_scad_file

@contextmanager
def translate(x: float = 0, y: float = 0, z: float = 0):
    if g_scad_file is not None:
        g_scad_file.write(f'translate([{x}, {y}, {z}]) {{')
        yield
        g_scad_file.write(f'}}')

@contextmanager
def rotate(x: float = 0, y: float = 0, z: float = 0):
    if g_scad_file is not None:
        g_scad_file.write(f'rotate([{x}, {y}, {z}]) {{')
        yield
        g_scad_file.write(f'}}')

@contextmanager
def scale(x: float = 0, y: float = 0, z: float = 0):
    if g_scad_file is not None:
        g_scad_file.write(f'scale([{x}, {y}, {z}]) {{')
        yield
        g_scad_file.write(f'}}')

def cube(x: float, y: float, z: float):
    if g_scad_file is not None:
        g_scad_file.write(f'cube([{x}, {y}, {z}]);')
