"""Example Binary Ninja plugin using binja-test-mocks for testing."""

import os
import sys
from pathlib import Path

# Add plugin directory to path
plugin_dir = str(Path(__file__).resolve().parent)
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

# For testing, load mock API
if os.environ.get("FORCE_BINJA_MOCK") == "1":
    from binja_test_mocks import binja_api  # noqa: F401

# Check if we're running in Binary Ninja
try:
    from .example_arch import ExampleArchitecture

    # Register the architecture
    ExampleArchitecture.register()
except ImportError:
    # Not running in Binary Ninja, likely in test mode
    pass
