"""Basic tests for binja-test-mocks package."""

import os

os.environ["FORCE_BINJA_MOCK"] = "1"


def test_basic_import() -> None:
    """Test that we can import the package."""
    import binja_test_mocks

    # Just verify the package has a version attribute
    assert hasattr(binja_test_mocks, "__version__")
    assert isinstance(binja_test_mocks.__version__, str)


def test_binja_api_import() -> None:
    """Test that binja_api can be imported and sets up mocks."""

    # Verify that binaryninja module is mocked
    import sys

    assert "binaryninja" in sys.modules

    # Test basic imports work
    from binaryninja import Architecture, RegisterName

    assert Architecture is not None
    assert RegisterName is not None


def test_branchtype_has_unresolved_branch() -> None:
    """Test that BranchType includes UnresolvedBranch for no-fallthrough CFG edges."""
    import importlib

    importlib.import_module("binja_test_mocks.binja_api")
    branch_type = importlib.import_module("binaryninja.enums").BranchType

    assert branch_type.UnresolvedBranch is not None


def test_mock_llil() -> None:
    """Test mock LLIL functionality."""
    from binja_test_mocks import binja_api  # noqa: F401
    from binja_test_mocks.mock_llil import MockLowLevelILFunction

    il = MockLowLevelILFunction()
    il.append(il.nop())

    assert len(il.ils) == 1
    assert il.ils[0].op == "NOP"


def test_mock_llil_instruction_surface() -> None:
    """Test Binary Ninja-like LowLevelILInstruction helpers on MockLLIL."""
    from typing import Any, cast

    import pytest
    from binaryninja.enums import LowLevelILOperation

    from binja_test_mocks import (
        binja_api,  # noqa: F401
        mock_llil,
    )
    from binja_test_mocks.mock_llil import MockLowLevelILFunction

    il = MockLowLevelILFunction()

    mock_llil.set_size_lookup({1: ".b", 2: ".w", 4: ".d"}, {"b": 1, "w": 2, "d": 4})

    const = cast(Any, il.const(4, -1))
    assert const.operation == LowLevelILOperation.LLIL_CONST
    assert const.operands == [-1]
    assert const.size == 4
    assert const.constant == -1

    const_ptr = cast(Any, il.const_pointer(4, 0x1234))
    assert const_ptr.operation == LowLevelILOperation.LLIL_CONST_PTR
    assert const_ptr.operands == [0x1234]
    assert const_ptr.size == 4
    assert const_ptr.constant == 0x1234

    reg = cast(Any, il.reg(4, "d0"))
    assert reg.operation == LowLevelILOperation.LLIL_REG
    assert reg.size == 4
    assert getattr(reg.operands[0], "name", None) == "d0"
    with pytest.raises(AttributeError):
        _ = reg.constant


def test_tokens() -> None:
    """Test token utilities."""
    from binja_test_mocks import binja_api  # noqa: F401
    from binja_test_mocks.tokens import TInt, TText

    # Test token creation
    int_token = TInt("42")
    assert hasattr(int_token, "value")
    assert int_token.value == "42"
    assert hasattr(int_token.__class__, "token_type")

    text_token = TText("hello")
    assert hasattr(text_token, "value")
    assert text_token.value == "hello"
    assert hasattr(text_token.__class__, "token_type")


def test_stubs_available() -> None:
    """Test that type stubs are accessible."""
    from pathlib import Path

    import binja_test_mocks

    package_dir = Path(binja_test_mocks.__file__).parent
    stubs_dir = package_dir / "stubs" / "binaryninja"

    assert stubs_dir.exists()
    assert (stubs_dir / "__init__.pyi").exists()
    assert (stubs_dir / "architecture.pyi").exists()


if __name__ == "__main__":
    test_basic_import()
    test_binja_api_import()
    test_mock_llil()
    test_tokens()
    test_stubs_available()
    print("All tests passed!")
