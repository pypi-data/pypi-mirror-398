from typing import Dict, Any, NewType

Context = Dict[str, Any]

StepType = NewType("StepType", str)
STEP_ALL = StepType("all")
