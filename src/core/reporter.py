# src/core/reporter.py
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader


@dataclass
class TestResult:
    module_name: str  # Test module name (e.g., "connectivity", "vlan")
    test_name: str  # Individual test name
    status: str  # "PASS" or "FAIL"
    duration: float
    timestamp: datetime
    error_message: Optional[str] = None
    details: Optional[Dict] = None


class TestReporter:
    _instance = None
    _execution_dir = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TestReporter, cls).__new__(cls)
        return cls._instance

    def __init__(self, output_dir: str = "reports", template_dir: str = "templates"):
        if not hasattr(self, "initialized"):
            self.base_output_dir = Path(output_dir)
            self.base_output_dir.mkdir(exist_ok=True)
            self.template_dir = Path(template_dir)
            self.results: Dict[str, List[TestResult]] = {}
            self.template_env = Environment(loader=FileSystemLoader(template_dir))
            # Create execution directory immediately
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._execution_dir = self.base_output_dir / f"execution_{timestamp}"
            self._execution_dir.mkdir(exist_ok=True)
            self._copy_static_files()
            self.initialized = True

    @property
    def execution_dir(self) -> Path:
        return self._execution_dir

    def _copy_static_files(self):
        """Copy static CSS and JS files to execution directory."""
        # Copy CSS file
        css_template = self.template_env.get_template("report.css")
        css_content = css_template.render()
        css_file = self.execution_dir / "report.css"
        with open(css_file, "w") as f:
            f.write(css_content)

        # Copy JS file
        js_template = self.template_env.get_template("report.js")
        js_content = js_template.render()
        js_file = self.execution_dir / "report.js"
        with open(js_file, "w") as f:
            f.write(js_content)

    def add_result(self, module_name: str, result: TestResult):
        """Add a test result to the current module."""
        if module_name not in self.results:
            self.results[module_name] = []
        self.results[module_name].append(result)
        self._save_results()

    def _save_results(self):
        """Save both JSON and HTML reports."""
        # Save JSON report with command logs
        json_data = {
            "execution_timestamp": self._execution_dir.name,
            "modules": {
                module: [
                    {
                        "test_name": r.test_name,
                        "status": r.status,
                        "duration": r.duration,
                        "timestamp": r.timestamp.isoformat(),
                        "error_message": r.error_message,
                        "details": r.details,
                    }
                    for r in results
                ]
                for module, results in self.results.items()
            },
        }

        json_file = self.execution_dir / "test_report.json"
        with open(json_file, "w") as f:
            json.dump(json_data, f, indent=2)

        # Generate and save HTML report
        self._generate_html_report()

    def _get_template_data(self):
        """Prepare data for the HTML template."""
        all_tests = [test for tests in self.results.values() for test in tests]
        total_tests = len(all_tests)
        passed_tests = sum(1 for t in all_tests if t.status == "PASS")
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        module_stats = {}
        for module, tests in self.results.items():
            module_passed = sum(1 for t in tests if t.status == "PASS")
            module_stats[module] = {
                "total": len(tests),
                "passed": module_passed,
                "failed": len(tests) - module_passed,
                "success_rate": (
                    f"{(module_passed / len(tests) * 100):.1f}" if tests else "0.0"
                ),
            }

        return {
            "execution_id": self._execution_dir.name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": f"{success_rate:.1f}",
                "total_modules": len(self.results),
            },
            "modules": {
                module: {
                    "stats": module_stats[module],
                    "tests": [
                        {
                            "name": r.test_name,
                            "status": r.status,
                            "duration": f"{r.duration:.2f}",
                            "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            "error_message": r.error_message,
                            "details": r.details,
                            "status_class": "pass" if r.status == "PASS" else "fail",
                        }
                        for r in tests
                    ],
                }
                for module, tests in self.results.items()
            },
        }

    def _generate_html_report(self):
        """Generate the HTML report using the template."""
        template_data = self._get_template_data()
        template = self.template_env.get_template("report.html")
        html_content = template.render(**template_data)

        html_file = self.execution_dir / "test_report.html"
        with open(html_file, "w") as f:
            f.write(html_content)

    def generate_summary(self):
        """Print execution summary to console."""
        template_data = self._get_template_data()
        summary = template_data["summary"]

        print("\nTest Execution Summary")
        print("=" * 50)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']}%")
        print(f"Total Modules: {summary['total_modules']}")

        print("\nModule Statistics:")
        for module, data in template_data["modules"].items():
            stats = data["stats"]
            print(f"\n{module}:")
            print(f"  Total: {stats['total']}")
            print(f"  Passed: {stats['passed']}")
            print(f"  Failed: {stats['failed']}")
            print(f"  Success Rate: {stats['success_rate']}%")

        print(f"\nDetailed report available at: {self.execution_dir}/test_report.html")
