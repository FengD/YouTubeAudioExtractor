"""
Unit tests for the core audio extraction module.
"""
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core import AudioExtractor


class TestAudioExtractor:
    """Test cases for AudioExtractor class."""

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        extractor = AudioExtractor()

        assert extractor.sanitize_filename("Test Video Title") == "Test Video Title"
        assert extractor.sanitize_filename("Test/Video\\Title") == "TestVideoTitle"
        assert extractor.sanitize_filename("  Test  Video  ") == "Test Video"
        assert extractor.sanitize_filename("") == "audio"
        assert extractor.sanitize_filename("a" * 200) == "a" * 120

    def test_normalize_audio_format(self):
        """Test audio format normalization."""
        extractor = AudioExtractor()

        assert extractor.normalize_audio_format("mp3") == "mp3"
        assert extractor.normalize_audio_format("MP3") == "mp3"
        assert extractor.normalize_audio_format("wav") == "wav"
        assert extractor.normalize_audio_format("WAV") == "wav"
        assert extractor.normalize_audio_format(None) == "mp3"
        assert extractor.normalize_audio_format("") == "mp3"

        with pytest.raises(ValueError, match="Format must be either"):
            extractor.normalize_audio_format("ogg")

    @patch("app.core.YoutubeDL")
    def test_extract_audio_success(self, mock_ydl_class):
        """Test successful audio extraction."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_info = {"title": "Test Video"}
        mock_ydl.extract_info.return_value = mock_info
        mock_ydl.download.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = AudioExtractor(output_dir=Path(tmpdir))

            with patch("pathlib.Path.glob") as mock_glob:
                mock_output_file = Path(tmpdir) / "Test Video.mp3"
                mock_output_file.touch()
                mock_glob.return_value = [mock_output_file]

                output_path, filename = extractor.extract_audio("https://youtube.com/watch?v=test", "mp3")

                assert output_path == mock_output_file
                assert filename == "Test Video.mp3"
                assert mock_ydl.extract_info.called
                assert mock_ydl.download.called

    @patch("app.core.YoutubeDL")
    def test_extract_audio_invalid_format(self, mock_ydl_class):
        """Test audio extraction with invalid format."""
        extractor = AudioExtractor()

        with pytest.raises(ValueError, match="Format must be either"):
            extractor.extract_audio("https://youtube.com/watch?v=test", "ogg")

    @patch("app.core.YoutubeDL")
    def test_extract_audio_to_file(self, mock_ydl_class):
        """Test extracting audio to a specific file path."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_info = {"title": "Test Video"}
        mock_ydl.extract_info.return_value = mock_info
        mock_ydl.download.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = AudioExtractor()
            output_file = Path(tmpdir) / "output.mp3"
            output_file.touch()

            with patch("pathlib.Path.glob") as mock_glob:
                mock_glob.return_value = [output_file]

                filename = extractor.extract_audio_to_file(
                    "https://youtube.com/watch?v=test", output_file, "mp3"
                )

                assert filename == "output.mp3"
                assert output_file.exists()


class TestConvenienceFunction:
    """Test cases for convenience functions."""

    @patch("app.core.AudioExtractor")
    def test_extract_audio_function(self, mock_extractor_class):
        """Test the convenience extract_audio function."""
        from app.core import extract_audio

        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        mock_extractor.extract_audio.return_value = (Path("/tmp/test.mp3"), "test.mp3")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path, filename = extract_audio("https://youtube.com/watch?v=test", "mp3", Path(tmpdir))

            assert mock_extractor.extract_audio.called
            assert filename == "test.mp3"
