from fastapi import FastAPI, UploadFile, File, HTTPException
import time
import asyncio
import subprocess
import tempfile
from pathlib import Path

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from app.services.video_ingredient_finalizer import finalize_video_ingredients
from app.services.video_ocr import get_video_ocr
from app.services.video_recipe_builder import build_video_recipe_data
from app.services.recipe_store import get_dataset_recipe_by_id
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from app.ml.recipe_classifier import predict_meal_type
from pydantic import BaseModel, HttpUrl
from app.models.recipe import Recipe
from app.services.dataset_importer import import_dataset_csv
from app.services.recipe_store import list_dataset_recipes
import requests
import csv
import io
from app.services.recipe_store import save_dataset_recipe
from app.services.feedback_store import (
    initialize_feedback_db,
    save_recipe_feedback,
    list_recipe_feedback,
    delete_recipe_feedback,
)
from app.services.recipe_store import (
    save_recipe,
    list_saved_recipes,
    get_recipe_stats,
    save_dataset_recipe,
)
from app.services.recipe_store import get_dataset_recipe_stats
from app.services.video_ingredient_extractor import extract_video_ingredients
from app.services.gemini_video_analyzer import analyze_video_with_gemini
from app.services.ingredient_verifier import compare_ingredients
from threading import Lock
import hashlib
from app.services.recipe_store import (
    save_video_recipe,
    list_video_recipes,
    get_video_recipe_by_id,
)

app = FastAPI(title="AI Recipe Intelligence Platform", version="0.1.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

class URLRequest(BaseModel):
    url: HttpUrl

@app.get("/health")
def health():
    return {"status": "ok", "phase": "foundation"}

@app.get("/schema/recipe")
def recipe_schema():
    return Recipe.model_json_schema()

@app.post("/recipes/url", status_code=501)
def recipe_url(payload: URLRequest):
    raise HTTPException(501, "Recipe extraction is scheduled for Phase 2")


MAX_CSV_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_CSV_ROWS = 1000



def process_recipe_url(url: str) -> dict:
    raw_recipe = scrape_recipe(url)

    recipe = normalize_recipe(raw_recipe)

    recipe["ml_prediction"] = predict_meal_type(recipe)

    # Save successfully extracted recipe to SQLite
    save_recipe(recipe, url)

    return recipe



@app.post("/recipes/csv")
async def recipe_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a .csv file."
        )

    try:
        content = await file.read(MAX_CSV_BYTES + 1)
    finally:
        await file.close()

    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(
            status_code=413,
            detail="CSV file must be 10 MB or smaller."
        )

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="CSV file must use UTF-8 encoding."
        )

    try:
        reader = csv.DictReader(io.StringIO(text, newline=""))

        if not reader.fieldnames:
            raise HTTPException(
                status_code=400,
                detail="CSV file is empty or missing a header."
            )

        headers = {
            header.strip().lower(): header
            for header in reader.fieldnames
            if header
        }

        if "url" not in headers:
            raise HTTPException(
                status_code=400,
                detail="CSV must contain a column named 'url'."
            )

        url_column = headers["url"]
        rows = list(reader)

    except csv.Error as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid CSV format: {exc}"
        )

    if not rows:
        raise HTTPException(
            status_code=400,
            detail="CSV contains no recipe URLs."
        )

    if len(rows) > MAX_CSV_ROWS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_CSV_ROWS} rows allowed per upload."
        )

    results = []

    for row_number, row in enumerate(rows, start=2):
        url = (row.get(url_column) or "").strip()

        if not url:
            results.append({
                "row": row_number,
                "url": "",
                "status": "error",
                "error": "Missing URL."
            })
            continue

        try:
            recipe = await run_in_threadpool(process_recipe_url, url)

            results.append({
                "row": row_number,
                "url": url,
                "status": "success",
                "recipe": recipe
            })

        except (ValueError, requests.exceptions.RequestException) as exc:
            results.append({
                "row": row_number,
                "url": url,
                "status": "error",
                "error": str(exc)
            })

        except Exception:
            results.append({
                "row": row_number,
                "url": url,
                "status": "error",
                "error": "Recipe processing failed."
            })

    success_count = sum(
        item["status"] == "success"
        for item in results
    )

    return {
        "total": len(results),
        "successful": success_count,
        "failed": len(results) - success_count,
        "results": results
    }


