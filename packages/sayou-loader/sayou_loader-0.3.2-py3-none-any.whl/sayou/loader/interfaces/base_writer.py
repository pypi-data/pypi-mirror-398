from abc import abstractmethod
from typing import Any

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time, retry

from ..core.exceptions import WriterError


class BaseWriter(BaseComponent):
    """
    (Tier 1) Abstract base class for data writers (Loaders).

    Implements the Template Method pattern with built-in retries and logging.
    """

    component_name = "BaseWriter"
    SUPPORTED_TYPES = []

    @classmethod
    def can_handle(
        cls, input_data: Any, destination: str, strategy: str = "auto"
    ) -> float:
        """
        Determines eligibility based on destination format (ext) or connection string.
        """
        return 0.0

    def initialize(self, **kwargs):
        """
        Optional hook for writer initialization (e.g., auth setup).
        """
        pass

    @measure_time
    @retry(max_retries=3, delay=1.0)
    def write(self, input_data: Any, destination: str, **kwargs) -> bool:
        """
        [Template Method] Execute the write operation.

        Args:
            input_data (Any): The payload to write (from Assembler).
            destination (str): Target location (File path, DB connection string, Table name).
            **kwargs: Additional options (mode, encoding, etc.).

        Returns:
            bool: True if successful.

        Raises:
            WriterError: If writing fails after retries.
        """
        self._emit("on_start", input_data={"destination": destination})
        self._log(f"Writing to '{destination}' (Type: {type(input_data).__name__})")

        if not input_data:
            self._log("Data is empty. Skipping write.", level="warning")
            return False

        try:
            result = self._do_write(input_data, destination, **kwargs)
            self._emit("on_finish", result_data={"success": result}, success=result)
            if result:
                self._log("Write completed successfully.")
            else:
                self._log("Write completed but returned False.", level="warning")
            return result

        except Exception as e:
            self._emit("on_error", error=e)
            self.logger.error(f"Write failed: {e}", exc_info=True)
            raise WriterError(f"[{self.component_name}] Failed: {str(e)}")

    @abstractmethod
    def _do_write(self, input_data: Any, destination: str, **kwargs) -> bool:
        """
        [Abstract Hook] Implement the actual I/O logic.
        """
        raise NotImplementedError
