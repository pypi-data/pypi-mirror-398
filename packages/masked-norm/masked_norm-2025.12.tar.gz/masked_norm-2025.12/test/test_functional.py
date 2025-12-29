"""
Functional module testing
"""

from __future__ import annotations

from torch import Tensor, tensor
from masked_norm import masked_norm
from masked_norm import affine_masked_norm
from masked_norm import batched_masked_norm

from .tensor_test_case import TensorTestCase


class TestMaskedNorm(TensorTestCase):
    """
    'masked_norm' (functional implementation) testing unit
    """

    def test_input_1_mask_0(self: TestMaskedNorm) -> None:
        """
        """

        inpt_1 = tensor(
            [
                [0.00, 1.00, 2.00],
                [3.00, 4.00, 5.00]
            ]
        )

        mask_0 = None

        out_1 = tensor(
            [
                [-1.0, 0.00, 1.00],
                [-1.0, 0.00, 1.00]
            ]
        )

        out = masked_norm(inpt_1, mask_0)

        self.assertEqTensor(out, out_1)

    def test_input_2_mask_0(self: TestMaskedNorm) -> None:
        """
        """

        inpt_2 = tensor(
            [
                [0.00, 1.00, 2.00],
                [0.00, 0.00, 0.00]
            ]
        )

        mask_0 = None

        out_2 = tensor(
            [
                [-1.0, 0.00, 1.00],
                [0.00, 0.00, 0.00]
            ]
        )

        out = masked_norm(inpt_2, mask_0)

        self.assertEqTensor(out, out_2)

    def test_input_2_mask_1(self: TestMaskedNorm) -> None:
        """
        """

        inpt_2 = tensor(
            [
                [0.00, 1.00, 2.00],
                [0.00, 0.00, 0.00]
            ]
        )

        mask_1 = tensor(
            [True, False]
        )

        out_2 = tensor(
            [
                [-1.0, 0.00, 1.00],
                [0.00, 0.00, 0.00]
            ]
        )

        out = masked_norm(inpt_2, mask_1)

        self.assertEqTensor(out, out_2)

    def test_input_3_mask_1(self: TestMaskedNorm) -> None:
        """
        """

        inpt_3 = tensor(
            [
                [
                    [0.00, 1.00, 2.00],
                    [3.00, 4.00, 5.00]
                ],
                [
                    [6.00, 7.00, 8.00],
                    [0.00, 0.00, 0.00]
                ]
            ]
        )

        mask_1 = tensor(
                [True, False]
        )

        out_3 = tensor(
            [
                [
                    [-1.0, 0.00, 1.00],
                    [-1.0, 0.00, 1.00]
                ],
                [
                    [6.00, 7.00, 8.00],
                    [0.00, 0.00, 0.00]
                ]
            ]
        )

        out = masked_norm(inpt_3, mask_1)

        self.assertEqTensor(out, out_3)

    def test_input_3_mask_2(self: TestMaskedNorm) -> None:
        """
        """

        inpt_3 = tensor(
            [
                [
                    [0.00, 1.00, 2.00],
                    [3.00, 4.00, 5.00]
                ],
                [
                    [6.00, 7.00, 8.00],
                    [0.00, 0.00, 0.00]
                ]
            ]
        )

        mask_2 = tensor(
            [
                [True, True],
                [True, False]
            ]
        )

        out_3 = tensor(
            [
                [
                    [-1.0, 0.00, 1.00],
                    [-1.0, 0.00, 1.00]
                ],
                [
                    [-1.0, 0.00, 1.00],
                    [0.00, 0.00, 0.00]
                ]
            ]
        )

        out = masked_norm(inpt_3, mask_2)

        self.assertEqTensor(out, out_3)

    def test_empty(self: TestMaskedNorm) -> None:
        """
        """

        empty_inpt = tensor([])

        out = masked_norm(empty_inpt)

        self.assertEqTensor(out, empty_inpt)

    def test_singleton_dim(self: TestMaskedNorm) -> None:
        """
        """

        inpt_4 = tensor(
            [
                [0.0],
                [1.0],
                [2.0]
            ]
        )

        out = masked_norm(inpt_4)

        self.assertEqTensor(out, inpt_4)


