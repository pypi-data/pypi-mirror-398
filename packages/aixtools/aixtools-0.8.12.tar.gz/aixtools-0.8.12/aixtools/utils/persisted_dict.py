"""
Dictionary implementation that automatically persists its contents to disk.
"""

import json
import pickle
from pathlib import Path

from aixtools.logging.logging_config import get_logger

logger = get_logger(__name__)

DATA_KEY = "__dictionary_data__"


class PersistedDict(dict):
    """
    A dictionary that persists to a file on disk as JSON.
    Keys are always converted to strings.
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path if isinstance(file_path, Path) else Path(file_path)
        self.use_pickle = None
        if file_path.suffix == ".json":
            self.use_pickle = False
        elif file_path.suffix == ".pkl":
            self.use_pickle = True
        else:
            raise ValueError(f"Unsupported file extension '{file_path.suffix}' for file '{file_path}'")
        self.load()

    def __contains__(self, key):
        return super().__contains__(str(key))

    def __delitem__(self, key):
        super().__delitem__(str(key))
        self.save()

    def get(self, key, default=None):
        return super().get(str(key), default)

    def __getitem__(self, key):
        return super().__getitem__(str(key))

    def load(self):
        """Load dictionary data from disk using either pickle or JSON format."""
        if self.use_pickle:
            self._load_pickle()
        else:
            self._load_json()

    def _load_json(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.update(json.load(f))
            logger.debug("Persistent dictionary: Loaded %d items from JSON file '%s'", len(self), self.file_path)
        except FileNotFoundError:
            pass

    def _load_pickle(self):
        try:
            with open(self.file_path, "rb") as f:
                object_data = pickle.load(f)
            for k, v in object_data[DATA_KEY].items():
                super().__setitem__(str(k), v)
            for k, v in object_data.items():
                if k != DATA_KEY:
                    self.__dict__[k] = v
            logger.debug("Persistent dictionary: Loaded %d items from pickle file '%s'", len(self), self.file_path)
        except FileNotFoundError:
            pass

    def save(self):
        """Save dictionary data to disk using either pickle or JSON format."""
        if self.use_pickle:
            self._save_pickle()
        else:
            self._save_json()

    def _save_json(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self, f, indent=2)

    def _save_pickle(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "wb") as f:
            object_data = dict(self.__dict__)
            object_data[DATA_KEY] = dict(self)
            pickle.dump(object_data, f)

    def __setitem__(self, key, value):
        super().__setitem__(str(key), value)
        self.save()

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        self.save()
