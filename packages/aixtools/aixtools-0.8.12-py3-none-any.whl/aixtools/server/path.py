"""
Workspace path handling for user sessions.
"""

import posixpath
from pathlib import Path, PurePosixPath

from fastmcp import Context

from ..utils.config import DATA_DIR
from .utils import get_session_id_tuple

WORKSPACES_ROOT_DIR = (DATA_DIR / "workspaces").resolve()  # Path on the host where workspaces are stored
CONTAINER_WORKSPACE_PATH = PurePosixPath("/workspace")  # Path inside the sandbox container where workspace is mounted
PRIVATE_DATA_DIR = (
    WORKSPACES_ROOT_DIR / "_private-data"
).resolve()  # Root dir for the .private_data files used to mark conversations as private


def get_workspace_path(ctx: Context | tuple | None = None) -> Path:
    """
    Get the workspace path (in the host) for a specific service (e.g. MCP server).
    Returns the path based on user and session IDs in the format:

        <DATA_DIR>/workspaces/<user_id>/<session_id>

    where `DATA_DIR` should come from the environment variables
    Example workspace path:

        /data/workspaces/foo-user/bar-session

    The `ctx` is used to get user and session IDs tuple. It can be passed directly
    or via HTTP headers from `Context`. If `ctx` is None, the current FastMCP
    request HTTP headers are used.

    Args:
        ctx: The FastMCP context, which contains the user session.

    Returns: The workspace path as a Path object.
    """
    user_id, session_id = ctx if isinstance(ctx, tuple) else get_session_id_tuple(ctx)
    user_id = user_id.lower()  # to handle tuple passed directly
    return WORKSPACES_ROOT_DIR / user_id / session_id


def get_private_data_path(ctx: Context | tuple | None = None) -> Path:
    """
    Returns the path to the private data file for a given conversation:

        <DATA_DIR>/private-data/.private_data-<user_id>-<session_id>

    where `DATA_DIR` should come from the environment variables

    The `ctx` is used to get user and session IDs tuple. It can be passed directly
    or via HTTP headers from `Context`. If `ctx` is None, the current FastMCP
    request HTTP headers are used.

    Returns: The path to the private data file for the given context.
    """

    user_id, session_id = ctx if isinstance(ctx, tuple) else get_session_id_tuple(ctx)
    user_id = user_id.lower()  # to handle tuple passed directly
    return PRIVATE_DATA_DIR / user_id / f"{session_id}.json"


def get_workspace_path_sandbox() -> PurePosixPath:
    """
    Get the workspace path in the sandbox container.

    We return PurePosixPath to ensure compatibility with Linux containers.

    The paths inside the sandbox cannot be resolved (because they don't exist
    on the host), so we use PurePosixPath instead of Path. Also Path could be
    a WindowsPath on Windows hosts, which would be incorrect for Linux containers.

    Returns: The workspace path as a PurePosixPath object.
    """
    return CONTAINER_WORKSPACE_PATH


def path_normalize(p: PurePosixPath) -> PurePosixPath:
    """
    Normalize a PurePosixPath (remove redundant separators and up-level references).
    """
    return PurePosixPath(posixpath.normpath(p.as_posix()))


def path_chroot(path: Path, old_root: Path, new_root: Path) -> Path:
    """
    Change the root of a given path from old_root to new_root.
    If the path is not absolute (e.g. 'my_file.txt', './my_file.txt', 'my_dir/file.txt')
    we treat it as relative to the 'new_root'
    """
    if not Path(path).is_absolute():
        new_path = Path(new_root / path).resolve()
        new_root = Path(new_root).resolve()
        if not new_path.is_relative_to(new_root):
            raise ValueError(f"Path must not escape the workspace root: '{path}'")
        return Path(new_path)
    # Otherwise, we treat it as absolute and change the root
    return new_root / Path(path).relative_to(old_root)


def container_to_host_path(path: PurePosixPath, *, ctx: Context | tuple | None = None) -> Path | None:
    """
    Convert a path in a sandbox container to a host path

    Args:
        container_path: Path inside the container (must be a subdir of CONTAINER_WORKSPACE_PATH).
        user_id: ID of the user.
        session_id: ID of the session.

    Returns:
        Path to the file on the host, or None if the conversion fails.
    """
    # Try without service name (maybe the LLM forgot to put the SERVICE_NAME in the path)
    old_root = get_workspace_path_sandbox()
    new_root = get_workspace_path(ctx=ctx)
    try:
        # Relative paths are treated as relative to the new_root
        if not PurePosixPath(path).is_absolute():
            # Resolve paths to prevent escaping the workspace root
            new_path = Path(new_root / path).resolve()
            new_root = Path(new_root.resolve())
            if not new_path.is_relative_to(new_root):
                raise ValueError(f"Path must not escape the workspace root: '{path}'")
            return new_path
        # Otherwise, we treat it as absolute and change the root
        return new_root / Path(path).relative_to(old_root)
    except ValueError as e:
        raise ValueError(f"Container path must be a subdir of '{old_root}', got '{path}' instead") from e


def host_to_container_path(path: Path, *, ctx: Context | tuple | None = None) -> PurePosixPath:
    """
    Convert a host path to a path in a sandbox container.
    Paths inside the sandbox MUST be PurePosixPath (i.e. we use Linux containers).
    """
    old_root = get_workspace_path(ctx=ctx)
    new_root = get_workspace_path_sandbox()
    try:
        # Relative paths are treated as relative to the new_root
        if not Path(path).is_absolute():
            # Normalize paths to prevent escaping the workspace root (we cannot resolve PurePosixPaths)
            new_path = path_normalize(new_root / path)
            new_root = path_normalize(new_root)
            if not new_path.is_relative_to(new_root):
                raise ValueError(f"Path must not escape the workspace root: '{path}'")
            return new_path
        # Otherwise, we treat it as absolute and change the root
        return new_root / Path(path).relative_to(old_root)
    except ValueError as e:
        raise ValueError(f"Host path must be a subdir of either '{old_root}', got '{path}' instead") from e
