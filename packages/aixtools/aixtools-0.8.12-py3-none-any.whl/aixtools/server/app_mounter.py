"""Utility for mounting sub-applications with lifespan management in Starlette/FastAPI."""

from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.types import ASGIApp


class AppMounter:  # pylint: disable=too-few-public-methods
    """
    A utility class for mounting sub-applications with their lifespans.

    This class handles the complexity of ensuring that mounted sub-applications
    have their lifespans properly managed alongside the parent application.
    """

    def __init__(self, parent_app: Starlette):
        """
        Initialize the SubAppMounter with a parent application.

        Args:
            parent_app: The parent Starlette/FastAPI application
        """
        self.parent_app = parent_app
        self.mounted_apps: list[tuple[str, ASGIApp]] = []
        self._original_lifespan = parent_app.router.lifespan_context
        self._setup_combined_lifespan()

    def mount_with_lifespan(self, path: str, app: ASGIApp, name: str = None) -> None:
        """
        Mount a sub-application and ensure its lifespan is managed.

        Args:
            path: The path to mount the application at
            app: The ASGI application to mount
            name: Optional name for the mounted application
        """
        # Mount the app using the parent app's mount method
        self.parent_app.mount(path, app=app, name=name)

        # Store the mounted app for lifespan management
        self.mounted_apps.append((path, app))

    def _setup_combined_lifespan(self) -> None:
        """
        Set up a combined lifespan that manages both the parent app and all mounted sub-apps.
        """

        @asynccontextmanager
        async def combined_lifespan(app):
            # First enter the parent app's lifespan
            async with self._original_lifespan(app):
                # Then enter each mounted app's lifespan in order
                # We use nested context managers to ensure proper cleanup
                async with self._create_nested_lifespans():
                    yield

        # Replace the parent app's lifespan with our combined one
        self.parent_app.router.lifespan_context = combined_lifespan

    @asynccontextmanager
    async def _create_nested_lifespans(self):
        """
        Create nested async context managers for all mounted apps.

        This ensures that all sub-app lifespans are entered and exited in the correct order.
        """
        # If no apps are mounted, just yield
        if not self.mounted_apps:
            yield
            return

        # Otherwise, create nested context managers for each mounted app
        async def enter_lifespans(index=0):
            if index >= len(self.mounted_apps):
                yield
                return

            _, app = self.mounted_apps[index]
            if hasattr(app, "router") and hasattr(app.router, "lifespan_context"):
                async with app.router.lifespan_context(app):
                    async for _ in enter_lifespans(index + 1):
                        yield
            else:
                # If the app doesn't have a lifespan, just move to the next one
                async for _ in enter_lifespans(index + 1):
                    yield

        async for _ in enter_lifespans():
            yield
