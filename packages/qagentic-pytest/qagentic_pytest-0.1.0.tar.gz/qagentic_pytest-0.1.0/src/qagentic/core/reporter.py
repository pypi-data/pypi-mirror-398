"""
Reporter classes for outputting test results to various destinations.
"""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import threading

from qagentic.core.config import get_config, QAgenticConfig
from qagentic.core.test_result import TestResult, TestRunResult
from qagentic.core.status import Status

if TYPE_CHECKING:
    pass


class BaseReporter(ABC):
    """Base class for all reporters."""
    
    @abstractmethod
    def start_run(self, run: TestRunResult) -> None:
        """Called when a test run starts."""
        pass
    
    @abstractmethod
    def end_run(self, run: TestRunResult) -> None:
        """Called when a test run ends."""
        pass
    
    @abstractmethod
    def report_test(self, test: TestResult) -> None:
        """Report a single test result."""
        pass


class ConsoleReporter(BaseReporter):
    """Rich console output reporter."""
    
    def __init__(self, config: Optional[QAgenticConfig] = None) -> None:
        self.config = config or get_config()
        self._use_rich = self.config.features.rich_console
        
        if self._use_rich:
            try:
                from rich.console import Console
                from rich.table import Table
                from rich.panel import Panel
                self._console = Console()
                self._rich_available = True
            except ImportError:
                self._rich_available = False
                self._use_rich = False
        else:
            self._rich_available = False
    
    def start_run(self, run: TestRunResult) -> None:
        """Print run start banner."""
        if self._use_rich and self._rich_available:
            from rich.panel import Panel
            self._console.print(Panel(
                f"[bold blue]QAagentic Test Run[/bold blue]\n"
                f"Project: {run.project_name}\n"
                f"Environment: {run.environment}",
                title="🚀 Starting Tests",
                border_style="blue",
            ))
        else:
            print(f"\n{'='*60}")
            print(f"QAagentic Test Run - {run.project_name}")
            print(f"Environment: {run.environment}")
            print(f"{'='*60}\n")
    
    def end_run(self, run: TestRunResult) -> None:
        """Print run summary."""
        if self._use_rich and self._rich_available:
            from rich.table import Table
            from rich.panel import Panel
            
            table = Table(show_header=True, header_style="bold")
            table.add_column("Status", style="bold")
            table.add_column("Count", justify="right")
            
            table.add_row("[green]Passed[/green]", str(run.passed))
            table.add_row("[red]Failed[/red]", str(run.failed))
            table.add_row("[yellow]Broken[/yellow]", str(run.broken))
            table.add_row("[blue]Skipped[/blue]", str(run.skipped))
            table.add_row("[bold]Total[/bold]", str(run.total))
            
            status_color = "green" if run.is_successful else "red"
            status_icon = "✅" if run.is_successful else "❌"
            
            self._console.print(Panel(
                table,
                title=f"{status_icon} Test Run Complete - {run.pass_rate:.1f}% Pass Rate",
                border_style=status_color,
            ))
        else:
            print(f"\n{'='*60}")
            print(f"Test Run Complete - {run.pass_rate:.1f}% Pass Rate")
            print(f"Passed: {run.passed} | Failed: {run.failed} | Skipped: {run.skipped}")
            print(f"{'='*60}\n")
    
    def report_test(self, test: TestResult) -> None:
        """Print test result."""
        if not self.config.features.console_output:
            return
        
        status_symbols = {
            Status.PASSED: ("✓", "green"),
            Status.FAILED: ("✗", "red"),
            Status.BROKEN: ("!", "yellow"),
            Status.SKIPPED: ("○", "blue"),
        }
        
        symbol, color = status_symbols.get(test.status, ("?", "white"))
        
        if self._use_rich and self._rich_available:
            self._console.print(f"  [{color}]{symbol}[/{color}] {test.name}")
            if test.error_message:
                self._console.print(f"    [dim red]{test.error_message[:100]}...[/dim red]")
        else:
            print(f"  {symbol} {test.name}")
            if test.error_message:
                print(f"    Error: {test.error_message[:100]}...")


