"""User store and management."""

import json
from pathlib import Path
from typing import Dict

from aixtools.utils import get_logger

logger = get_logger(__name__)


class User:
    """User data structure for authentication."""

    def __init__(self, username: str, role: str = "user"):
        """Initialize a User object.

        Args:
            username: The user's username
            role: The user's role (default: "user")
        """
        self.username = username
        self.role = role

    def to_dict(self) -> dict:
        """Convert the User object to a dictionary for serialization."""
        return {
            "username": self.username,
            "role": self.role,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create a User object from a dictionary.

        Args:
            data: Dictionary containing user data

        Returns:
            A User object
        """
        return cls(username=data["username"].lower(), role=data.get("role", "user"))


class UserStore:  # pylint: disable=too-few-public-methods
    """Store and manage user data."""

    def __init__(self, file_path: str = "users.json"):
        """Initialize the UserStore.

        Args:
            file_path: Path to the JSON file storing user data
        """
        self.file_path = Path(file_path)
        self.users: Dict[str, User] = {}
        self.load_users()

    def load_users(self) -> None:
        """Load users from the JSON file."""
        if self.file_path.exists():
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.users = {username.lower(): User.from_dict(user_data) for username, user_data in data.items()}
            logger.info("Loaded %d users from %s", len(self.users), self.file_path)
