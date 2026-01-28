"""
Unit tests for the MCP server module.
"""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.mcp_server import extract_audio, extract_audio_to_file


class TestMCPServer:
    """Test cases for MCP server tools."""

    @patch("app.mcp_server.AudioExtractor")
    def test_extract_audio_success(self, mock_extractor_class):
        """Test successful audio extraction via MCP."""
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        mock_extractor.extract_audio.return_value = (Path("/tmp/test.mp3"), "test.mp3")

        result = extract_audio("https://youtube.com/watch?v=test", "mp3")

        assert result["success"] is True
        assert result["filename"] == "test.mp3"
        assert "file_path" in result

    @patch("app.mcp_server.AudioExtractor")
    def test_extract_audio_with_output_path(self, mock_extractor_class):
        """Test audio extraction with output path via MCP."""
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        mock_extractor.extract_audio_to_file.return_value = "output.mp3"

        result = extract_audio("https://youtube.com/watch?v=test", "mp3", "/tmp/output.mp3")

        assert result["success"] is True
        assert result["filename"] == "output.mp3"
        assert mock_extractor.extract_audio_to_file.called

    @patch("app.mcp_server.AudioExtractor")
    def test_extract_audio_error(self, mock_extractor_class):
        """Test error handling in MCP extract_audio."""
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        mock_extractor.extract_audio.side_effect = ValueError("Invalid format")

        result = extract_audio("https://youtube.com/watch?v=test", "ogg")

        assert result["success"] is False
        assert "error" in result
        assert "Invalid input" in result["error"]

    @patch("app.mcp_server.AudioExtractor")
    def test_extract_audio_to_file_success(self, mock_extractor_class):
        """Test successful extract_audio_to_file via MCP."""
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        mock_extractor.extract_audio_to_file.return_value = "output.mp3"

        result = extract_audio_to_file("https://youtube.com/watch?v=test", "/tmp/output.mp3", "mp3")

        assert result["success"] is True
        assert result["filename"] == "output.mp3"
        assert result["file_path"] == "/tmp/output.mp3"

    @patch("app.mcp_server.AudioExtractor")
    def test_extract_audio_to_file_error(self, mock_extractor_class):
        """Test error handling in MCP extract_audio_to_file."""
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        mock_extractor.extract_audio_to_file.side_effect = RuntimeError("Extraction failed")

        result = extract_audio_to_file("https://youtube.com/watch?v=test", "/tmp/output.mp3", "mp3")

        assert result["success"] is False
        assert "error" in result
        assert "Extraction failed" in result["error"]
