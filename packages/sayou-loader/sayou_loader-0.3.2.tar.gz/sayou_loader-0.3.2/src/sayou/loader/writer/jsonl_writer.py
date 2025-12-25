import json
import os
from typing import Any

from sayou.core.registry import register_component

from ..interfaces.base_writer import BaseWriter


@register_component("writer")
class JsonLineWriter(BaseWriter):
    """
    Writes a list of dictionaries to a JSONL file.

    Useful for large datasets like logs or vector embeddings where
    loading the entire file into memory is inefficient.
    """

    component_name = "JsonLineWriter"
    SUPPORTED_TYPES = ["jsonl", "stream"]

    @classmethod
    def can_handle(
        cls, input_data: Any, destination: str, trategy: str = "auto"
    ) -> float:
        if strategy in cls.SUPPORTED_TYPES:
            return 1.0

        if destination and destination.endswith(".jsonl"):
            return 1.0

        return 0.0

    def _do_write(self, input_data: Any, destination: str, **kwargs) -> bool:
        """
        Iterate through the list and write each item as a JSON line.
        """
        if not isinstance(input_data, list):
            self._log("JsonLineWriter expects a list of data.", level="warning")
            return False

        folder = os.path.dirname(destination)
        if folder:
            os.makedirs(folder, exist_ok=True)

        mode = kwargs.get("mode", "w")

        with open(destination, mode, encoding="utf-8") as f:
            for item in input_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        return True
