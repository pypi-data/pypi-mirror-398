from typing import Literal
from pydantic import BaseModel, Field
from pushikoo_interface import ProcesserConfig, ProcesserInstanceConfig


class Terminate(BaseModel):
    """
    Terminate action - stops processing and terminates the flow when the pattern matches.
    """

    type: Literal["terminate"] = "terminate"
    pass


class Replace(BaseModel):
    """
    Replace action - replaces the matched pattern with the specified string.
    """

    type: Literal["replace"] = "replace"

    replace: str = Field(
        ..., description="The string to replace the matched pattern with"
    )


class Rule(BaseModel):
    """
    A regex matching rule with an associated action.

    The `find` field contains a regex pattern to match against text content.
    The `process` field determines what happens when a match is found:
    - Terminate: stops processing and raises TerminateFlowException
    - Replace: replaces all matches with the specified replacement string
    """

    find: str = Field(..., description="Regex pattern to match")
    process: Terminate | Replace = Field(
        ..., description="Action to perform when pattern matches"
    )


class AdapterConfig(ProcesserConfig):
    """
    Adapter-level configuration (shared across all instances).
    Currently no adapter-level settings are required.
    """

    pass


class InstanceConfig(ProcesserInstanceConfig):
    """
    Instance-level configuration for the regex processer.

    Each instance can define its own set of regex rules.
    """

    rules: list[Rule] = Field(
        default_factory=list,
        description="List of regex rules to apply. Rules are processed in order.",
    )
