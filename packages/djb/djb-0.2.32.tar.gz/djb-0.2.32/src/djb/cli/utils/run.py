"""Functions for running shell commands with streaming output."""

from __future__ import annotations

import os
import select
import subprocess
import sys
import threading
from pathlib import Path
from typing import BinaryIO, Literal, overload

import click

from djb.core.logging import get_logger

logger = get_logger(__name__)

# select.poll() is not available on Windows
_HAS_POLL = hasattr(select, "poll")

# Buffer size for reading subprocess output
_READ_BUFFER_SIZE = 4096


def _get_clean_env(cwd: Path | None) -> dict[str, str] | None:
    """Get environment with VIRTUAL_ENV cleared if running in a different directory.

    When running commands in a different project directory (e.g., djb editable from host),
    the inherited VIRTUAL_ENV would point to the wrong venv and cause uv to emit:

        warning: `VIRTUAL_ENV=...` does not match the project environment path `.venv`
        and will be ignored; use `--active` to target the active environment instead

    Clearing VIRTUAL_ENV lets uv auto-detect the correct .venv for the target directory.
    """
    if cwd is None:
        return None
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    return env


def run_cmd(
    cmd: list[str],
    cwd: Path | None = None,
    label: str | None = None,
    done_msg: str | None = None,
    fail_msg: str | None = None,
    halt_on_fail: bool = True,
    quiet: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a shell command with optional error handling.

    Args:
        cmd: Command and arguments to run
        cwd: Working directory
        label: Human-readable label (logged with logger.next)
        done_msg: Success message (logged with logger.done)
        fail_msg: Failure message (logged with logger.fail if halt_on_fail=False)
        halt_on_fail: Whether to raise ClickException on failure
        quiet: Suppress all logging output (except for halt_on_fail errors)

    Returns:
        CompletedProcess with stdout/stderr as text
    """
    if label and not quiet:
        logger.next(label)
    logger.debug(f"Executing: {' '.join(cmd)}")
    env = _get_clean_env(cwd)
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        if halt_on_fail:
            logger.error(f"{label or 'Command'} failed with exit code {result.returncode}")
            if result.stderr:
                logger.debug(result.stderr)
            raise click.ClickException(f"{label or 'Command'} failed")
        elif fail_msg and not quiet:
            logger.fail(fail_msg)
            if result.stderr:
                logger.info(f"  {result.stderr.strip()}")
    if done_msg and result.returncode == 0 and not quiet:
        logger.done(done_msg)
    return result


def check_cmd(cmd: list[str], cwd: Path | None = None) -> bool:
    """Check if a command succeeds (returns True if exit code is 0).

    Useful for checking if something is installed or available.
    """
    result = subprocess.run(cmd, cwd=cwd, capture_output=True)
    return result.returncode == 0


@overload
def run_streaming(
    cmd: list[str],
    cwd: Path | None = ...,
    label: str | None = ...,
    *,
    combine_output: Literal[True],
    forward_stdin: bool = ...,
) -> tuple[int, str]: ...


@overload
def run_streaming(
    cmd: list[str],
    cwd: Path | None = ...,
    label: str | None = ...,
    combine_output: Literal[False] = ...,
    forward_stdin: bool = ...,
) -> tuple[int, str, str]: ...


def run_streaming(
    cmd: list[str],
    cwd: Path | None = None,
    label: str | None = None,
    combine_output: bool = False,
    forward_stdin: bool = True,
) -> tuple[int, str, str] | tuple[int, str]:
    """Run a command while streaming output to terminal and capturing it.

    Uses select.poll() (Unix) or threads (Windows) for non-blocking I/O to stream
    both stdout and stderr to the terminal in real-time while capturing them.
    Terminal stdin is forwarded to the subprocess by default, enabling interactive
    commands (e.g., confirmation prompts).

    Args:
        cmd: Command and arguments to run
        cwd: Working directory
        label: Optional label to print before running
        combine_output: If True, return combined stdout+stderr as single string
        forward_stdin: If True (default), forward terminal stdin to the subprocess

    Returns:
        If combine_output=False: Tuple of (return_code, captured_stdout, captured_stderr)
        If combine_output=True: Tuple of (return_code, combined_output)
    """
    if label:
        logger.next(label)

    env = _get_clean_env(cwd)
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdin=subprocess.PIPE if forward_stdin else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert process.stdout is not None
    assert process.stderr is not None

    if _HAS_POLL:
        return _run_streaming_poll(process, combine_output, forward_stdin)
    else:
        return _run_streaming_threads(process, combine_output, forward_stdin)


def _run_streaming_poll(
    process: subprocess.Popen[bytes],
    combine_output: bool,
    forward_stdin: bool,
) -> tuple[int, str, str] | tuple[int, str]:
    """Stream output using select.poll() (Unix).

    When forward_stdin=True, also monitors terminal stdin and forwards input
    to the subprocess, enabling interactive commands like confirmation prompts.
    """
    assert process.stdout is not None
    assert process.stderr is not None

    # Get file descriptors for polling
    stdout_fd = process.stdout.fileno()
    stderr_fd = process.stderr.fileno()

    # Get stdin fd if forwarding is enabled and stdin is a real file
    stdin_fd: int | None = None
    proc_stdin_fd: int | None = None
    if forward_stdin and process.stdin:
        try:
            stdin_fd = sys.stdin.fileno()
            proc_stdin_fd = process.stdin.fileno()
        except (OSError, ValueError):
            # stdin is not a real file (e.g., pytest captures it)
            pass

    # Set up polling
    poller = select.poll()
    poller.register(stdout_fd, select.POLLIN)
    poller.register(stderr_fd, select.POLLIN)
    if stdin_fd is not None:
        poller.register(stdin_fd, select.POLLIN)

    stdout_chunks: list[bytes] = []
    stderr_chunks: list[bytes] = []
    output_fds = {stdout_fd, stderr_fd}
    stdin_open = stdin_fd is not None

    while output_fds:
        # Poll with 100ms timeout
        events = poller.poll(100)

        for fd, event in events:
            if event & select.POLLIN:
                if stdin_fd is not None and fd == stdin_fd:
                    # Read from terminal stdin and forward to subprocess
                    chunk = os.read(fd, _READ_BUFFER_SIZE)
                    if chunk and proc_stdin_fd is not None:
                        try:
                            os.write(proc_stdin_fd, chunk)
                        except OSError:
                            # Process stdin closed, stop forwarding
                            if stdin_open:
                                poller.unregister(stdin_fd)
                                stdin_open = False
                    elif not chunk and stdin_open:
                        # EOF on terminal stdin, close process stdin
                        if process.stdin:
                            process.stdin.close()
                        poller.unregister(stdin_fd)
                        stdin_open = False
                else:
                    # Read from subprocess stdout/stderr
                    chunk = os.read(fd, _READ_BUFFER_SIZE)
                    if chunk:
                        # Write to appropriate output stream
                        if fd == stdout_fd:
                            sys.stdout.buffer.write(chunk)
                            sys.stdout.buffer.flush()
                            stdout_chunks.append(chunk)
                        else:
                            sys.stderr.buffer.write(chunk)
                            sys.stderr.buffer.flush()
                            stderr_chunks.append(chunk)
                    else:
                        # EOF on this fd
                        poller.unregister(fd)
                        output_fds.discard(fd)
            elif event & (select.POLLHUP | select.POLLERR):
                if fd == stdin_fd:
                    if stdin_open:
                        poller.unregister(fd)
                        stdin_open = False
                else:
                    poller.unregister(fd)
                    output_fds.discard(fd)

        # Check if process has exited
        if process.poll() is not None and not events:
            # Process done and no more data, drain any remaining
            for fd in list(output_fds):
                try:
                    while True:
                        chunk = os.read(fd, _READ_BUFFER_SIZE)
                        if not chunk:
                            break
                        if fd == stdout_fd:
                            sys.stdout.buffer.write(chunk)
                            sys.stdout.buffer.flush()
                            stdout_chunks.append(chunk)
                        else:
                            sys.stderr.buffer.write(chunk)
                            sys.stderr.buffer.flush()
                            stderr_chunks.append(chunk)
                except OSError:
                    pass
                poller.unregister(fd)
                output_fds.discard(fd)

    # Clean up stdin polling if still registered
    if stdin_open and stdin_fd is not None:
        try:
            poller.unregister(stdin_fd)
        except KeyError:
            pass

    process.wait()
    stdout = b"".join(stdout_chunks).decode(errors="replace")
    stderr = b"".join(stderr_chunks).decode(errors="replace")
    if combine_output:
        return process.returncode, stdout + stderr
    return process.returncode, stdout, stderr


def _run_streaming_threads(
    process: subprocess.Popen[bytes],
    combine_output: bool,
    forward_stdin: bool,
) -> tuple[int, str, str] | tuple[int, str]:
    """Stream output using threads (Windows fallback).

    On Windows, select.poll() is not available and select.select() only works
    with sockets, not pipes. This implementation uses threads to read from
    stdout and stderr concurrently.

    When forward_stdin=True, an additional thread forwards terminal stdin to
    the subprocess for interactive commands.
    """
    assert process.stdout is not None
    assert process.stderr is not None

    stdout_chunks: list[bytes] = []
    stderr_chunks: list[bytes] = []
    lock = threading.Lock()
    stdin_stop = threading.Event()

    def read_stream(
        stream: BinaryIO,
        chunks: list[bytes],
        output_buffer: BinaryIO,
    ) -> None:
        """Read from stream and write to output buffer."""
        while True:
            chunk = stream.read(_READ_BUFFER_SIZE)
            if not chunk:
                break
            with lock:
                output_buffer.write(chunk)
                output_buffer.flush()
                chunks.append(chunk)

    def forward_stdin_thread() -> None:
        """Forward terminal stdin to subprocess stdin."""
        assert process.stdin is not None
        try:
            while not stdin_stop.is_set():
                # Read from terminal stdin (blocking)
                # Use read1 if available (BufferedReader), otherwise read
                if hasattr(sys.stdin.buffer, "read1"):
                    chunk = sys.stdin.buffer.read1(_READ_BUFFER_SIZE)  # type: ignore[attr-defined]
                else:
                    chunk = sys.stdin.buffer.read(_READ_BUFFER_SIZE)
                if not chunk:
                    break
                try:
                    process.stdin.write(chunk)
                    process.stdin.flush()
                except (OSError, BrokenPipeError):
                    # Process stdin closed
                    break
        except Exception:
            pass
        finally:
            try:
                if process.stdin:
                    process.stdin.close()
            except Exception:
                pass

    # Check if stdin forwarding is possible (stdin must be a real file)
    can_forward_stdin = False
    if forward_stdin and process.stdin:
        try:
            sys.stdin.fileno()  # Will raise if stdin is captured/redirected
            can_forward_stdin = True
        except (OSError, ValueError):
            pass

    stdout_thread = threading.Thread(
        target=read_stream,
        args=(process.stdout, stdout_chunks, sys.stdout.buffer),
    )
    stderr_thread = threading.Thread(
        target=read_stream,
        args=(process.stderr, stderr_chunks, sys.stderr.buffer),
    )

    threads = [stdout_thread, stderr_thread]

    if can_forward_stdin:
        stdin_thread = threading.Thread(target=forward_stdin_thread, daemon=True)
        threads.append(stdin_thread)

    for t in threads:
        t.start()

    # Wait for output threads (stdin thread is daemon, will be stopped)
    stdout_thread.join()
    stderr_thread.join()

    # Signal stdin thread to stop
    stdin_stop.set()

    process.wait()
    stdout = b"".join(stdout_chunks).decode(errors="replace")
    stderr = b"".join(stderr_chunks).decode(errors="replace")
    if combine_output:
        return process.returncode, stdout + stderr
    return process.returncode, stdout, stderr
