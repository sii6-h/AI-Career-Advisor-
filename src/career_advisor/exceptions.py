class AgentError(Exception):
    pass

class ToolExecutionError(AgentError):
    pass

class MaxStepsError(AgentError):
    pass

class LoopDetectedError(AgentError):
    pass
