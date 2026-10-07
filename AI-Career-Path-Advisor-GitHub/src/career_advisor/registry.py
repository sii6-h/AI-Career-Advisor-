from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
from .exceptions import ToolExecutionError

@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable[..., Any]

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        function: Callable[..., Any],
    ):
        self._tools[name] = Tool(
            name=name,
            description=description,
            parameters=parameters,
            function=function,
        )

    def schemas(self, allowed_tools: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        names = allowed_tools or list(self._tools.keys())
        return [
            {
                "type": "function",
                "function": {
                    "name": self._tools[name].name,
                    "description": self._tools[name].description,
                    "parameters": self._tools[name].parameters,
                },
            }
            for name in names
            if name in self._tools
        ]

    def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        if name not in self._tools:
            raise ToolExecutionError(f"Unknown tool: {name}")

        try:
            return self._tools[name].function(**arguments)
        except Exception as exc:
            raise ToolExecutionError(f"Tool '{name}' failed: {exc}") from exc

registry = ToolRegistry()