class JSONReporter(BaseReporter):
    """JSON file reporter."""
    
    def __init__(self, config: Optional[QAgenticConfig] = None) -> None:
        self.config = config or get_config()
        self.output_dir = Path(self.config.local.output_dir)
        self._tests: List[dict] = []
        self._run: Optional[TestRunResult] = None
    
    def start_run(self, run: TestRunResult) -> None:
        """Initialize for new run."""
        self._run = run
        self._tests = []
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean previous results if configured
        if self.config.local.clean_on_start:
            for f in self.output_dir.glob("*.json"):
                f.unlink()
    
    def end_run(self, run: TestRunResult) -> None:
        """Write final JSON report."""
        if not self.config.local.enabled or "json" not in self.config.local.formats:
            return
        
        # Write run summary
        run_file = self.output_dir / "run.json"
        with open(run_file, "w") as f:
            json.dump(run.to_dict(), f, indent=2, default=str)
        
        # Write individual test results
        tests_dir = self.output_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        for test in run.tests:
            test_file = tests_dir / f"{test.id}.json"
            with open(test_file, "w") as f:
                json.dump(test.to_dict(), f, indent=2, default=str)
    
    def report_test(self, test: TestResult) -> None:
        """Add test to collection."""
        self._tests.append(test.to_dict())


class JUnitReporter(BaseReporter):
    """JUnit XML reporter for CI/CD compatibility."""
    
    def __init__(self, config: Optional[QAgenticConfig] = None) -> None:
        self.config = config or get_config()
        self.output_dir = Path(self.config.local.output_dir)
        self._run: Optional[TestRunResult] = None
    
    def start_run(self, run: TestRunResult) -> None:
        """Initialize for new run."""
        self._run = run
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def end_run(self, run: TestRunResult) -> None:
        """Write JUnit XML report."""
        if not self.config.local.enabled or "junit" not in self.config.local.formats:
            return
        
        import xml.etree.ElementTree as ET
        
        # Create testsuite element
        testsuite = ET.Element("testsuite")
        testsuite.set("name", run.project_name)
        testsuite.set("tests", str(run.total))
        testsuite.set("failures", str(run.failed))
        testsuite.set("errors", str(run.broken))
        testsuite.set("skipped", str(run.skipped))
        testsuite.set("time", str(run.duration_ms / 1000))
        testsuite.set("timestamp", run.start_time.isoformat() if run.start_time else "")
        
        for test in run.tests:
            testcase = ET.SubElement(testsuite, "testcase")
            testcase.set("name", test.name)
            testcase.set("classname", test.class_name or test.module or "")
            testcase.set("time", str(test.duration_ms / 1000))
            
            if test.status == Status.FAILED:
                failure = ET.SubElement(testcase, "failure")
                failure.set("message", test.error_message or "Test failed")
                failure.set("type", test.error_type or "AssertionError")
                if test.stack_trace:
                    failure.text = test.stack_trace
            
            elif test.status == Status.BROKEN:
                error = ET.SubElement(testcase, "error")
                error.set("message", test.error_message or "Test error")
                error.set("type", test.error_type or "Error")
                if test.stack_trace:
                    error.text = test.stack_trace
            
            elif test.status == Status.SKIPPED:
                skipped = ET.SubElement(testcase, "skipped")
                if test.error_message:
                    skipped.set("message", test.error_message)
        
        # Write to file
        tree = ET.ElementTree(testsuite)
        junit_file = self.output_dir / "junit.xml"
        tree.write(junit_file, encoding="unicode", xml_declaration=True)
    
    def report_test(self, test: TestResult) -> None:
        """No-op for JUnit - all written at end."""
        pass


