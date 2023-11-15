import torch

__all__ = ["Flops", "FlopsScheduler"]


class FlopsScheduler:
    """Flops scheduler.

    References
    ----------
    1. [MINIMIZING FLOPS TO LEARN EFFICIENT SPARSE REPRESENTATIONS](https://arxiv.org/pdf/2004.05665.pdf)
    2. [SPLADE: Sparse Lexical and Expansion Model for First Stage Ranking](https://arxiv.org/pdf/2107.05720.pdf)
    """

    def __init__(self, weight: float = 3e-5, steps: int = 10000):
        self._weight = weight
        self.weight = 0
        self.steps = steps
        self._step = 0

    def step(self) -> None:
        if self._step >= self.steps:
            pass
        else:
            self._step += 1
            self.weight = self._weight * (self._step / self.steps) ** 2

    def get(self):
        return self.weight


class Flops(torch.nn.Module):
    """Flops loss, act as regularization loss over sparse activations.

    Example
    -------
    >>> from sparsembed import models, utils, losses
    >>> import torch

    >>> _ = torch.manual_seed(42)

    >>> model = models.Splade(
    ...     model_name_or_path="distilbert-base-uncased",
    ...     device="mps",
    ... )

    >>> anchor_activations = model(
    ...     ["Sports", "Music"],
    ...     query_mode=True,
    ... )

    >>> positive_activations = model(
    ...    ["Sports", "Music"],
    ...     query_mode=False,
    ... )

    >>> negative_activations = model(
    ...    ["Cinema", "Movie"],
    ...     query_mode=False,
    ... )

    >>> losses.Flops()(
    ...     anchor_activations=anchor_activations["sparse_activations"],
    ...     positive_activations=positive_activations["sparse_activations"],
    ...     negative_activations=negative_activations["sparse_activations"],
    ... )
    tensor(1., device='mps:0', grad_fn=<ClampBackward1>)

    References
    ----------
    1. [MINIMIZING FLOPS TO LEARN EFFICIENT SPARSE REPRESENTATIONS](https://arxiv.org/pdf/2004.05665.pdf)
    2. [SPLADE: Sparse Lexical and Expansion Model for First Stage Ranking](https://arxiv.org/pdf/2107.05720.pdf)

    """

    def __init__(self):
        super(Flops, self).__init__()

    def __call__(
        self,
        anchor_activations: torch.Tensor,
        positive_activations: torch.Tensor,
        negative_activations: torch.Tensor,
        threshold: float = 30.0,
        max_loss: float = 1.0,
    ) -> torch.Tensor:
        """Loss which tend to reduce sparse activation."""
        activations = torch.cat(
            [anchor_activations, positive_activations, negative_activations], dim=0
        )

        loss = torch.abs(
            threshold - torch.sum(torch.mean(torch.abs(activations), dim=0) ** 2, dim=0)
        )

        return torch.clip(loss, min=0.0, max=max_loss)
