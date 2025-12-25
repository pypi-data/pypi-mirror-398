import subprocess

import pytest
from mat3ra.utils import command as utils
from mat3ra.utils.command import TIMEOUT_RETURNCODE

COMMAND_TO_SUCCEED = "echo 'Hello, World!'"
COMMAND_TO_FAIL = "false"
COMMAND_TO_TIMEOUT = "sleep 10"


def test_run_command_to_succeed():
    retcode, stdout, stderr = utils.run_command(COMMAND_TO_SUCCEED)
    assert retcode == 0
    assert stdout == "Hello, World!\n"
    assert stderr == ""


def test_run_command_failure(monkeypatch):
    # Define a mock function to replace subprocess.Popen
    class MockPopen:
        def __init__(self, *args, **kwargs):
            self._terminated = None
            self.returncode = 1  # Simulate a failure
            self.args = args

        def communicate(self):
            return "", "error message"  # Simulate empty stdout and error in stderr

        def terminate(self):
            self._terminated = True  # Flag to indicate terminate was called
            self.returncode = -1  # Simulate timeout behavior with a returncode

    # Use monkeypatch to replace subprocess.Popen with MockPopen
    monkeypatch.setattr(subprocess, "Popen", MockPopen)

    # Run the test, expecting a RuntimeError due to command failure
    with pytest.raises(RuntimeError):
        utils.run_command(COMMAND_TO_FAIL)


def test_run_command_to_timeout():
    with pytest.raises(RuntimeError):
        retcode, stdout, stderr = utils.run_command(COMMAND_TO_TIMEOUT, timeout=1)
        assert retcode == TIMEOUT_RETURNCODE
        assert stdout == ""
        assert stderr == "ERROR: command timed out."