@app.post("/recipes/import-csv")
async def import_recipe_dataset(file: UploadFile = File(...)):
    MAX_DATASET_BYTES = 10 * 1024 * 1024
    MAX_DATASET_ROWS = 1000

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file.",
        )

    try:
        content = await file.read(MAX_DATASET_BYTES + 1)
    finally:
        await file.close()

    if len(content) > MAX_DATASET_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Dataset CSV must be 10 MB or smaller.",
        )

    try:
        result = await run_in_threadpool(
            import_dataset_csv,
            content,
        )
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="CSV must use UTF-8 encoding.",
        )
    except (ValueError, csv.Error) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if result["total"] == 0:
        raise HTTPException(
            status_code=400,
            detail="Dataset CSV contains no recipe rows.",
        )

    if result["total"] > MAX_DATASET_ROWS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_DATASET_ROWS} rows per upload.",
        )

    
    saved = 0
    duplicates = 0
    storage_failed = 0

    for item in result["results"]:
        if item["status"] != "success":
            continue

        try:
            storage_result = await run_in_threadpool(
                save_dataset_recipe,
                item["recipe"],
            )

            item["storage_status"] = storage_result["status"]
            item["database_id"] = storage_result["id"]

            if storage_result["status"] == "saved":
                saved += 1
            elif storage_result["status"] == "duplicate":
                duplicates += 1

        except Exception as exc:
            item["storage_status"] = "error"
            item["storage_error"] = str(exc)
            storage_failed += 1

    result["saved"] = saved
    result["duplicates"] = duplicates
    result["storage_failed"] = storage_failed


    return result


MAX_VIDEO_BYTES = 50 * 1024 * 1024  # 50 MB
gemini_analysis_lock = Lock()


def process_video(video_path: Path, frames_dir: Path):
    total_start = time.perf_counter()

    frames_dir.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-loglevel", "error",
        "-i", str(video_path),
        "-vf", "fps=2",
        "-frames:v", "120",
        str(frames_dir / "frame_%03d.png"),
    ]

    print("[Video] Starting FFmpeg frame extraction...", flush=True)

    start = time.perf_counter()

    subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=90,
    )

    ffmpeg_time = time.perf_counter() - start

    print("[Video] FFmpeg frame extraction completed.", flush=True)

    print("[Video] Starting EasyOCR extraction...", flush=True)

    start = time.perf_counter()
    ocr = get_video_ocr()
    model_load_time = time.perf_counter() - start

    start = time.perf_counter()
    raw_results = ocr.extract_text(str(frames_dir))
    ocr_time = time.perf_counter() - start

    start = time.perf_counter()
    result = build_video_recipe_data(raw_results)
    recipe_builder_time = time.perf_counter() - start

    print("[Video] EasyOCR extraction completed.", flush=True)

    start = time.perf_counter()
    ingredient_analysis = extract_video_ingredients(raw_results)
    ingredient_time = time.perf_counter() - start

    # Keep original ingredients for debugging
    result["original_ingredients"] = result.get("ingredients", []).copy()

    # Generate the clean ingredient list
    final_ingredients = finalize_video_ingredients(ingredient_analysis)

    # Update the final API response
    result["ingredients"] = final_ingredients
    result["ingredient_count"] = len(final_ingredients)

    # Preserve OCR and ingredient analysis
    result["raw_detection_count"] = len(raw_results)
    result["ingredient_analysis"] = ingredient_analysis

    print("\n=== VIDEO PERFORMANCE REPORT ===")
    print(f"FFmpeg: {ffmpeg_time:.2f}s")
    print(f"OCR model initialization: {model_load_time:.2f}s")
    print(f"OCR frame processing: {ocr_time:.2f}s")
    print(f"Recipe builder: {recipe_builder_time:.2f}s")
    print(f"Ingredient analysis: {ingredient_time:.2f}s")
    print(f"Total processing: {time.perf_counter() - total_start:.2f}s")
    print("================================\n")

    return result


@app.post("/videos/upload")
async def video_upload(file: UploadFile = File(...)):
    filename = file.filename or ""

    if Path(filename).suffix.lower() != ".mp4":
        raise HTTPException(
            status_code=400,
            detail="Only MP4 videos are supported right now.",
        )

    if file.content_type not in ("video/mp4", "application/octet-stream"):
        raise HTTPException(
            status_code=400,
            detail="Invalid video content type.",
        )

    try:
        with tempfile.TemporaryDirectory(prefix="recipe_video_") as temp:
            work_dir = Path(temp)
            video_path = work_dir / "input.mp4"
            frames_dir = work_dir / "frames"

            total_bytes = 0

            with video_path.open("wb") as destination:
                while chunk := await file.read(1024 * 1024):
                    total_bytes += len(chunk)

                    if total_bytes > MAX_VIDEO_BYTES:
                        raise HTTPException(
                            status_code=413,
                            detail="Video exceeds the 50 MB limit.",
                        )

                    destination.write(chunk)

            if total_bytes == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded video is empty.",
                )

            try:
                result = await run_in_threadpool(
                    process_video,
                    video_path,
                    frames_dir,
                )

                return result

            except subprocess.TimeoutExpired:
                raise HTTPException(
                    status_code=408,
                    detail="Video frame extraction timed out.",
                )

            except subprocess.CalledProcessError:
                raise HTTPException(
                    status_code=422,
                    detail="FFmpeg could not decode the uploaded video.",
                )

    finally:
        await file.close()


