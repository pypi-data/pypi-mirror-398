"""Severity levels for test cases."""

from enum import Enum


class Severity(str, Enum):
    """Test severity levels - compatible with Allure."""
    
    BLOCKER = "blocker"
    CRITICAL = "critical"
    NORMAL = "normal"
    MINOR = "minor"
    TRIVIAL = "trivial"
    
    def __str__(self) -> str:
        return self.value
    
    @classmethod
    def from_string(cls, value: str) -> "Severity":
        """Convert string to Severity enum."""
        value_lower = value.lower()
        for severity in cls:
            if severity.value == value_lower:
                return severity
        return cls.NORMAL
