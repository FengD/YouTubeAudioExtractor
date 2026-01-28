"""
CLI tool for extracting audio from YouTube URLs.
"""
import sys
from pathlib import Path

import click

from app.core import AudioExtractor


@click.command()
@click.argument("url", type=str)
@click.option(
    "--format",
    "-f",
    "audio_format",
    type=click.Choice(["mp3", "wav"], case_sensitive=False),
    default="mp3",
    help="Audio format (mp3 or wav)",
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file path. If not specified, uses video title in current directory.",
)
@click.option(
    "--output-dir",
    "-d",
    "output_dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=None,
    help="Output directory. If not specified, uses current directory.",
)
def main(url: str, audio_format: str, output_path: Path, output_dir: Path):
    """
    Extract audio from a YouTube URL.

    URL: YouTube video URL to extract audio from
    """
    try:
        extractor = AudioExtractor(output_dir=output_dir or Path.cwd())

        if output_path:
            click.echo(f"Extracting audio to {output_path}...", err=True)
            filename = extractor.extract_audio_to_file(url, output_path, audio_format)
            click.echo(f"Successfully extracted audio: {output_path}", err=True)
        else:
            click.echo(f"Extracting audio from {url}...", err=True)
            output_file, filename = extractor.extract_audio(url, audio_format)
            click.echo(f"Successfully extracted audio: {output_file}", err=True)

        click.echo(f"Output: {filename}", err=True)
        sys.exit(0)

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nInterrupted by user", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
