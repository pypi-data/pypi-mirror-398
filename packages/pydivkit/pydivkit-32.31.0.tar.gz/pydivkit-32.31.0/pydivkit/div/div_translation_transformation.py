# Generated code. Do not modify.
# flake8: noqa: F401, F405, F811

from __future__ import annotations

import enum
import typing

from pydivkit.core import BaseDiv, Expr, Field

from . import div_translation


# Translation transformation.
class DivTranslationTransformation(BaseDiv):

    def __init__(
        self, *,
        type: str = "translation",
        x: typing.Optional[div_translation.DivTranslation] = None,
        y: typing.Optional[div_translation.DivTranslation] = None,
        **kwargs: typing.Any,
    ):
        super().__init__(
            type=type,
            x=x,
            y=y,
            **kwargs,
        )

    type: str = Field(default="translation")
    x: typing.Optional[div_translation.DivTranslation] = Field(
        description="X coordinate of the translation.",
    )
    y: typing.Optional[div_translation.DivTranslation] = Field(
        description="Y coordinate of the translation.",
    )


DivTranslationTransformation.update_forward_refs()
