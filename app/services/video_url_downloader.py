
import ipaddress
import socket
import tempfile
from pathlib import Path
from urllib.parse import urlparse
import subprocess
import yt_dlp


MAX_VIDEO_BYTES = 50 * 1024 * 1024  # 50 MB

ALLOWED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "instagram.com",
    "www.instagram.com",
}


def detect_video_platform(url: str) -> str | None:
    parsed = urlparse(url.strip())

    if parsed.scheme != "https":
        return None

    hostname = (parsed.hostname or "").lower()

    if hostname in {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
    }:
        return "youtube"

    if hostname in {"instagram.com", "www.instagram.com"}:
        return "instagram"

    return None


def download_video_from_url(url: str, work_dir: Path) -> Path:
    platform = detect_video_platform(url)

    if platform is None:
        raise ValueError("Only HTTPS YouTube and Instagram video URLs are supported.")

    parsed = urlparse(url)
    if parsed.username or parsed.password or parsed.port:
        raise ValueError("Invalid video URL.")

    work_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(work_dir / "downloaded.%(ext)s")
    options = {
        "format": (
        "bv*[height<=480]+ba/b[height<=480]"
        if platform == "youtube"
        else "bv*+ba/b"
        ),
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "max_filesize": MAX_VIDEO_BYTES,
        "socket_timeout": 15,
        "retries": 1,
        "fragment_retries": 1,
        "js_runtimes": {"node": {}},
        "remote_components": {"ejs:github"},
        "quiet": True,
        "no_warnings": True,
    }


    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            downloader.download([url])
    except yt_dlp.utils.DownloadError as exc:
        raise ValueError(
            f"Could not retrieve this {platform} video. It may be private, restricted, or unavailable."
        ) from exc

        # Find the completed downloaded video.
    candidates = [
        path
        for path in work_dir.glob("downloaded.*")
        if path.suffix.lower() in {".mp4", ".webm", ".mkv", ".mov"}
    ]

    if not candidates:
        raise ValueError("Video download did not produce a supported file.")

    # Prefer the largest completed media file.
    video_path = max(
        candidates,
        key=lambda path: path.stat().st_size,
    )

    if video_path.stat().st_size > MAX_VIDEO_BYTES:
        raise ValueError("Video exceeds the 50 MB limit.")

    # Gemini and our pipeline expect an MP4 video.
    if video_path.suffix.lower() != ".mp4":

        converted_path = work_dir / "converted.mp4"

        command = [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(video_path),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "28",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(converted_path),
        ]

        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=180,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise ValueError(
                "Could not convert the downloaded video to MP4."
            ) from exc

        if not converted_path.exists():
            raise ValueError("MP4 conversion did not produce a file.")

        if converted_path.stat().st_size > MAX_VIDEO_BYTES:
            raise ValueError("Converted video exceeds the 50 MB limit.")

        video_path = converted_path

    return video_path