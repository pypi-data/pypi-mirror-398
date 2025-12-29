
# Masked Norm

Self-attention-based neural network architectures pad input sequences to an
expected length prior to processing. Generally, an attention mask is generated
for each sequence in order to retain its original length and further instruct
the model on which sequence instances are relevant.

Normalization transformations suppress the internal covariance shift problem
in deep neural networks, leading to a reduction training time. Layer
normalization - popular in self-attention-based architectures - normalizes
each instance of the input sequences. Notably, the output of this
transformation is invariant under a re-scaling operation of each sequence
instance.

When input sequences are padded with a constant value, the variances of the
padded instances are null. Standard layer normalization implementations
introduce a stabilising constant $\epsilon$ to prevent arithmetic errors.
This can lead to overflows further along the computational graph.

The masked normalization transformation uses the input's attention mask such
that only the relevant instances of the sequence are normalized. Moreover, by
applying simple shape-shifting operations (such as axis permutation or
unfoldings) over the input tensor, masked normalization can reproduce batch,
group, layer, and instance normalization.

This masked normalization implementation refrains from tracking the running
statistics during training, since this breaks re-scaling invariance. Also, the
proposed implementation employs the variance's unbiased estimator, as each
scalar tensor element is considered a true sample.

This repository contains a PyTorch implementation of masked normalization.

To use it in your project, install it via `pip`:

```bash
pip install masked_norm
```

Three core user-facing implementations are presented: a plain masked
normalization `masked_norm`, a batched masked normalization
`batched_masked_norm`, and an affine masked normalization
`LazyAffineMaskedNorm`. Plain `masked_norm` normalizes values along the last
axis of the input, while `batched_masked_norm` normalizes along the first
axis. These two variant cover most functional use cases.
`LazyAffineMaskedNorm` performs an affine transformation after normalization,
it can have a batched or unbatched behaviour which is specified by a keyword
argument to the constructor.

You can use the functional form of the masked normalization transformation
directy in your model's forward call:

```python
from torch import tensor, rand
from masked_norm import masked_norm

inpt = rand(2, 2, 3)
mask = tensor(
    [
        [True, True],
        [True, False]
    ]
)

masked_norm(inpt, mask)
```

Our use its class equivalent:

```python
from torch import tensor, rand
from masked_norm import MaskedNorm

inpt = rand(4, 2, 2)
mask = tensor(
    [
        [True, True],
        [True, False]
    ]
)

norm_layer = MaskedNorm(batched=True)

norm_layer(inpt, mask)
```

You can apply the affine masked normalization transformation, by instantiating
a lazy layer:

```python
from torch import tensor, rand
from masked_norm import LazyAffineMaskedNorm

inpt = rand(2, 2, 3)
mask = tensor(
    [
        [True, True],
        [True, False]
    ]
)

affine_norm_layer = LazyAffineMaskedNorm()

affine_norm_layer(inpt, mask)
```

To see how you can reproduce the batch, group, layer, or instance
normalization procedures with masked normalization take a look at the `test`
subdirectory. Note that the variance estimator of the official Pytorch
implementations of these layers is biased.

If, either by chance or design, a selection of samples is constant, the
proposed `masked_norm` and `affine_masked_norm` implementations ignore
this selection, and pass the values along unaltered.

To run the test suite:

```bash
git clone https://github.com/algmarques/masked_norm.git
cd masked_norm
python -m venv .venv
.venv/bin/pip install .
.venv/bin/python -Bm unittest
```
