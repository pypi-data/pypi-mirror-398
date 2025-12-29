from __future__ import annotations

from typing import Any

class WorkflowResult:
    def __init__(
        self,
        result: Any | None,
        is_end: bool,
        is_error: bool,
    ) -> None:
        # when is_end is True, result is from the output port of the workflow
        self.result = result
        self.is_end = is_end
        self.is_error = is_error