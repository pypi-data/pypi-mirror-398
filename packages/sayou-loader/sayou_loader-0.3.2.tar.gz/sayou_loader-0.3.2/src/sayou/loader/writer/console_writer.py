import json
from typing import Any

from sayou.core.registry import register_component

from ..interfaces.base_writer import BaseWriter


@register_component("writer")
class ConsoleWriter(BaseWriter):
    """
    (Tier 2) Prints data to stdout. Useful for debugging pipelines.
    """

    component_name = "ConsoleWriter"
    SUPPORTED_TYPES = ["console", "stdout", "print"]

    @classmethod
    def can_handle(
        cls, input_data: Any, destination: str, strategy: str = "auto"
    ) -> float:
        if strategy in cls.SUPPORTED_TYPES:
            return 1.0

        if destination and destination.lower() in ["stdout", "console", "print"]:
            return 1.0

        return 0.0

    def _do_write(self, input_data: Any, destination: str, **kwargs) -> bool:
        print(f"\n--- [ConsoleWriter] Output to: {destination} ---")

        if isinstance(input_data, (dict, list)):
            print(json.dumps(input_data, indent=2, ensure_ascii=False))
        else:
            print(input_data)

        print("----------------------------------------------\n")
        return True