class TestAffineMaskedNorm(TensorTestCase):
    """
    'affine_masked_norm' testing unit
    """

    def test_input_1_mask_0_weight_1_bias_0(
        self: TestAffineMaskedNorm
    ) -> None:
        """
        """

        inpt_1 = tensor(
            [
                [0.00, 1.00, 2.00],
                [3.00, 4.00, 5.00]
            ]
        )

        mask_0 = None

        weight_1 = tensor(
            [2.00, 1.00]
        )

        bias_0 = None

        out_1 = tensor(
            [
                [-2.0, 0.00, 2.00],
                [-1.0, 0.00, 1.00]
            ]
        )

        out = affine_masked_norm(inpt_1, mask_0, weight_1, bias_0)

        self.assertEqTensor(out, out_1)

    def test_input_1_mask_0_weight_1_bias_1(
        self: TestAffineMaskedNorm
    ) -> None:
        """
        """

        inpt_1 = tensor(
            [
                [0.00, 1.00, 2.00],
                [3.00, 4.00, 5.00]
            ]
        )

        mask_0 = None

        weight_1 = tensor(
            [2.00, 1.00]
        )

        bias_1 = tensor(
            [1.00, 1.00]
        )

        out_2 = tensor(
            [
                [-1.0, 1.00, 3.00],
                [0.00, 1.00, 2.00]
            ]
        )

        out = affine_masked_norm(inpt_1, mask_0, weight_1, bias_1)

        self.assertEqTensor(out, out_2)

    def test_input_2_mask_1_weight_1_bias_0(
        self: TestAffineMaskedNorm
    ) -> None:
        """
        """

        inpt_2 = tensor(
            [
                [0.00, 1.00, 2.00],
                [0.00, 0.00, 0.00]
            ]
        )

        mask_1 = tensor(
            [True, False]
        )

        weight_1 = tensor(
            [2.00, 1.00]
        )

        bias_0 = None

        out_3 = tensor(
            [
                [-2.0, 0.00, 2.00],
                [0.00, 0.00, 0.00]
            ]
        )

        out = affine_masked_norm(inpt_2, mask_1, weight_1, bias_0)

        self.assertEqTensor(out, out_3)

    def test_input_2_mask_1_weight_1_bias_1(
        self: TestAffineMaskedNorm
    ) -> None:
        """
        """

        inpt_2 = tensor(
            [
                [0.00, 1.00, 2.00],
                [0.00, 0.00, 0.00]
            ]
        )

        mask_1 = tensor(
            [True, False]
        )

        weight_1 = tensor(
            [2.00, 1.00]
        )

        bias_1 = tensor(
            [1.00, 1.00]
        )

        out_4 = tensor(
            [
                [-1.0, 1.00, 3.00],
                [1.00, 1.00, 1.00]
            ]
        )

        out = affine_masked_norm(inpt_2, mask_1, weight_1, bias_1)

        self.assertEqTensor(out, out_4)

    def test_input_3_mask_2_weight_2_bias_0(
        self: TestAffineMaskedNorm
    ) -> None:
        """
        """

        inpt_3 = tensor(
            [
                [
                    [0.00, 1.00, 2.00],
                    [3.00, 4.00, 5.00]
                ],
                [
                    [6.00, 7.00, 8.00],
                    [0.00, 0.00, 0.00]
                ]
            ]
        )

        mask_2 = tensor(
            [
                [True, True],
                [True, False]
            ]
        )

        weigth_2 = tensor(
            [
                [2.00, 1.00],
                [3.00, 1.00]
            ]
        )

        bias_0 = None

        out_5 = tensor(
            [
                [
                    [-2.0, 0.00, 2.00],
                    [-1.0, 0.00, 1.00]
                ],
                [
                    [-3.0, 0.00, 3.00],
                    [0.00, 0.00, 0.00]
                ]
            ]
        )

        out = affine_masked_norm(inpt_3, mask_2, weigth_2, bias_0)

        self.assertEqTensor(out, out_5)

    def test_input_3_mask_2_weight_2_bias_2(
        self: TestAffineMaskedNorm
    ) -> None:
        """
        """

        inpt_3 = tensor(
            [
                [
                    [0.00, 1.00, 2.00],
                    [3.00, 4.00, 5.00]
                ],
                [
                    [6.00, 7.00, 8.00],
                    [0.00, 0.00, 0.00]
                ]
            ]
        )

        mask_2 = tensor(
            [
                [True, True],
                [True, False]
            ]
        )

        weigth_2 = tensor(
            [
                [2.00, 1.00],
                [3.00, 1.00]
            ]
        )

        bias_2 = tensor(
            [
                [0.00, 1.00],
                [2.00, -1.0]
            ]
        )

        out_6 = tensor(
            [
                [
                    [-2.0, 0.00, 2.00],
                    [0.00, 1.00, 2.00]
                ],
                [
                    [-1.0, 2.00, 5.00],
                    [-1.0, -1.0, -1.0]
                ]
            ]
        )

        out = affine_masked_norm(inpt_3, mask_2, weigth_2, bias_2)

        self.assertEqTensor(out, out_6)


