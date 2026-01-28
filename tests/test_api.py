"""
API tests for the FastAPI service.
"""
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

TEST_URL = "https://www.youtube.com/watch?v=WRvWLWfv4Ts"


def _write_audio_file(path: Path) -> Path:
    path.write_bytes(b"audio-bytes")
    return path


def test_health():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_extract_get_success(tmp_path):
    audio_file = _write_audio_file(tmp_path / "Test Title.mp3")

    with patch("app.main.tempfile.mkdtemp", return_value=str(tmp_path)), patch(
        "app.main.AudioExtractor"
    ) as mock_extractor:
        mock_extractor.return_value.extract_audio.return_value = (audio_file, "Test Title.mp3")
        client = TestClient(app)
        response = client.get("/api/extract", params={"url": TEST_URL, "format": "mp3"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/mpeg")
    assert "Test Title.mp3" in response.headers.get("content-disposition", "")


def test_extract_post_json_success(tmp_path):
    audio_file = _write_audio_file(tmp_path / "Test Title.wav")

    with patch("app.main.tempfile.mkdtemp", return_value=str(tmp_path)), patch(
        "app.main.AudioExtractor"
    ) as mock_extractor:
        mock_extractor.return_value.extract_audio.return_value = (audio_file, "Test Title.wav")
        client = TestClient(app)
        response = client.post("/api/extract", json={"url": TEST_URL, "format": "wav"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/wav")


def test_extract_form_success(tmp_path):
    audio_file = _write_audio_file(tmp_path / "Test Title.mp3")

    with patch("app.main.tempfile.mkdtemp", return_value=str(tmp_path)), patch(
        "app.main.AudioExtractor"
    ) as mock_extractor:
        mock_extractor.return_value.extract_audio.return_value = (audio_file, "Test Title.mp3")
        client = TestClient(app)
        response = client.post(
            "/api/extract/form",
            data={"url": TEST_URL, "format": "mp3"},
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/mpeg")


def test_extract_invalid_format():
    client = TestClient(app)
    response = client.get("/api/extract", params={"url": TEST_URL, "format": "ogg"})
    assert response.status_code == 400
    assert "Format must be either" in response.json()["detail"]
