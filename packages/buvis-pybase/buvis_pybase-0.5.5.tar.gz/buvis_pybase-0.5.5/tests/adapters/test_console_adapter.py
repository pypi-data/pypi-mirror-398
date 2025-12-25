from typing import Any

import pytest
from buvis.pybase.adapters.console.console import ConsoleAdapter, console
from rich.console import Console
from rich.status import Status


@pytest.fixture
def console_adapter() -> ConsoleAdapter:
    return ConsoleAdapter()


def test_format_success(console_adapter: ConsoleAdapter) -> None:
    message = "Success message"
    expected = " [bold green1]\u2714[/bold green1] [spring_green1]Success message[/spring_green1]"
    assert console_adapter.format_success(message) == expected


def test_format_warning(console_adapter: ConsoleAdapter) -> None:
    message = "Warning message"
    expected = " [bold orange3]\u26a0[/bold orange3] [light_goldenrod3]Warning message[/light_goldenrod3]"
    assert console_adapter.format_warning(message) == expected


def test_format_failure(console_adapter: ConsoleAdapter) -> None:
    message = "Failure message"
    details = "Failure details"
    expected = " [bold indian_red]\u2718[/bold indian_red] [bold light_salmon3]Failure message[/bold light_salmon3]"
    assert console_adapter.format_failure(message) == expected

    expected_with_details = (
        " [bold indian_red]\u2718[/bold indian_red] [bold light_salmon3]Failure message[/bold light_salmon3] \n\n "
        "Details:\n\n Failure details"
    )
    assert console_adapter.format_failure(message, details) == expected_with_details


def test_success(capsys: Any, console_adapter: ConsoleAdapter) -> None:
    message = "Success message"
    console_adapter.success(message)
    captured = capsys.readouterr()
    assert captured.out.strip() == f"✔ {message}"


def test_warning(capsys: Any, console_adapter: ConsoleAdapter) -> None:
    message = "Warning message"
    console_adapter.warning(message)
    captured = capsys.readouterr()
    assert captured.out.strip() == f"⚠ {message}"


def test_failure(capsys: Any, console_adapter: ConsoleAdapter) -> None:
    message = "Failure message"
    details = "Failure details"
    console_adapter.failure(message, details)
    captured = capsys.readouterr()
    assert captured.out.strip() == f"✘ {message} \n\n Details:\n\n {details}"


def test_panic(capsys: Any, console_adapter: ConsoleAdapter) -> None:
    message = "Panic message"
    details = "Panic details"
    with pytest.raises(SystemExit):
        console_adapter.panic(message, details)
    captured = capsys.readouterr()
    assert captured.out.strip() == f"✘ {message} \n\n Details:\n\n {details}"


def test_status(console_adapter: ConsoleAdapter) -> None:
    message = "Status message"
    status = console_adapter.status(message)
    assert isinstance(status, Status)
    assert status.status == message


def test_print(capsys: Any, console_adapter: ConsoleAdapter) -> None:
    message = "Print message"
    console_adapter.print(message)
    captured = capsys.readouterr()
    assert captured.out.strip() == message


def test_nl(capsys: Any, console_adapter: ConsoleAdapter) -> None:
    console_adapter.nl()
    captured = capsys.readouterr()
    assert captured.out.strip() == ""


def test_console_instance() -> None:
    assert isinstance(console, ConsoleAdapter)
