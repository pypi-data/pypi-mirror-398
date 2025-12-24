"""
Context managers for test steps and nested operations.

Usage:
    with step("Login to application"):
        # test code
        pass
    
    with step("Verify dashboard") as s:
        s.attach_screenshot("dashboard.png")
"""

import time
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Generator, List, Optional, TYPE_CHECKING
from uuid import uuid4

from qagentic.core.status import Status

if TYPE_CHECKING:
    from qagentic.core.test_result import StepResult


# Thread-local storage for current step context
import threading
_step_context = threading.local()


def _get_current_steps() -> List["Step"]:
    """Get the current step stack."""
    if not hasattr(_step_context, "steps"):
        _step_context.steps = []
    return _step_context.steps


def _get_current_step() -> Optional["Step"]:
    """Get the current active step."""
    steps = _get_current_steps()
    return steps[-1] if steps else None


@dataclass
class Step:
    """
    Represents a test step with timing and status tracking.
    
    Can be used as a context manager or decorator.
    """
    
    name: str
    description: Optional[str] = None
    status: Status = Status.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: float = 0
    error: Optional[str] = None
    error_trace: Optional[str] = None
    attachments: List[dict] = field(default_factory=list)
    children: List["Step"] = field(default_factory=list)
    parameters: dict = field(default_factory=dict)
    _id: str = field(default_factory=lambda: str(uuid4()))
    
    def __enter__(self) -> "Step":
        """Enter the step context."""
        self.start_time = datetime.now(timezone.utc)
        self.status = Status.RUNNING
        _get_current_steps().append(self)
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Exit the step context."""
        self.end_time = datetime.now(timezone.utc)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        
        steps = _get_current_steps()
        if steps and steps[-1] is self:
            steps.pop()
        
        # Add this step to parent if exists
        parent = _get_current_step()
        if parent:
            parent.children.append(self)
        
        if exc_type is not None:
            self.status = Status.FAILED
            self.error = str(exc_val)
            self.error_trace = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
            return False  # Re-raise the exception
        
        self.status = Status.PASSED
        return False
    
    def attach(
        self,
        data: Any,
        name: str,
        attachment_type: str = "text/plain",
    ) -> "Step":
        """
        Attach data to this step.
        
        Args:
            data: Data to attach (bytes, string, or path)
            name: Attachment name
            attachment_type: MIME type
        
        Returns:
            Self for chaining
        """
        self.attachments.append({
            "name": name,
            "type": attachment_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return self
    
    def attach_screenshot(self, path: str, name: str = "Screenshot") -> "Step":
        """Attach a screenshot to this step."""
        return self.attach(path, name, "image/png")
    
    def attach_json(self, data: dict, name: str = "JSON Data") -> "Step":
        """Attach JSON data to this step."""
        import json
        return self.attach(json.dumps(data, indent=2), name, "application/json")
    
    def attach_text(self, text: str, name: str = "Text") -> "Step":
        """Attach text to this step."""
        return self.attach(text, name, "text/plain")
    
    def set_parameter(self, name: str, value: Any) -> "Step":
        """Set a step parameter."""
        self.parameters[name] = value
        return self
    
    def to_dict(self) -> dict:
        """Convert step to dictionary."""
        return {
            "id": self._id,
            "name": self.name,
            "description": self.description,
            "status": str(self.status),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "error_trace": self.error_trace,
            "attachments": self.attachments,
            "children": [child.to_dict() for child in self.children],
            "parameters": self.parameters,
        }


@contextmanager
def step(
    name: str,
    description: Optional[str] = None,
    **parameters: Any,
) -> Generator[Step, None, None]:
    """
    Context manager for defining test steps.
    
    Args:
        name: Step name
        description: Optional step description
        **parameters: Step parameters to log
    
    Yields:
        Step instance
    
    Example:
        with step("Login to application") as s:
            s.attach_screenshot("login.png")
            # test code
        
        with step("Enter credentials", username="test@example.com"):
            # test code
    """
    s = Step(name=name, description=description, parameters=parameters)
    with s:
        yield s


def step_decorator(
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Callable:
    """
    Decorator version of step.
    
    Args:
        name: Step name (defaults to function name)
        description: Optional step description
    
    Example:
        @step_decorator("Login step")
        def login(username, password):
            # login code
            pass
    """
    def decorator(func: Callable) -> Callable:
        import functools
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            step_name = name or func.__name__
            with step(step_name, description):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


class StepCollector:
    """Collects steps for a test run."""
    
    def __init__(self) -> None:
        self.steps: List[Step] = []
        self._root_steps: List[Step] = []
    
    def add_step(self, s: Step) -> None:
        """Add a step to the collector."""
        self.steps.append(s)
        if not _get_current_step():
            self._root_steps.append(s)
    
    def get_root_steps(self) -> List[Step]:
        """Get top-level steps."""
        return self._root_steps
    
    def clear(self) -> None:
        """Clear all collected steps."""
        self.steps.clear()
        self._root_steps.clear()
