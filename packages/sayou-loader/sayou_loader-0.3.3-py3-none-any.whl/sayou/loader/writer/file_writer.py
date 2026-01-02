import json
import os
import pickle
from typing import Any

from sayou.core.registry import register_component

from ..interfaces.base_writer import BaseWriter


@register_component("writer")
class FileWriter(BaseWriter):
    """
    Writes data to the local file system.

    Automatically handles format serialization:
    - Dict/List -> JSON
    - Str -> Text file
    - Bytes -> Binary file
    - Others -> Pickle
    """

    component_name = "FileWriter"
    SUPPORTED_TYPES = ["file", "local", "json", "pickle"]

    @classmethod
    def can_handle(
        cls, input_data: Any, destination: str, strategy: str = "auto"
    ) -> float:
        if strategy in cls.SUPPORTED_TYPES:
            return 1.0

        if not destination:
            return 0.0

        if "://" not in destination:
            if destination.endswith(".jsonl"):
                return 0.5
            return 0.9

        if destination.startswith("file://"):
            return 1.0

        return 0.0

    def _do_write(self, input_data: Any, destination: str, **kwargs) -> bool:
        """
        Write data to file. Creates parent directories if they don't exist.
        """
        # 1. Handle Directory Destination
        if destination.endswith(os.sep) or (
            os.path.exists(destination) and os.path.isdir(destination)
        ):
            destination = os.path.join(destination, "output.json")
            self._log(f"Destination is a directory. Appended filename: {destination}")

        # 2. Create Parent Directory
        folder = os.path.dirname(destination)
        if folder:
            os.makedirs(folder, exist_ok=True)

        mode = kwargs.get("mode", "w")
        encoding = kwargs.get("encoding", "utf-8")

        # 3. Determine Content & Mode
        if isinstance(input_data, (dict, list)):
            content = json.dumps(input_data, indent=2, ensure_ascii=False)
        elif isinstance(input_data, str):
            content = input_data
        elif isinstance(input_data, bytes):
            content = input_data
            mode = "wb"
            encoding = None
        else:
            # Fallback: Pickle
            if not destination.endswith(".pkl"):
                destination += ".pkl"

            with open(destination, "wb") as f:
                pickle.dump(input_data, f)
            return True

        # 4. Write File
        with open(destination, mode, encoding=encoding) as f:
            f.write(content)

        return True
