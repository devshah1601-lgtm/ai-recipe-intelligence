
import json
import os
import time
from pathlib import Path

from google import genai
from google.genai import types


GEMINI_MODEL = "gemini-3.5-flash-lite"


def analyze_video_with_gemini(video_path: Path) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    if not video_path.is_file():
        raise FileNotFoundError(video_path)

    client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        timeout=120000,
        retry_options=types.HttpRetryOptions(
            attempts=1,
        ),
    ),
)
    uploaded_file = None

    prompt = """
    Analyze this cooking video and extract a structured recipe.

    Return JSON containing:
    - title
    - ingredients: name, quantity, unit
    - instructions: step_number, description, timestamp_seconds
    - uncertain_details

    Rules:
    1. Include only ingredients and actions supported by the video.
    2. Read visible ingredient labels.
    3. Keep cooking steps in chronological order.
    4. Do not invent measurements, temperatures, or cooking times.
    5. Use null for unknown quantities and units.
    6. Do not guess the final dish based on one ingredient.
    7. Report uncertain information in uncertain_details.
    """

    try:
        print("[Gemini] Starting video upload...", flush=True)
        uploaded_file = client.files.upload(
            file=str(video_path),
            config={"mime_type": "video/mp4"},
        )
        print("[Gemini] Video uploaded successfully.", flush=True)

        processing_deadline = time.monotonic() + 120

        while uploaded_file.state and uploaded_file.state.name == "PROCESSING":
            if time.monotonic() >= processing_deadline:
                raise TimeoutError(
                    "Gemini video processing exceeded 120 seconds."
                )

            print("[Gemini] Video still processing...", flush=True)
            time.sleep(5)
            uploaded_file = client.files.get(name=uploaded_file.name)

        if (
            uploaded_file.state
            and uploaded_file.state.name == "FAILED"
        ):
            raise RuntimeError("Gemini video processing failed.")

        print("[Gemini] Starting recipe generation...", flush=True)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[uploaded_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0,
            ),
        )

        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")

        recipe = json.loads(response.text)
        print("[Gemini] Recipe JSON parsed successfully.", flush=True)

        if not isinstance(recipe, dict):
            raise ValueError("Gemini response must be a JSON object.")

        return recipe

    finally:
        if uploaded_file is not None:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                # Cleanup failure must not hide the original error.
                pass
