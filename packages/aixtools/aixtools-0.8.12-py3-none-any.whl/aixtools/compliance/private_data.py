"""Private data management module for aixtools compliance."""

import json
from pathlib import Path

from fastmcp import Context

from aixtools.context import SessionIdTuple
from aixtools.server.path import get_private_data_path


class PrivateData:
    """
    Class to manage private data file in the workspace.

    The information is stored in a JSON file named `.private_data` within the workspace directory.
    If the file does not exist, it indicates that there is no private data.

    IMPORTANT: All modifications save the data to the file immediately.

    FIXME: We should add some level of mutex/locking to prevent concurrent writes.
    """

    def __init__(self, ctx: Context | SessionIdTuple | None = None):
        self.ctx: Context | SessionIdTuple | None = ctx
        self._has_private_data: bool = False  # Flag indicating if private data exists
        self._private_datasets: list[str] = []  # List of private datasets
        self._idap_datasets: list[str] = []  # List of dataset with IDAP
        self.load()

    def add_private_dataset(self, dataset_name: str) -> None:
        """
        Add a private dataset to the list.
        Save the state after modification.
        """
        if dataset_name not in self._private_datasets:
            self._private_datasets.append(dataset_name)
            self._has_private_data = True
            self.save()

    def add_idap_dataset(self, dataset_name: str) -> None:
        """
        Add a dataset with IDAP to the list.
        This also adds it to the private datasets if not already present.
        Save the state after modification.
        """
        if not self.has_idap_dataset(dataset_name):
            self._idap_datasets.append(dataset_name)
            self._has_private_data = True
            # An IDAP dataset is also a private dataset
            if not self.has_private_dataset(dataset_name):
                self._private_datasets.append(dataset_name)
            self.save()

    def get_private_datasets(self) -> list[str]:
        """Get the list of private datasets as a copy (to avoid modification)."""
        return list(self._private_datasets)

    def get_idap_datasets(self) -> list[str]:
        """Get the list of datasets with IDAP as a copy (to avoid modification)."""
        return list(self._idap_datasets)

    def has_private_dataset(self, dataset_name: str) -> bool:
        """Check if a specific private dataset exists."""
        return dataset_name in self._private_datasets

    def has_idap_dataset(self, dataset_name: str) -> bool:
        """Check if a specific dataset with IDAP exists."""
        return dataset_name in self._idap_datasets

    @property
    def has_private_data(self) -> bool:
        """Check if private data exists."""
        return self._has_private_data

    @has_private_data.setter
    def has_private_data(self, value: bool) -> None:
        """
        Set the flag indicating if private data exists.
        Save the state after modification.
        """
        self._has_private_data = value
        if not value:
            self._private_datasets = []
            self._idap_datasets = []
        self.save()

    def _get_private_data_path(self) -> Path:
        """Get the path to the private data file."""
        return get_private_data_path(self.ctx)

    def _has_private_data_file(self) -> bool:
        """Check if the private data file exists in the workspace."""
        private_data_path = self._get_private_data_path()
        return private_data_path.exists()

    def save(self) -> None:
        """Save content to the private data file in the workspace."""
        private_data_path = self._get_private_data_path()
        # No private data? Delete the file if it exists
        if not self.has_private_data:
            private_data_path.unlink(missing_ok=True)
            return
        # If there is private data, serialize this object as JSON
        private_data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(private_data_path, "w", encoding="utf-8") as f:
            # Dump class as JSON, excluding the context
            data_dict = self.__dict__.copy()
            data_dict["ctx"] = None
            json_data = json.dumps(data_dict, indent=4)
            f.write(json_data)

    def load(self) -> None:
        """Load content from the private data file in the workspace."""
        private_data_path = self._get_private_data_path()
        if not private_data_path.exists():
            # No private data file
            self._has_private_data = False
            self._private_datasets = []
            self._idap_datasets = []
            return
        with open(private_data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self._has_private_data = data.get("_has_private_data", False)
            self._private_datasets = data.get("_private_datasets", [])
            self._idap_datasets = data.get("_idap_datasets", [])

    def __repr__(self) -> str:
        return (
            f"PrivateData(has_private_data={self.has_private_data}, "
            f"private_datasets={self._private_datasets}, "
            f"idap_datasets={self._idap_datasets}), "
            f"file_path={self._get_private_data_path()})"
        )

    def __str__(self) -> str:
        return self.__repr__()
