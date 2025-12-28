from werkzeug.datastructures.file_storage import FileStorage
from werkzeug.utils import secure_filename
from pathlib import Path
import shutil


class Dataset:
    """Represents a dataset that is stored on the file system."""

    dataset_root_folder: str

    def __init__(self, address: Path) -> None:
        self._address = address.with_name(secure_filename(address.stem))
        if not (
            self._address.is_dir()
            and self._address.is_relative_to(Dataset.dataset_root_folder)
        ):
            raise ValueError(f"Invalid dataset path: {self.address}")
        self.files = list(self._address.glob("*"))

    @property
    def address(self) -> Path:
        return self._address

    @property
    def num_files(self) -> int:
        return len(self.files)


class DatasetManager:
    """Singleton that manages all currently stored datasets."""

    _instance = None
    managed_datasets: set[Dataset] = set()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatasetManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def add(cls, dataset: Dataset) -> None:
        cls.managed_datasets.add(dataset)

    @classmethod
    def remove(cls, dataset_name: str) -> None:
        """
        Remove dataset from internal memory and delete dataset folder.
        """
        dataset: Dataset = list(
            filter(
                lambda dataset: dataset.address.stem == dataset_name,
                DatasetManager.managed_datasets,
            )
        )[0]
        cls.managed_datasets.remove(dataset)
        if (
            Path(__file__).parent in Path(Dataset.dataset_root_folder).parents
            and Path(Dataset.dataset_root_folder) in dataset.address.parents
        ):
            print(f"Removing {dataset.address} ({dataset.num_files} images).")
            shutil.rmtree(dataset.address)

    def __len__(self) -> int:
        return len(self.managed_datasets)

    def __getitem__(self, dataset_name: str) -> Dataset:
        """
        Convinience method to retrieve Dataset objects held by this
        DatasetManager.
        """
        for managed_datasets in DatasetManager.managed_datasets:
            if managed_datasets.address.stem == dataset_name:
                return managed_datasets
        raise KeyError(f"Dataset {dataset_name} is not managed by this DatasetManager.")

    def __str__(self) -> str:
        s = f"DatasetManager holding {len(self)} datasets:\n"
        for dataset in self.managed_datasets:
            s += f"{dataset.address} ({dataset.num_files} images)\n"
        return s
