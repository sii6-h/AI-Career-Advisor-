import json
import time
from typing import Any, Dict, List, Optional
from .config import CONFIG
from .client import create_client
from .exceptions import AgentError, ToolExecutionError, MaxStepsError, LoopDetectedError
from .loop_detection import LoopDetector
from .observability import observer
from .registry import registry

client = None
def _client():
    global client
    if client is None: client = create_client()
    return client

class BaseAgent:
    def __init__(
        self,
        name: str,
        system_prompt: str,
        allowed_tools: Optional[List[str]] = None,
        max_steps: Optional[int] = None,
        max_tool_calls: int = 4,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.allowed_tools = allowed_tools or []
        self.max_steps = max_steps or CONFIG.max_agent_steps
        self.max_tool_calls = max_tool_calls

    def run(self, task: str) -> Dict[str, Any]:
        observer.metrics.agent_calls += 1
        observer.log("agent_start", self.name, task=task)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": task},
        ]

        detector = LoopDetector(CONFIG.max_repeated_actions)
        tool_schemas = registry.schemas(self.allowed_tools)

        tool_calls_used = 0
        budget_notice_added = False

        for step in range(1, self.max_steps + 1):
            observer.log(
                "agent_step",
                self.name,
                step=step,
                tool_calls_used=tool_calls_used,
            )

            try:
                tools_available = (
                    bool(tool_schemas)
                    and tool_calls_used < self.max_tool_calls
                )

                if (
                    tool_schemas
                    and not tools_available
                    and not budget_notice_added
                ):
                    messages.append(
                        {
                            "role": "system",
                            "content": (
                                "The tool-call budget is exhausted. "
                                "Do not request more tools. "
                                "Return the final answer using the "
                                "evidence already collected."
                            ),
                        }
                    )
                    budget_notice_added = True

                kwargs = {
                    "model": CONFIG.model,
                    "messages": messages,
                    "temperature": CONFIG.temperature,
                }

                if tools_available:
                    kwargs["tools"] = tool_schemas
                    kwargs["tool_choice"] = "auto"

                response = None

                # Retry temporary API errors and rate limits.
                for attempt in range(5):
                    try:
                        response = _client().chat.completions.create(**kwargs)
                        break

                    except Exception as exc:
                        error_text = str(exc)

                        # Rate limit: wait for the next quota window.
                        if "429" in error_text and attempt < 4:
                            wait_seconds = 30

                            observer.log(
                                "rate_limit_retry",
                                self.name,
                                attempt=attempt + 1,
                                wait_seconds=wait_seconds,
                                error="429 Rate Limit",
                            )

                            print(
                                f"{self.name}: rate limit reached. "
                                f"Waiting {wait_seconds} seconds..."
                            )

                            time.sleep(wait_seconds)
                            continue

                        # Temporary Gemini service overload.
                        if "503" in error_text and attempt < 4:
                            wait_seconds = 10 * (attempt + 1)

                            observer.log(
                                "service_retry",
                                self.name,
                                attempt=attempt + 1,
                                wait_seconds=wait_seconds,
                                error="503 Service Unavailable",
                            )

                            print(
                                f"{self.name}: Gemini is busy. "
                                f"Retrying in {wait_seconds} seconds..."
                            )

                            time.sleep(wait_seconds)
                            continue

                        raise

                if response is None:
                    raise AgentError(
                        f"{self.name} did not receive an LLM response."
                    )

                observer.record_usage(response.usage)

                message = response.choices[0].message

                if not message.tool_calls:
                    answer = (message.content or "").strip()

                    if not answer:
                        raise AgentError(
                            f"{self.name} returned an empty final answer."
                        )

                    observer.log(
                        "agent_finish",
                        self.name,
                        step=step,
                        tool_calls_used=tool_calls_used,
                        answer_preview=answer[:300],
                    )

                    return {
                        "answer": answer,
                        "steps": step,
                        "tool_calls_used": tool_calls_used,
                        "status": "completed",
                    }

                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name

                    if tool_name not in self.allowed_tools:
                        raise ToolExecutionError(
                            f"{self.name} attempted to use "
                            f"unauthorized tool: {tool_name}"
                        )

                messages.append(message)

                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name

                    if tool_calls_used >= self.max_tool_calls:
                        observer.log(
                            "tool_budget_exhausted",
                            self.name,
                            tool=tool_name,
                            max_tool_calls=self.max_tool_calls,
                        )

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(
                                    {
                                        "status": "skipped",
                                        "reason": (
                                            "Tool-call budget exhausted. "
                                            "Use the evidence already collected "
                                            "and return the final answer."
                                        ),
                                    }
                                ),
                            }
                        )
                        continue

                    try:
                        arguments = json.loads(
                            tool_call.function.arguments or "{}"
                        )
                    except json.JSONDecodeError as exc:
                        raise ToolExecutionError(
                            f"Invalid tool arguments from "
                            f"{self.name}: {exc}"
                        )

                    detector.check(tool_name, arguments)

                    tool_calls_used += 1
                    observer.metrics.tool_calls += 1

                    observer.log(
                        "tool_start",
                        self.name,
                        tool=tool_name,
                        arguments=arguments,
                        tool_call_number=tool_calls_used,
                    )

                    started = time.time()

                    try:
                        result = registry.execute(
                            tool_name,
                            arguments,
                        )
                    except Exception as exc:
                        raise ToolExecutionError(
                            f"Tool '{tool_name}' failed for "
                            f"{self.name}: {exc}"
                        ) from exc

                    elapsed = time.time() - started

                    observer.log(
                        "tool_finish",
                        self.name,
                        tool=tool_name,
                        elapsed_seconds=round(elapsed, 3),
                        result_preview=str(result)[:500],
                    )

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(
                                result,
                                ensure_ascii=False,
                                default=str,
                            ),
                        }
                    )

            except (
                LoopDetectedError,
                ToolExecutionError,
                AgentError,
            ):
                observer.metrics.errors += 1
                raise

            except Exception as exc:
                observer.metrics.errors += 1

                observer.log(
                    "agent_error",
                    self.name,
                    step=step,
                    error=repr(exc),
                )

                raise AgentError(
                    f"{self.name} failed at step {step}: {exc}"
                ) from exc

        observer.metrics.errors += 1

        observer.log(
            "max_steps_reached",
            self.name,
            max_steps=self.max_steps,
            tool_calls_used=tool_calls_used,
        )

        raise MaxStepsError(
            f"{self.name} exceeded the maximum of "
            f"{self.max_steps} steps."
        )
