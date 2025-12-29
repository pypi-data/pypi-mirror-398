"""
Nn module
"""

from __future__ import annotations
from typing import Any, Optional

from torch import Tensor
from torch.nn import Module
from torch.nn.modules.lazy import LazyModuleMixin
from torch.nn.parameter import UninitializedParameter
from torch.nn.init import ones_, zeros_

from .functional import masked_norm
from .functional import batched_masked_norm
from .functional import affine_masked_norm
from .functional import batched_affine_masked_norm
from .util import get_factory_key


class MaskedNorm(Module):
    """
    MaskedNorm class
    """

    def __init__(
        self: MaskedNorm,
        batched: Optional[bool] = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        """

        super().__init__(*args, **kwargs)
        self.batched = batched

    def forward(
        self: MaskedNorm,
        inpt: Tensor,
        mask: Optional[Tensor] = None,
    ) -> Tensor:
        """
        """

        if self.batched:
            return batched_masked_norm(inpt, mask)

        return masked_norm(inpt, mask)


class LazyMaskedNorm(MaskedNorm, LazyModuleMixin):
    """
    LazyMaskedNorm class

    Stateful implementation of MaskedNorm is crazy. And a lazy variation of a
    MaskedNorm stateful implementation is absolutely ludicrous. You can use
    it, but it simply serves as inheritence reference for
    LazyAffineMaskedNorm.
    """

    def __init__(
        self: LazyMaskedNorm,
        batched: Optional[bool] = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        """

        super().__init__(batched, *args, **kwargs)
        super(MaskedNorm, self).__init__()

    def initialize_parameters(
        self: LazyMaskedNorm,
        inpt: Tensor,
        mask: Optional[Tensor] = None,
    ) -> None:
        """
        Lazy-specific method for initializing parameters according to the
        input.
        """

        pass


class LazyAffineMaskedNorm(LazyMaskedNorm):
    """
    LazyAffineMaskedNorm class

    As a lazy module, the weight and bias parameters are initialized
    dynamically as the forward method is called.
    """

    # affine transformation parameters
    weight: UninitializedParameter
    bias: UninitializedParameter

    def __init__(
        self: LazyAffineMaskedNorm,
        batched: Optional[bool] = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        """

        super().__init__(batched, *args, **kwargs)

        # the module's weight and bias parameters must be initialized with the
        # correct "device" and "dtype" that are passed onto the module
        factory_kwargs = dict(filter(get_factory_key, kwargs))

        self.weight = UninitializedParameter(**factory_kwargs)
        self.bias = UninitializedParameter(**factory_kwargs)

    def initialize_parameters(
        self: LazyAffineMaskedNorm,
        inpt: Tensor,
        mask: Optional[Tensor] = None,
    ) -> None:
        """
        Lazy-specific method for initializing parameters according to the
        input.
        """

        if self.has_uninitialized_params():

            # allocate memory to the parameters accordingly
            if mask is None:
                shape = inpt.shape[0: -1]
                if self.batched:
                    shape = inpt.shape[1: ]
                self.weight.materialize(shape)
                self.bias.materialize(shape)
            else:
                self.weight.materialize(mask.shape)
                self.bias.materialize(mask.shape)

            # fill allocated parameters with initial values
            ones_(self.weight)
            zeros_(self.bias)

    def forward(
        self: LazyMaskedNorm,
        inpt: Tensor,
        mask: Optional[Tensor] = None
    ) -> Tensor:
        """
        """

        self.initialize_parameters(inpt, mask)

        if self.batched:
            return batched_affine_masked_norm(
                inpt,
                mask,
                self.weight,
                self.bias
            )

        return affine_masked_norm(inpt, mask, self.weight, self.bias)
