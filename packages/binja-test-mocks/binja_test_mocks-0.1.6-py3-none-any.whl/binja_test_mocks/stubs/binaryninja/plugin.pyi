from typing import Any

class PluginCommand:
    @staticmethod
    def register_for_address(*args: Any, **kwargs: Any) -> None: ...
    @staticmethod
    def register(*args: Any, **kwargs: Any) -> None: ...
