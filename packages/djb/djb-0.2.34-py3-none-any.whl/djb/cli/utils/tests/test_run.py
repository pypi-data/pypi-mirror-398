"""Tests for djb.cli.utils.run module."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from unittest.mock import patch

import click
import pytest

from djb.cli.utils.run import (
    _get_clean_env,
    _run_streaming_threads,
    check_cmd,
    run_cmd,
    run_streaming,
)


class TestGetCleanEnv:
    """Tests for _get_clean_env helper."""

    def test_returns_none_when_no_cwd(self):
        """Test returns None when cwd is None."""
        result = _get_clean_env(None)
        assert result is None

    def test_removes_virtual_env_when_cwd_provided(self, tmp_path):
        """Test removes VIRTUAL_ENV from environment when cwd is provided."""
        with patch.dict(os.environ, {"VIRTUAL_ENV": "/some/venv", "OTHER_VAR": "value"}):
            result = _get_clean_env(tmp_path)
            assert result is not None
            assert "VIRTUAL_ENV" not in result
            assert result["OTHER_VAR"] == "value"

    def test_works_without_virtual_env_set(self, tmp_path):
        """Test works when VIRTUAL_ENV is not in environment."""
        env_without_venv = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
        with patch.dict(os.environ, env_without_venv, clear=True):
            result = _get_clean_env(tmp_path)
            assert result is not None
            assert "VIRTUAL_ENV" not in result


class TestRunCmd:
    """Tests for run_cmd function."""

    def test_successful_command(self, tmp_path):
        """Test running a successful command."""
        result = run_cmd(["echo", "hello"], cwd=tmp_path)
        assert result.returncode == 0
        assert "hello" in result.stdout

    def test_successful_command_with_label(self, tmp_path):
        """Test running command with label logs correctly."""
        with patch("djb.cli.utils.run.logger") as mock_logger:
            result = run_cmd(["echo", "test"], cwd=tmp_path, label="Test command")
            assert result.returncode == 0
            mock_logger.next.assert_called_with("Test command")

    def test_successful_command_with_done_msg(self, tmp_path):
        """Test done message is logged on success."""
        with patch("djb.cli.utils.run.logger") as mock_logger:
            run_cmd(["echo", "test"], cwd=tmp_path, done_msg="All done!")
            mock_logger.done.assert_called_with("All done!")

    def test_quiet_mode_suppresses_logging(self, tmp_path):
        """Test quiet mode suppresses label and done_msg logging."""
        with patch("djb.cli.utils.run.logger") as mock_logger:
            run_cmd(
                ["echo", "test"],
                cwd=tmp_path,
                label="Should not log",
                done_msg="Should not log either",
                quiet=True,
            )
            mock_logger.next.assert_not_called()
            mock_logger.done.assert_not_called()

    def test_failed_command_with_halt_on_fail(self, tmp_path):
        """Test failed command raises ClickException when halt_on_fail=True."""
        with pytest.raises(click.ClickException):
            run_cmd(["false"], cwd=tmp_path, halt_on_fail=True)

    def test_failed_command_without_halt_on_fail(self, tmp_path):
        """Test failed command returns result when halt_on_fail=False."""
        result = run_cmd(["false"], cwd=tmp_path, halt_on_fail=False)
        assert result.returncode != 0

    def test_failed_command_logs_fail_msg(self, tmp_path):
        """Test failed command logs fail_msg when halt_on_fail=False."""
        with patch("djb.cli.utils.run.logger") as mock_logger:
            run_cmd(
                ["false"],
                cwd=tmp_path,
                halt_on_fail=False,
                fail_msg="Command failed!",
            )
            mock_logger.fail.assert_called_with("Command failed!")

    def test_failed_command_logs_stderr(self, tmp_path):
        """Test failed command logs stderr when halt_on_fail=False."""
        # Create a script that outputs to stderr
        script = tmp_path / "fail.sh"
        script.write_text("#!/bin/bash\necho 'error message' >&2\nexit 1")
        script.chmod(0o755)

        with patch("djb.cli.utils.run.logger") as mock_logger:
            run_cmd(
                [str(script)],
                cwd=tmp_path,
                halt_on_fail=False,
                fail_msg="Failed",
            )
            # Check that info was called with stderr content
            calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any("error message" in call for call in calls)

    def test_failed_command_with_label_in_error(self, tmp_path):
        """Test failed command includes label in error message."""
        with pytest.raises(click.ClickException) as exc_info:
            run_cmd(["false"], cwd=tmp_path, label="My command", halt_on_fail=True)
        assert "My command" in str(exc_info.value)


class TestCheckCmd:
    """Tests for check_cmd function."""

    def test_returns_true_for_successful_command(self, tmp_path):
        """Test returns True when command succeeds."""
        result = check_cmd(["true"], cwd=tmp_path)
        assert result is True

    def test_returns_false_for_failed_command(self, tmp_path):
        """Test returns False when command fails."""
        result = check_cmd(["false"], cwd=tmp_path)
        assert result is False

    def test_works_with_real_command(self, tmp_path):
        """Test with a real command that produces output."""
        result = check_cmd(["echo", "test"], cwd=tmp_path)
        assert result is True


class TestRunStreaming:
    """Tests for run_streaming function."""

    def test_captures_stdout(self, tmp_path):
        """Test captures stdout from command."""
        returncode, stdout, stderr = run_streaming(["echo", "hello world"], cwd=tmp_path)
        assert returncode == 0
        assert "hello world" in stdout

    def test_captures_stderr(self, tmp_path):
        """Test captures stderr from command."""
        script = tmp_path / "stderr.sh"
        script.write_text("#!/bin/bash\necho 'error output' >&2")
        script.chmod(0o755)

        returncode, stdout, stderr = run_streaming([str(script)], cwd=tmp_path)
        assert returncode == 0
        assert "error output" in stderr

    def test_returns_nonzero_for_failed_command(self, tmp_path):
        """Test returns non-zero code for failed command."""
        returncode, stdout, stderr = run_streaming(["false"], cwd=tmp_path)
        assert returncode != 0

    def test_logs_label_when_provided(self, tmp_path):
        """Test logs label when provided."""
        with patch("djb.cli.utils.run.logger") as mock_logger:
            run_streaming(["echo", "test"], cwd=tmp_path, label="Running test")
            mock_logger.next.assert_called_with("Running test")

    def test_handles_mixed_stdout_stderr(self, tmp_path):
        """Test handles interleaved stdout and stderr."""
        script = tmp_path / "mixed.sh"
        script.write_text(
            "#!/bin/bash\n"
            "echo 'stdout line 1'\n"
            "echo 'stderr line 1' >&2\n"
            "echo 'stdout line 2'\n"
        )
        script.chmod(0o755)

        returncode, stdout, stderr = run_streaming([str(script)], cwd=tmp_path)
        assert returncode == 0
        assert "stdout line 1" in stdout
        assert "stdout line 2" in stdout
        assert "stderr line 1" in stderr

    def test_combine_output_returns_two_tuple(self, tmp_path):
        """Test combine_output=True returns (returncode, combined)."""
        script = tmp_path / "mixed.sh"
        script.write_text("#!/bin/bash\n" "echo 'stdout output'\n" "echo 'stderr output' >&2\n")
        script.chmod(0o755)

        returncode, combined = run_streaming([str(script)], cwd=tmp_path, combine_output=True)
        assert returncode == 0
        assert "stdout output" in combined
        assert "stderr output" in combined


class TestRunStreamingThreads:
    """Tests for _run_streaming_threads (Windows fallback).

    These tests run on all platforms to ensure the Windows code path is tested.
    """

    def test_captures_stdout(self, tmp_path):
        """Test captures stdout from command."""
        process = subprocess.Popen(
            ["echo", "hello world"],
            cwd=tmp_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        result = _run_streaming_threads(process, combine_output=False, forward_stdin=False)
        assert len(result) == 3
        returncode, stdout, stderr = result
        assert returncode == 0
        assert "hello world" in stdout

    def test_captures_stderr(self, tmp_path):
        """Test captures stderr from command."""
        script = tmp_path / "stderr.sh"
        script.write_text("#!/bin/bash\necho 'error output' >&2")
        script.chmod(0o755)

        process = subprocess.Popen(
            [str(script)],
            cwd=tmp_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        result = _run_streaming_threads(process, combine_output=False, forward_stdin=False)
        assert len(result) == 3
        returncode, stdout, stderr = result
        assert returncode == 0
        assert "error output" in stderr

    def test_handles_mixed_stdout_stderr(self, tmp_path):
        """Test handles interleaved stdout and stderr."""
        script = tmp_path / "mixed.sh"
        script.write_text(
            "#!/bin/bash\n"
            "echo 'stdout line 1'\n"
            "echo 'stderr line 1' >&2\n"
            "echo 'stdout line 2'\n"
            "echo 'stderr line 2' >&2\n"
        )
        script.chmod(0o755)

        process = subprocess.Popen(
            [str(script)],
            cwd=tmp_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        result = _run_streaming_threads(process, combine_output=False, forward_stdin=False)
        assert len(result) == 3
        returncode, stdout, stderr = result
        assert returncode == 0
        assert "stdout line 1" in stdout
        assert "stdout line 2" in stdout
        assert "stderr line 1" in stderr

    def test_combine_output(self, tmp_path):
        """Test combine_output=True returns (returncode, combined)."""
        script = tmp_path / "mixed.sh"
        script.write_text("#!/bin/bash\necho 'stdout'\necho 'stderr' >&2\n")
        script.chmod(0o755)

        process = subprocess.Popen(
            [str(script)],
            cwd=tmp_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        result = _run_streaming_threads(process, combine_output=True, forward_stdin=False)
        assert len(result) == 2
        returncode, combined = result
        assert returncode == 0
        assert "stdout" in combined
        assert "stderr" in combined


class TestRunStreamingThreadsStdinForwarding:
    """Tests for stdin forwarding in _run_streaming_threads (Windows fallback).

    Uses PTYs to simulate a real terminal and test interactive stdin forwarding.
    All scripts use short timeouts (1-2 seconds) to avoid hanging if forwarding fails.

    Note on timing: We use a 100ms initial delay before sending input to give
    the subprocess time to start and set up its stdin reading.
    """

    # Initial delay before first input (gives process time to start)
    INITIAL_DELAY = 0.1  # 100ms
    # Delay between repeated inputs
    RETRY_DELAY = 0.05  # 50ms

    @pytest.mark.skipif(not hasattr(os, "openpty"), reason="PTY not available")
    def test_stdin_forwarding(self, tmp_path, pty_stdin):
        """Test stdin forwarding works in threaded variant."""
        master_fd = pty_stdin

        script = tmp_path / "echo_stdin.sh"
        script.write_text(
            "#!/bin/bash\n"
            "if read -t 2 -r line; then\n"
            '  echo "Got: $line"\n'
            "else\n"
            "  echo 'TIMEOUT' >&2\n"
            "  exit 1\n"
            "fi\n"
        )
        script.chmod(0o755)

        stop_event = threading.Event()

        def send_input_repeatedly():
            time.sleep(self.INITIAL_DELAY)
            while not stop_event.is_set():
                try:
                    os.write(master_fd, b"threaded input\n")
                except OSError:
                    break
                time.sleep(self.RETRY_DELAY)

        input_thread = threading.Thread(target=send_input_repeatedly)
        input_thread.start()

        process = subprocess.Popen(
            [str(script)],
            cwd=tmp_path,
            stdin=sys.stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        result = _run_streaming_threads(process, combine_output=False, forward_stdin=True)

        stop_event.set()
        input_thread.join(timeout=1)

        assert len(result) == 3
        returncode, stdout, stderr = result
        assert returncode == 0, f"Script failed: stderr={stderr!r}"
        assert "Got: threaded input" in stdout

    @pytest.mark.skipif(not hasattr(os, "openpty"), reason="PTY not available")
    def test_stdin_forwarding_confirmation_prompt(self, tmp_path, pty_stdin):
        """Test stdin forwarding works for confirmation prompts."""
        master_fd = pty_stdin

        script = tmp_path / "confirm.sh"
        script.write_text(
            "#!/bin/bash\n"
            "echo 'Continue? [y/n]'\n"
            "if read -t 2 -r answer; then\n"
            '  if [ "$answer" = "y" ]; then\n'
            "    echo 'Confirmed!'\n"
            "  else\n"
            "    echo 'Cancelled.'\n"
            "  fi\n"
            "else\n"
            "  echo 'TIMEOUT' >&2\n"
            "  exit 1\n"
            "fi\n"
        )
        script.chmod(0o755)

        stop_event = threading.Event()

        def send_input_repeatedly():
            time.sleep(self.INITIAL_DELAY)
            while not stop_event.is_set():
                try:
                    os.write(master_fd, b"y\n")
                except OSError:
                    break
                time.sleep(self.RETRY_DELAY)

        input_thread = threading.Thread(target=send_input_repeatedly)
        input_thread.start()

        process = subprocess.Popen(
            [str(script)],
            cwd=tmp_path,
            stdin=sys.stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        result = _run_streaming_threads(process, combine_output=False, forward_stdin=True)

        stop_event.set()
        input_thread.join(timeout=1)

        assert len(result) == 3
        returncode, stdout, stderr = result
        assert returncode == 0, f"Script failed: stderr={stderr!r}"
        assert "Continue? [y/n]" in stdout
        assert "Confirmed!" in stdout

    def test_stdin_forwarding_disabled_gracefully_when_not_available(self, tmp_path):
        """Test that stdin forwarding is disabled gracefully when stdin is not a real file."""
        script = tmp_path / "simple.sh"
        script.write_text("#!/bin/bash\necho 'hello'")
        script.chmod(0o755)

        process = subprocess.Popen(
            [str(script)],
            cwd=tmp_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        result = _run_streaming_threads(process, combine_output=False, forward_stdin=True)

        assert len(result) == 3
        returncode, stdout, stderr = result
        assert returncode == 0
        assert "hello" in stdout


class TestRunStreamingStdinForwarding:
    """Tests for stdin forwarding in run_streaming.

    Uses PTYs to simulate a real terminal and test interactive stdin forwarding.
    All scripts use short timeouts (1-2 seconds) to avoid hanging if forwarding fails.

    Note on timing: We use a 100ms initial delay before sending input to give
    the subprocess time to start and set up its stdin reading. The loop then
    sends input every 50ms. With a 2 second script timeout, this gives 40
    opportunities to deliver input, making these tests robust against timing
    variations on slow systems.
    """

    # Initial delay before first input (gives process time to start)
    INITIAL_DELAY = 0.1  # 100ms
    # Delay between repeated inputs
    RETRY_DELAY = 0.05  # 50ms

    @pytest.mark.skipif(not hasattr(os, "openpty"), reason="PTY not available")
    def test_stdin_forwarding_with_pty(self, tmp_path, pty_stdin):
        """Test stdin is forwarded to subprocess using PTY."""
        master_fd = pty_stdin

        # Create a script that reads from stdin with a short timeout
        script = tmp_path / "echo_stdin.sh"
        script.write_text(
            "#!/bin/bash\n"
            "# Use timeout to avoid hanging if stdin forwarding fails\n"
            "if read -t 2 -r line; then\n"
            '  echo "Got: $line"\n'
            "else\n"
            "  echo 'TIMEOUT: no input received' >&2\n"
            "  exit 1\n"
            "fi\n"
        )
        script.chmod(0o755)

        stop_event = threading.Event()

        def send_input_repeatedly():
            """Write input repeatedly until stopped, in case thread starts late."""
            time.sleep(self.INITIAL_DELAY)
            while not stop_event.is_set():
                try:
                    os.write(master_fd, b"hello from pty\n")
                except OSError:
                    break
                time.sleep(self.RETRY_DELAY)

        input_thread = threading.Thread(target=send_input_repeatedly)
        input_thread.start()

        returncode, stdout, stderr = run_streaming([str(script)], cwd=tmp_path, forward_stdin=True)

        stop_event.set()
        input_thread.join(timeout=1)

        assert returncode == 0, f"Script failed: stdout={stdout!r}, stderr={stderr!r}"
        assert "Got: hello from pty" in stdout, f"Expected output not found: {stdout!r}"

    @pytest.mark.skipif(not hasattr(os, "openpty"), reason="PTY not available")
    def test_stdin_forwarding_confirmation_prompt(self, tmp_path, pty_stdin):
        """Test stdin forwarding works for confirmation prompts.

        Uses a thread to write input after a short delay, simulating a user
        typing after seeing the prompt.
        """
        master_fd = pty_stdin

        # Create a script that asks for confirmation with timeout
        script = tmp_path / "confirm.sh"
        script.write_text(
            "#!/bin/bash\n"
            "echo 'Continue? [y/n]'\n"
            "# Use timeout to avoid hanging if stdin forwarding fails\n"
            "if read -t 2 -r answer; then\n"
            '  if [ "$answer" = "y" ]; then\n'
            "    echo 'Confirmed!'\n"
            "  else\n"
            "    echo 'Cancelled.'\n"
            "  fi\n"
            "else\n"
            "  echo 'TIMEOUT: no input received' >&2\n"
            "  exit 1\n"
            "fi\n"
        )
        script.chmod(0o755)

        stop_event = threading.Event()

        def send_input_repeatedly():
            """Write input repeatedly until stopped, in case thread starts late."""
            time.sleep(self.INITIAL_DELAY)
            while not stop_event.is_set():
                try:
                    os.write(master_fd, b"y\n")
                except OSError:
                    break
                time.sleep(self.RETRY_DELAY)

        input_thread = threading.Thread(target=send_input_repeatedly)
        input_thread.start()

        returncode, stdout, stderr = run_streaming([str(script)], cwd=tmp_path, forward_stdin=True)

        stop_event.set()
        input_thread.join(timeout=1)

        assert returncode == 0, f"Script failed: stdout={stdout!r}, stderr={stderr!r}"
        assert "Continue? [y/n]" in stdout, f"Prompt not found: {stdout!r}"
        assert "Confirmed!" in stdout, f"Confirmation not found: {stdout!r}"

    def test_stdin_forwarding_disabled_gracefully_when_not_available(self, tmp_path):
        """Test that stdin forwarding is disabled gracefully when stdin is not a real file."""
        # This test runs under pytest's captured stdin, which doesn't have a fileno
        # The code should handle this gracefully
        script = tmp_path / "simple.sh"
        script.write_text("#!/bin/bash\necho 'hello'")
        script.chmod(0o755)

        # This should not raise even though stdin is captured by pytest
        returncode, stdout, stderr = run_streaming([str(script)], cwd=tmp_path, forward_stdin=True)

        assert returncode == 0
        assert "hello" in stdout
