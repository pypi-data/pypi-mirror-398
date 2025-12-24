"""
QAagentic pytest plugin - Automatic test reporting with AI-powered insights.

This plugin automatically hooks into pytest to collect test results,
capture failures, and report to QAagentic for analysis.

Usage:
    # Just install the package - plugin auto-registers
    pip install qagentic-pytest
    
    # Run tests with QAagentic reporting
    pytest --qagentic
    
    # Or configure in pytest.ini/pyproject.toml
    [tool.pytest.ini_options]
    addopts = "--qagentic"
"""

import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator
from uuid import uuid4

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.nodes import Item
from _pytest.reports import TestReport
from _pytest.runner import CallInfo
from _pytest.terminal import TerminalReporter

from qagentic.core.config import configure, get_config, QAgenticConfig
from qagentic.core.decorators import get_test_metadata, QAGENTIC_MARKER
from qagentic.core.reporter import QAgenticReporter, get_reporter
from qagentic.core.status import Status
from qagentic.core.test_result import TestResult, StepResult
from qagentic.core.context import _get_current_steps, Step
from qagentic.core.attachments import _get_attachments, _clear_attachments


def pytest_addoption(parser: Parser) -> None:
    """Add QAagentic command line options."""
    group = parser.getgroup("qagentic", "QAagentic AI-Powered Test Reporting")
    
    group.addoption(
        "--qagentic",
        action="store_true",
        default=False,
        help="Enable QAagentic test reporting",
    )
    
    group.addoption(
        "--qagentic-project",
        action="store",
        default=None,
        help="QAagentic project name",
    )
    
    group.addoption(
        "--qagentic-api-url",
        action="store",
        default=None,
        help="QAagentic API URL",
    )
    
    group.addoption(
        "--qagentic-api-key",
        action="store",
        default=None,
        help="QAagentic API key",
    )
    
    group.addoption(
        "--qagentic-output-dir",
        action="store",
        default=None,
        help="Output directory for local reports",
    )
    
    group.addoption(
        "--qagentic-no-console",
        action="store_true",
        default=False,
        help="Disable console output",
    )
    
    group.addoption(
        "--qagentic-no-api",
        action="store_true",
        default=False,
        help="Disable API reporting",
    )
    
    group.addoption(
        "--qagentic-no-local",
        action="store_true",
        default=False,
        help="Disable local file reporting",
    )


def pytest_configure(config: Config) -> None:
    """Configure QAagentic plugin."""
    # Register markers
    config.addinivalue_line(
        "markers", "qagentic: mark test for QAagentic reporting"
    )
    
    # Check if QAagentic is enabled
    if not config.getoption("--qagentic", default=False):
        # Check environment variable
        if not os.getenv("QAGENTIC_ENABLED", "").lower() == "true":
            return
    
    # Configure QAagentic
    qagentic_config = configure(
        project_name=config.getoption("--qagentic-project") or os.getenv("QAGENTIC_PROJECT_NAME"),
        api_url=config.getoption("--qagentic-api-url") or os.getenv("QAGENTIC_API_URL"),
        api_key=config.getoption("--qagentic-api-key") or os.getenv("QAGENTIC_API_KEY"),
        output_dir=config.getoption("--qagentic-output-dir") or os.getenv("QAGENTIC_OUTPUT_DIR"),
    )
    
    # Apply command line overrides
    if config.getoption("--qagentic-no-console", default=False):
        qagentic_config.features.console_output = False
    
    if config.getoption("--qagentic-no-api", default=False):
        qagentic_config.api.enabled = False
    
    if config.getoption("--qagentic-no-local", default=False):
        qagentic_config.local.enabled = False
    
    # Create and register the plugin
    plugin = QAgenticPytestPlugin(qagentic_config)
    config.pluginmanager.register(plugin, "qagentic_plugin")


