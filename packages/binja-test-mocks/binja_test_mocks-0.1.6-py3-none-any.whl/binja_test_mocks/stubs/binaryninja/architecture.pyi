from typing import Any

from . import FlagWriteTypeName, RegisterInfo, RegisterName

class Architecture:
    address_size: int
    name: str
    regs: dict[RegisterName, RegisterInfo]
    stack_pointer: str
    flag_write_types: list[FlagWriteTypeName | str]
    standalone_platform: Any

    def __getitem__(self, name: str) -> Architecture: ...
    @classmethod
    def __class_getitem__(cls, name: str) -> Architecture: ...

class FlagName(str): ...
