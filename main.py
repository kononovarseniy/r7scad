"""
Creates something.
"""

from pathlib import Path

from scad.core import ScadObject
from scad.operators import IDUObject
from scad.primitives import box, sphere


def test() -> ScadObject:
    """
    Create something.
    """
    result = IDUObject()
    result += box(10, 10, 5, center=True).translated((0, 0, -1)).named("Translated big box")
    result -= box(4, 4, 4, center=True)
    result += box(10, 10, 5)
    result *= sphere(7).translated((0, 0, 1))

    return (
        result.rotated((-45, 0, 0))
        .rendered(10)
        .commented("Render it now!")
        .colored("green", alpha=0.5)
        .commented(
            """
            This file is autogenerated by r7scad.
            It is not supposed to be edited manually.
            """
        )
    )


test().to_command().write_to(Path("test.scad"))
