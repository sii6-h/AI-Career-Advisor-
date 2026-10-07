import hashlib
import json
from typing import Any, Dict, Optional
from .exceptions import LoopDetectedError

class LoopDetector:
    def __init__(
        self,
        max_repeats: int = 2,
        max_stagnant_steps: int = 3,
    ):
        self.max_repeats = max_repeats
        self.max_stagnant_steps = max_stagnant_steps
        self.history: Dict[str, int] = {}
        self.last_tool_name: Optional[str] = None
        self.stagnant_steps = 0

    def _signature(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> str:
        normalized = json.dumps(
            {
                "tool": tool_name,
                "arguments": arguments,
            },
            sort_keys=True,
            ensure_ascii=True,
        )

        return hashlib.sha256(
            normalized.encode()
        ).hexdigest()

    def check(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ):
        signature = self._signature(
            tool_name,
            arguments,
        )

        self.history[signature] = (
            self.history.get(signature, 0) + 1
        )

        # Detect exact repetition
        if self.history[signature] > self.max_repeats:
            raise LoopDetectedError(
                f"Repeated action detected: "
                f"{tool_name} with identical arguments."
            )

        # Detect stagnation
        if tool_name == self.last_tool_name:
            self.stagnant_steps += 1
        else:
            self.stagnant_steps = 1
            self.last_tool_name = tool_name

        if self.stagnant_steps > self.max_stagnant_steps:
            raise LoopDetectedError(
                f"Stagnation detected: {tool_name} "
                f"was used repeatedly without changing strategy."
            )
