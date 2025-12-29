"""
Nns module testing
"""

from __future__ import annotations

from math import sqrt

from torch import Tensor, tensor, ones_like, zeros_like, ones
from torch.nn import BatchNorm1d, LayerNorm, InstanceNorm1d, GroupNorm

from masked_norm import masked_norm, batched_masked_norm
from masked_norm import MaskedNorm
from masked_norm import LazyMaskedNorm

from masked_norm import affine_masked_norm
from masked_norm import batched_affine_masked_norm
from masked_norm import LazyAffineMaskedNorm
from masked_norm.validation import validate_affine_masked_norm

from .tensor_test_case import TensorTestCase


class TestMaskedNorm(TensorTestCase):
    """
    'MaskedNorm' testing unit
    """

    def assertApprox(
        self: TestMaskedNorm,
        x: Tensor,
        y: Tensor,
        msg: str | None = None
    ) -> None:
        """
        Element-wise approximation assertion method
        """

        cond = (x - y).abs() < self.eps
        cond = cond.all()

        self.assertTrue(cond, msg)

    def setUp(self: TestMaskedNorm) -> None:
        """
        """

        self.inpt_1 = tensor(
            [
                [0.00, 1.00, 2.00],
                [3.00, 4.00, 5.00]
            ]
        )

        self.inpt_2 = tensor(
            [
                [
                    [0.00, 1.00, 2.00],
                    [3.00, 4.00, 5.00],
                    [6.00, 7.00, 8.00],
                    [9.00, 10.0, 11.0]
                ],
                [
                    [12.0, 13.0, 14.0],
                    [15.0, 16.0, 17.0],
                    [18.0, 19.0, 20.0],
                    [21.0, 22.0, 23.0]
                ]
            ]
        )

        self.eps = 1e-6

    def test_forward_mask_0(self: TestMaskedNorm) -> None:
        """
        """

        mask_0 = None

        layer = MaskedNorm()
        layer_out = layer(self.inpt_1, mask_0)

        functional_out = masked_norm(self.inpt_1, mask_0)

        self.assertEqTensor(layer_out, functional_out)

    def test_forward_mask_1(self: TestMaskedNorm) -> None:
        """
        """

        mask_1 = tensor(
            [True, False]
        )

        layer = MaskedNorm()
        layer_out = layer(self.inpt_1, mask_1)

        functional_out = masked_norm(self.inpt_1, mask_1)

        self.assertEqTensor(layer_out, functional_out)

    def test_forward_batched_mask_0(self: TestMaskedNorm) -> None:
        """
        """

        mask_0 = None

        layer = MaskedNorm(batched=True)
        layer_out = layer(self.inpt_1, mask_0)

        functional_out = batched_masked_norm(self.inpt_1, mask_0)

        self.assertEqTensor(layer_out, functional_out)

    def test_forward_batched_mask_1(self: TestMaskedNorm) -> None:
        """
        """

        mask_2 = tensor(
            [True, True, False]
        )

        layer = MaskedNorm(batched=True)
        layer_out = layer(self.inpt_1, mask_2)

        functional_out = batched_masked_norm(self.inpt_1, mask_2)

        self.assertEqTensor(layer_out, functional_out)

    def test_batch_norm(self: TestMaskedNorm) -> None:
        """
        Asserts the equivalency between the MaskedNorm and BatchNorm
        implementations
        """

        masked_norm_layer = MaskedNorm()
        batch_norm_layer = BatchNorm1d(4, eps=0.0, affine=False)

        inpt = self.inpt_2.transpose(0, 1)
        shape = inpt.shape
        inpt = inpt.flatten(start_dim=1)
        masked_norm_out = masked_norm_layer(inpt)
        masked_norm_out = masked_norm_out.view(*shape)
        masked_norm_out = masked_norm_out.transpose(0, 1)

        batch_norm_out = batch_norm_layer(self.inpt_2)

        # variance biasness bessel correction
        batch_norm_out *= sqrt(5/6)

        self.assertApprox(masked_norm_out, batch_norm_out)

    def test_layer_norm(self: TestMaskedNorm) -> None:
        """
        Asserts the equivalency between the MaskedNorm and LayerNorm
        implementations
        """

        masked_norm_layer = MaskedNorm()
        layer_norm_layer = LayerNorm((4, 3), eps=0.0, elementwise_affine=False)

        inpt = self.inpt_2
        shape = inpt.shape
        inpt = inpt.flatten(start_dim=1)
        masked_norm_out = masked_norm_layer(inpt)
        masked_norm_out = masked_norm_out.view(*shape)

        layer_norm_out = layer_norm_layer(self.inpt_2)

        # variance biassness bessel correction
        layer_norm_out *= sqrt(11/12)

        self.assertApprox(masked_norm_out, layer_norm_out)

    def test_instance_norm(self: TestMaskedNorm) -> None:
        """
        Asserts the equivalency between the MaskedNorm and InstanceNorm
        implementations
        """

        masked_norm_layer = MaskedNorm()
        inst_norm_layer = InstanceNorm1d(4, eps=0.0, affine=False)

        mask_shape = self.inpt_2.shape[0: 2]
        mask = ones(mask_shape).to(bool)

        masked_norm_out = masked_norm_layer(self.inpt_2, mask)

        inst_norm_out = inst_norm_layer(self.inpt_2)

        # variance biassness bessel correction
        inst_norm_out *= sqrt(2/3)

        self.assertApprox(masked_norm_out, inst_norm_out)

    def test_group_norm(self: TestMaskedNorm) -> None:
        """
        Asserts the equivalency between the MaskedNorm and GroupNorm
        implementations
        """

        n_channels = 4
        n_groups = 2

        masked_norm_layer = MaskedNorm()
        group_norm_layer = GroupNorm(
            n_groups,
            n_channels,
            eps=0.0,
            affine=False
        )

        inpt = self.inpt_2.unfold(1, n_groups, n_channels // n_groups)

        inpt = inpt.transpose(2, 3)
        inpt = inpt.flatten(start_dim=0, end_dim=1)

        shape = inpt.shape
        inpt = inpt.flatten(start_dim=1)
        masked_norm_out = masked_norm_layer(inpt)
        masked_norm_out = masked_norm_out.view(*shape)
        masked_norm_out = masked_norm_out.reshape((2, 4, 3))

        group_norm_out = group_norm_layer(self.inpt_2)

        # variance biassness bessel correction
        group_norm_out *= sqrt(5/6)

        self.assertApprox(masked_norm_out, group_norm_out)


class TestLazyMaskedNorm(TensorTestCase):
    """
    'LazyMaskedNorm' testing unit
    """

    def setUp(self: TestLazyMaskedNorm) -> None:
        """
        """

        self.inpt = tensor(
            [
                [0.00, 1.00, 2.00],
                [3.00, 4.00, 5.00]
            ]
        )

    def test_init_mask_0(self: TestLazyMaskedNorm) -> None:
        """
        """

        mask_0 = None

        try:
            layer = LazyMaskedNorm()
            layer.forward(self.inpt, mask_0)
            self.assertTrue(True)

        except:
            self.assertTrue(False)

    def test_init_mask_1(self: TestLazyMaskedNorm) -> None:
        """
        """

        mask_1 = tensor(
            [True, False]
        )

        try:
            layer = LazyMaskedNorm()
            layer.forward(self.inpt, mask_1)
            self.assertTrue(True)

        except:
            self.assertTrue(False)


class TestLazyAffineMaskedNorm(TensorTestCase):
    """
    'LazyAffineMaskedNorm' testing unit
    """

    def setUp(self: TestAffineMaskedNorm) -> None:
        """
        """

        self.inpt = tensor(
            [
                [0.00, 1.00, 2.00],
                [3.00, 4.00, 5.00]
            ]
        )

    def test_param_init_mask_0(self: TestLazyAffineMaskedNorm) -> None:
        """
        """

        mask_0 = None

        layer = LazyAffineMaskedNorm()

        layer.forward(self.inpt, mask_0)

        try:
            validate_affine_masked_norm(
                self.inpt,
                mask_0,
                layer.weight,
                layer.bias
            )

            self.assertTrue(True)

        except:
            self.assertTrue(False)

    def test_param_init_mask_1(self: TestLazyAffineMaskedNorm) -> None:
        """
        """

        mask_1 = tensor(
            [True, False]
        )

        layer = LazyAffineMaskedNorm()

        layer.forward(self.inpt, mask_1)

        try:
            validate_affine_masked_norm(
                self.inpt,
                mask_1,
                layer.weight,
                layer.bias
            )
            self.assertTrue(True)

        except:
            self.assertTrue(False)

        weight_1 = ones_like(mask_1)
        bias_1 = zeros_like(mask_1)

        self.assertEqTensor(layer.weight, weight_1)
        self.assertEqTensor(layer.bias, bias_1)

    def test_forward_mask_0(self: TestLazyAffineMaskedNorm) -> None:
        """
        """

        mask_0 = None

        layer = LazyAffineMaskedNorm()

        layer_out = layer(self.inpt, mask_0)

        functional_out = affine_masked_norm(
            self.inpt,
            mask_0,
            layer.weight,
            layer.bias
        )

        self.assertEqTensor(layer_out, functional_out)

    def test_forward_mask_1(self: TestLazyAffineMaskedNorm) -> None:
        """
        """

        mask_1 = tensor(
            [True, False]
        )

        layer = LazyAffineMaskedNorm()

        layer_out = layer(self.inpt, mask_1)

        functional_out = affine_masked_norm(
            self.inpt,
            mask_1,
            layer.weight,
            layer.bias
        )

        self.assertEqTensor(layer_out, functional_out)

    def test_forward_batched_mask_0(self: TestLazyAffineMaskedNorm) -> None:
        """
        """

        mask_0 = None

        layer = LazyAffineMaskedNorm(batched=True)

        layer_out = layer(self.inpt, mask_0)

        functional_out = batched_affine_masked_norm(
            self.inpt,
            mask_0,
            layer.weight,
            layer.bias
        )

        self.assertEqTensor(layer_out, functional_out)

    def test_forward_batched_mask_1(self: TestLazyAffineMaskedNorm) -> None:
        """
        """

        mask_1 = tensor(
            [True, True, False]
        )

        layer = LazyAffineMaskedNorm(batched=True)

        layer_out = layer(self.inpt, mask_1)

        functional_out = batched_affine_masked_norm(
            self.inpt,
            mask_1,
            layer.weight,
            layer.bias
        )

        self.assertEqTensor(layer_out, functional_out)
