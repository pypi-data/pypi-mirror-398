"""
Test result models for storing and transmitting test execution data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from qagentic.core.status import Status
from qagentic.core.severity import Severity


@dataclass
class StepResult:
    """Result of a single test step."""
    
    name: str
    status: Status = Status.PASSED
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: float = 0
    error: Optional[str] = None
    error_trace: Optional[str] = None
    attachments: List[dict] = field(default_factory=list)
    children: List["StepResult"] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": str(self.status),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "error_trace": self.error_trace,
            "attachments": self.attachments,
            "children": [c.to_dict() for c in self.children],
            "parameters": self.parameters,
        }


@dataclass
class TestResult:
    """Complete result of a test execution."""
    
    # Identification
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    full_name: str = ""
    description: Optional[str] = None
    
    # Execution
    status: Status = Status.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: float = 0
    
    # Error information
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # Labels and metadata
    labels: Dict[str, Any] = field(default_factory=dict)
    links: List[dict] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Steps and attachments
    steps: List[StepResult] = field(default_factory=list)
    attachments: List[dict] = field(default_factory=list)
    
    # Location
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    module: Optional[str] = None
    class_name: Optional[str] = None
    
    # Retry information
    retry_count: int = 0
    is_retry: bool = False
    original_test_id: Optional[str] = None
    
    # Flaky detection
    is_flaky: bool = False
    flaky_reason: Optional[str] = None
    
    @property
    def severity(self) -> Severity:
        """Get test severity from labels."""
        sev = self.labels.get("severity", "normal")
        return Severity.from_string(sev) if isinstance(sev, str) else sev
    
    @property
    def feature(self) -> Optional[str]:
        """Get feature label."""
        return self.labels.get("feature")
    
    @property
    def story(self) -> Optional[str]:
        """Get story label."""
        return self.labels.get("story")
    
    @property
    def epic(self) -> Optional[str]:
        """Get epic label."""
        return self.labels.get("epic")
    
    @property
    def tags(self) -> List[str]:
        """Get test tags."""
        tags = self.labels.get("tags", [])
        return tags if isinstance(tags, list) else [tags]
    
    def add_step(self, step: StepResult) -> None:
        """Add a step to the test result."""
        self.steps.append(step)
    
    def add_attachment(self, attachment: dict) -> None:
        """Add an attachment to the test result."""
        self.attachments.append(attachment)
    
    def set_error(
        self,
        message: str,
        error_type: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> None:
        """Set error information."""
        self.error_message = message
        self.error_type = error_type
        self.stack_trace = stack_trace
        if self.status not in (Status.FAILED, Status.BROKEN):
            self.status = Status.FAILED
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "full_name": self.full_name,
            "description": self.description,
            "status": str(self.status),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "stack_trace": self.stack_trace,
            "labels": self.labels,
            "links": self.links,
            "parameters": self.parameters,
            "steps": [s.to_dict() for s in self.steps],
            "attachments": self.attachments,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "module": self.module,
            "class_name": self.class_name,
            "retry_count": self.retry_count,
            "is_retry": self.is_retry,
            "is_flaky": self.is_flaky,
            "flaky_reason": self.flaky_reason,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TestResult":
        """Create from dictionary."""
        result = cls(
            id=data.get("id", str(uuid4())),
            name=data.get("name", ""),
            full_name=data.get("full_name", ""),
            description=data.get("description"),
            status=Status(data.get("status", "unknown")),
            error_message=data.get("error_message"),
            error_type=data.get("error_type"),
            stack_trace=data.get("stack_trace"),
            labels=data.get("labels", {}),
            links=data.get("links", []),
            parameters=data.get("parameters", {}),
            attachments=data.get("attachments", []),
            file_path=data.get("file_path"),
            line_number=data.get("line_number"),
            module=data.get("module"),
            class_name=data.get("class_name"),
            retry_count=data.get("retry_count", 0),
            is_retry=data.get("is_retry", False),
            is_flaky=data.get("is_flaky", False),
            flaky_reason=data.get("flaky_reason"),
        )
        
        # Parse times
        if data.get("start_time"):
            result.start_time = datetime.fromisoformat(data["start_time"])
        if data.get("end_time"):
            result.end_time = datetime.fromisoformat(data["end_time"])
        
        result.duration_ms = data.get("duration_ms", 0)
        
        return result


@dataclass
class TestRunResult:
    """Result of a complete test run."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    project_name: str = ""
    environment: str = "local"
    
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: float = 0
    
    tests: List[TestResult] = field(default_factory=list)
    
    # Summary counts
    total: int = 0
    passed: int = 0
    failed: int = 0
    broken: int = 0
    skipped: int = 0
    
    # Metadata
    labels: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # CI/CD information
    ci_build_id: Optional[str] = None
    ci_build_url: Optional[str] = None
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    
    def add_test(self, test: TestResult) -> None:
        """Add a test result and update counts."""
        self.tests.append(test)
        self.total += 1
        
        if test.status == Status.PASSED:
            self.passed += 1
        elif test.status == Status.FAILED:
            self.failed += 1
        elif test.status == Status.BROKEN:
            self.broken += 1
        elif test.status == Status.SKIPPED:
            self.skipped += 1
    
    @property
    def pass_rate(self) -> float:
        """Calculate pass rate percentage."""
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100
    
    @property
    def is_successful(self) -> bool:
        """Check if the run was successful (no failures)."""
        return self.failed == 0 and self.broken == 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "project_name": self.project_name,
            "environment": self.environment,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "broken": self.broken,
            "skipped": self.skipped,
            "pass_rate": self.pass_rate,
            "labels": self.labels,
            "parameters": self.parameters,
            "ci_build_id": self.ci_build_id,
            "ci_build_url": self.ci_build_url,
            "branch": self.branch,
            "commit_hash": self.commit_hash,
            "tests": [t.to_dict() for t in self.tests],
        }
