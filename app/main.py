import logging
import re
import shutil
import tempfile
import time
import uuid
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi import Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl
from starlette.background import BackgroundTask
from yt_dlp import YoutubeDL

from app.logging_config import get_client_id, get_client_ip, setup_logging


APP_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"

app = FastAPI(title="YouTube Audio Extractor", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

logger = setup_logging()


class ExtractRequest(BaseModel):
    url: HttpUrl
    format: Optional[str] = None


def _sanitize_filename(name: str, max_len: int = 120) -> str:
    name = name.strip()
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"[^a-zA-Z0-9 \-_\.\(\)\[\]]+", "", name)
    name = name.strip(" .-_")
    if not name:
        name = "audio"
    return name[:max_len]


def _redact_youtube_url_for_logs(url: str) -> str:
    """
    Log-safe-ish view of the target URL:
    - keep scheme + host + path
    - keep only the 'v' query param when present
    """
    try:
        u = urlparse(url)
        q = parse_qs(u.query)
        keep = {}
        if "v" in q and q["v"]:
            keep["v"] = q["v"][0]
        new_query = urlencode(keep) if keep else ""
        return urlunparse((u.scheme, u.netloc, u.path, "", new_query, ""))
    except Exception:
        return url


def _request_ctx(request: Request) -> dict:
    headers = {k.lower(): v for k, v in request.headers.items()}
    client_id = get_client_id(headers)
    client_ip = get_client_ip(headers, getattr(request.client, "host", None) if request.client else None)
    ua = headers.get("user-agent")
    return {
        "request_id": getattr(request.state, "request_id", None),
        "client_id": client_id,
        "client_ip": client_ip,
        "user_agent": ua,
        "method": request.method,
        "path": request.url.path,
    }


def _normalize_audio_format(value: Optional[str]) -> str:
    fmt = (value or "mp3").strip().lower()
    if fmt not in {"mp3", "wav"}:
        raise HTTPException(status_code=400, detail="Format must be either 'mp3' or 'wav'.")
    return fmt


def _extract_audio_file_response(url: str, *, request: Request, audio_format: str) -> FileResponse:
    tmp_dir = Path(tempfile.mkdtemp(prefix="yt-extract-"))

    try:
        start = time.perf_counter()
        ctx = _request_ctx(request)
        ctx["youtube_url"] = _redact_youtube_url_for_logs(url)
        logger.info("extract.start", extra={"ctx": ctx})

        # First get metadata (title) without downloading so we can name the file nicely.
        with YoutubeDL(
            {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
            }
        ) as ydl:
            info = ydl.extract_info(str(url), download=False)

        title = _sanitize_filename(info.get("title") or "audio")
        outtmpl = str(tmp_dir / f"{title}.%(ext)s")

        postprocessor = {
            "key": "FFmpegExtractAudio",
            "preferredcodec": audio_format,
        }
        if audio_format == "mp3":
            postprocessor["preferredquality"] = "192"

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "postprocessors": [postprocessor],
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([str(url)])

        output_path: Optional[Path] = None
        for p in tmp_dir.glob(f"*.{audio_format}"):
            output_path = p
            break

        if not output_path or not output_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"{audio_format.upper()} was not created. Is ffmpeg installed and available on PATH?",
            )

        download_name = f"{title}.{audio_format}"
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "extract.success",
            extra={"ctx": {**ctx, "status": "success", "duration_ms": duration_ms, "filename": download_name}},
        )
        media_type = "audio/mpeg" if audio_format == "mp3" else "audio/wav"
        return FileResponse(
            path=str(output_path),
            media_type=media_type,
            filename=download_name,
            background=BackgroundTask(shutil.rmtree, str(tmp_dir), ignore_errors=True),
        )
    except HTTPException:
        logger.warning("extract.fail", extra={"ctx": {**_request_ctx(request), "status": "failed"}})
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise
    except Exception as e:
        logger.exception(
            "extract.error",
            extra={"ctx": {**_request_ctx(request), "status": "failed", "error": str(e)}},
        )
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id

    start = time.perf_counter()
    ctx = _request_ctx(request)
    logger.info("request.start", extra={"ctx": ctx})

    try:
        response = await call_next(request)
    except Exception as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.exception(
            "request.error",
            extra={"ctx": {**ctx, "duration_ms": duration_ms, "status": "failed", "error": str(e)}},
        )
        raise

    duration_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        "request.end",
        extra={"ctx": {**ctx, "duration_ms": duration_ms, "status_code": response.status_code}},
    )

    response.headers["X-Request-Id"] = request_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    ctx = _request_ctx(request)
    logger.warning(
        "http_exception",
        extra={"ctx": {**ctx, "status_code": exc.status_code, "detail": str(exc.detail)}},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "request_id": getattr(request.state, "request_id", None)},
        headers={"X-Request-Id": getattr(request.state, "request_id", "")},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    ctx = _request_ctx(request)
    logger.exception("unhandled_exception", extra={"ctx": {**ctx, "error": str(exc)}})
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": getattr(request.state, "request_id", None)},
        headers={"X-Request-Id": getattr(request.state, "request_id", "")},
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/health")
async def health(request: Request):
    logger.info("health", extra={"ctx": _request_ctx(request)})
    return {"ok": True}

@app.get("/api/extract")
async def extract_audio_get(request: Request, url: HttpUrl, format: Optional[str] = None):
    # curl-friendly: GET /api/extract?url=...
    audio_format = _normalize_audio_format(format)
    return _extract_audio_file_response(str(url), request=request, audio_format=audio_format)

@app.post("/api/extract")
async def extract_audio_post(request: Request, payload: ExtractRequest, format: Optional[str] = None):
    # JSON API: { "url": "https://..." }
    audio_format = _normalize_audio_format(payload.format or format)
    return _extract_audio_file_response(str(payload.url), request=request, audio_format=audio_format)


@app.post("/api/extract/form")
async def extract_audio_form(request: Request, url: HttpUrl = Form(...), format: Optional[str] = Form(None)):
    # Form API: url=<youtube-url>
    audio_format = _normalize_audio_format(format)
    return _extract_audio_file_response(str(url), request=request, audio_format=audio_format)

