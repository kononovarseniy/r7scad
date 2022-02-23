from pathlib import Path

from scad.core import ScadObject
from scad.operators import IDUObject
from scad.primitives import box, sphere


def test() -> ScadObject:
    result = IDUObject()
    result += box(10, 10, 5, center=True).translated((0, 0, -1))
    result -= box(4, 4, 4, center=True)
    result += box(10, 10, 5)
    result *= sphere(7).translated((0, 0, 1))

    return result.rotated((-45, 0, 0)).rendered(10).colored("green", alpha=0.5)


test().to_command().write_to(Path("test.scad"))
