import time
from dataclasses import dataclass, field
from typing import Any, Dict, List
from .config import CONFIG

@dataclass
class TraceEvent:
    timestamp: float
    event_type: str
    agent: str
    details: Dict[str, Any]

@dataclass
class RunMetrics:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    tool_calls: int = 0
    agent_calls: int = 0
    errors: int = 0
    started_at: float = field(default_factory=time.time)

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.started_at

class Observer:
    def __init__(self):
        self.events: List[TraceEvent] = []
        self.metrics = RunMetrics()

    def log(self, event_type: str, agent: str, **details):
        self.events.append(
            TraceEvent(
                timestamp=time.time(),
                event_type=event_type,
                agent=agent,
                details=details,
            )
        )

    def record_usage(self, usage):
        if not usage:
            return
        prompt = getattr(usage, "prompt_tokens", 0) or 0
        completion = getattr(usage, "completion_tokens", 0) or 0
        total = getattr(usage, "total_tokens", prompt + completion) or 0

        self.metrics.prompt_tokens += prompt
        self.metrics.completion_tokens += completion
        self.metrics.total_tokens += total
        self.metrics.estimated_cost += (
            prompt / 1_000_000 * CONFIG.input_cost_per_million
            + completion / 1_000_000 * CONFIG.output_cost_per_million
        )

    def summary(self) -> Dict[str, Any]:
        return {
            "agent_calls": self.metrics.agent_calls,
            "tool_calls": self.metrics.tool_calls,
            "prompt_tokens": self.metrics.prompt_tokens,
            "completion_tokens": self.metrics.completion_tokens,
            "total_tokens": self.metrics.total_tokens,
            "estimated_cost_usd": round(self.metrics.estimated_cost, 6),
            "errors": self.metrics.errors,
            "elapsed_seconds": round(self.metrics.elapsed_seconds, 2),
        }



observer = Observer()
