"""Test status definitions."""

from enum import Enum


class Status(str, Enum):
    """Test execution status."""
    
    PASSED = "passed"
    FAILED = "failed"
    BROKEN = "broken"
    SKIPPED = "skipped"
    PENDING = "pending"
    RUNNING = "running"
    UNKNOWN = "unknown"
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def is_successful(self) -> bool:
        """Check if status represents a successful outcome."""
        return self == Status.PASSED
    
    @property
    def is_failure(self) -> bool:
        """Check if status represents a failure."""
        return self in (Status.FAILED, Status.BROKEN)
    
    @classmethod
    def from_pytest_outcome(cls, outcome: str) -> "Status":
        """Convert pytest outcome to Status."""
        mapping = {
            "passed": cls.PASSED,
            "failed": cls.FAILED,
            "skipped": cls.SKIPPED,
            "error": cls.BROKEN,
            "xfailed": cls.PASSED,  # Expected failure
            "xpassed": cls.FAILED,  # Unexpected pass
        }
        return mapping.get(outcome.lower(), cls.UNKNOWN)
