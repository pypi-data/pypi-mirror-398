from enum import IntEnum


class ExitCode(IntEnum):
    """An enumeration of common exit codes used in shell commands."""

    SUCCESS = 0
    """An exit code indicating success."""
    FAILURE = 1
    """An exit code indicating a general error."""
    MISUSE_OF_SHELL_COMMAND = 2
    """An exit code indicating misuse of a shell command."""
    COMMAND_CANNOT_EXECUTE = 126
    """An exit code indicating that the command invoked cannot execute."""
    COMMAND_NOT_FOUND = 127
    """An exit code indicating that the command was not found."""
    INVALID_ARGUMENT_TO_EXIT = 128
    """An exit code indicating an invalid argument to exit."""
    SCRIPT_TERMINATED_BY_CONTROL_C = 130
    """An exit code indicating that the script was terminated by Control-C."""
    PROCESS_KILLED_BY_SIGKILL = 137
    """An exit code indicating that the process was killed by SIGKILL (9)."""
    SEGMENTATION_FAULT = 139
    """An exit code indicating a segmentation fault (core dumped)."""
    PROCESS_TERMINATED_BY_SIGTERM = 143
    """An exit code indicating that the process was terminated by SIGTERM (15)."""
    EXIT_STATUS_OUT_OF_RANGE = 255
    """An exit code indicating that the exit status is out of range."""
