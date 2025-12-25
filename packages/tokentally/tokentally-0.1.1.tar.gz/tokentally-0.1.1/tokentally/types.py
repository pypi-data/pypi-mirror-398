"""Type definitions for TokenTally SDK."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class UsageData:
    """Data for tracking AI API usage."""

    tokens_in: int
    tokens_out: int
    model: str
    provider: str = "anthropic"
    runtime_ms: Optional[int] = None
    stop_reason: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data = {
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "model": self.model,
            "provider": self.provider,
            "metadata": self.metadata,
        }

        if self.runtime_ms is not None:
            data["runtime_ms"] = self.runtime_ms
        if self.stop_reason is not None:
            data["stop_reason"] = self.stop_reason
        if self.error_message is not None:
            data["error_message"] = self.error_message
        if self.timestamp is not None:
            data["timestamp"] = self.timestamp.isoformat()

        return data


@dataclass
class UsageResponse:
    """Response from recording usage."""

    success: bool
    record_id: str
    cost_usd: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UsageResponse":
        """Create from API response dictionary."""
        return cls(
            success=data.get("success", False),
            record_id=data.get("record_id", ""),
            cost_usd=data.get("cost_usd", 0.0),
        )
