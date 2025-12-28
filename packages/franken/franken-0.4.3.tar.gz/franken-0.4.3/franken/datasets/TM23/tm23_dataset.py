from functools import reduce
import operator
from pathlib import Path
import zipfile

from franken.datasets.registry import DATASET_REGISTRY, BaseRegisteredDataset
from franken.utils.file_utils import download_file

TM23_ELEMENTS = [
    "Ag",
    "Au",
    "Cd",
    "Co",
    "Cr",
    "Cu",
    "Fe",
    "Hf",
    "Hg",
    "Ir",
    "Mn",
    "Mo",
    "Nb",
    "Ni",
    "Os",
    "Pd",
    "Pt",
    "Re",
    "Rh",
    "Ru",
    "Ta",
    "Tc",
    "Ti",
    "V",
    "W",
    "Zn",
    "Zr",
]

TM23_DATASETS = list(
    reduce(
        operator.concat,
        [
            [f"TM23/{el}", f"TM23/{el}-cold", f"TM23/{el}-warm", f"TM23/{el}-melt"]
            for el in TM23_ELEMENTS
        ],
    )
)


@DATASET_REGISTRY.register(TM23_DATASETS)
class TM23RegisteredDataset(BaseRegisteredDataset):
    relative_paths = reduce(
        operator.ior,
        [
            {
                f"TM23/{el}": {
                    "train": f"TM23/{el}_2700cwm_train.xyz",
                    "val": f"TM23/{el}_2700cwm_test.xyz",
                },
                f"TM23/{el}-cold": {
                    "train": f"TM23/{el}_cold_nequip_train.xyz",
                    "val": f"TM23/{el}_cold_nequip_test.xyz",
                },
                f"TM23/{el}-warm": {
                    "train": f"TM23/{el}_warm_nequip_train.xyz",
                    "val": f"TM23/{el}_warm_nequip_test.xyz",
                },
                f"TM23/{el}-melt": {
                    "train": f"TM23/{el}_melt_nequip_train.xyz",
                    "val": f"TM23/{el}_melt_nequip_test.xyz",
                },
            }
            for el in TM23_ELEMENTS
        ],
        {},
    )  # merge list of dicts

    @classmethod
    def get_path(
        cls, name: str, split: str, base_path: Path | None, download: bool = True
    ):
        if base_path is None:
            raise KeyError(None)
        relative_path = cls.relative_paths[name][split]
        path = base_path / relative_path
        if not path.is_file() and download:
            cls.download(base_path)
        if path.is_file():
            return path
        else:
            raise ValueError(f"Dataset not found at '{path.resolve()}'")

    @classmethod
    def download(cls, base_path: Path):
        tm23_base_path = base_path / "TM23"
        tm23_base_path.mkdir(exist_ok=True, parents=True)
        # Download
        download_file(
            url="https://archive.materialscloud.org/record/file?record_id=2113&filename=benchmarking_master_collection-20240316T202423Z-001.zip",
            filename=tm23_base_path / "data.zip",
            desc="Downloading TM23 dataset",
        )
        # Extract
        with zipfile.ZipFile(tm23_base_path / "data.zip", "r") as zf:
            zf.extractall(tm23_base_path)
        # Move files up one level
        for origin in (tm23_base_path / "benchmarking_master_collection").glob("*"):
            origin.rename(tm23_base_path / origin.name)
        # Cleanup
        (tm23_base_path / "data.zip").unlink()
        (tm23_base_path / "benchmarking_master_collection").rmdir()
