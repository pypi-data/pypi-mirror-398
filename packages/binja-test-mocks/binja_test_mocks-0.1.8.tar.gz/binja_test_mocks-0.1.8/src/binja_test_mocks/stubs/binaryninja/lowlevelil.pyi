from collections.abc import Callable
from typing import Any

from . import ILIntrinsic, ILRegister, IntrinsicIndex, IntrinsicName, RegisterIndex, RegisterName
from .architecture import Architecture
from .function import Function

ExpressionIndex = int

def LLIL_TEMP(n: int) -> ExpressionIndex:  # noqa: N802
    ...

class LowLevelILFunction:
    @property
    def source_function(self) -> Function:
        """The source function that this LLIL belongs to."""
        ...

    @property
    def arch(self) -> Architecture:
        """The architecture for this LLIL function."""
        ...

    def expr(self, *args: Any, size: int | None, flags: Any | None = None) -> ExpressionIndex: ...
    def reg(self, size: int, reg: RegisterName | ILRegister | RegisterIndex) -> ExpressionIndex: ...
    def set_reg(
        self,
        size: int,
        reg: RegisterName | ILRegister | RegisterIndex,
        value: Any,
        flags: Any | None = None,
    ) -> ExpressionIndex: ...
    def intrinsic(
        self,
        outputs: list[Any],
        name: IntrinsicName | ILIntrinsic | IntrinsicIndex,
        inputs: list[Any],
    ) -> ExpressionIndex: ...
    def __getattr__(self, name: str) -> Callable[..., ExpressionIndex]: ...

class LowLevelILLabel: ...

class ILSourceLocation:
    instr_index: int
