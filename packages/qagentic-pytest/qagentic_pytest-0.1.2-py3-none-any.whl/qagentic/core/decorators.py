"""
Decorators for annotating test functions with metadata.

These decorators are compatible with Allure-style annotations and provide
additional QAagentic-specific functionality.

Usage:
    @feature("Authentication")
    @story("User Login")
    @severity(Severity.CRITICAL)
    def test_login():
        pass
"""

import functools
from typing import Any, Callable, Optional, TypeVar, Union

from qagentic.core.severity import Severity

F = TypeVar("F", bound=Callable[..., Any])

# Marker attribute name for storing test metadata
QAGENTIC_MARKER = "_qagentic_metadata"


def _get_metadata(func: Callable[..., Any]) -> dict:
    """Get or create metadata dictionary for a function."""
    if not hasattr(func, QAGENTIC_MARKER):
        setattr(func, QAGENTIC_MARKER, {
            "labels": {},
            "links": [],
            "attachments": [],
            "steps": [],
        })
    return getattr(func, QAGENTIC_MARKER)


def _add_label(name: str, value: str) -> Callable[[F], F]:
    """Create a decorator that adds a label to the test."""
    def decorator(func: F) -> F:
        metadata = _get_metadata(func)
        metadata["labels"][name] = value
        return func
    return decorator


def feature(name: str) -> Callable[[F], F]:
    """
    Mark test with a feature label.
    
    Args:
        name: Feature name (e.g., "Authentication", "Payments")
    
    Example:
        @feature("User Management")
        def test_create_user():
            pass
    """
    return _add_label("feature", name)


def story(name: str) -> Callable[[F], F]:
    """
    Mark test with a user story label.
    
    Args:
        name: Story name (e.g., "User can login", "User can reset password")
    
    Example:
        @story("User Login")
        def test_login_success():
            pass
    """
    return _add_label("story", name)


def epic(name: str) -> Callable[[F], F]:
    """
    Mark test with an epic label.
    
    Args:
        name: Epic name (e.g., "Authentication System", "E-commerce")
    
    Example:
        @epic("User Authentication")
        def test_oauth_login():
            pass
    """
    return _add_label("epic", name)


def severity(level: Union[Severity, str]) -> Callable[[F], F]:
    """
    Mark test with a severity level.
    
    Args:
        level: Severity level (Severity.CRITICAL, Severity.NORMAL, etc.)
    
    Example:
        @severity(Severity.CRITICAL)
        def test_payment_processing():
            pass
    """
    if isinstance(level, str):
        level = Severity.from_string(level)
    return _add_label("severity", str(level))


def tag(*tags: str) -> Callable[[F], F]:
    """
    Add tags to a test.
    
    Args:
        *tags: One or more tag strings
    
    Example:
        @tag("smoke", "regression", "api")
        def test_api_endpoint():
            pass
    """
    def decorator(func: F) -> F:
        metadata = _get_metadata(func)
        existing_tags = metadata["labels"].get("tags", [])
        if isinstance(existing_tags, str):
            existing_tags = [existing_tags]
        metadata["labels"]["tags"] = list(existing_tags) + list(tags)
        return func
    return decorator


def label(name: str, value: str) -> Callable[[F], F]:
    """
    Add a custom label to a test.
    
    Args:
        name: Label name
        value: Label value
    
    Example:
        @label("team", "platform")
        @label("priority", "high")
        def test_critical_feature():
            pass
    """
    return _add_label(name, value)


def link(url: str, name: Optional[str] = None, link_type: str = "link") -> Callable[[F], F]:
    """
    Add a link to a test.
    
    Args:
        url: Link URL
        name: Optional display name
        link_type: Type of link (link, issue, tms)
    
    Example:
        @link("https://jira.example.com/browse/PROJ-123", "PROJ-123", "issue")
        def test_feature():
            pass
    """
    def decorator(func: F) -> F:
        metadata = _get_metadata(func)
        metadata["links"].append({
            "url": url,
            "name": name or url,
            "type": link_type,
        })
        return func
    return decorator


