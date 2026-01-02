"""API client types for the klab-pytest-toolkit-web package."""

import abc


class ApiClient(abc.ABC):
    """Abstract base class for API clients."""

    def close(self) -> None:
        """Close any resources held by the client."""
        raise NotImplementedError

    def __enter__(self):
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context related to this object."""
        self.close()


__all__ = ["ApiClient"]
