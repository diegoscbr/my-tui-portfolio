"""
Spike test: validate that we can create a Textual driver that writes
to a custom stream instead of sys.stdout.

This test uses a StringIO buffer as a stand-in for an SSH channel.
If this fails, the SSHDriver approach needs rethinking.
"""
import io
import pytest


@pytest.mark.asyncio
async def test_ssh_driver_writes_to_custom_stream():
    """SSHDriver should write output to the provided stream, not sys.stdout."""
    from ssh_driver import SSHDriver

    buffer = io.StringIO()
    driver = SSHDriver.create_for_test(output_stream=buffer)
    driver.write("\x1b[2J")  # ANSI clear screen
    driver.flush()
    assert "\x1b[2J" in buffer.getvalue()


@pytest.mark.asyncio
async def test_ssh_driver_reports_terminal_size():
    """SSHDriver should report the terminal size from SSH PTY dimensions."""
    from ssh_driver import SSHDriver

    buffer = io.StringIO()
    driver = SSHDriver.create_for_test(output_stream=buffer, size=(120, 40))
    width, height = driver.get_size()
    assert width == 120
    assert height == 40


@pytest.mark.asyncio
async def test_ssh_driver_set_size_updates_dimensions():
    """set_size should update the stored terminal dimensions."""
    from ssh_driver import SSHDriver

    buffer = io.StringIO()
    driver = SSHDriver.create_for_test(output_stream=buffer, size=(80, 24))
    driver.set_size(160, 48)
    assert driver.get_size() == (160, 48)
