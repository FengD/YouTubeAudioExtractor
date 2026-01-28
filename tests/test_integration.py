"""
Optional integration tests for real YouTube downloads.
"""
import os

import pytest

from app.core import AudioExtractor

TEST_URL = os.getenv("YOUTUBE_TEST_URL", "https://www.youtube.com/watch?v=WRvWLWfv4Ts")
RUN_INTEGRATION = os.getenv("RUN_YT_INTEGRATION") == "1"


@pytest.mark.skipif(not RUN_INTEGRATION, reason="Set RUN_YT_INTEGRATION=1 to run.")
def test_extract_audio_mp3_real(tmp_path):
    extractor = AudioExtractor(output_dir=tmp_path)
    output_path, filename = extractor.extract_audio(TEST_URL, "mp3")

    assert output_path.exists()
    assert output_path.suffix == ".mp3"
    assert filename.endswith(".mp3")
    assert output_path.stat().st_size > 0
