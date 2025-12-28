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
