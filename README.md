## YouTube Audio Extractor (MP3)

Paste a YouTube link in the web UI and download the extracted audio as an **MP3**.

![App screenshot](docs/example.png)

### Requirements

- Python 3.10+
- `ffmpeg` installed on your system (required for MP3 conversion)
- Python packaging tools (`pip`, `venv`) available on your system

Install ffmpeg on Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y ffmpeg
```

If you don't have `pip` / `venv`:

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv
```

### Setup

```bash
cd /home/ding/Documents/youtube_extractor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open:

- `http://localhost:8000`

### API (curl)

Health check:

```bash
curl -s http://localhost:8000/api/health
```

### Logging / audit trail

The app logs **who** made the request, **what** happened, and whether it **succeeded or failed**.

- **Request correlation**: every response includes `X-Request-Id` (you can also send your own `X-Request-Id`)
- **Who (caller identity)**: send `X-Client-Id: my-service` (preferred) or `X-Api-Key: ...` (only partially logged)
- **Where logs go**: stdout + rotating file at `./logs/app.log` (configurable via env)

Environment variables:

- **LOG_LEVEL**: `DEBUG|INFO|WARNING|ERROR` (default `INFO`)
- **LOG_FORMAT**: `json|text` (default `json`)
- **LOG_FILE**: path (default `./logs/app.log`)
- **TRUST_PROXY_HEADERS**: set to `1` if running behind a proxy and you want to trust `X-Forwarded-For`

Download MP3 via **POST JSON** (most reliable):

```bash
curl -L -X POST http://localhost:8000/api/extract \
  -H 'Content-Type: application/json' \
  -H 'X-Client-Id: my-cli' \
  -d '{"url":"https://www.youtube.com/watch?v=VIDEO_ID"}' \
  -OJ
```

Download MP3 via **GET** with URL encoding (curl-friendly):

```bash
curl -L -G http://localhost:8000/api/extract \
  --data-urlencode "url=https://www.youtube.com/watch?v=VIDEO_ID" \
  -OJ
```

Download MP3 via **POST form**:

```bash
curl -L -X POST http://localhost:8000/api/extract/form \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "url=https://www.youtube.com/watch?v=VIDEO_ID" \
  -OJ
```

### CLI Usage

The project includes a command-line interface for local audio extraction:

```bash
# Basic usage - extract to current directory
python -m app.cli "https://www.youtube.com/watch?v=VIDEO_ID"

# Specify output format (mp3 or wav)
python -m app.cli "https://www.youtube.com/watch?v=VIDEO_ID" --format wav

# Specify output file path
python -m app.cli "https://www.youtube.com/watch?v=VIDEO_ID" --output audio.mp3

# Specify output directory
python -m app.cli "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir /path/to/output
```

CLI options:
- `--format`, `-f`: Audio format (mp3 or wav), default is mp3
- `--output`, `-o`: Output file path
- `--output-dir`, `-d`: Output directory (used when --output is not specified)

### MCP Server

The project includes an MCP (Model Context Protocol) server for integration with LLM workflows.

#### Running the MCP Server

```bash
python -m app.mcp_server
```

The MCP server exposes two tools:

1. **extract_audio**: Extract audio from a YouTube URL
   - Parameters:
     - `url` (required): YouTube video URL
     - `format` (optional): Audio format ('mp3' or 'wav'), default is 'mp3'
     - `output_path` (optional): Output file path. If not provided, uses a temporary file.

2. **extract_audio_to_file**: Extract audio to a specific file path
   - Parameters:
     - `url` (required): YouTube video URL
     - `output_path` (required): Target output file path
     - `format` (optional): Audio format ('mp3' or 'wav'), default is 'mp3'

#### MCP Server Configuration

To use the MCP server with an MCP client (e.g., Claude Desktop, Cursor), add it to your MCP configuration:

```json
{
  "mcpServers": {
    "youtube-audio-extractor": {
      "command": "python",
      "args": ["-m", "app.mcp_server"]
    }
  }
}
```

The server uses stdio transport by default, which is compatible with most MCP clients.

### Testing

Run unit tests using pytest:

```bash
# Install test dependencies (if using uv)
uv pip install pytest

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_core.py

# Run with verbose output
pytest tests/ -v
```

### Notes

- This app uses `yt-dlp` to download audio and `ffmpeg` to convert to MP3.
- Some videos may be unavailable due to region/age restrictions or DRM.
- The core extraction logic is encapsulated in `app.core.AudioExtractor` for reuse across CLI, web API, and MCP server.

