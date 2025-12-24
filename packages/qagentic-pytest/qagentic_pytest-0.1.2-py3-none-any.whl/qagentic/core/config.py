"""Configuration management for QAagentic SDK."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml


@dataclass
class APIConfig:
    """API reporting configuration."""
    
    enabled: bool = True
    url: str = "http://localhost:8080"
    key: Optional[str] = None
    timeout: int = 30
    retry_count: int = 3
    batch_size: int = 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "url": self.url,
            "key": self.key,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "batch_size": self.batch_size,
        }


@dataclass
class LocalConfig:
    """Local file reporting configuration."""
    
    enabled: bool = True
    output_dir: str = "./qagentic-results"
    formats: List[str] = field(default_factory=lambda: ["json", "html"])
    clean_on_start: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "output_dir": self.output_dir,
            "formats": self.formats,
            "clean_on_start": self.clean_on_start,
        }


@dataclass
class FeaturesConfig:
    """Feature flags configuration."""
    
    ai_analysis: bool = True
    failure_clustering: bool = True
    flaky_detection: bool = True
    screenshots: str = "on_failure"  # always, on_failure, never
    videos: str = "on_failure"
    console_output: bool = True
    rich_console: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "ai_analysis": self.ai_analysis,
            "failure_clustering": self.failure_clustering,
            "flaky_detection": self.flaky_detection,
            "screenshots": self.screenshots,
            "videos": self.videos,
            "console_output": self.console_output,
            "rich_console": self.rich_console,
        }


@dataclass
class LabelsConfig:
    """Default labels for all tests."""
    
    team: Optional[str] = None
    component: Optional[str] = None
    environment: Optional[str] = None
    custom: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "team": self.team,
            "component": self.component,
            "environment": self.environment,
            "custom": self.custom,
        }


@dataclass
class QAgenticConfig:
    """Main configuration for QAagentic SDK."""
    
    project_name: str = "default"
    environment: str = "local"
    api: APIConfig = field(default_factory=APIConfig)
    local: LocalConfig = field(default_factory=LocalConfig)
    features: FeaturesConfig = field(default_factory=FeaturesConfig)
    labels: LabelsConfig = field(default_factory=LabelsConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "project_name": self.project_name,
            "environment": self.environment,
            "api": self.api.to_dict(),
            "local": self.local.to_dict(),
            "features": self.features.to_dict(),
            "labels": self.labels.to_dict(),
        }
    
    def __str__(self) -> str:
        """String representation for serialization."""
        import json
        return json.dumps(self.to_dict())
    
    def encode(self, encoding: str = "utf-8") -> bytes:
        """Encode configuration to bytes for serialization."""
        return str(self).encode(encoding)
    
    @classmethod
    def from_env(cls) -> "QAgenticConfig":
        """Create configuration from environment variables."""
        config = cls()
        
        # Project settings
        config.project_name = os.getenv("QAGENTIC_PROJECT_NAME", config.project_name)
        config.environment = os.getenv("QAGENTIC_ENVIRONMENT", config.environment)
        
        # API settings
        config.api.enabled = os.getenv("QAGENTIC_API_ENABLED", "true").lower() == "true"
        config.api.url = os.getenv("QAGENTIC_API_URL", config.api.url)
        config.api.key = os.getenv("QAGENTIC_API_KEY", config.api.key)
        
        # Local settings
        config.local.enabled = os.getenv("QAGENTIC_LOCAL_ENABLED", "true").lower() == "true"
        config.local.output_dir = os.getenv("QAGENTIC_OUTPUT_DIR", config.local.output_dir)
        formats = os.getenv("QAGENTIC_OUTPUT_FORMAT")
        if formats:
            config.local.formats = [f.strip() for f in formats.split(",")]
        
        # Feature flags
        config.features.ai_analysis = os.getenv("QAGENTIC_AI_ANALYSIS", "true").lower() == "true"
        config.features.screenshots = os.getenv("QAGENTIC_SCREENSHOTS", config.features.screenshots)
        config.features.videos = os.getenv("QAGENTIC_VIDEOS", config.features.videos)
        
        # Labels
        config.labels.team = os.getenv("QAGENTIC_TEAM", config.labels.team)
        config.labels.component = os.getenv("QAGENTIC_COMPONENT", config.labels.component)
        
        return config
    
    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "QAgenticConfig":
        """Load configuration from YAML file."""
        path = Path(path)
        if not path.exists():
            return cls.from_env()
        
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        
        config = cls()
        
        # Project settings
        project = data.get("project", {})
        config.project_name = project.get("name", config.project_name)
        config.environment = project.get("environment", config.environment)
        
        # Reporting settings
        reporting = data.get("reporting", {})
        
        api_data = reporting.get("api", {})
        config.api.enabled = api_data.get("enabled", config.api.enabled)
        config.api.url = api_data.get("url", config.api.url)
        config.api.key = api_data.get("key", config.api.key)
        
        local_data = reporting.get("local", {})
        config.local.enabled = local_data.get("enabled", config.local.enabled)
        config.local.output_dir = local_data.get("output_dir", config.local.output_dir)
        config.local.formats = local_data.get("formats", config.local.formats)
        
        # Features
        features = data.get("features", {})
        config.features.ai_analysis = features.get("ai_analysis", config.features.ai_analysis)
        config.features.failure_clustering = features.get("failure_clustering", config.features.failure_clustering)
        config.features.flaky_detection = features.get("flaky_detection", config.features.flaky_detection)
        config.features.screenshots = features.get("screenshots", config.features.screenshots)
        config.features.videos = features.get("videos", config.features.videos)
        
        # Labels
        labels = data.get("labels", {})
        config.labels.team = labels.get("team", config.labels.team)
        config.labels.component = labels.get("component", config.labels.component)
        config.labels.custom = {k: v for k, v in labels.items() if k not in ("team", "component")}
        
        # Override with environment variables
        env_config = cls.from_env()
        if os.getenv("QAGENTIC_API_URL"):
            config.api.url = env_config.api.url
        if os.getenv("QAGENTIC_API_KEY"):
            config.api.key = env_config.api.key
        
        return config
    
    @classmethod
    def auto_discover(cls) -> "QAgenticConfig":
        """Auto-discover configuration from common locations."""
        search_paths = [
            Path.cwd() / "qagentic.yaml",
            Path.cwd() / "qagentic.yml",
            Path.cwd() / ".qagentic.yaml",
            Path.cwd() / ".qagentic.yml",
            Path.home() / ".qagentic" / "config.yaml",
        ]
        
        for path in search_paths:
            if path.exists():
                return cls.from_file(path)
        
        return cls.from_env()


# Global configuration instance
_config: Optional[QAgenticConfig] = None


def configure(
    project_name: Optional[str] = None,
    environment: Optional[str] = None,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    output_dir: Optional[str] = None,
    **kwargs: Any,
) -> QAgenticConfig:
    """
    Configure QAagentic SDK.
    
    Args:
        project_name: Name of the project
        environment: Environment name (e.g., 'staging', 'production')
        api_url: URL of the QAagentic API
        api_key: API key for authentication
        output_dir: Directory for local reports
        **kwargs: Additional configuration options
    
    Returns:
        The configured QAgenticConfig instance
    
    Example:
        >>> qagentic.configure(
        ...     project_name="my-project",
        ...     api_url="http://localhost:8080",
        ...     api_key="your-api-key",
        ... )
    """
    global _config
    
    _config = QAgenticConfig.auto_discover()
    
    if project_name:
        _config.project_name = project_name
    if environment:
        _config.environment = environment
    if api_url:
        _config.api.url = api_url
    if api_key:
        _config.api.key = api_key
    if output_dir:
        _config.local.output_dir = output_dir
    
    # Handle additional kwargs
    for key, value in kwargs.items():
        if hasattr(_config.features, key):
            setattr(_config.features, key, value)
        elif hasattr(_config.labels, key):
            setattr(_config.labels, key, value)
    
    return _config


def get_config() -> QAgenticConfig:
    """Get the current configuration."""
    global _config
    if _config is None:
        _config = QAgenticConfig.auto_discover()
    return _config
