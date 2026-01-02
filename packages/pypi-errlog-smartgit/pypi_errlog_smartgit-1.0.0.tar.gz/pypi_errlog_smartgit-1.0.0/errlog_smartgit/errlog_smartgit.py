"""SmartGit Error Handler with detailed feedback"""

import subprocess
import sys
from datetime import datetime
from typing import Optional, List
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


class SmartGitErr:
    """SmartGit Error Handler - provides detailed feedback"""

    def __init__(self, path: Optional[str] = None):
        self.path = path
        self.process_log = None

    def all(self, no_version: bool = False, no_deploy: bool = False) -> None:
        """Complete workflow with detailed feedback"""
        args = []
        if no_version:
            args.append("-no-version")
        if no_deploy:
            args.append("-no-deploy")

        self._execute_command("smartgit all", args, 10)

    def repo(self, project_name: str) -> None:
        """Create repository with detailed feedback"""
        self._execute_command(f"smartgit repo {project_name}", [], 3)

    def ignore(self, files: List[str]) -> None:
        """Ignore files with detailed feedback"""
        self._execute_command(f"smartgit ignore {', '.join(files)}", [], 2)

    def include(self, files: List[str]) -> None:
        """Include files with detailed feedback"""
        self._execute_command(f"smartgit include {', '.join(files)}", [], 2)

    def version(
        self, project_name: str, version_name: str, files: Optional[List[str]] = None
    ) -> None:
        """Create version with detailed feedback"""
        self._execute_command(
            f"smartgit version {project_name} {version_name}", [], 3
        )

    def addfile(
        self, project_name: str, version_name: str, files: List[str]
    ) -> None:
        """Add files to version with detailed feedback"""
        self._execute_command(
            f"smartgit addfile {project_name} {version_name}", [], 3
        )

    def lab(self, project_name: Optional[str] = None) -> None:
        """Activate GitLab mode with detailed feedback"""
        self._execute_command(f"smartgit lab {project_name or ''}", [], 2)

    def shortcut(self, shortcut_name: str, command: str) -> None:
        """Create shortcut with detailed feedback"""
        self._execute_command(f"smartgit shortcut {shortcut_name}", [], 3)

    def _execute_command(
        self, command: str, args: List[str], total_steps: int
    ) -> None:
        """Execute command with detailed error handling"""
        self._start_process(command, total_steps)

        try:
            for i in range(1, total_steps + 1):
                self._log_step(i, f"Executing step {i}/{total_steps}")

            # Execute the actual smartgit command
            full_command = f"{command} {' '.join(args)}".strip()
            result = subprocess.run(
                full_command, shell=True, capture_output=False, text=True
            )

            self._end_process(result.returncode == 0)
            if result.returncode == 0:
                self._print_success()
            else:
                self._print_error(f"Command failed with code {result.returncode}")
        except Exception as error:
            self._end_process(False)
            self._print_error(str(error))

    def _start_process(self, command: str, total_steps: int) -> None:
        """Start process logging"""
        self.process_log = {
            "command": command,
            "start_time": datetime.now(),
            "steps": [],
            "success": False,
            "total_duration": 0,
        }

        print(f"\n{Fore.CYAN}{Style.BRIGHT}▶ {command}{Style.RESET_ALL}")
        print(f"{Style.DIM}Total steps: {total_steps}{Style.RESET_ALL}\n")

    def _log_step(self, step_number: int, message: str) -> None:
        """Log a step"""
        if not self.process_log:
            return

        self.process_log["steps"].append(
            {
                "step": step_number,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }
        )

        progress = f"[{step_number}/{len(self.process_log['steps'])}]"
        print(f"{Fore.BLUE}{progress}{Style.RESET_ALL} {Style.DIM}{message}{Style.RESET_ALL}")

    def _end_process(self, success: bool) -> None:
        """End process logging"""
        if not self.process_log:
            return

        end_time = datetime.now()
        self.process_log["success"] = success
        self.process_log["total_duration"] = (
            end_time - self.process_log["start_time"]
        ).total_seconds() * 1000

    def _print_success(self) -> None:
        """Print success message"""
        if not self.process_log:
            return

        print(f"\n{Fore.GREEN}{Style.BRIGHT}✓ Success{Style.RESET_ALL}")
        print(
            f"{Style.DIM}Completed in {self.process_log['total_duration']:.0f}ms{Style.RESET_ALL}\n"
        )

    def _print_error(self, error_message: str) -> None:
        """Print error message"""
        if not self.process_log:
            return

        print(f"\n{Fore.RED}{Style.BRIGHT}✗ Error{Style.RESET_ALL}")
        print(f"{Fore.RED}{error_message}{Style.RESET_ALL}")
        print(
            f"{Style.DIM}Failed after {self.process_log['total_duration']:.0f}ms{Style.RESET_ALL}\n"
        )
