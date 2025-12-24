#!/usr/bin/env python
"""
QAagentic CLI - One-command setup and integration tool.
Simplifies QAagentic integration across all testing frameworks.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional
import click


class QAgenticSetup:
    """Handles automatic QAagentic setup and configuration."""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.config_dir = self.project_root / ".qagentic"
        self.config_file = self.config_dir / "config.json"
    
    def init(self, project_name: str, framework: str = "pytest", api_url: str = "http://localhost:8080"):
        """Initialize QAagentic in the project."""
        self.config_dir.mkdir(exist_ok=True)
        
        config = {
            "project_name": project_name,
            "framework": framework,
            "api_url": api_url,
            "enabled": True,
            "api_reporting": True,
            "local_reporting": True,
            "report_dir": "./qagentic-results"
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Create framework-specific setup
        if framework == "pytest":
            self._setup_pytest(project_name, api_url)
        elif framework == "cypress":
            self._setup_cypress(project_name, api_url)
        elif framework == "playwright":
            self._setup_playwright(project_name, api_url)
        
        return config
    
    def _setup_pytest(self, project_name: str, api_url: str):
        """Auto-setup pytest configuration."""
        pytest_ini = self.project_root / "pytest.ini"
        
        if not pytest_ini.exists():
            pytest_content = f"""[pytest]
pythonpath = .
testpaths = tests
python_files = test_*.py

markers =
    integration: integration tests
    smoke: smoke tests
    critical: critical tests

# QAagentic Configuration
qagentic_enabled = true
qagentic_api_url = {api_url}
qagentic_project_name = {project_name}
qagentic_environment = integration
"""
            pytest_ini.write_text(pytest_content)
        
        # Create conftest.py if it doesn't exist
        conftest = self.project_root / "conftest.py"
        if not conftest.exists():
            conftest_content = '''import pytest
from qagentic import QAgenticReporter, configure, QAgenticConfig

@pytest.fixture(scope="session", autouse=True)
def qagentic_reporter():
    """Auto-initialized QAagentic reporter."""
    config = QAgenticConfig(
        project_name="My Project",
        environment="integration",
    )
    config.api.enabled = True
    config.local.enabled = True
    
    configure(config)
    reporter = QAgenticReporter()
    reporter.start_run(
        name="Integration Tests",
        project_name="My Project",
        environment="integration",
    )
    
    yield reporter
    reporter.end_run()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Auto-capture test results."""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call":
        status = "passed" if report.passed else "failed"
        duration_ms = (report.stop - report.start) * 1000 if hasattr(report, 'start') else 0
'''
            conftest.write_text(conftest_content)
    
    def _setup_cypress(self, project_name: str, api_url: str):
        """Auto-setup Cypress configuration."""
        cypress_config = self.project_root / "cypress.config.js"
        
        if not cypress_config.exists():
            config_content = f"""const {{ defineConfig }} = require('cypress');

module.exports = defineConfig({{
  e2e: {{
    baseUrl: 'http://localhost:3000',
    setupNodeEvents(on, config) {{
      // QAagentic integration
      require('qagentic-reporter/cypress')(on, config, {{
        projectName: '{project_name}',
        apiUrl: '{api_url}',
        enabled: true,
      }});
      return config;
    }},
  }},
}});
"""
            cypress_config.write_text(config_content)
    
    def _setup_playwright(self, project_name: str, api_url: str):
        """Auto-setup Playwright configuration."""
        playwright_config = self.project_root / "playwright.config.ts"
        
        if not playwright_config.exists():
            config_content = f"""import {{ defineConfig, devices }} from '@playwright/test';
import {{ qagenticReporter }} from 'qagentic-reporter/playwright';

export default defineConfig({{
  testDir: './tests',
  reporter: [
    ['html'],
    qagenticReporter({{
      projectName: '{project_name}',
      apiUrl: '{api_url}',
      enabled: true,
    }}),
  ],
  use: {{
    baseURL: 'http://localhost:3000',
  }},
}});
"""
            playwright_config.write_text(config_content)


@click.group()
def cli():
    """QAagentic CLI - Simplified test reporting integration."""
    pass


@cli.command()
@click.option('--name', prompt='Project name', help='Name of your project')
@click.option('--framework', type=click.Choice(['pytest', 'cypress', 'playwright', 'jest']), 
              default='pytest', help='Testing framework')
@click.option('--api-url', default='http://localhost:8080', help='QAagentic API URL')
def init(name: str, framework: str, api_url: str):
    """Initialize QAagentic in your project (one command setup)."""
    click.echo(f"🚀 Initializing QAagentic for {framework}...")
    
    setup = QAgenticSetup()
    config = setup.init(name, framework, api_url)
    
    click.echo(f"✅ QAagentic initialized successfully!")
    click.echo(f"   Project: {config['project_name']}")
    click.echo(f"   Framework: {config['framework']}")
    click.echo(f"   API URL: {config['api_url']}")
    click.echo(f"\n📝 Configuration saved to: .qagentic/config.json")
    click.echo(f"\n🎯 Next steps:")
    click.echo(f"   1. Install dependencies: pip install qagentic-pytest")
    click.echo(f"   2. Run your tests: pytest -v")
    click.echo(f"   3. View results: http://localhost:3000")


@cli.command()
def status():
    """Check QAagentic status and configuration."""
    setup = QAgenticSetup()
    
    if setup.config_file.exists():
        with open(setup.config_file) as f:
            config = json.load(f)
        
        click.echo("✅ QAagentic is configured")
        click.echo(f"   Project: {config['project_name']}")
        click.echo(f"   Framework: {config['framework']}")
        click.echo(f"   API: {config['api_url']}")
    else:
        click.echo("❌ QAagentic not initialized. Run 'qagentic init' first.")


@cli.command()
def doctor():
    """Diagnose QAagentic setup issues."""
    click.echo("🔍 Running QAagentic health check...")
    
    checks = {
        "Configuration": Path(".qagentic/config.json").exists(),
        "pytest.ini": Path("pytest.ini").exists(),
        "conftest.py": Path("conftest.py").exists(),
    }
    
    for check, status in checks.items():
        symbol = "✅" if status else "❌"
        click.echo(f"   {symbol} {check}")
    
    if all(checks.values()):
        click.echo("\n✅ All checks passed!")
    else:
        click.echo("\n⚠️  Some checks failed. Run 'qagentic init' to fix.")


if __name__ == '__main__':
    cli()
