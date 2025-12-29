"""
Validation module testing
"""

from __future__ import annotations

from torch import Tensor, tensor
from masked_norm.validation import validate_masked_norm
from masked_norm.validation import validate_affine_masked_norm

from .tensor_test_case import TensorTestCase


class TestValidateMaskedNorm(TensorTestCase):
    """
    'validate_masked_norm' testing unit
    """

    def setUp(self: TestValidateMaskedNorm) -> None:
        """
        """

        self.inpt = tensor(
            [
                [0.00, 1.00, 2.00],
                [3.00, 4.00, 5.00]
            ]
        )

    def test_mask_0(self: TestValidateMaskedNorm) -> None:
        """
        """

        mask_0 = None

        try:
            validate_masked_norm(self.inpt, mask_0)
            self.assertTrue(True)

        except:
            self.assertTrue(False)

    def test_mask_1(self: TestValidateMaskedNorm) -> None:
        """
        """

        mask_1 = tensor(
            [True, False]
        )

        try:
            validate_masked_norm(self.inpt, mask_1)
            self.assertTrue(True)

        except:
            self.assertTrue(False)

    def test_mask_3(self: TestValidateMaskedNorm) -> None:
        """
        """

        mask_3 = tensor(
            [
                [
                    [True]
                ]
            ]
        )

        with self.assertRaisesRegex(
            ValueError,
            "the shape of 'inpt' must be larger than the shape of 'mask'"
        ):
            validate_masked_norm(self.inpt, mask_3)

    def test_mask_4(self: TestValidateMaskedNorm) -> None:
        """
        """

        mask_4 = tensor(
            [True]
        )

        with self.assertRaisesRegex(
            ValueError,
            "dim mismatch between 'inpt' and 'mask'"
        ):

            validate_masked_norm(self.inpt, mask_4)


class TestValidateAffineMaskedNorm(TensorTestCase):
    """
    'validate_affine_masked_norm' testing unit
    """

    def setUp(self: TestValidateAffineMaskedNorm) -> None:
        """
        """


        self.inpt = tensor(
            [
                [0.00, 1.00, 2.00],
                [3.00, 4.00, 5.00]
            ]
        )

    def test_mask_0_weight_1_bias_0(
        self: TestValidateAffineMaskedNorm
    ) -> None:
        """
        """

        mask_0 = None

        weight_1 = tensor(
            [1.0, 1.0]
        )

        bias_0 = None

        try:
            validate_affine_masked_norm(self.inpt, mask_0, weight_1, bias_0)
            self.assertTrue(True)

        except:
            self.assertTrue(False)

    def test_mask_0_weight_1_bias_1(
        self: TestValidateAffineMaskedNorm
    ) -> None:
        """
        """

        mask_0 = None

        weight_1 = tensor(
            [1.0, 1.0]
        )

        bias_1 = tensor(
            [0.0, 0.0]
        )

        try:
            validate_affine_masked_norm(self.inpt, mask_0, weight_1, bias_1)
            self.assertTrue(True)

        except:
            self.assertTrue(False)

    def test_mask_0_weight_2_bias_0(
            self: TestValidateAffineMaskedNorm
    ) -> None:
        """
        """

        mask_0 = None

        weight_2 = tensor(
            [1.0, 1.0, 1.0]
        )

        bias_0 = None

        with self.assertRaisesRegex(
            ValueError,
            "'weight' must be a tensor with shape"
        ):
            validate_affine_masked_norm(self.inpt, mask_0, weight_2, bias_0)

    def test_mask_0_weigth_1_bias_2(
        self: TestValidateAffineMaskedNorm
    ) -> None:
        """
        """

        mask_0 = None

        weight_1 = tensor(
            [1.0, 1.0]
        )

        bias_2 = tensor(
            [0.0, 0.0, 0.0]
        )

        with self.assertRaisesRegex(
            ValueError,
            "'bias' must be a tensor with shape"
        ):
            validate_affine_masked_norm(self.inpt, mask_0, weight_1, bias_2)

    def test_mask_1_weight_1_bias_0(
        self: TestValidateAffineMaskedNorm
    ) -> None:
        """
        """

        mask_1 = tensor(
            [True, False]
        )

        weight_1 = tensor(
            [1.0, 1.0]
        )

        bias_0 = None

        try:
            validate_affine_masked_norm(self.inpt, mask_1, weight_1, bias_0)
            self.assertTrue(True)

        except:
            self.assertTrue(False)

    def test_mask_1_weight_1_bias_1(
        self: TestValidateAffineMaskedNorm
    ) -> None:
        """
        """

        mask_1 = tensor(
            [True, False]
        )

        weight_1 = tensor(
            [1.0, 1.0]
        )

        bias_1 = tensor(
            [0.0, 0.0]
        )

        try:
            validate_affine_masked_norm(self.inpt, mask_1, weight_1, bias_1)
            self.assertTrue(True)

        except:
            self.assertTrue(False)

    def test_mask_1_weight_2_bias_0(
        self: TestValidateAffineMaskedNorm
    ) -> None:
        """
        """

        mask_1 = tensor(
            [True, False]
        )

        weight_2 = tensor(
            [1.0, 1.0, 1.0]
        )

        bias_0 = None

        with self.assertRaisesRegex(
            ValueError,
            "'weight' must have the same shape as 'mask'"
        ):
            validate_affine_masked_norm(self.inpt, mask_1, weight_2, bias_0)

    def test_mask_1_weight_1_bias_2(
        self: TestValidateAffineMaskedNorm
    ) -> None:
        """
        """

        mask_1 = tensor(
            [True, False]
        )

        weight_1 = tensor(
            [1.0, 1.0]
        )

        bias_2 = tensor(
            [0.0, 0.0, 0.0]
        )

        with self.assertRaisesRegex(
            ValueError,
            "'bias' must have the same shape as 'mask'"
        ):
            validate_affine_masked_norm(self.inpt, mask_1, weight_1, bias_2)
