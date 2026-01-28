"""
Unit tests for the CLI module.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from app.cli import main


class TestCLI:
    """Test cases for CLI commands."""

    def test_cli_help(self):
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Extract audio from a YouTube URL" in result.output

    @patch("app.cli.AudioExtractor")
    def test_cli_extract_success(self, mock_extractor_class):
        """Test successful CLI extraction."""
        runner = CliRunner()

        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        mock_extractor.extract_audio.return_value = (Path("/tmp/test.mp3"), "test.mp3")

        result = runner.invoke(main, ["https://youtube.com/watch?v=test"])

        assert result.exit_code == 0
        assert "Successfully extracted audio" in result.output
        assert mock_extractor.extract_audio.called

    @patch("app.cli.AudioExtractor")
    def test_cli_extract_with_output(self, mock_extractor_class):
        """Test CLI extraction with output file."""
        runner = CliRunner()

        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        mock_extractor.extract_audio_to_file.return_value = "output.mp3"

        with runner.isolated_filesystem():
            output_file = Path("output.mp3")
            result = runner.invoke(
                main, ["https://youtube.com/watch?v=test", "--output", str(output_file)]
            )

            assert result.exit_code == 0
            assert "Successfully extracted audio" in result.output
            assert mock_extractor.extract_audio_to_file.called

    @patch("app.cli.AudioExtractor")
    def test_cli_extract_with_format(self, mock_extractor_class):
        """Test CLI extraction with format option."""
        runner = CliRunner()

        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        mock_extractor.extract_audio.return_value = (Path("/tmp/test.wav"), "test.wav")

        result = runner.invoke(main, ["https://youtube.com/watch?v=test", "--format", "wav"])

        assert result.exit_code == 0
        call_args = mock_extractor.extract_audio.call_args
        assert call_args[0][1] == "wav"

    @patch("app.cli.AudioExtractor")
    def test_cli_extract_error(self, mock_extractor_class):
        """Test CLI extraction error handling."""
        runner = CliRunner()

        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        mock_extractor.extract_audio.side_effect = ValueError("Invalid format")

        result = runner.invoke(main, ["https://youtube.com/watch?v=test"])

        assert result.exit_code == 1
        assert "Error:" in result.output
