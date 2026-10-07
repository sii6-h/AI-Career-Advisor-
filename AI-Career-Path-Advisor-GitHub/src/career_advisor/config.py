from dataclasses import dataclass

@dataclass
class AppConfig:
    model: str = "gemini-3.5-flash-lite"
    max_agent_steps: int = 8
    max_repeated_actions: int = 2
    temperature: float = 0.2
    max_search_results: int = 5
    input_cost_per_million: float = 0.30
    output_cost_per_million: float = 2.50

CONFIG = AppConfig()
