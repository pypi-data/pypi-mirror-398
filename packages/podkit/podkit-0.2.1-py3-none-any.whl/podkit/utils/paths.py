"""Path translation utilities for container and host filesystems."""

from pathlib import Path


def container_to_host_path(
    container_path: Path,
    workspace_base: Path,
    container_workspace: Path = Path("/workspace"),
) -> Path:
    """
    Convert a container path to a host path.

    Args:
        container_path: Path inside the container.
        workspace_base: Base workspace directory on the host.
        container_workspace: Workspace path inside the container (default: /workspace).

    Returns:
        Path on the host filesystem.

    Raises:
        ValueError: If container_path is not within the container workspace.

    Example:
        >>> container_to_host_path(
        ...     Path("/workspace/test.txt"),
        ...     Path("/home/user/.podkit/test/user1/session1"),
        ...     Path("/workspace")
        ... )
        Path("/home/user/.podkit/test/user1/session1/test.txt")
    """
    # Ensure paths are Path objects
    container_path = Path(container_path)
    workspace_base = Path(workspace_base)
    container_workspace = Path(container_workspace)

    # Check if container_path is within the container workspace
    try:
        relative_path = container_path.relative_to(container_workspace)
    except ValueError as e:
        raise ValueError(
            f"Container path '{container_path}' must be within container workspace '{container_workspace}'"
        ) from e

    # Construct host path
    host_path = workspace_base / relative_path
    return host_path


def host_to_container_path(
    host_path: Path,
    workspace_base: Path,
    container_workspace: Path = Path("/workspace"),
) -> Path:
    """
    Convert a host path to a container path.

    Args:
        host_path: Path on the host filesystem.
        workspace_base: Base workspace directory on the host.
        container_workspace: Workspace path inside the container (default: /workspace).

    Returns:
        Path inside the container.

    Raises:
        ValueError: If host_path is not within the workspace base.

    Example:
        >>> host_to_container_path(
        ...     Path("/home/user/.podkit/test/user1/session1/test.txt"),
        ...     Path("/home/user/.podkit/test/user1/session1"),
        ...     Path("/workspace")
        ... )
        Path("/workspace/test.txt")
    """
    # Ensure paths are Path objects
    host_path = Path(host_path)
    workspace_base = Path(workspace_base)
    container_workspace = Path(container_workspace)

    # Check if host_path is within the workspace base
    try:
        relative_path = host_path.relative_to(workspace_base)
    except ValueError as e:
        raise ValueError(f"Host path '{host_path}' must be within workspace base '{workspace_base}'") from e

    # Construct container path
    container_path = container_workspace / relative_path
    return container_path


def get_workspace_path(
    workspace_base: Path,
    user_id: str,
    session_id: str,
) -> Path:
    """
    Get the workspace path for a specific user and session.

    Args:
        workspace_base: Base workspace directory.
        user_id: User identifier.
        session_id: Session identifier.

    Returns:
        Path to the user's session workspace.

    Example:
        >>> get_workspace_path(Path("/var/lib/podkit/workspaces"), "user1", "session1")
        Path("/var/lib/podkit/workspaces/user1/session1")
    """
    return workspace_base / user_id / session_id
