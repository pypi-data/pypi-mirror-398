"""Base session manager for managing user sessions."""

import logging
import os
import uuid
from pathlib import Path
from threading import Lock

import docker

from podkit.core.manager import BaseContainerManager
from podkit.core.models import ContainerConfig, ContainerStatus, Session
from podkit.utils.paths import get_workspace_path

logger = logging.getLogger("podkit")


class BaseSessionManager:
    """Base session manager for managing user sessions."""

    def __init__(
        self,
        container_manager: BaseContainerManager,
        default_image: str | None = None,
    ):
        """
        Initialize the session manager.

        Args:
            container_manager: Container manager instance.
            default_image: Default Docker image to use for containers.
                          If None, will auto-detect from current container or raise error.
        """
        self.container_manager = container_manager
        self.default_image = default_image or self._detect_default_image()
        self.sessions: dict[str, Session] = {}
        self.lock = Lock()
        self._recover_sessions()

    def _detect_default_image(self) -> str:
        """Detect the default image to use for sandboxes.

        Returns:
            Detected image name.

        Raises:
            RuntimeError: If cannot detect image and none specified.
        """
        # Try to detect if we're running in a container
        try:
            client = docker.from_env()
            # Get current container's hostname (which is container ID in Docker)
            hostname = os.uname().nodename

            try:
                container = client.containers.get(hostname)
                image_name = container.image.tags[0] if container.image.tags else container.image.id
                logger.warning(f"No default_image specified. Auto-detected from current container: {image_name}")
                return image_name
            except docker.errors.NotFound as exc:
                # Not running in a Docker container
                raise RuntimeError(
                    "No default_image specified and could not auto-detect "
                    "(not running in a container). Please specify an image."
                ) from exc
        except Exception as e:
            raise RuntimeError(
                f"No default_image specified and detection failed: {e}. Please specify an image explicitly."
            ) from e

    def _recover_sessions(self) -> None:
        """Discover and reconnect to existing containers on startup.

        This allows sessions to survive server restarts by reconnecting to
        containers that are still running.
        """
        try:
            discovered = self.container_manager.discover_existing_containers()

            if not discovered:
                logger.info("No existing containers to recover")
                return

            logger.info(f"Discovering {len(discovered)} existing container(s)...")

            for container_info in discovered:
                try:
                    container_id = container_info["container_id"]
                    user_id = container_info["user_id"]
                    session_id = container_info["session_id"]

                    # Get workspace path using utility function
                    workspace_path = get_workspace_path(self.container_manager.workspace_base, user_id, session_id)

                    # Create session object
                    session = Session(
                        user_id=user_id,
                        session_id=session_id,
                        container_id=container_id,
                        container_name=container_info["container_name"],
                        status=ContainerStatus.RUNNING,
                        config=ContainerConfig(image=self.default_image),
                        data_dir=str(workspace_path),
                    )

                    # Add to sessions
                    session_key = f"{user_id}:{session_id}"
                    self.sessions[session_key] = session

                    logger.info(f"Recovered session: {session_key} (container: {container_id[:12]})")

                except Exception as e:  # pylint: disable=broad-except
                    logger.error(f"Failed to recover container {container_info.get('container_id')}: {e}")

            logger.info(f"Session recovery complete. Recovered {len(self.sessions)} session(s)")

        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Session recovery failed: {e}")

    def create_session(
        self,
        user_id: str,
        session_id: str | None = None,
        config: ContainerConfig | None = None,
    ) -> Session:
        """
        Create a new session.

        Args:
            user_id: ID of the user.
            session_id: ID of the session. If None, a new ID will be generated.
            config: Container configuration. If None, default configuration will be used.

        Returns:
            The created session.

        Raises:
            RuntimeError: If the session creation fails.
        """
        with self.lock:
            if session_id is None:
                session_id = str(uuid.uuid4())

            session_key = f"{user_id}:{session_id}"
            if session_key in self.sessions:
                return self.sessions[session_key]

            if config is None:
                config = ContainerConfig(image=self.default_image)

            workspace_path = self.container_manager.workspace_base / user_id / session_id
            data_dir = str(workspace_path)

            session = Session(
                user_id=user_id,
                session_id=session_id,
                config=config,
                data_dir=data_dir,
            )

            container_id = None
            try:
                container_id, container_name = self.container_manager.create_container(
                    user_id=user_id,
                    session_id=session_id,
                    config=config,
                )

                session.container_id = container_id
                session.container_name = container_name
                session.status = ContainerStatus.RUNNING

                self.container_manager.start_container(container_id)
                self.sessions[session_key] = session

                return session

            except Exception as e:
                if container_id is not None:
                    try:
                        self.container_manager.remove_container(container_id)
                    except Exception:  # pylint: disable=broad-exception-caught
                        pass

                raise RuntimeError(f"Failed to create session: {e}") from e

    def get_session(self, user_id: str, session_id: str) -> Session | None:
        """
        Get a session.

        Args:
            user_id: ID of the user.
            session_id: ID of the session.

        Returns:
            The session, or None if not found.
        """
        session_key = f"{user_id}:{session_id}"
        return self.sessions.get(session_key)

    def update_session_activity(self, user_id: str, session_id: str) -> None:
        """
        Update the last activity timestamp of a session.

        Args:
            user_id: ID of the user.
            session_id: ID of the session.

        Raises:
            RuntimeError: If the session is not found.
        """
        session_key = f"{user_id}:{session_id}"
        session = self.sessions.get(session_key)

        if session is None:
            raise RuntimeError(f"Session not found: {session_key}")

        session.update_activity()

    def execute_command(
        self,
        user_id: str,
        session_id: str,
        command: str | list[str],
        working_dir: Path | None = None,
        environment: dict[str, str] | None = None,
        timeout: int | None = None,
    ):
        """
        Execute a command in a session's container.

        This is a convenience method that combines session lookup, command execution,
        and activity tracking in one call.

        Args:
            user_id: ID of the user.
            session_id: ID of the session.
            command: Command to execute.
            working_dir: Working directory for command execution.
            environment: Environment variables.
            timeout: Timeout in seconds.

        Returns:
            ProcessResult with exit code and output.

        Raises:
            RuntimeError: If the session is not found or command execution fails.
        """
        session = self.get_session(user_id, session_id)
        if session is None:
            raise RuntimeError(f"Session not found: {user_id}:{session_id}")

        result = self.container_manager.execute_command(
            container_id=session.container_id,
            command=command,
            working_dir=working_dir,
            environment=environment,
            timeout=timeout,
        )

        self.update_session_activity(user_id, session_id)

        return result

    def write_file(
        self,
        user_id: str,
        session_id: str,
        container_path: Path,
        content: str,
    ) -> None:
        """
        Write a file to a session's container workspace.

        This method combines session lookup, path translation, file writing,
        and activity tracking in one call.

        Args:
            user_id: ID of the user.
            session_id: ID of the session.
            container_path: Path inside the container.
            content: Content to write.

        Raises:
            RuntimeError: If the session is not found or file write fails.
        """
        session = self.get_session(user_id, session_id)
        if session is None:
            raise RuntimeError(f"Session not found: {user_id}:{session_id}")

        host_path = self.container_manager.to_host_path(
            container_path=container_path,
            user_id=user_id,
            session_id=session_id,
        )

        host_path.parent.mkdir(parents=True, exist_ok=True)
        host_path.write_text(content, encoding="utf-8")
        self.update_session_activity(user_id, session_id)

    def close_session(self, user_id: str, session_id: str) -> None:
        """
        Close a session.

        Args:
            user_id: ID of the user.
            session_id: ID of the session.

        Raises:
            RuntimeError: If the session is not found.
        """
        with self.lock:
            session_key = f"{user_id}:{session_id}"
            session = self.sessions.get(session_key)

            if session is None:
                raise RuntimeError(f"Session not found: {session_key}")

            if session.container_id:
                try:
                    self.container_manager.remove_container(session.container_id)
                except Exception:  # pylint: disable=broad-except
                    pass

            session.status = ContainerStatus.STOPPED
            del self.sessions[session_key]

    def cleanup_all(self) -> None:
        """Clean up all sessions and their containers."""
        with self.lock:
            session_keys = list(self.sessions.keys())

        for session_key in session_keys:
            user_id, session_id = session_key.split(":", 1)
            try:
                self.close_session(user_id, session_id)
            except Exception:  # pylint: disable=broad-except
                pass
