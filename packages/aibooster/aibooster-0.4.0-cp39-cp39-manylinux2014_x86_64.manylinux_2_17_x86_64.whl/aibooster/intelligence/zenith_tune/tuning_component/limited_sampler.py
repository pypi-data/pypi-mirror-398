import math
from typing import Iterator, Sized

import torch
from torch.utils.data import Sampler

from ..distributed import get_rank, get_world_size


class LimitedSampler(Sampler):
    def __init__(
        self,
        dataset: Sized,
        shuffle: bool = True,
        seed: int = 0,
        round_up: bool = True,
        limited_samples: int = 1024,
    ) -> None:
        """Initializes the LimitedSampler.

        Args:
            dataset (Sized): The dataset to sample from.
            shuffle (bool, optional): Whether to shuffle the dataset. Defaults to True.
            seed (int, optional): The random seed for shuffling. Defaults to 0.
            round_up (bool, optional): Whether to round up the number of samples per process. Defaults to True.
            limited_samples (int, optional): The maximum number of samples to use. Defaults to 1024.
        """
        self.rank = get_rank()
        self.world_size = get_world_size()

        self.dataset = dataset
        self.shuffle = shuffle
        self.seed = seed
        self.epoch = 0
        self.round_up = round_up

        if self.round_up:
            self.num_samples = math.ceil(len(self.dataset) / self.world_size)
            self.total_size = self.num_samples * self.world_size
        else:
            self.num_samples = math.ceil(
                (len(self.dataset) - self.rank) / self.world_size
            )
            self.total_size = len(self.dataset)

        if self.total_size > limited_samples:
            if limited_samples % self.world_size != 0:
                # Make total_size divisible by world_size
                limited_samples += self.world_size - limited_samples % self.world_size

            self.num_samples = limited_samples // self.world_size
            self.total_size = limited_samples

    def __iter__(self) -> Iterator[int]:
        """Returns an iterator over the sampled indices.

        Yields:
            Iterator[int]: An iterator yielding the sampled indices.
        """
        if self.shuffle:
            g = torch.Generator()
            g.manual_seed(self.seed + self.epoch)
            indices = torch.randperm(len(self.dataset), generator=g).tolist()
        else:
            indices = torch.arange(len(self.dataset)).tolist()

        if self.round_up:
            indices = (indices * int(self.total_size / len(indices) + 1))[
                : self.total_size
            ]

        indices = indices[self.rank : self.total_size : self.world_size]

        return iter(indices)

    def __len__(self) -> int:
        """Returns the number of samples in the sampler.

        Returns:
            int: The number of samples.
        """
        return self.num_samples

    def set_epoch(self, epoch: int) -> None:
        """Sets the current epoch.

        Args:
            epoch (int): The epoch number.
        """
        self.epoch = epoch


try:
    from ..integration.mmengine.registry import DATA_SAMPLERS

    DATA_SAMPLERS.register_module(module=LimitedSampler)
except Exception:
    pass
    pass
