"""Functions to download foreign trade data."""

import sys
import time
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def is_more_recent(headers: dict, dest: Path) -> bool:
    """Check if the remote file is more recent than the local file."""
    if not dest.exists():
        return False

    last_modified = headers.get("Last-Modified")
    if last_modified:
        # Parse standard HTTP date format
        remote_mtime = time.mktime(
            time.strptime(last_modified, "%a, %d %b %Y %H:%M:%S %Z")
        )
        if dest.stat().st_mtime < remote_mtime:
            return True

    return False


def download_file(
    url: str,
    output: Path,
    retry: int = 3,
    blocksize: int = 8192,
    verify_ssl: bool = False,
) -> Path:
    """
    Downloads a file from a URL to a specific output path.

    Args:
        url: Source URL.
        output: Destination local path.
        retry: Number of retries.
        blocksize: Chunk size for download.
        verify_ssl: Whether to verify SSL certificates.

    Returns:
        The path to the downloaded file.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    }

    # Ensure parent directory exists
    output.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(retry):
        sys.stdout.write(f"Downloading: {url:<50} --> {output.name}\n")
        sys.stdout.flush()

        try:
            # Check for updates with HEAD request
            head_resp = requests.head(
                url, headers=headers, timeout=10, verify=verify_ssl
            )

            if output.exists() and not is_more_recent(head_resp.headers, output):
                sys.stdout.write(f"             {output.name} is up to date.\n")
                sys.stdout.flush()
                return output

            # Perform the specific download
            with requests.get(
                url, headers=headers, stream=True, timeout=30, verify=verify_ssl
            ) as r:
                r.raise_for_status()
                total_length = int(r.headers.get("content-length", 0))

                downloaded_size = 0
                with open(output, "wb") as f:
                    for chunk in r.iter_content(chunk_size=blocksize):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)

                            # Simple progress bar
                            if total_length:
                                percent = downloaded_size / total_length
                                bar_length = 50
                                filled = int(percent * bar_length)
                                bar = "=" * filled + "-" * (bar_length - filled)
                                size_mb = downloaded_size / (1024 * 1024)
                                sys.stdout.write(
                                    f"\r[{bar}] {percent:.1%} ({size_mb:.2f} MiB)"
                                )
                                sys.stdout.flush()

            sys.stdout.write("\n")
            return output

        except requests.RequestException as e:
            sys.stdout.write(f"\nError downloading {url}: {e}\n")
            if attempt < retry - 1:
                time.sleep(2)
            else:
                raise

    return output
