"""
Validation module

Contains routines for input validation of both the masked_norm and
affine_masked_norm procedures.
"""

from __future__ import annotations

from torch import Tensor
from torch import Size as Shape
from torch import float32, float64, float16, bfloat16
from torch import float8_e4m3fn, float8_e5m2
from torch import bool as bool_dtype


# PyTorch doesn't offer abstract type hinting for xfloat* dtypes
# you can work around this by verifying membership on a set of xfloat* dtypes
float_dtype = {
    float64,
    float32,
    float16,
    bfloat16,
    float8_e4m3fn,
    float8_e5m2
}


def validate_masked_norm(inpt: Tensor, mask: Optional[Tensor]) -> None:
    """
    Validates the input of the masked_norm procedure.
    """

    if not inpt.dtype in float_dtype:
        raise ValueError("'inpt' must be a tensor of xfloat* dtype")

    if mask is None:
        return

    if not mask.dtype == bool_dtype:
        # mask tensor must be necessarily of bool dtype
        raise ValueError("'mask' must be a tensor of bool dtype")

    if not len(inpt.shape) > len(mask.shape):
        raise ValueError(
            "the shape of 'inpt' must be larger than the shape of 'mask'"
        )

    # mask shape must partially match input shape
    for axis, dim in enumerate(zip(inpt.shape, mask.shape)):
        inpt_dim, mask_dim = dim
        if inpt_dim != mask_dim:
            raise ValueError(
                f"dim mismatch between 'inpt' and 'mask' on axis {axis}"
        )


def validate_affine_masked_norm(
    inpt: Tensor,
    mask: Optional[Tensor],
    weight: Tensor,
    bias: Optional[Tensor]
) -> None:
    """
    Validates the input of the affine_masked_norm procedure.
    """

    validate_masked_norm(inpt, mask)

    # weight and bias must have proper dtype
    if not weight.dtype in float_dtype:
        raise ValueError("'weight' must be a tensor of xfloat* dtype")

    if not bias is None and not bias.dtype in float_dtype:
        raise ValueError("'bias' must be a tensor of xfloat* dtype")


    # if no mask is passed, weight and bias tensor must have shape
    # inpt.shape[0: -1]
    if mask is None:
        shape = inpt.shape[0: -1]

        if weight.shape != shape:
            raise ValueError(
                f"'weight' must be a tensor with shape {shape}"
            )

        if not bias is None and bias.shape != shape:
            raise ValueError(
                f"'bias' must be a tensor with shape {shape}"
            )

        return

    # if a mask is passed, weight and bias must have the same shape as mask
    if weight.shape != mask.shape:
        raise ValueError(
            "'weight' must have the same shape as 'mask'"
        )

    if not bias is None and bias.shape != mask.shape:
        raise ValueError(
            "'bias' must have the same shape as 'mask'"
        )

