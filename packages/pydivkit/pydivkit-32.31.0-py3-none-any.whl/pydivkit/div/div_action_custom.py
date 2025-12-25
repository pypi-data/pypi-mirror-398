# Generated code. Do not modify.
# flake8: noqa: F401, F405, F811

from __future__ import annotations

import enum
import typing

from pydivkit.core import BaseDiv, Expr, Field


# Custom action. A handler is required on the host. The parameters can be passed
# via the action payload.
class DivActionCustom(BaseDiv):

    def __init__(
        self, *,
        type: str = "custom",
        **kwargs: typing.Any,
    ):
        super().__init__(
            type=type,
            **kwargs,
        )

    type: str = Field(default="custom")


DivActionCustom.update_forward_refs()