from pydantic import BaseModel
from app.services.ai_extractor import extract_ingredients_rules


class IngredientRequest(BaseModel):
    text: str


@app.post("/videos/analyze-recipe")
async def analyze_video_recipe(file: UploadFile = File(...)):
    filename = file.filename or ""

    if Path(filename).suffix.lower() != ".mp4":
        raise HTTPException(
            status_code=400,
            detail="Only MP4 videos are supported.",
        )

    if file.content_type not in (
        "video/mp4",
        "application/octet-stream",
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid video content type.",
        )

    try:
        with tempfile.TemporaryDirectory(
            prefix="recipe_analysis_"
        ) as temp:
            work_dir = Path(temp)
            video_path = work_dir / "input.mp4"
            frames_dir = work_dir / "frames"

            total_bytes = 0
            video_hasher = hashlib.sha256()

            with video_path.open("wb") as destination:
                while chunk := await file.read(1024 * 1024):
                    total_bytes += len(chunk)

                    if total_bytes > MAX_VIDEO_BYTES:
                        raise HTTPException(
                            status_code=413,
                            detail="Video exceeds the 50 MB limit.",
                        )

                    destination.write(chunk)
                    video_hasher.update(chunk)

            if total_bytes == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded video is empty.",
                )

            try:
                # Gemini generates the structured recipe.
                def analyze_with_lock():
                    if not gemini_analysis_lock.acquire(blocking=False):
                        raise RuntimeError("GEMINI_ANALYSIS_BUSY")

                    try:
                        return analyze_video_with_gemini(video_path)
                    finally:
                        gemini_analysis_lock.release()

                gemini_recipe = await run_in_threadpool(
                    analyze_with_lock
                )
            except ValueError as exc:
                print(
                    f"Gemini returned an invalid recipe: {exc}",
                    flush=True,
                )

                raise HTTPException(
                    status_code=502,
                    detail="AI returned an invalid recipe structure. Please try again.",
                ) from exc

            except RuntimeError as exc:
                if str(exc) == "GEMINI_ANALYSIS_BUSY":
                    raise HTTPException(
                        status_code=429,
                        detail="A Gemini video analysis is already running. Please wait."
                    ) from exc

                print(f"Gemini analysis failed: {type(exc).__name__}: {exc}")
                raise HTTPException(
                    status_code=502,
                    detail="Gemini video analysis failed."
                ) from exc

            except Exception as exc:
                print(
                    f"Gemini analysis failed: {type(exc).__name__}: {exc}",
                    flush=True
                )

                if getattr(exc, "code", None) == 503:
                    raise HTTPException(
                        status_code=503,
                        detail="AI recipe analysis is temporarily unavailable. Please try again later.",
                        headers={"Retry-After": "120"},
                    ) from exc

                raise HTTPException(
                    status_code=502,
                    detail="Gemini video analysis failed."
                ) from exc

            try:
                # EasyOCR extracts supporting ingredient evidence.
                ocr_result = await run_in_threadpool(
                    process_video,
                    video_path,
                    frames_dir,
                )

            except (
                subprocess.TimeoutExpired,
                subprocess.CalledProcessError,
            ) as exc:
                raise HTTPException(
                    status_code=422,
                    detail="Local video processing failed.",
                ) from exc

            verified_ingredients = compare_ingredients(
                gemini_recipe.get("ingredients", []),
                ocr_result.get("ingredients", []),
            )

            recipe = {
                "source_type": "video",
                "extraction_method": "gemini_with_ocr_verification",
                "title": gemini_recipe.get("title"),
                "ingredients": verified_ingredients,
                "ingredient_count": len(verified_ingredients),
                "instructions": gemini_recipe.get(
                    "instructions", []
                ),
                "uncertain_details": gemini_recipe.get(
                    "uncertain_details", []
                ),
                "verification_summary": {
                    "ocr_corroborated": sum(
                        ingredient["ocr_confirmed"]
                        for ingredient in verified_ingredients
                    ),
                    "needs_visual_review": sum(
                        not ingredient["ocr_confirmed"]
                        for ingredient in verified_ingredients
                    ),
                },
                "ocr_ingredient_analysis": ocr_result.get(
                    "ingredient_analysis", {}
                ),
            }

            save_result = await run_in_threadpool(
                save_video_recipe,
                recipe,
                video_hasher.hexdigest(),
            )

            recipe["storage"] = {
                "status": save_result["status"],
                "id": save_result["id"],
            }

            return recipe

    finally:
        await file.close()



