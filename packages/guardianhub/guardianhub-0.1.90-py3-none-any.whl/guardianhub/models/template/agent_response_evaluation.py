from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum
from ..registry.registry import register_model


class EvaluationMetric(str, Enum):
    """Standard evaluation metrics."""
    RELEVANCE = "relevance"
    GROUNDEDNESS = "groundedness"
    COHERENCE = "coherence"
    FLUENCY = "fluency"
    COMPLETENESS = "completeness"
    CORRECTNESS = "correctness"
    SAFETY = "safety"


# New model for structured LLM output
@register_model
class EvaluationScoresModel(BaseModel):
    """Pydantic model for the structured JSON output expected from the LLM."""
    relevance: float = Field(..., ge=0.0, le=1.0,
                             description="Score for how well the response addresses the query (0.0 to 1.0).")
    groundedness: float = Field(..., ge=0.0, le=1.0,
                                description="Score for whether the response is supported by the context (0.0 to 1.0).")
    coherence: float = Field(..., ge=0.0, le=1.0,
                             description="Score for the logical flow and consistency of the response (0.0 to 1.0).")
    fluency: float = Field(..., ge=0.0, le=1.0,
                           description="Score for the readability and grammatical correctness (0.0 to 1.0).")
    completeness: float = Field(..., ge=0.0, le=1.0,
                                description="Score for whether the response fully answers all parts of the query (0.0 to 1.0).")

    # Optional fields for other potential metrics, if the LLM supports them
    # correctness: Optional[float] = Field(None, ge=0.0, le=1.0, description="Factual accuracy score.")
    # safety: Optional[float] = Field(None, ge=0.0, le=1.0, description="Safety compliance score.")

class EvaluationErrorLevel(str, Enum):
    """Severity levels for evaluation errors."""
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@register_model
class EvaluationResult(BaseModel):
    """Container for evaluation results and metrics."""
    scores: Dict[EvaluationMetric, float] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    error_level: Optional[EvaluationErrorLevel] = None

    @property
    def overall_score(self) -> float:
        """Calculate an overall score from individual metrics."""
        if not self.scores:
            return 0.0
        return sum(self.scores.values()) / len(self.scores)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "scores": {k.value: v for k, v in self.scores.items()},
            "overall_score": self.overall_score,
            "metadata": self.metadata,
            "error": self.error,
            "error_level": self.error_level.value if self.error_level else None
        }