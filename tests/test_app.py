from unittest.mock import patch

import requests

from app import main

def test_help_command(capsys):
    """Verify that the /help command displays the expected help message."""
    with patch("builtins.input", side_effect=["/help", "/exit"]):
        main()

    output = capsys.readouterr().out

    assert "Commands:" in output
    assert "/config" in output
    assert "/exit" in output

def test_config_command(capsys):
    """Verify that the /config command displays the current configuration."""
    with patch("builtins.input", side_effect=["/config", "/exit"]):
        main()

    output = capsys.readouterr().out

    assert "Configuration:" in output
    assert "Workspace:" in output
    assert "Ollama URL:" in output

def test_exit_command(capsys):
    """Verify that the /exit command terminates the application gracefully."""
    with patch("builtins.input", return_value="/exit"):
        main()

    assert "Goodbye." in capsys.readouterr().out

def test_empty_input(capsys):
    """Verify that empty input prompts the user to enter a request."""
    with patch("builtins.input", side_effect=["", "/exit"]):
        main()

    assert "Please enter a request." in capsys.readouterr().out

@patch("app.run_agent")
def test_normal_request(mock_run_agent, capsys):
    """Verify that a normal user request is processed and the response is displayed."""
    mock_run_agent.return_value = "Test assistant response"

    with patch("builtins.input", side_effect=["Hello", "/exit"]):
        main()

    mock_run_agent.assert_called_once_with("Hello")
    assert "Test assistant response" in capsys.readouterr().out

@patch("app.run_agent")
def test_connection_error(mock_run_agent, capsys):
    """Verify that a connection error to Ollama is handled gracefully."""
    mock_run_agent.side_effect = requests.ConnectionError()

    with patch("builtins.input", side_effect=["Hello", "/exit"]):
        main()

    output = capsys.readouterr().out

    assert "Could not connect to Ollama" in output

@patch("app.run_agent")
def test_timeout_error(mock_run_agent, capsys):
    """Verify that a timeout error from Ollama is handled gracefully."""
    mock_run_agent.side_effect = requests.Timeout()

    with patch("builtins.input", side_effect=["Hello", "/exit"]):
        main()

    output = capsys.readouterr().out

    assert "took too long to respond" in output