#!/usr/bin/env python3

"""
Integration test for wait-ci CLI.

Tests that the CLI can successfully load and display a captured GitHub Actions run.
"""

import subprocess
import time
import os
from pathlib import Path
import pytest


def test_wait_ci_with_debug_capture_file():
    """Test that wait-ci can load and process a debug capture file using subprocess."""
    # Path to the test capture file
    repo_root = Path(__file__).parent.parent
    capture_file = repo_root / "src/wait_ci/dev_tools/test_vectors/captures/gh_run_19332482748_capture.json"
    assert capture_file.exists(), f"Test capture file not found: {capture_file}"

    # Run wait-ci as a module with the debug capture file
    # Update PYTHONPATH to make wait_ci importable while preserving existing environment
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")

    # Start the process
    process = subprocess.Popen(
        ["python3", "-m", "wait_ci", "-D", str(capture_file)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # Line buffered
        env=env,
        cwd=str(repo_root),
    )

    # Wait a fixed short time for the UI to start rendering
    # Give it 5 seconds for Rich to initialize and display progress
    wait_seconds = 5
    time.sleep(wait_seconds)

    try:
        # Terminate the process now that we've given it time to display
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

        # Read all output
        output = process.stdout.read()

        # Assert that key elements were displayed
        assert "watching github action run" in output.lower(), \
            f"Expected 'watching github action run' in output. Got: {output[:500]}"
        assert "19332482748" in output, \
            f"Expected run ID 19332482748 in output. Got: {output[:500]}"

        # Success! The CLI started successfully and loaded the capture file
        # (Rich's Live display uses terminal control codes that don't fully capture in subprocess,
        # but the initial message proves the CLI is working)
        print(f"\n✓ Integration test passed - CLI started and loaded capture file in {wait_seconds} seconds")

    finally:
        # Ensure process is terminated
        if process.poll() is None:
            process.kill()
            process.wait()


if __name__ == "__main__":
    # Allow running the test directly
    pytest.main([__file__, "-v"])
