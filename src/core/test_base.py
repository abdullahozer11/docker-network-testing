# src/core/test_base.py

import time
from datetime import datetime
from typing import Dict, Tuple

import docker
from docker.errors import NotFound

from src.core.config import ConfigManager
from src.core.logging import CommandLog, TestCommandLogger
from src.core.reporter import TestReporter, TestResult


class NetworkTestBase:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.config_manager = ConfigManager()
        self.reporter = TestReporter()
        self.current_module = self.__class__.__module__.split(".")[-1]
        self.command_logger = TestCommandLogger()
        self.current_test_name = None  # Add this to track current test

    def _execute_command(
        self, container, command: str, node_name: str
    ) -> Tuple[int, str]:
        """Execute a command in a container and log it."""
        start_time = time.time()

        try:
            result = container.exec_run(command)
            duration = time.time() - start_time

            if self.current_test_name:  # Use the tracked test name
                log = CommandLog(
                    node=node_name,
                    command=command,
                    exit_code=result.exit_code,
                    output=result.output.decode("utf-8"),
                    timestamp=datetime.now(),
                    duration=duration,
                )

                self.command_logger.add_log(self.current_test_name, log)
            else:
                print("No current test name available for logging command")

            return result.exit_code, result.output.decode("utf-8")
        except Exception as e:
            print(f"Error executing command on {node_name}: {str(e)}")
            raise

    def run_test(self, test_name: str, test_func, *args, **kwargs):
        """Run a test with command logging."""
        self.current_test_name = test_name  # Set the current test name
        start_time = time.time()
        error_message = None
        status = "PASS"

        try:
            test_func(*args, **kwargs)
        except Exception as e:
            status = "FAIL"
            error_message = str(e)
            print(f"Test failed: {str(e)}")
        finally:
            duration = time.time() - start_time

            # Get command logs for this test
            test_logs = self.command_logger.get_logs(test_name)

            # Convert command logs to dictionary format
            command_logs = [
                {
                    "node": log.node,
                    "command": log.command,
                    "exit_code": log.exit_code,
                    "output": log.output,
                    "timestamp": log.timestamp.isoformat(),
                    "duration": log.duration,
                }
                for log in test_logs
            ]

            details = {"command_logs": command_logs}

            result = TestResult(
                module_name=self.current_module,
                test_name=test_name,
                status=status,
                duration=duration,
                timestamp=datetime.now(),
                error_message=error_message,
                details=details,
            )

            self.reporter.add_result(self.current_module, result)

            # Clear logs for this test
            self.command_logger.clear_logs(test_name)
            self.current_test_name = None  # Clear the current test name

    def verify_interface(self, node: str, interface: str) -> Dict[str, str]:
        """Verify interface configuration with logging."""
        cmd = f"ip addr show {interface}"

        try:
            container = self.docker_client.containers.get(
                f"network-test-framework-{node}-1"
            )
            exit_code, output = self._execute_command(container, cmd, node)

            if exit_code != 0:
                raise Exception(f"Failed to get interface information: {output}")

            return {"status": "UP" if "UP" in output else "DOWN", "details": output}
        except NotFound:
            raise Exception(f"Container {node} not found")

    def check_routing_table(self, node: str) -> Dict[str, str]:
        """Check routing table with logging."""
        cmd = "ip route"

        try:
            container = self.docker_client.containers.get(
                f"network-test-framework-{node}-1"
            )
            exit_code, output = self._execute_command(container, cmd, node)

            if exit_code != 0:
                raise Exception(f"Failed to get routing table: {output}")

            return {"status": "SUCCESS", "routes": output}
        except NotFound:
            raise Exception(f"Container {node} not found")
