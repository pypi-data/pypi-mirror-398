"""
Utilities module
"""

from torch import Tensor


def unsqueeze_as(dst: Tensor, src: Tensor) -> Tensor:
    """
    Unsqueezes singleton dim axis according to the shape of a source tensor.
    """

    diff = len(src.shape) - len(dst.shape)

    if diff < 0:
        raise ValueError(
            "the shape of 'src' cannot be smaller than the shape of 'dst'"
        )

    for i in range(diff):
        dst = dst.unsqueeze(-1)

    return dst


def get_factory_key(key: str) -> bool:
    """
    Filtering procedure for selecting factory kwargs.
    """

    if key == "device":
        return True

    if key == "dtype":
        return True

    return False
