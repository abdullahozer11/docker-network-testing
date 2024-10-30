import argparse
import importlib
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

from src.core.reporter import TestReporter


class TestRunner:
    def __init__(self, report_dir: Optional[str] = None):
        self.console = Console()
        self.reporter = TestReporter(report_dir) if report_dir else TestReporter()

    def check_docker_status(self) -> bool:
        """Check if Docker daemon is running."""
        try:
            result = subprocess.run(
                ["docker", "info"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            self.console.print("[red]Docker is not installed or not in PATH[/red]")
            return False

    def check_docker_containers(self) -> bool:
        """Check if Docker containers are running."""
        try:
            result = subprocess.run(
                ["docker", "ps"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            # Check if there are any running containers (more than just the header line)
            return len(result.stdout.strip().split("\n")) > 1
        except Exception as e:
            self.console.print(f"[red]Error checking Docker containers: {str(e)}[/red]")
            return False

    def prompt_start_containers(self) -> bool:
        """Prompt user to start Docker containers if they're not running."""
        response = input(
            "Docker containers are not running. Would you like to start them? (y/n): "
        ).lower()
        if response == "y":
            try:
                self.console.print("[cyan]Starting Docker containers...[/cyan]")
                result = subprocess.run(
                    ["make", "up"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                if result.returncode == 0:
                    self.console.print(
                        "[green]Docker containers started successfully![/green]"
                    )
                    return True
                else:
                    self.console.print(
                        f"[red]Failed to start Docker containers: {result.stderr}[/red]"
                    )
                    return False
            except Exception as e:
                self.console.print(
                    f"[red]Error starting Docker containers: {str(e)}[/red]"
                )
                return False
        return False

    @staticmethod
    def discover_test_modules() -> List[str]:
        """Discover all test modules in the tests directory."""
        test_dir = Path(__file__).parent.parent / "tests"
        test_files = test_dir.glob("test_*.py")
        return [
            f"src.tests.{f.stem}"
            for f in test_files
            if f.is_file() and not f.name.startswith("__")
        ]

    def run_tests(self, test_modules: Optional[List[str]] = None) -> bool:
        """Run tests and consolidate results."""
        # Check Docker status first
        if not self.check_docker_status():
            self.console.print(
                "[red]Docker is not running. Please start Docker first.[/red]"
            )
            return False

        # Check if containers are running
        if not self.check_docker_containers():
            if not self.prompt_start_containers():
                self.console.print(
                    "[yellow]Exiting as Docker containers are not running.[/yellow]"
                )
                return False

        if test_modules is None:
            test_modules = self.discover_test_modules()

        self.console.print(
            Panel.fit(
                "[bold blue]Network Test Framework[/bold blue]\n"
                "[cyan]Running test suites...[/cyan]"
            )
        )

        success = True
        with Progress() as progress:
            task = progress.add_task("[cyan]Running tests...", total=len(test_modules))
            for module_name in test_modules:
                try:
                    # Import the test module
                    module = importlib.import_module(module_name)
                    # Run tests for this module
                    result = pytest.main(["-v", module.__file__])
                    if result != 0:
                        success = False
                    progress.update(task, advance=1)
                except Exception as e:
                    self.console.print(
                        f"[red]Error running {module_name}: {str(e)}[/red]"
                    )
                    success = False

        self.console.print("\n[green]Test execution completed![/green]")
        self.reporter.generate_summary()
        return success


def main():
    parser = argparse.ArgumentParser(description="Network Test Framework CLI Runner")
    parser.add_argument(
        "--report-dir", help="Custom directory for test reports", default=None
    )
    parser.add_argument(
        "test_modules",
        nargs="*",
        help="Specific test modules to run (without the .py extension)",
    )
    args = parser.parse_args()
    runner = TestRunner(args.report_dir)

    # If specific modules provided, format them correctly
    test_modules = None
    if args.test_modules:
        test_modules = [f"src.tests.test_{module}" for module in args.test_modules]

    success = runner.run_tests(test_modules)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
