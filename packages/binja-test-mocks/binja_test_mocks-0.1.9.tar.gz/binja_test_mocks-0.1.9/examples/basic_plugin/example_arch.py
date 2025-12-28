"""Example architecture implementation."""

from typing import ClassVar

from binaryninja import Architecture, InstructionInfo, RegisterInfo, RegisterName
from binaryninja.enums import BranchType
from binaryninja.lowlevelil import LowLevelILFunction


class ExampleArchitecture(Architecture):
    """Simple example architecture for demonstration."""

    name = "Example"
    address_size = 4
    default_int_size = 4

    # Define registers
    regs: ClassVar[dict[RegisterName, RegisterInfo]] = {
        RegisterName("r0"): RegisterInfo(RegisterName("r0"), 4),
        RegisterName("r1"): RegisterInfo(RegisterName("r1"), 4),
        RegisterName("sp"): RegisterInfo(RegisterName("sp"), 4),
        RegisterName("pc"): RegisterInfo(RegisterName("pc"), 4),
    }

    def get_instruction_info(self, data: bytes, addr: int) -> InstructionInfo | None:
        """Analyze instruction for branches and calls."""
        if len(data) < 1:
            return None

        info = InstructionInfo()
        info.length = 1  # Simple 1-byte instructions

        opcode = data[0]
        if opcode == 0x90:  # NOP
            pass
        elif opcode == 0xC3:  # JMP
            if len(data) >= 5:
                target = int.from_bytes(data[1:5], "little")
                info.add_branch(BranchType.UnconditionalBranch, target)
                info.length = 5
        elif opcode == 0xC9:  # RET
            info.add_branch(BranchType.FunctionReturn)

        return info

    def get_instruction_text(self, data: bytes, addr: int) -> tuple[list, int] | None:
        """Disassemble instruction to text."""
        if len(data) < 1:
            return None

        from binaryninja import InstructionTextToken
        from binaryninja.enums import InstructionTextTokenType

        tokens = []
        length = 1

        opcode = data[0]
        if opcode == 0x90:  # NOP
            tokens.append(InstructionTextToken(InstructionTextTokenType.InstructionToken, "nop"))
        elif opcode == 0xC3:  # JMP
            if len(data) >= 5:
                target = int.from_bytes(data[1:5], "little")
                tokens.append(
                    InstructionTextToken(InstructionTextTokenType.InstructionToken, "jmp")
                )
                tokens.append(InstructionTextToken(InstructionTextTokenType.TextToken, " "))
                tokens.append(
                    InstructionTextToken(
                        InstructionTextTokenType.PossibleAddressToken, f"0x{target:x}"
                    )
                )
                length = 5
        elif opcode == 0xC9:  # RET
            tokens.append(InstructionTextToken(InstructionTextTokenType.InstructionToken, "ret"))
        else:
            tokens.append(
                InstructionTextToken(
                    InstructionTextTokenType.InstructionToken, f"db 0x{opcode:02x}"
                )
            )

        return tokens, length

    def get_instruction_low_level_il(
        self, data: bytes, addr: int, il: LowLevelILFunction
    ) -> int | None:
        """Lift instruction to LLIL."""
        if len(data) < 1:
            return None

        opcode = data[0]
        if opcode == 0x90:  # NOP
            il.append(il.nop())
            return 1
        if opcode == 0xC3:  # JMP
            if len(data) >= 5:
                target = int.from_bytes(data[1:5], "little")
                il.append(il.jump(il.const(4, target)))
                return 5
        elif opcode == 0xC9:  # RET
            il.append(il.ret(il.pop(4)))
            return 1
        else:
            il.append(il.unimplemented())
            return 1

        return None
