# binja-test-mocks

[![CI](https://github.com/mblsha/binja-test-mocks/actions/workflows/tests.yml/badge.svg)](https://github.com/mblsha/binja-test-mocks/actions/workflows/tests.yml)
[![PyPI version](https://badge.fury.io/py/binja-test-mocks.svg)](https://badge.fury.io/py/binja-test-mocks)
[![Python versions](https://img.shields.io/pypi/pyversions/binja-test-mocks.svg)](https://pypi.org/project/binja-test-mocks/)

Mock Binary Ninja API for testing Binary Ninja plugins without requiring a Binary Ninja license.

## Overview

`binja-test-mocks` provides a comprehensive set of mock objects and utilities that allow you to:
- Unit test Binary Ninja plugins without a Binary Ninja installation
- Run type checking with mypy/pyright using accurate type stubs
- Develop and test plugins in CI/CD environments

## Installation

```bash
pip install binja-test-mocks
```

For development:
```bash
pip install -e /path/to/binja-test-mocks
```

## Quick Start

### Basic Usage

```python
# In your test files, set the environment variable before imports
import os
os.environ["FORCE_BINJA_MOCK"] = "1"

# Import the mock API before importing your plugin
from binja_test_mocks import binja_api  # noqa: F401

# Now you can import your plugin modules that use Binary Ninja
from your_plugin import YourArchitecture
```

### Example Test

```python
import os
os.environ["FORCE_BINJA_MOCK"] = "1"

from binja_test_mocks import binja_api  # noqa: F401
from binja_test_mocks.mock_llil import MockLowLevelILFunction
from your_plugin.arch import MyArchitecture

def test_instruction_lifting():
    # Create mock LLIL function
    il = MockLowLevelILFunction()
    
    # Test your architecture's IL generation
    arch = MyArchitecture()
    arch.get_instruction_low_level_il(b"\x90", 0x1000, il)
    
    # Verify the generated IL
    assert len(il.operations) == 1
    assert il.operations[0].op == "NOP"
```

## Components

### Mock Modules

- **binja_api.py**: Core mock loader that intercepts Binary Ninja imports
- **mock_llil.py**: Mock Low Level IL classes and operations
- **mock_binaryview.py**: Mock BinaryView for testing file format plugins
- **mock_analysis.py**: Mock analysis information (branches, calls, etc.)
- **tokens.py**: Token generation utilities for disassembly
- **coding.py**: Binary encoding/decoding helpers
- **eval_llil.py**: LLIL expression evaluator for testing

### Type Stubs

Complete type stubs for Binary Ninja API in `stubs/binaryninja/`:
- architecture.pyi
- binaryview.pyi
- lowlevelil.pyi
- enums.pyi
- types.pyi
- function.pyi
- log.pyi
- interaction.pyi

## Integration Examples

### Plugin Structure

```python
# your_plugin/__init__.py
import sys
from pathlib import Path

# Add plugin directory to path
plugin_dir = str(Path(__file__).resolve().parent)
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

# For testing, load mock API
import os
if os.environ.get("FORCE_BINJA_MOCK") == "1":
    from binja_test_mocks import binja_api  # noqa: F401

# Your normal plugin code
from binaryninja import Architecture
from .arch import MyArchitecture

MyArchitecture.register()
```

### Type Checking Configuration

#### mypy.ini
```ini
[mypy]
mypy_path = /path/to/binja-test-mocks/src/binja_test_mocks/stubs
plugins = mypy_binja_plugin

[mypy-binaryninja.*]
ignore_missing_imports = False
```

#### pyrightconfig.json
```json
{
  "extraPaths": [
    "/path/to/binja-test-mocks/src/binja_test_mocks/stubs"
  ],
  "typeCheckingMode": "strict"
}
```

### Running Tests

```bash
# Set environment variable and run pytest
FORCE_BINJA_MOCK=1 pytest

# Or use a test runner script
python -m binja_test_mocks.scripts.run_tests
```

## Advanced Usage

### Custom Mock Behavior

```python
from binja_test_mocks.mock_llil import MockLowLevelILFunction

class CustomMockIL(MockLowLevelILFunction):
    def __init__(self):
        super().__init__()
        self.custom_data = []
    
    def append(self, expr):
        self.custom_data.append(expr)
        return super().append(expr)
```

### Testing Binary Views

```python
from binja_test_mocks.mock_binaryview import MockBinaryView

def test_binary_view_parsing():
    data = b"\x4d\x5a\x90\x00"  # PE header
    bv = MockBinaryView(data)
    
    # Your binary view implementation
    my_view = MyBinaryView(bv)
    assert my_view.init()
```

## Migration from binja_helpers

If you're migrating from the old `binja_helpers`:

1. Update imports:
   ```python
   # Old
   from binja_helpers import binja_api
   
   # New
   from binja_test_mocks import binja_api
   ```

2. Update path additions if needed:
   ```python
   # Old
   sys.path.insert(0, str(plugin_dir / "binja_helpers_tmp"))
   
   # New - not needed if installed via pip
   ```

## Contributing

Contributions are welcome! Please ensure:
- All tests pass with `pytest`
- Type checking passes with `mypy` and `pyright`
- Code is formatted with `ruff`

## License

MIT License - see LICENSE file for details.