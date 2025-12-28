from binaryninja import Architecture, InstructionInfo
from binaryninja.enums import BranchType

from . import binja_api  # noqa: F401


class MockAnalysisInfo(InstructionInfo):
    def __init__(self) -> None:
        self.length = 0
        self.mybranches: list[tuple[BranchType, int | None]] = []

    def add_branch(
        self, branch_type: BranchType, target: int | None = None, arch: Architecture | None = None
    ) -> None:
        self.mybranches.append((branch_type, target))
