from typing import Optional, Iterator

from torch.utils.data import Sampler, Dataset
import torch.distributed as dist


class SimpleUnevenDistributedSampler(Sampler):
    def __init__(
        self,
        dataset: Dataset,
        num_replicas: Optional[int] = None,
        rank: Optional[int] = None,
    ) -> None:
        if num_replicas is None:
            if not dist.is_available():
                raise RuntimeError("Requires distributed package to be available")
            num_replicas = dist.get_world_size()
        if rank is None:
            if not dist.is_available():
                raise RuntimeError("Requires distributed package to be available")
            rank = dist.get_rank()
        if rank >= num_replicas or rank < 0:
            raise ValueError(
                f"Invalid rank {rank}, rank should be in the interval [0, {num_replicas - 1}]"
            )
        self.dataset = dataset
        self.num_replicas = num_replicas
        self.rank = rank
        self.epoch = 0
        self.total_size = len(self.dataset)  # type: ignore[arg-type]
        # num_samples indicates the number of samples for the current process
        self.num_samples = len(range(self.rank, self.total_size, self.num_replicas))

    def __iter__(self) -> Iterator:
        indices = list(range(len(self.dataset)))  # type: ignore[arg-type]

        # subsample
        indices = indices[self.rank : self.total_size : self.num_replicas]
        assert len(indices) == self.num_samples

        return iter(indices)

    def __len__(self) -> int:
        return self.num_samples
