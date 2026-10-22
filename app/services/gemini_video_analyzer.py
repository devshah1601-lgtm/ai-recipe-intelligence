
import json
import os
import time
from pathlib import Path

from google import genai
from google.genai import types


GEMINI_MODEL = "gemini-3.5-flash-lite"
def validate_recipe_response(recipe: dict) -> dict:
    if not isinstance(recipe, dict):
        raise ValueError("Gemini response must be a JSON object.")

    if not isinstance(recipe.get("title"), str) or not recipe["title"].strip():
        raise ValueError("Gemini response has an invalid title.")

    ingredients = recipe.get("ingredients")

    if not isinstance(ingredients, list):
        raise ValueError("Gemini ingredients must be a list.")

    for index, ingredient in enumerate(ingredients):
        if not isinstance(ingredient, dict):
            raise ValueError(
                f"Ingredient {index + 1} must be an object."
            )

        if (
            not isinstance(ingredient.get("name"), str)
            or not ingredient["name"].strip()
        ):
            raise ValueError(
                f"Ingredient {index + 1} has an invalid name."
            )

        quantity = ingredient.get("quantity")

        if quantity is not None and (
            isinstance(quantity, bool)
            or not isinstance(quantity, (str, int, float))
        ):
            raise ValueError(
                f"Ingredient {index + 1} has an invalid quantity."
            )

        unit = ingredient.get("unit")

        if unit is not None and not isinstance(unit, str):
            raise ValueError(
                f"Ingredient {index + 1} has an invalid unit."
            )

    instructions = recipe.get("instructions")
    if not isinstance(instructions, list):
        raise ValueError("Gemini instructions must be a list.")

    for index, instruction in enumerate(instructions):
        if not isinstance(instruction, dict):
            raise ValueError(f"Instruction {index + 1} must be an object.")

        if not isinstance(instruction.get("description"), str) or not instruction["description"].strip():
            raise ValueError(f"Instruction {index + 1} has an invalid description.")

        step_number = instruction.get("step_number")
        if (
            not isinstance(step_number, int)
            or isinstance(step_number, bool)
            or step_number < 1
        ):
            raise ValueError(
                f"Instruction {index + 1} has an invalid step number."
            )

        timestamp = instruction.get("timestamp_seconds")
        if timestamp is not None and (
            isinstance(timestamp, bool)
            or not isinstance(timestamp, (int, float))
            or not 0 <= timestamp < float("inf")
        ):
            raise ValueError(
                f"Instruction {index + 1} has an invalid timestamp."
            )

    uncertain_details = recipe.get("uncertain_details", [])
    if not isinstance(uncertain_details, list):
        raise ValueError("Gemini uncertain_details must be a list.")

    recipe["uncertain_details"] = uncertain_details

    return recipe


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

        return validate_recipe_response(recipe)

    finally:
        if uploaded_file is not None:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                # Cleanup failure must not hide the original error.
                pass
