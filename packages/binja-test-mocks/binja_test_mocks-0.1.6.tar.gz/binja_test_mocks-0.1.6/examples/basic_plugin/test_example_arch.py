"""Test file for the example architecture."""

import os

os.environ["FORCE_BINJA_MOCK"] = "1"

# Import mock API first to set up the binaryninja module
from binja_test_mocks import binja_api  # noqa: F401, I001
from binja_test_mocks.mock_llil import MockLowLevelILFunction, set_size_lookup

from binaryninja.enums import BranchType

# Import after setting up mocks
from example_arch import ExampleArchitecture

# Set up size lookup for our 32-bit architecture
set_size_lookup({1: ".b", 2: ".w", 4: ".4"}, {"b": 1, "w": 2, "4": 4})


def test_nop_instruction() -> None:
    """Test NOP instruction handling."""
    arch = ExampleArchitecture()
    data = b"\x90"  # NOP

    # Test disassembly
    result = arch.get_instruction_text(data, 0x1000)
    assert result is not None
    tokens, length = result
    assert length == 1
    assert len(tokens) == 1
    assert tokens[0].text == "nop"

    # Test LLIL generation
    il = MockLowLevelILFunction()
    length = arch.get_instruction_low_level_il(data, 0x1000, il)
    assert length == 1
    assert len(il.ils) == 1
    assert il.ils[0].op == "NOP"


def test_jmp_instruction() -> None:
    """Test JMP instruction handling."""
    arch = ExampleArchitecture()
    data = b"\xc3\x00\x20\x00\x00"  # JMP 0x2000

    # Test instruction info
    info = arch.get_instruction_info(data, 0x1000)
    assert info is not None
    assert info.length == 5
    assert len(info.branches) == 1
    assert info.branches[0].type == BranchType.UnconditionalBranch
    assert info.branches[0].target == 0x2000

    # Test disassembly
    result = arch.get_instruction_text(data, 0x1000)
    assert result is not None
    tokens, length = result
    assert length == 5
    assert tokens[0].text == "jmp"
    assert "0x2000" in tokens[2].text

    # Test LLIL generation
    il = MockLowLevelILFunction()
    length = arch.get_instruction_low_level_il(data, 0x1000, il)
    assert length == 5
    assert len(il.ils) == 1
    assert il.ils[0].op == "JUMP"
    # The jump destination is a CONST expression
    assert il.ils[0].ops[0].op == "CONST.4"
    assert il.ils[0].ops[0].ops[0] == 0x2000


def test_ret_instruction() -> None:
    """Test RET instruction handling."""
    arch = ExampleArchitecture()
    data = b"\xc9"  # RET

    # Test instruction info
    info = arch.get_instruction_info(data, 0x1000)
    assert info is not None
    assert info.length == 1
    assert len(info.branches) == 1
    assert info.branches[0].type == BranchType.FunctionReturn

    # Test LLIL generation
    il = MockLowLevelILFunction()
    length = arch.get_instruction_low_level_il(data, 0x1000, il)
    assert length == 1
    assert len(il.ils) == 1
    assert il.ils[0].op == "RET"


def test_unknown_instruction() -> None:
    """Test handling of unknown instructions."""
    arch = ExampleArchitecture()
    data = b"\xff"  # Unknown opcode

    # Test disassembly shows db
    result = arch.get_instruction_text(data, 0x1000)
    assert result is not None
    tokens, length = result
    assert length == 1
    assert "db 0xff" in tokens[0].text

    # Test LLIL shows unimplemented
    il = MockLowLevelILFunction()
    length = arch.get_instruction_low_level_il(data, 0x1000, il)
    assert length == 1
    assert il.ils[0].op == "UNIMPL"


if __name__ == "__main__":
    test_nop_instruction()
    test_jmp_instruction()
    test_ret_instruction()
    test_unknown_instruction()
    print("All tests passed!")
