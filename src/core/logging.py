# src/core/logging.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List


@dataclass
class CommandLog:
    """Represents a single command execution log."""

    node: str
    command: str
    exit_code: int
    output: str
    timestamp: datetime
    duration: float


class TestCommandLogger:
    """Manages command logging for test executions."""

    def __init__(self):
        self.logs: Dict[str, List[CommandLog]] = {}  # test_name -> [logs]

    def add_log(self, test_name: str, log: CommandLog):
        """Add a command log to a specific test."""
        if test_name not in self.logs:
            self.logs[test_name] = []
        self.logs[test_name].append(log)

    def get_logs(self, test_name: str) -> List[CommandLog]:
        """Get all logs for a specific test."""
        return self.logs.get(test_name, [])

    def clear_logs(self, test_name: str):
        """Clear logs for a specific test."""
        if test_name in self.logs:
            del self.logs[test_name]

    def to_dict(self) -> Dict:
        """Convert logs to dictionary format for reporting."""
        return {
            test_name: [
                {
                    "node": log.node,
                    "command": log.command,
                    "exit_code": log.exit_code,
                    "output": log.output,
                    "timestamp": log.timestamp.isoformat(),
                    "duration": log.duration,
                }
                for log in logs
            ]
            for test_name, logs in self.logs.items()
        }
