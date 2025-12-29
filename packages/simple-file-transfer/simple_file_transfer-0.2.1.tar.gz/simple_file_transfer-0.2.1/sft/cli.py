import hashlib
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import click
import requests

__version__ = "0.1.1"


def get_service_url():
    service = os.environ.get("SFT_SERVICE", "sft.pzjj.org:12345")

    if not service.startswith("http://") and not service.startswith("https://"):
        service = f"http://{service}"

    return service


def parse_time_duration(duration_str):
    duration_str = duration_str.strip().lower()

    if duration_str.endswith("m"):
        return int(duration_str[:-1]) * 60
    elif duration_str.endswith("h"):
        return int(duration_str[:-1]) * 3600
    elif duration_str.endswith("d"):
        return int(duration_str[:-1]) * 86400
    elif duration_str.endswith("w"):
        return int(duration_str[:-1]) * 604800
    else:
        try:
            return int(duration_str)
        except ValueError:
            raise ValueError(f"Invalid duration format: {duration_str}")


def format_size(size_bytes):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"


def format_time_remaining(expiry_iso):
    expiry = datetime.fromisoformat(expiry_iso)
    now = datetime.now()

    if now > expiry:
        return "expired"

    delta = expiry - now
    total_seconds = int(delta.total_seconds())

    if total_seconds < 60:
        return f"{total_seconds}s"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes}min"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours}h"
    else:
        days = total_seconds // 86400
        return f"{days}d"


def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_git_info():
    """Get git commit hash and datetime."""
    try:
        # Get the directory where this file is located
        cli_dir = Path(__file__).parent
        
        # Get commit hash
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=cli_dir,
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        # Get commit datetime in ISO format
        commit_datetime = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI"],
            cwd=cli_dir,
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        return commit_hash, commit_datetime
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None, None


def print_version(ctx, param, value):
    """Print version information and exit."""
    if not value or ctx.resilient_parsing:
        return
    
    click.echo(f"sft version {__version__}")
    
    commit_hash, commit_datetime = get_git_info()
    if commit_hash:
        click.echo(f"commit {commit_hash}")
        click.echo(f"date   {commit_datetime}")
    
    ctx.exit()


@click.group()
@click.option('--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True,
              help='Show version, commit hash, and commit datetime.')
def cli():
    pass


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.argument("duration", default="1h")
@click.option("--service", help="Override SFT_SERVICE environment variable")
@click.option("--id", "file_id", help="Custom file ID (default: server-generated)")
def upload(filepath, duration, service, file_id):
    if service:
        os.environ["SFT_SERVICE"] = service

    service_url = get_service_url()

    try:
        expiry_seconds = parse_time_duration(duration)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    filepath = Path(filepath)
    file_size = filepath.stat().st_size

    click.echo(f"Uploading {filepath.name} ({format_size(file_size)})...")

    try:
        with open(filepath, "rb") as f:
            files = {"file": (filepath.name, f)}
            data = {"expiry": expiry_seconds}
            if file_id:
                data["file_id"] = file_id

            response = requests.post(
                f"{service_url}/upload", files=files, data=data, timeout=300
            )

        if response.status_code != 200:
            click.echo(f"Error: Upload failed - {response.text}", err=True)
            sys.exit(1)

        result = response.json()

        expiry_time = datetime.fromisoformat(result["expiry"])

        click.echo(
            f"Uploaded {filepath.name} {format_size(result['size'])} sha256:{result['sha256'][:16]}..."
        )
        click.echo(
            f"The file will be deleted in {duration} ({expiry_time.strftime('%Y-%m-%d %H:%M:%S')})"
        )
        click.echo(f"To download your file, enter: sft download {result['file_id']}")

    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Connection failed - {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("file_id")
@click.option("--service", help="Override SFT_SERVICE environment variable")
@click.option("--output", "-o", help="Output filename (default: original filename)")
def download(file_id, service, output):
    if service:
        os.environ["SFT_SERVICE"] = service

    service_url = get_service_url()

    try:
        info_response = requests.get(f"{service_url}/info/{file_id}", timeout=30)

        if info_response.status_code != 200:
            click.echo(f"Error: File not found or expired", err=True)
            sys.exit(1)

        info = info_response.json()
        filename = output or info["filename"]

        click.echo(f"Downloading {info['filename']} ({format_size(info['size'])})...")

        response = requests.get(
            f"{service_url}/download/{file_id}", stream=True, timeout=300
        )

        if response.status_code != 200:
            click.echo(f"Error: Download failed", err=True)
            sys.exit(1)

        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        downloaded_sha256 = calculate_sha256(filename)

        if downloaded_sha256 != info["sha256"]:
            click.echo(f"Warning: SHA256 mismatch!", err=True)
            click.echo(f"Expected: {info['sha256']}", err=True)
            click.echo(f"Got: {downloaded_sha256}", err=True)

        expiry_time = datetime.fromisoformat(info["expiry"])
        time_remaining = format_time_remaining(info["expiry"])

        click.echo(
            f"File downloaded {filename} {format_size(info['size'])} sha256:{info['sha256'][:16]}..."
        )
        click.echo(
            f"The file will be deleted in {time_remaining} ({expiry_time.strftime('%Y-%m-%d %H:%M:%S')})"
        )

    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Connection failed - {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=12345, help="Port to bind to")
def serve(host, port):
    from sft.server import run_server

    run_server(host=host, port=port)


if __name__ == "__main__":
    cli()
