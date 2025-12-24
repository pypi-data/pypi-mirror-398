"""
Attachment utilities for adding files, screenshots, and data to test reports.

Usage:
    qagentic.attach("screenshot.png", "Login Screenshot")
    qagentic.attach_json({"key": "value"}, "API Response")
    qagentic.attach_screenshot("path/to/screenshot.png")
"""

import base64
import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union
from uuid import uuid4

from qagentic.core.context import _get_current_step

# Global attachment storage for current test
import threading
_attachment_storage = threading.local()


def _get_attachments() -> list:
    """Get current test attachments."""
    if not hasattr(_attachment_storage, "attachments"):
        _attachment_storage.attachments = []
    return _attachment_storage.attachments


def _clear_attachments() -> None:
    """Clear attachments for new test."""
    _attachment_storage.attachments = []


def attach(
    data: Union[str, bytes, Path],
    name: str,
    attachment_type: Optional[str] = None,
    extension: Optional[str] = None,
) -> str:
    """
    Attach data to the current test or step.
    
    Args:
        data: Data to attach - can be file path, bytes, or string
        name: Display name for the attachment
        attachment_type: MIME type (auto-detected if not provided)
        extension: File extension for type detection
    
    Returns:
        Attachment ID
    
    Example:
        qagentic.attach("screenshot.png", "Login Screenshot")
        qagentic.attach(b"binary data", "Raw Data", "application/octet-stream")
        qagentic.attach('{"key": "value"}', "JSON", "application/json")
    """
    attachment_id = str(uuid4())
    
    # Handle file path
    if isinstance(data, (str, Path)):
        path = Path(data)
        if path.exists() and path.is_file():
            with open(path, "rb") as f:
                content = f.read()
            if not attachment_type:
                attachment_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            if not extension:
                extension = path.suffix.lstrip(".")
        else:
            # Treat as string content
            content = data.encode() if isinstance(data, str) else data
            if not attachment_type:
                attachment_type = "text/plain"
    elif isinstance(data, bytes):
        content = data
        if not attachment_type:
            attachment_type = "application/octet-stream"
    else:
        content = str(data).encode()
        if not attachment_type:
            attachment_type = "text/plain"
    
    attachment = {
        "id": attachment_id,
        "name": name,
        "type": attachment_type,
        "extension": extension,
        "content": base64.b64encode(content).decode() if isinstance(content, bytes) else content,
        "size": len(content),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    # Add to current step if in step context
    current_step = _get_current_step()
    if current_step:
        current_step.attachments.append(attachment)
    else:
        # Add to test-level attachments
        _get_attachments().append(attachment)
    
    return attachment_id


def attach_file(
    path: Union[str, Path],
    name: Optional[str] = None,
) -> str:
    """
    Attach a file to the current test.
    
    Args:
        path: Path to the file
        name: Display name (defaults to filename)
    
    Returns:
        Attachment ID
    
    Example:
        qagentic.attach_file("logs/test.log", "Test Logs")
    """
    path = Path(path)
    display_name = name or path.name
    return attach(path, display_name)


def attach_screenshot(
    path: Union[str, Path, bytes],
    name: str = "Screenshot",
) -> str:
    """
    Attach a screenshot to the current test.
    
    Args:
        path: Path to screenshot or raw image bytes
        name: Display name
    
    Returns:
        Attachment ID
    
    Example:
        qagentic.attach_screenshot("screenshots/login.png", "Login Page")
    """
    if isinstance(path, bytes):
        return attach(path, name, "image/png", "png")
    return attach(path, name, "image/png")


def attach_json(
    data: Union[dict, list],
    name: str = "JSON Data",
    indent: int = 2,
) -> str:
    """
    Attach JSON data to the current test.
    
    Args:
        data: Dictionary or list to serialize
        name: Display name
        indent: JSON indentation
    
    Returns:
        Attachment ID
    
    Example:
        qagentic.attach_json({"status": "success", "data": [1, 2, 3]}, "API Response")
    """
    json_str = json.dumps(data, indent=indent, default=str)
    return attach(json_str, name, "application/json", "json")


def attach_text(
    text: str,
    name: str = "Text",
) -> str:
    """
    Attach plain text to the current test.
    
    Args:
        text: Text content
        name: Display name
    
    Returns:
        Attachment ID
    
    Example:
        qagentic.attach_text("Test output logs...", "Console Output")
    """
    return attach(text, name, "text/plain", "txt")


def attach_html(
    html: str,
    name: str = "HTML",
) -> str:
    """
    Attach HTML content to the current test.
    
    Args:
        html: HTML content
        name: Display name
    
    Returns:
        Attachment ID
    
    Example:
        qagentic.attach_html("<h1>Test Report</h1>", "Report")
    """
    return attach(html, name, "text/html", "html")


def attach_video(
    path: Union[str, Path],
    name: str = "Video",
) -> str:
    """
    Attach a video to the current test.
    
    Args:
        path: Path to video file
        name: Display name
    
    Returns:
        Attachment ID
    
    Example:
        qagentic.attach_video("recordings/test.mp4", "Test Recording")
    """
    path = Path(path)
    mime_type = mimetypes.guess_type(str(path))[0] or "video/mp4"
    return attach(path, name, mime_type)


def attach_csv(
    data: Union[str, list],
    name: str = "CSV Data",
) -> str:
    """
    Attach CSV data to the current test.
    
    Args:
        data: CSV string or list of rows
        name: Display name
    
    Returns:
        Attachment ID
    
    Example:
        qagentic.attach_csv([["Name", "Value"], ["test", "123"]], "Data")
    """
    if isinstance(data, list):
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(data)
        data = output.getvalue()
    return attach(data, name, "text/csv", "csv")


def attach_xml(
    xml: str,
    name: str = "XML",
) -> str:
    """
    Attach XML content to the current test.
    
    Args:
        xml: XML content
        name: Display name
    
    Returns:
        Attachment ID
    """
    return attach(xml, name, "application/xml", "xml")
