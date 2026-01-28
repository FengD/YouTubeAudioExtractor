"""
MCP server for YouTube audio extraction.
"""
import tempfile
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from app.core import AudioExtractor

mcp = FastMCP("YouTube Audio Extractor", json_response=True)


@mcp.tool()
def extract_audio(
    url: str,
    format: str = "mp3",
    output_path: Optional[str] = None,
) -> dict:
    """
    Extract audio from a YouTube URL.

    Args:
        url: YouTube video URL
        format: Audio format ('mp3' or 'wav'), default is 'mp3'
        output_path: Optional output file path. If not provided, uses a temporary file.

    Returns:
        Dictionary with 'success', 'file_path', 'filename', and optional 'error' keys
    """
    try:
        extractor = AudioExtractor()

        if output_path:
            output_file = Path(output_path)
            filename = extractor.extract_audio_to_file(url, output_file, format)
            return {
                "success": True,
                "file_path": str(output_file),
                "filename": filename,
            }
        else:
            output_file, filename = extractor.extract_audio(url, format)
            return {
                "success": True,
                "file_path": str(output_file),
                "filename": filename,
            }
    except ValueError as e:
        return {
            "success": False,
            "error": f"Invalid input: {str(e)}",
        }
    except RuntimeError as e:
        return {
            "success": False,
            "error": f"Extraction failed: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
        }


@mcp.tool()
def extract_audio_to_file(
    url: str,
    output_path: str,
    format: str = "mp3",
) -> dict:
    """
    Extract audio from a YouTube URL and save to a specific file path.

    Args:
        url: YouTube video URL
        output_path: Target output file path
        format: Audio format ('mp3' or 'wav'), default is 'mp3'

    Returns:
        Dictionary with 'success', 'file_path', 'filename', and optional 'error' keys
    """
    try:
        extractor = AudioExtractor()
        output_file = Path(output_path)
        filename = extractor.extract_audio_to_file(url, output_file, format)
        return {
            "success": True,
            "file_path": str(output_file),
            "filename": filename,
        }
    except ValueError as e:
        return {
            "success": False,
            "error": f"Invalid input: {str(e)}",
        }
    except RuntimeError as e:
        return {
            "success": False,
            "error": f"Extraction failed: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
        }


if __name__ == "__main__":
    mcp.run()
