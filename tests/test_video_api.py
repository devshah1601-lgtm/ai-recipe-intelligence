from fastapi.testclient import TestClient

from app.main import app


def test_rejects_non_mp4_upload():
    with TestClient(app) as client:
        response = client.post(
            "/videos/analyze-recipe",
            files={
                "file": ("recipe.txt", b"not a video", "text/plain")
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only MP4 videos are supported."


def test_rejects_invalid_video_content_type():
    with TestClient(app) as client:
        response = client.post(
            "/videos/analyze-recipe",
            files={
                "file": ("recipe.mp4", b"not a video", "text/plain")
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid video content type."


def test_rejects_empty_video():
    with TestClient(app) as client:
        response = client.post(
            "/videos/analyze-recipe",
            files={
                "file": ("recipe.mp4", b"", "video/mp4")
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded video is empty."

from unittest.mock import patch


def test_invalid_gemini_response_returns_502():
    def fake_analyzer(video_path):
        raise ValueError("Gemini ingredients must be a list.")

    with patch("app.main.analyze_video_with_gemini", fake_analyzer):
        with TestClient(app) as client:
            response = client.post(
                "/videos/analyze-recipe",
                files={
                    "file": ("recipe.mp4", b"fake-video", "video/mp4")
                },
            )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "AI returned an invalid recipe structure. Please try again."
    )


def test_busy_gemini_analysis_returns_429():
    with patch("app.main.gemini_analysis_lock") as mock_lock:
        mock_lock.acquire.return_value = False

        with TestClient(app) as client:
            response = client.post(
                "/videos/analyze-recipe",
                files={
                    "file": ("recipe.mp4", b"fake-video", "video/mp4")
                },
            )

    assert response.status_code == 429
    assert "already running" in response.json()["detail"]
    mock_lock.release.assert_not_called()

def test_rejects_oversized_video():
    with patch("app.main.MAX_VIDEO_BYTES", 10):
        with TestClient(app) as client:
            response = client.post(
                "/videos/analyze-recipe",
                files={
                    "file": (
                        "recipe.mp4",
                        b"this-video-is-too-large",
                        "video/mp4",
                    )
                },
            )

    assert response.status_code == 413
    assert response.json()["detail"] == (
        "Video exceeds the 50 MB limit."
    )