def issue(url: str, name: Optional[str] = None) -> Callable[[F], F]:
    """
    Link test to an issue tracker.
    
    Args:
        url: Issue URL or ID
        name: Optional display name
    
    Example:
        @issue("JIRA-123")
        def test_bug_fix():
            pass
    """
    return link(url, name, "issue")


def testcase(url: str, name: Optional[str] = None) -> Callable[[F], F]:
    """
    Link test to a test management system.
    
    Args:
        url: Test case URL or ID
        name: Optional display name
    
    Example:
        @testcase("TC-456")
        def test_documented_case():
            pass
    """
    return link(url, name, "tms")


def description(text: str) -> Callable[[F], F]:
    """
    Add a description to a test.
    
    Args:
        text: Description text (supports Markdown)
    
    Example:
        @description('''
        This test verifies the login flow:
        1. Navigate to login page
        2. Enter credentials
        3. Verify redirect to dashboard
        ''')
        def test_login():
            pass
    """
    return _add_label("description", text)


def title(name: str) -> Callable[[F], F]:
    """
    Set a custom title for the test.
    
    Args:
        name: Custom test title
    
    Example:
        @title("Verify user can login with valid credentials")
        def test_login():
            pass
    """
    return _add_label("title", name)


def owner(name: str) -> Callable[[F], F]:
    """
    Set the test owner.
    
    Args:
        name: Owner name or email
    
    Example:
        @owner("john.doe@example.com")
        def test_feature():
            pass
    """
    return _add_label("owner", name)


def layer(name: str) -> Callable[[F], F]:
    """
    Set the test layer (unit, integration, e2e, etc.).
    
    Args:
        name: Layer name
    
    Example:
        @layer("integration")
        def test_api_integration():
            pass
    """
    return _add_label("layer", name)


def parent_suite(name: str) -> Callable[[F], F]:
    """
    Set the parent suite name.
    
    Args:
        name: Parent suite name
    
    Example:
        @parent_suite("API Tests")
        def test_endpoint():
            pass
    """
    return _add_label("parentSuite", name)


def suite(name: str) -> Callable[[F], F]:
    """
    Set the suite name.
    
    Args:
        name: Suite name
    
    Example:
        @suite("Authentication")
        def test_login():
            pass
    """
    return _add_label("suite", name)


def sub_suite(name: str) -> Callable[[F], F]:
    """
    Set the sub-suite name.
    
    Args:
        name: Sub-suite name
    
    Example:
        @sub_suite("Login Tests")
        def test_login():
            pass
    """
    return _add_label("subSuite", name)


def flaky(reason: Optional[str] = None, max_reruns: int = 3) -> Callable[[F], F]:
    """
    Mark a test as flaky with optional rerun configuration.
    
    Args:
        reason: Reason why the test is flaky
        max_reruns: Maximum number of reruns
    
    Example:
        @flaky("Network timing issues", max_reruns=2)
        def test_external_api():
            pass
    """
    def decorator(func: F) -> F:
        metadata = _get_metadata(func)
        metadata["labels"]["flaky"] = True
        metadata["labels"]["flaky_reason"] = reason
        metadata["labels"]["max_reruns"] = max_reruns
        return func
    return decorator


def manual() -> Callable[[F], F]:
    """
    Mark a test as a manual test case.
    
    Example:
        @manual()
        def test_visual_inspection():
            pass
    """
    return _add_label("manual", "true")


def automated() -> Callable[[F], F]:
    """
    Mark a test as automated (default).
    
    Example:
        @automated()
        def test_api_endpoint():
            pass
    """
    return _add_label("automated", "true")


def get_test_metadata(func: Callable[..., Any]) -> dict:
    """
    Get all metadata for a test function.
    
    Args:
        func: Test function
    
    Returns:
        Dictionary containing all test metadata
    """
    return getattr(func, QAGENTIC_MARKER, {
        "labels": {},
        "links": [],
        "attachments": [],
        "steps": [],
    })
