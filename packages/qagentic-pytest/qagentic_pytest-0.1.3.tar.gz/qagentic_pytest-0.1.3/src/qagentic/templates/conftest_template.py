"""
QAagentic Auto-Generated conftest.py
Copy this file to your tests directory for instant QAagentic integration.
"""

import pytest
from qagentic import QAgenticReporter, configure, QAgenticConfig


@pytest.fixture(scope="session", autouse=True)
def qagentic_reporter():
    """Auto-initialized QAagentic reporter - zero config needed."""
    # Auto-detect configuration
    config = QAgenticConfig(
        project_name="My Project",
        environment="integration",
    )
    
    # Enable both API and local reporting
    config.api.enabled = True
    config.api.url = "http://localhost:8080"
    config.local.enabled = True
    config.local.output_dir = "./qagentic-results"
    
    configure(config)
    reporter = QAgenticReporter()
    
    # Start test run
    reporter.start_run(
        name="Integration Tests",
        project_name="My Project",
        environment="integration",
    )
    
    yield reporter
    
    # End test run (automatically sends results to API)
    reporter.end_run()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Auto-capture individual test results."""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call":
        status = "passed" if report.passed else "failed"
        duration_ms = (report.stop - report.start) * 1000 if hasattr(report, 'start') else 0