class QAgenticPytestPlugin:
    """Main pytest plugin for QAagentic reporting."""
    
    def __init__(self, config: QAgenticConfig) -> None:
        self.config = config
        self.reporter = QAgenticReporter(config)
        self._test_results: Dict[str, TestResult] = {}
        self._current_test: Optional[TestResult] = None
    
    def pytest_sessionstart(self, session: pytest.Session) -> None:
        """Called when test session starts."""
        # Get CI/CD information from environment
        ci_info = self._get_ci_info()
        
        self.reporter.start_run(
            name=f"pytest_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            project_name=self.config.project_name,
            environment=self.config.environment,
            ci_build_id=ci_info.get("build_id"),
            ci_build_url=ci_info.get("build_url"),
            branch=ci_info.get("branch"),
            commit_hash=ci_info.get("commit"),
        )
    
    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        """Called when test session ends."""
        self.reporter.end_run()
    
    def pytest_runtest_setup(self, item: Item) -> None:
        """Called before each test setup."""
        # Clear attachments from previous test
        _clear_attachments()
        
        # Create test result
        test_result = self._create_test_result(item)
        test_result.start_time = datetime.now(timezone.utc)
        test_result.status = Status.RUNNING
        
        self._test_results[item.nodeid] = test_result
        self._current_test = test_result
    
    def pytest_runtest_makereport(self, item: Item, call: CallInfo) -> Generator[None, TestReport, None]:
        """Process test report for each phase (setup, call, teardown)."""
        report = yield
        
        if item.nodeid not in self._test_results:
            return
        
        test_result = self._test_results[item.nodeid]
        
        # Handle different phases
        if report.when == "setup":
            if report.failed:
                test_result.status = Status.BROKEN
                test_result.error_message = str(report.longrepr)
                test_result.error_type = "SetupError"
                if hasattr(report, "longreprtext"):
                    test_result.stack_trace = report.longreprtext
        
        elif report.when == "call":
            if report.passed:
                test_result.status = Status.PASSED
            elif report.failed:
                test_result.status = Status.FAILED
                self._extract_error_info(test_result, report)
            elif report.skipped:
                test_result.status = Status.SKIPPED
                if hasattr(report, "wasxfail"):
                    test_result.error_message = report.wasxfail
        
        elif report.when == "teardown":
            if report.failed and test_result.status == Status.PASSED:
                test_result.status = Status.BROKEN
                test_result.error_message = str(report.longrepr)
                test_result.error_type = "TeardownError"
    
    def pytest_runtest_teardown(self, item: Item) -> None:
        """Called after each test teardown."""
        if item.nodeid not in self._test_results:
            return
        
        test_result = self._test_results[item.nodeid]
        test_result.end_time = datetime.now(timezone.utc)
        
        if test_result.start_time:
            test_result.duration_ms = (
                test_result.end_time - test_result.start_time
            ).total_seconds() * 1000
        
        # Collect steps from context
        steps = _get_current_steps()
        for step in steps:
            test_result.steps.append(StepResult(
                name=step.name,
                status=step.status,
                start_time=step.start_time,
                end_time=step.end_time,
                duration_ms=step.duration_ms,
                error=step.error,
                error_trace=step.error_trace,
                attachments=step.attachments,
                parameters=step.parameters,
            ))
        
        # Collect test-level attachments
        test_result.attachments.extend(_get_attachments())
        
        # Report the test
        self.reporter.report_test(test_result)
        
        # Cleanup
        self._current_test = None
        _clear_attachments()
    
    def _create_test_result(self, item: Item) -> TestResult:
        """Create a TestResult from a pytest Item."""
        # Get test metadata from decorators
        metadata = get_test_metadata(item.obj) if hasattr(item, "obj") else {}
        labels = metadata.get("labels", {})
        links = metadata.get("links", [])
        
        # Extract location info
        file_path = str(item.fspath) if item.fspath else None
        line_number = item.reportinfo()[1] if hasattr(item, "reportinfo") else None
        
        # Get module and class names
        module = item.module.__name__ if hasattr(item, "module") else None
        class_name = item.cls.__name__ if hasattr(item, "cls") and item.cls else None
        
        # Get description from docstring
        description = item.obj.__doc__ if hasattr(item, "obj") and item.obj.__doc__ else None
        
        # Get parameters for parametrized tests
        parameters = {}
        if hasattr(item, "callspec"):
            parameters = dict(item.callspec.params)
        
        # Add pytest markers as labels
        for marker in item.iter_markers():
            if marker.name not in ("parametrize", "usefixtures"):
                if marker.args:
                    labels[marker.name] = marker.args[0] if len(marker.args) == 1 else list(marker.args)
                else:
                    labels[marker.name] = True
        
        return TestResult(
            id=str(uuid4()),
            name=item.name,
            full_name=item.nodeid,
            description=description,
            labels=labels,
            links=links,
            parameters=parameters,
            file_path=file_path,
            line_number=line_number,
            module=module,
            class_name=class_name,
        )
    
    def _extract_error_info(self, test_result: TestResult, report: TestReport) -> None:
        """Extract error information from a failed test report."""
        if hasattr(report, "longrepr"):
            longrepr = report.longrepr
            
            if hasattr(longrepr, "reprcrash"):
                crash = longrepr.reprcrash
                test_result.error_message = crash.message if hasattr(crash, "message") else str(crash)
                test_result.error_type = type(crash).__name__ if crash else "AssertionError"
            else:
                test_result.error_message = str(longrepr)
                test_result.error_type = "AssertionError"
            
            if hasattr(report, "longreprtext"):
                test_result.stack_trace = report.longreprtext
            elif hasattr(longrepr, "reprtraceback"):
                test_result.stack_trace = str(longrepr.reprtraceback)
    
    def _get_ci_info(self) -> Dict[str, Optional[str]]:
        """Extract CI/CD information from environment."""
        # GitHub Actions
        if os.getenv("GITHUB_ACTIONS"):
            return {
                "build_id": os.getenv("GITHUB_RUN_ID"),
                "build_url": f"{os.getenv('GITHUB_SERVER_URL')}/{os.getenv('GITHUB_REPOSITORY')}/actions/runs/{os.getenv('GITHUB_RUN_ID')}",
                "branch": os.getenv("GITHUB_REF_NAME"),
                "commit": os.getenv("GITHUB_SHA"),
            }
        
        # GitLab CI
        if os.getenv("GITLAB_CI"):
            return {
                "build_id": os.getenv("CI_PIPELINE_ID"),
                "build_url": os.getenv("CI_PIPELINE_URL"),
                "branch": os.getenv("CI_COMMIT_REF_NAME"),
                "commit": os.getenv("CI_COMMIT_SHA"),
            }
        
        # Jenkins
        if os.getenv("JENKINS_URL"):
            return {
                "build_id": os.getenv("BUILD_NUMBER"),
                "build_url": os.getenv("BUILD_URL"),
                "branch": os.getenv("GIT_BRANCH"),
                "commit": os.getenv("GIT_COMMIT"),
            }
        
        # Azure DevOps
        if os.getenv("TF_BUILD"):
            return {
                "build_id": os.getenv("BUILD_BUILDID"),
                "build_url": f"{os.getenv('SYSTEM_TEAMFOUNDATIONSERVERURI')}{os.getenv('SYSTEM_TEAMPROJECT')}/_build/results?buildId={os.getenv('BUILD_BUILDID')}",
                "branch": os.getenv("BUILD_SOURCEBRANCHNAME"),
                "commit": os.getenv("BUILD_SOURCEVERSION"),
            }
        
        # CircleCI
        if os.getenv("CIRCLECI"):
            return {
                "build_id": os.getenv("CIRCLE_BUILD_NUM"),
                "build_url": os.getenv("CIRCLE_BUILD_URL"),
                "branch": os.getenv("CIRCLE_BRANCH"),
                "commit": os.getenv("CIRCLE_SHA1"),
            }
        
        # Travis CI
        if os.getenv("TRAVIS"):
            return {
                "build_id": os.getenv("TRAVIS_BUILD_ID"),
                "build_url": os.getenv("TRAVIS_BUILD_WEB_URL"),
                "branch": os.getenv("TRAVIS_BRANCH"),
                "commit": os.getenv("TRAVIS_COMMIT"),
            }
        
        return {}


# Fixture for accessing QAagentic in tests
@pytest.fixture
def qagentic_reporter(request: pytest.FixtureRequest) -> QAgenticReporter:
    """
    Fixture providing access to the QAagentic reporter.
    
    Usage:
        def test_example(qagentic_reporter):
            qagentic_reporter.current_run  # Access current run
    """
    return get_reporter()


@pytest.fixture
def qagentic_test(request: pytest.FixtureRequest) -> Optional[TestResult]:
    """
    Fixture providing access to the current test result.
    
    Usage:
        def test_example(qagentic_test):
            qagentic_test.labels["custom"] = "value"
    """
    plugin = request.config.pluginmanager.get_plugin("qagentic_plugin")
    if plugin:
        return plugin._current_test
    return None
