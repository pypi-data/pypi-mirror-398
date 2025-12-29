"""
"""

from __future__ import annotations

from unittest import TestCase

from torch import tensor, rand
from torch.optim import SGD, Adam

from masked_norm import masked_norm
from masked_norm import MaskedNorm, LazyAffineMaskedNorm


class TestMaskedNormTraining(TestCase):
    """
    masked_norm "in-place modification" testing unit

    Torch autograd mechanics do not allow modifying tensor values in-place
    Some of these in-place modifications were introduced and carefully guarded
    against in the masked_norm implementation
    The purpose of this unit is to test such safe-guards
    """

    def setUp(self: TestMaskedNormTraining) -> None:
        """
        """

        self.n_epochs = 2

        self.inpt_shape = (2, 3, 2)

        self.loss = lambda x: x.sum() ** 2

    def test_mask_0(self: TestMaskedNormTraining) -> None:
        """
        """

        mask_0 = None

        try:
            for epoch in range(self.n_epochs):
                inpt = rand(self.inpt_shape, requires_grad=True)
                out = masked_norm(inpt, mask_0)
                loss = self.loss(out)

                loss.backward()

            self.assertTrue(True)

        except:
            self.assertTrue(False)

    def test_mask_1(self: TestMaskedNormTraining) -> None:
        """
        """

        mask_1 = tensor(
            [
                [True, True, True],
                [True, True, False]
            ]
        )

        try:
            for epoch in range(self.n_epochs):
                inpt = rand(self.inpt_shape, requires_grad=True)
                out = masked_norm(inpt, mask_1)
                loss = self.loss(out)

                loss.backward()

            self.assertTrue(True)

        except:
            self.assertTrue(False)


class TestLazyAffineMaskedNormTraining(TestCase):
    """
    LazyAffineMaskedNorm "in-pace modification" testing unit

    Torch autograd mechanics do not allow modifying tensor values in-place
    Some of these in-place modification were introduced and carefully guarded
    in the affine_masked_norm implementation
    The purpose of this unit is to test such safe-guards
    """

    def setUp(self: TestLazyAffineMaskedNormTraining) -> None:
        """
        """

        self.n_epochs = 2

        self.inpt_shape = (2, 3, 2)

        self.loss = lambda x: x.sum() ** 2

    def test_mask_0(self: TestLazyAffineMaskedNormTraining) -> None:
        """
        """

        mask_0 = None

        affine_masked_norm = LazyAffineMaskedNorm()

        sgd = SGD(affine_masked_norm.parameters())
        adam = Adam(affine_masked_norm.parameters())

        try:
            for optimizer in [sgd, adam]:
                for epoch in range(self.n_epochs):
                    inpt = rand(self.inpt_shape, requires_grad=True)
                    out = affine_masked_norm(inpt, mask_0)
                    loss = self.loss(out)

                    loss.backward()
                    optimizer.step()
                    optimizer.zero_grad()

            self.assertTrue(True)

        except:
            self.assertTrue(False)

    def test_mask_1(self: TestLazyAffineMaskedNormTraining) -> None:
        """
        """

        mask_1 = tensor(
            [
                [True, True, True],
                [True, True, False]
            ]
        )

        affine_masked_norm = LazyAffineMaskedNorm()

        sgd = SGD(affine_masked_norm.parameters())
        adam = Adam(affine_masked_norm.parameters())

        try:
            for optimizer in [sgd, adam]:
                for epoch in range(self.n_epochs):
                    inpt = rand(self.inpt_shape, requires_grad=True)
                    out = affine_masked_norm(inpt, mask_1)
                    loss = self.loss(out)

                    loss.backward()
                    optimizer.step()
                    optimizer.zero_grad()

            self.assertTrue(True)

        except:
            self.assertTrue(False)