class TestBatchedMaskedNorm(TensorTestCase):
    """
    'batched_masked_norm' (functional implementation) testing unit
    """

    def test_input_1_mask_0(self: TestBatchedMaskedNorm) -> None:
        """
        """

        inpt_1 = tensor(
            [
                [0.00, 3.00],
                [1.00, 4.00],
                [2.00, 5.00]
            ]
        )

        mask_0 = None

        out_1 = tensor(
            [
                [-1.0, -1.0],
                [0.00, 0.00],
                [1.00, 1.00]
            ]
        )

        out = batched_masked_norm(inpt_1, mask_0)

        self.assertEqTensor(out, out_1)

    def test_input_2_mask_0(self: TestBatchedMaskedNorm) -> None:
        """
        """

        inpt_2 = tensor(
            [
                [0.00, 0.00],
                [1.00, 0.00],
                [2.00, 0.00]
            ]
        )

        mask_0 = None

        out_2 = tensor(
            [
                [-1.0, 0.00],
                [0.00, 0.00],
                [1.00, 0.00]
            ]
        )

        out = batched_masked_norm(inpt_2, mask_0)

        self.assertEqTensor(out, out_2)

    def test_input_2_mask_1(self: TestBatchedMaskedNorm) -> None:
        """
        """

        inpt_2 = tensor(
            [
                [0.00, 0.00],
                [1.00, 0.00],
                [2.00, 0.00]
            ]
        )

        mask_1 = tensor(
            [True, False]
        )

        out_2 = tensor(
            [
                [-1.0, 0.00],
                [0.00, 0.00],
                [1.00, 0.00]
            ]
        )

        out = batched_masked_norm(inpt_2, mask_1)

        self.assertEqTensor(out, out_2)

    def test_input_3_mask_2(self: TestBatchedMaskedNorm) -> None:
        """
        """

        inpt_3 = tensor(
            [
                [
                    [0.00, 3.00],
                    [6.00, 0.00]
                ],
                [
                    [1.00, 4.00],
                    [7.00, 0.00]
                ],
                [
                    [2.00, 5.00],
                    [8.00, 0.00]
                ]
            ]
        )

        mask_2 = tensor(
            [
                [True, True],
                [True, False]
            ]
        )

        out_3 = tensor(
            [
                [
                    [-1.0, -1.0],
                    [-1.0, 0.00]
                ],
                [
                    [0.00, 0.00],
                    [0.00, 0.00]
                ],
                [
                    [1.00, 1.00],
                    [1.00, 0.00]
                ]
            ]
        )

        out = batched_masked_norm(inpt_3, mask_2)

        self.assertEqTensor(out, out_3)
