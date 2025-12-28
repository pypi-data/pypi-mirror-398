"""binja-test-mocks - Mock Binary Ninja API for testing plugins without a license."""

__version__ = "0.1.6"

# Re-export commonly used items for convenience
from . import binja_api

__all__ = ["binja_api"]