@app.post("/extract-ingredients")
def extract_ingredients_api(request: IngredientRequest):
    result = extract_ingredients_rules(request.text)
    return result


from fastapi import HTTPException
from app.services.recipe_scraper import scrape_recipe
from app.services.recipe_normalizer import normalize_recipe


class RecipeURLRequest(BaseModel):
    url: str



@app.post("/extract-recipe-url")
def extract_recipe_url(request: RecipeURLRequest):
    try:
        raw_recipe = scrape_recipe(request.url)

        recipe = normalize_recipe(raw_recipe)

        recipe["ml_prediction"] = predict_meal_type(recipe)
    
        save_recipe(recipe, request.url)

        return recipe

    except (ValueError, requests.exceptions.RequestException) as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )


from typing import Any, Literal
from pydantic import Field


class RecipeFeedbackRequest(BaseModel):
    recipe_title: str = Field(min_length=1, max_length=300)
    source_url: HttpUrl
    original_meal_type: str | None = None
    corrected_meal_type: Literal[
        "Breakfast", "Lunch", "Dinner", "Snack", "Dessert"
    ]
    original_confidence: float | None = Field(
        default=None, ge=0, le=1
    )
    ingredients: list[Any] = Field(default_factory=list)


@app.post("/feedback/recipe")
def submit_recipe_feedback(request: RecipeFeedbackRequest):
    result = save_recipe_feedback(
        recipe_title=request.recipe_title,
        source_url=str(request.source_url),
        original_meal_type=request.original_meal_type,
        corrected_meal_type=request.corrected_meal_type,
        original_confidence=request.original_confidence,
        ingredients=request.ingredients,
    )

    return {
        "status": "saved",
        "feedback": result,
    }


@app.get("/feedback/recipes")
def get_recipe_feedback():
    return {
        "feedback": list_recipe_feedback()
    }

@app.delete("/feedback/recipe/{feedback_id}")
def remove_recipe_feedback(feedback_id: int):
    if feedback_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid feedback ID.",
        )

    deleted = delete_recipe_feedback(feedback_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Feedback not found.",
        )

    return {
        "status": "deleted",
        "feedback_id": feedback_id,
    }

@app.get("/recipes/saved")
def get_saved_recipes():
    return {
        "recipes": list_saved_recipes()
    }


@app.get("/recipes/stats")
def get_saved_recipe_stats():
    return get_recipe_stats()


@app.get("/recipes/dataset/stats")
def dataset_recipe_stats():
    return get_dataset_recipe_stats()


@app.get("/recipes/dataset/saved")
def get_saved_dataset_recipes(limit: int = 100):
    limit = max(1, min(limit, 1000))

    recipes = list_dataset_recipes(limit)

    return {
        "count": len(recipes),
        "recipes": recipes,
    }


@app.get("/recipes/dataset/saved/{recipe_id}")
def get_dataset_recipe_details(recipe_id: int):
    if recipe_id < 1:
        raise HTTPException(
            status_code=400,
            detail="Recipe ID must be positive.",
        )

    result = get_dataset_recipe_by_id(recipe_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found.",
        )

    return result

@app.get("/recipes/dataset/saved/{recipe_id}")
def get_dataset_recipe_details(recipe_id: int):
    if recipe_id < 1:
        raise HTTPException(
            status_code=400,
            detail="Recipe ID must be positive.",
        )

    result = get_dataset_recipe_by_id(recipe_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found.",
        )

    return result

@app.get("/recipes/video/saved")
async def get_saved_video_recipes():
    recipes = await run_in_threadpool(list_video_recipes)

    return {
        "total": len(recipes),
        "recipes": recipes,
    }

@app.get("/recipes/video/saved/{recipe_id}")
async def get_saved_video_recipe(recipe_id: int):
    result = await run_in_threadpool(
        get_video_recipe_by_id,
        recipe_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Saved video recipe not found.",
        )

    return result