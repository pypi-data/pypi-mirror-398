"""Type definitions and models for the Arato API."""
from typing import List, Dict, Any, Optional, Union, Literal
from typing_extensions import TypedDict


# Generic types
Tags = List[str]
APIKeys = Dict[str, str]

# Prompt Config
class PromptMessage(TypedDict):
    """Represents a message in a prompt conversation."""
    role: Literal["user", "system", "assistant"]
    content: str

class PromptConfig(TypedDict):
    """Configuration for prompt templates."""
    model_id: str
    vendor_id: str
    prompt_template: Union[str, List[PromptMessage]]
    model_parameters: Optional[Dict[str, Any]]

# Evals
class NumericRange(TypedDict, total=False):
    """Defines a numeric range for evaluation scoring."""
    range_id: str
    min_score: float
    max_score: float
    is_pass: bool

class ClassificationClass(TypedDict, total=False):
    """Defines a classification class for evaluation."""
    id: str
    title: str
    is_pass: bool
    color: Optional[str]
