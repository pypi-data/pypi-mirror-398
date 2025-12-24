"""
QAagentic SDK - AI-Powered Test Intelligence Platform

A next-generation test reporting library that brings AI-powered insights
to your test automation. Drop-in replacement for Allure with superpowers.

Usage:
    import qagentic
    from qagentic import feature, story, step, severity, Severity

    @feature("Authentication")
    @story("User Login")
    @severity(Severity.CRITICAL)
    def test_login():
        with step("Enter credentials"):
            # test code
            pass

    qagentic.attach("screenshot.png", "Login Screenshot")
"""

from qagentic.core.config import configure, get_config, QAgenticConfig
from qagentic.core.decorators import (
    feature,
    story,
    epic,
    severity,
    tag,
    label,
    link,
    issue,
    testcase,
    description,
    title,
    owner,
    layer,
    parent_suite,
    suite,
    sub_suite,
)
from qagentic.core.context import step, Step
from qagentic.core.attachments import (
    attach,
    attach_file,
    attach_screenshot,
    attach_json,
    attach_text,
    attach_html,
    attach_video,
)
from qagentic.core.severity import Severity
from qagentic.core.status import Status
from qagentic.core.reporter import QAgenticReporter, get_reporter
from qagentic.core.test_result import TestResult, StepResult

__version__ = "0.1.0"
__author__ = "QAagentic Team"
__email__ = "team@qagentic.io"

__all__ = [
    # Configuration
    "configure",
    "get_config",
    "QAgenticConfig",
    # Decorators
    "feature",
    "story",
    "epic",
    "severity",
    "tag",
    "label",
    "link",
    "issue",
    "testcase",
    "description",
    "title",
    "owner",
    "layer",
    "parent_suite",
    "suite",
    "sub_suite",
    # Context managers
    "step",
    "Step",
    # Attachments
    "attach",
    "attach_file",
    "attach_screenshot",
    "attach_json",
    "attach_text",
    "attach_html",
    "attach_video",
    # Enums
    "Severity",
    "Status",
    # Reporter
    "QAgenticReporter",
    "get_reporter",
    # Models
    "TestResult",
    "StepResult",
    # Version
    "__version__",
]
