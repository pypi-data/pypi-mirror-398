from typing import Callable, ClassVar
from pathlib import Path


class BaseRegisteredDataset:
    relative_paths: ClassVar[dict[str, dict[str, str]]]

    @classmethod
    def get_path(
        cls, name: str, split: str, base_path: Path | None, download: bool = True
    ) -> Path:
        raise NotImplementedError()

    @classmethod
    def is_valid_split(cls, name: str, split: str) -> bool:
        return split in cls.relative_paths[name]


_KT = str
_VT = type[BaseRegisteredDataset]


class DatasetRegistry(dict[_KT, _VT]):
    def register(self, name: _KT | list[_KT] | tuple[_KT]) -> Callable[[_VT], _VT]:
        def decorator(func: _VT) -> _VT:
            if isinstance(name, (list, tuple)):
                for name_single in name:
                    self[name_single] = func
            else:
                self[name] = func
            return func

        return decorator

    def get_path(
        self, name: str, split: str, base_path: Path | None, download: bool = True
    ):
        """Fetch the path for a dataset-split pair. If the dataset does not exist under
        the `base_path` directory, a download will be attempted.

        Args:
            name (str): dataset name (e.g. "water", "TM23/Ag-cold", "PtH2O")
            split (str): data-split, for example "train", "val" or "test"
            base_path (Path): the base path at which the dataset is stored.
            download (bool, optional): Whether to download the dataset if it does not exist.
                Defaults to True.

        Returns:
            dset_path (Path): a path to the ase-readable dataset.
        """
        return self[name].get_path(name, split, base_path, download)

    def is_valid_split(self, name: str, split: str) -> bool:
        return self[name].is_valid_split(name, split)


DATASET_REGISTRY = DatasetRegistry()