class APIReporter(BaseReporter):
    """Reporter that sends results to QAagentic API."""
    
    def __init__(self, config: Optional[QAgenticConfig] = None) -> None:
        self.config = config or get_config()
        self._client: Optional[Any] = None
        self._run: Optional[TestRunResult] = None
        self._batch: List[TestResult] = []
    
    def _get_client(self) -> Any:
        """Get or create HTTP client."""
        if self._client is None:
            import httpx
            self._client = httpx.Client(
                base_url=self.config.api.url,
                timeout=self.config.api.timeout,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": self.config.api.key or "",
                    "X-Project": self.config.project_name,
                },
            )
        return self._client
    
    def start_run(self, run: TestRunResult) -> None:
        """Register run with API."""
        if not self.config.api.enabled:
            return
        
        self._run = run
        self._batch = []
        
        try:
            client = self._get_client()
            response = client.post("/api/v1/runs", json={
                "id": run.id,
                "name": run.name,
                "project_name": run.project_name,
                "environment": run.environment,
                "start_time": run.start_time.isoformat() if run.start_time else None,
                "labels": run.labels,
                "ci_build_id": run.ci_build_id,
                "branch": run.branch,
                "commit_hash": run.commit_hash,
            })
            response.raise_for_status()
        except Exception as e:
            # Log but don't fail tests
            print(f"Warning: Failed to register run with API: {e}")
    
    def end_run(self, run: TestRunResult) -> None:
        """Finalize run with API."""
        if not self.config.api.enabled:
            return
        
        # Flush any remaining batch
        self._flush_batch()
        
        try:
            client = self._get_client()
            response = client.patch(f"/api/v1/runs/{run.id}", json={
                "end_time": run.end_time.isoformat() if run.end_time else None,
                "duration_ms": run.duration_ms,
                "total": run.total,
                "passed": run.passed,
                "failed": run.failed,
                "broken": run.broken,
                "skipped": run.skipped,
                "status": "completed",
            })
            response.raise_for_status()
        except Exception as e:
            print(f"Warning: Failed to finalize run with API: {e}")
        finally:
            if self._client:
                self._client.close()
                self._client = None
    
    def report_test(self, test: TestResult) -> None:
        """Add test to batch and flush if needed."""
        if not self.config.api.enabled:
            return
        
        self._batch.append(test)
        
        if len(self._batch) >= self.config.api.batch_size:
            self._flush_batch()
    
    def _flush_batch(self) -> None:
        """Send batch of tests to API."""
        if not self._batch or not self._run:
            return
        
        try:
            client = self._get_client()
            response = client.post(
                f"/api/v1/runs/{self._run.id}/results",
                json=[t.to_dict() for t in self._batch],
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Warning: Failed to send test results to API: {e}")
        finally:
            self._batch = []


class QAgenticReporter:
    """
    Main reporter that coordinates multiple output destinations.
    
    This is the primary interface for reporting test results.
    """
    
    _instance: Optional["QAgenticReporter"] = None
    _lock = threading.Lock()
    
    def __init__(self, config: Optional[QAgenticConfig] = None) -> None:
        self.config = config or get_config()
        self._reporters: List[BaseReporter] = []
        self._current_run: Optional[TestRunResult] = None
        
        # Initialize reporters based on config
        if self.config.features.console_output:
            self._reporters.append(ConsoleReporter(self.config))
        
        if self.config.local.enabled:
            self._reporters.append(JSONReporter(self.config))
            if "junit" in self.config.local.formats:
                self._reporters.append(JUnitReporter(self.config))
        
        if self.config.api.enabled:
            self._reporters.append(APIReporter(self.config))
    
    @classmethod
    def get_instance(cls, config: Optional[QAgenticConfig] = None) -> "QAgenticReporter":
        """Get singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(config)
            return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset singleton instance."""
        with cls._lock:
            cls._instance = None
    
    def start_run(
        self,
        name: Optional[str] = None,
        project_name: Optional[str] = None,
        environment: Optional[str] = None,
        **kwargs: Any,
    ) -> TestRunResult:
        """Start a new test run."""
        self._current_run = TestRunResult(
            name=name or f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            project_name=project_name or self.config.project_name,
            environment=environment or self.config.environment,
            start_time=datetime.now(timezone.utc),
            labels=self.config.labels.custom.copy(),
            **kwargs,
        )
        
        for reporter in self._reporters:
            reporter.start_run(self._current_run)
        
        return self._current_run
    
    def end_run(self) -> Optional[TestRunResult]:
        """End the current test run."""
        if not self._current_run:
            return None
        
        self._current_run.end_time = datetime.now(timezone.utc)
        self._current_run.duration_ms = (
            self._current_run.end_time - self._current_run.start_time
        ).total_seconds() * 1000
        
        for reporter in self._reporters:
            reporter.end_run(self._current_run)
        
        run = self._current_run
        self._current_run = None
        return run
    
    def report_test(self, test: TestResult) -> None:
        """Report a test result."""
        if self._current_run:
            self._current_run.add_test(test)
        
        for reporter in self._reporters:
            reporter.report_test(test)
    
    @property
    def current_run(self) -> Optional[TestRunResult]:
        """Get the current test run."""
        return self._current_run


def get_reporter(config: Optional[QAgenticConfig] = None) -> QAgenticReporter:
    """Get the global reporter instance."""
    return QAgenticReporter.get_instance(config)
