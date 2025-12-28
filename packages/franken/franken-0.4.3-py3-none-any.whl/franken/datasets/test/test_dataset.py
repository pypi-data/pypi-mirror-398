from importlib import resources
from pathlib import Path

import franken.datasets
from franken.datasets.registry import DATASET_REGISTRY, BaseRegisteredDataset


@DATASET_REGISTRY.register("test")
class TestRegisteredDataset(BaseRegisteredDataset):
    relative_paths = {
        "test": {
            "train": "test/train.xyz",
            "val": "test/validation.xyz",
            "test": "test/test.xyz",
            "md": "test/md.xyz",
            "long": "test/long.xyz",
        },
    }

    @classmethod
    def get_path(
        cls, name: str, split: str, base_path: Path | None, download: bool = True
    ):
        relative_path = cls.relative_paths[name][split]
        path = resources.files(franken.datasets) / relative_path
        if path.is_file():
            return path
        else:
            raise ValueError(f"Dataset not found at '{path}'")
