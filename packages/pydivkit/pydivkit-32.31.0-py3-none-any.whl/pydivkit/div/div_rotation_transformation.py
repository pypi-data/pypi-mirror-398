# Generated code. Do not modify.
# flake8: noqa: F401, F405, F811

from __future__ import annotations

import enum
import typing

from pydivkit.core import BaseDiv, Expr, Field

from . import div_pivot


# Rotation transformation.
class DivRotationTransformation(BaseDiv):

    def __init__(
        self, *,
        type: str = "rotation",
        angle: typing.Optional[typing.Union[Expr, float]] = None,
        pivot_x: typing.Optional[div_pivot.DivPivot] = None,
        pivot_y: typing.Optional[div_pivot.DivPivot] = None,
        **kwargs: typing.Any,
    ):
        super().__init__(
            type=type,
            angle=angle,
            pivot_x=pivot_x,
            pivot_y=pivot_y,
            **kwargs,
        )

    type: str = Field(default="rotation")
    angle: typing.Union[Expr, float] = Field(
        description="Rotation angle in degrees.",
    )
    pivot_x: typing.Optional[div_pivot.DivPivot] = Field(
        description="X coordinate of the rotation pivot point.",
    )
    pivot_y: typing.Optional[div_pivot.DivPivot] = Field(
        description="Y coordinate of the rotation pivot point.",
    )


DivRotationTransformation.update_forward_refs()
