from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

import pexpect


class ShellAdapter:
    """
    A class for executing shell commands and logging their output, with support for command aliases and environment variables.

    It executes shell commands, logs the output, and handles errors.
    """

    def __init__(self: ShellAdapter, *, suppress_logging: bool = False) -> None:
        """
        Initialize the ShellCommandExecutor and set up the logger.
        """
        self.aliases: dict[str, str] = {}
        self.child = None
        self.is_logging = not suppress_logging

    def alias(self: ShellAdapter, alias: str, command: str) -> None:
        """
        Define a command alias.

        :param alias: The alias name to define.
        :param command: The command string that the alias maps to.
        """
        self.aliases[alias] = command

    def exe(
        self: ShellAdapter,
        command: str,
        working_dir: Path | None,
    ) -> tuple[str, str]:
        """
        Execute a shell command and log its output.

        This method runs the given command, logs stdout as info and stderr as error.
        If the command fails, it logs both stdout and stderr.

        :param command: A string representing the command to execute.
        :param working_dir: Path to directory where the command will be executed.
        :raises subprocess.CalledProcessError: If the command execution fails.
        """
        expanded_command = self._expand_alias(command)
        expanded_command = self._expand_environment_variables(expanded_command)

        cwd = Path.cwd()

        if working_dir and not Path(working_dir).is_dir():
            cwd = Path(working_dir)

        try:
            result = subprocess.run(
                expanded_command,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                env=os.environ.copy(),  # Use the current environment variables
            )
            if self.is_logging:
                self._log_normal_output(result.stdout, result.stderr)
        except subprocess.CalledProcessError as e:
            if self.is_logging:
                self._log_error_output(e)
            return str(e), ""
        else:
            return result.stderr, result.stdout

    def interact(
        self: ShellAdapter, command: str, prompt: str, working_dir: Path | None
    ) -> tuple[str, str]:
        expanded_command = self._expand_alias(command)
        expanded_command = self._expand_environment_variables(expanded_command)

        cwd = Path.cwd()

        if working_dir and not Path(working_dir).is_dir():
            cwd = Path(working_dir)

        try:
            self.child = pexpect.spawn(expanded_command, encoding="utf-8", cwd=cwd)

            while True:
                index = self.child.expect(
                    [
                        prompt,
                        pexpect.EOF,
                        pexpect.TIMEOUT,
                    ],
                )

                if index == 0:
                    print(
                        self.child.before.decode("utf-8")
                        if isinstance(self.child.before, bytes)
                        else self.child.before,
                    )
                    user_input = input(prompt)
                    self.child.sendline(user_input)
                elif index == 1:
                    break
                elif index == 2:
                    logging.error("Timeout occurred.")
                    break

        except pexpect.ExceptionPexpect as _:
            logging.exception("An error occurred")
        finally:
            if self.child:
                self.child.close()

    def is_command_available(self: ShellAdapter, command: str) -> bool:
        """
        Check if a given command is available in the system PATH.

        :param command: The name of the command to check.
        :return: True if the command exists, False otherwise.
        """
        return shutil.which(command) is not None

    def _expand_alias(self: ShellAdapter, command: str) -> str:
        """
        Expand aliases in the command string.

        :param command: The command string potentially containing aliases.
        :return: The command string with any aliases expanded.
        """
        for alias, cmd in self.aliases.items():
            if command.startswith(alias):
                return command.replace(alias, cmd, 1)
        return command

    def _expand_environment_variables(self: ShellAdapter, command: str) -> str:
        """
        Expand environment variables in the command string.

        :param command: The command string potentially containing environment variables in ${VAR} format.
        :return: The command string with environment variables expanded.
        """
        return os.path.expandvars(command)

    def _log_normal_output(
        self: ShellAdapter,
        stdout: None | str,
        stderr: None | str,
    ) -> None:
        """
        Log the successful output of a command.

        :param stdout: The standard output of the command.
        :param stderr: The standard error output of the command.
        """
        if stdout:
            logging.info(stdout)
        if stderr:
            logging.error(stderr)

    def _log_error_output(self: ShellAdapter, e: subprocess.CalledProcessError) -> None:
        """
        Log the error output of a failed command execution.

        :param e: The exception raised for the failed command execution.
        """
        logging.error("Command failed with return code %s", e.returncode)
        if e.stdout:
            logging.error("STDOUT: %s", e.stdout)
        if e.stderr:
            logging.error("STDERR: %s", e.stderr)
