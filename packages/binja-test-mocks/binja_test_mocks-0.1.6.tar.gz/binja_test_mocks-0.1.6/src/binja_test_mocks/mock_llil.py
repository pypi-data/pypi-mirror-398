# Make LLIL unit-testable.

from dataclasses import dataclass
from typing import Any

from binaryninja.lowlevelil import (
    ExpressionIndex,
    ILSourceLocation,
    LowLevelILFunction,
    LowLevelILLabel,
)

from . import binja_api  # noqa: F401

# Default size lookup table - can be overridden per architecture
DEFAULT_SZ_LOOKUP = {1: ".b", 2: ".w", 3: ".l", 4: ".error"}
DEFAULT_SUFFIX_SZ = {"b": 1, "w": 2, "l": 3}

# Current active size lookup - can be modified by set_size_lookup()
SZ_LOOKUP = DEFAULT_SZ_LOOKUP.copy()
SUFFIX_SZ = DEFAULT_SUFFIX_SZ.copy()


def set_size_lookup(size_lookup: dict[int, str], suffix_sz: dict[str, int] | None = None) -> None:
    """
    Set custom size lookup tables for architecture-specific width suffixes.

    Args:
        size_lookup: Map from byte size to suffix string (e.g., {4: ".4"})
        suffix_sz: Optional reverse mapping from suffix to size (e.g., {"4": 4})
    """
    global SZ_LOOKUP, SUFFIX_SZ
    SZ_LOOKUP = size_lookup.copy()
    if suffix_sz is not None:
        SUFFIX_SZ = suffix_sz.copy()


def reset_size_lookup() -> None:
    """Reset size lookup tables to defaults."""
    global SZ_LOOKUP, SUFFIX_SZ
    SZ_LOOKUP = DEFAULT_SZ_LOOKUP.copy()
    SUFFIX_SZ = DEFAULT_SUFFIX_SZ.copy()


@dataclass
class MockReg:
    name: str


@dataclass
class MockFlag:
    name: str


# we cannot use real Architecture (it requires a Binary Ninja license)
class MockArch:
    address_size = 4  # SCUMM6 uses 4-byte addresses

    def get_reg_index(self, name: object) -> Any:
        assert name != "IMR"

        if isinstance(name, int):
            result = MockReg(f"TEMP{name - 2147483648}")
        else:
            result = MockReg(str(name))
        return result

    def get_flag_by_name(self, name: str) -> Any:
        return MockFlag(name)


class MockHandle:
    pass


@dataclass
class MockLLIL:
    """Simplified stand-in for Binary Ninja's LLIL expression.

    WARNING: On a real Binary Ninja instance these expressions are
    represented by ``ExpressionIndex`` integers.  This class exists only
    for testing and should not be confused with the real API.
    """

    op: str
    ops: list[Any]

    def width(self) -> int | None:
        op = self.op.split("{")[0]
        opsplit = op.split(".")
        op = opsplit[0]
        if len(opsplit) > 1:
            suffix = opsplit[1]
            size = SUFFIX_SZ.get(suffix, None)
        else:
            size = None
        return size

    def flags(self) -> str | None:
        flagssplit = self.op.split("{")
        flags = flagssplit[1].rstrip("}") if len(flagssplit) > 1 else None
        return flags

    def bare_op(self) -> str:
        return self.op.split("{")[0].split(".")[0]


ExprType = MockLLIL | ExpressionIndex


def mreg(name: str) -> MockReg:
    return MockReg(name)


def mllil(op: str, ops: list[object] | None = None) -> MockLLIL:
    if ops is None:
        ops = []
    return MockLLIL(op, ops)


@dataclass
class MockIfExpr(MockLLIL):
    cond: Any
    t: Any
    f: Any

    def __init__(self, cond: Any, t: Any, f: Any) -> None:
        super().__init__("IF", [])
        self.cond = cond
        self.t = t
        self.f = f


@dataclass
class MockLabel(MockLLIL):
    label: LowLevelILLabel

    def __init__(self, label: LowLevelILLabel) -> None:
        super().__init__("LABEL", [])
        self.label = label


@dataclass
class MockIntrinsic(MockLLIL):
    name: str
    outputs: Any
    params: Any

    def __init__(self, name: str, outputs: Any, params: Any) -> None:
        super().__init__("INTRINSIC", [])
        self.name = name
        self.outputs = outputs
        self.params = params


@dataclass
class MockGoto:
    label: Any


class MockSourceFunction:
    """Mock source function with arch attribute."""

    def __init__(self, arch: Any) -> None:
        self.arch = arch


class MockLowLevelILFunction(LowLevelILFunction):
    def __init__(self, arch: Any | None = None) -> None:
        # self.handle = MockHandle()
        self._arch = arch if arch is not None else MockArch()
        self.ils: list[MockLLIL] = []
        self.current_address: int = 0
        self._labels_by_addr: dict[int, LowLevelILLabel] = {}
        self._source_function = MockSourceFunction(self._arch)

    @property
    def source_function(self) -> Any:
        """The source function that this LLIL belongs to."""
        return self._source_function

    @property
    def arch(self) -> Any:
        """The architecture for this LLIL function."""
        return self._arch

    def __del__(self) -> None:
        pass

    def mark_label(self, label: LowLevelILLabel) -> Any:
        return label

    def goto(self, label: LowLevelILLabel, loc: ILSourceLocation | None = None) -> Any:
        from types import SimpleNamespace

        return self.expr(SimpleNamespace(name="LLIL_GOTO"), label, size=None)

    def if_expr(self, cond, t, f) -> Any:  # type: ignore
        from types import SimpleNamespace

        return self.expr(SimpleNamespace(name="LLIL_IF"), cond, t, f, size=None)

    def intrinsic(self, outputs, name: str, params) -> Any:  # type: ignore
        return MockIntrinsic(name, outputs, params)

    def append(self, il: Any) -> Any:
        self.ils.append(il)
        return len(self.ils) - 1

    def __iter__(self) -> Any:
        return iter(self.ils)

    def __getitem__(self, idx: object) -> object:
        if isinstance(idx, int):
            return self.ils[idx]
        return idx

    def expr(self, *args, **kwargs) -> ExprType:  # type: ignore
        llil, *ops = args
        kwargs.pop("source_location", None)
        size = kwargs.get("size")
        flags = kwargs.get("flags")
        if flags in (0, "0"):
            flags = None

        name = llil.name
        # remove the "LLIL_" prefix
        name = name[5:]
        suffix = SZ_LOOKUP.get(size, "") if isinstance(size, int) else ""
        name = name + suffix
        name = name + f"{{{flags}}}" if flags is not None else name
        return MockLLIL(name, ops)

    def get_label_for_address(self, arch: Any, addr: int) -> LowLevelILLabel | None:
        """Return a stable label if one has been registered for an address."""
        return self._labels_by_addr.get(int(addr))

    def register_label_for_address(
        self, addr: int, label: LowLevelILLabel | None = None
    ) -> LowLevelILLabel:
        """Register a label for an address so `get_label_for_address` can return it."""
        if label is None:
            label = LowLevelILLabel()
        self._labels_by_addr[int(addr)] = label
        return label

    def flag_condition(self, cond: int, loc: ILSourceLocation | None = None) -> ExprType:
        from types import SimpleNamespace

        return self.expr(SimpleNamespace(name="LLIL_FLAG_COND"), int(cond), None, size=None)
