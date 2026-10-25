
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


DATABASE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "recipe_feedback.db"
)


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_recipe_db():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                meal_type TEXT,
                confidence REAL,
                needs_review INTEGER DEFAULT 0,
                recipe_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def save_recipe(recipe: dict, source_url: str):
    initialize_recipe_db()

    prediction = recipe.get("ml_prediction") or {}

    title = recipe.get("title") or "Untitled Recipe"
    meal_type = prediction.get("meal_type")
    confidence = prediction.get("confidence")
    needs_review = int(bool(prediction.get("needs_review")))

    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO recipes (
                source_url,
                title,
                meal_type,
                confidence,
                needs_review,
                recipe_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_url) DO UPDATE SET
                title = excluded.title,
                meal_type = excluded.meal_type,
                confidence = excluded.confidence,
                needs_review = excluded.needs_review,
                recipe_json = excluded.recipe_json,
                updated_at = excluded.updated_at
            """,
            (
                source_url,
                title,
                meal_type,
                confidence,
                needs_review,
                json.dumps(recipe, ensure_ascii=False),
                now,
                now,
            ),
        )


def list_saved_recipes():
    initialize_recipe_db()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                source_url,
                title,
                meal_type,
                confidence,
                needs_review,
                created_at,
                updated_at
            FROM recipes
            ORDER BY updated_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def get_recipe_stats():
    initialize_recipe_db()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total_recipes,
                COALESCE(SUM(needs_review), 0) AS needs_review
            FROM recipes
            """
        ).fetchone()

    return dict(row)


import hashlib


def initialize_dataset_recipe_db():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS dataset_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_key TEXT UNIQUE NOT NULL,
                source_record_id TEXT,
                source_url TEXT,
                title TEXT NOT NULL,
                meal_type TEXT,
                confidence REAL,
                needs_review INTEGER DEFAULT 0,
                recipe_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)


def save_dataset_recipe(recipe: dict):
    initialize_dataset_recipe_db()

    prediction = recipe.get("ml_prediction") or {}
    source_url = recipe.get("source_url") or ""
    source_record_id = recipe.get("source_record_id") or ""

    if source_url:
        identity = "url:" + source_url.strip().lower()
    else:
        identity = (
            "content:"
            + (recipe.get("title") or "").strip().lower()
            + "|"
            + (recipe.get("raw_ingredients") or "").strip().lower()
        )

    recipe_key = hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()

    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM dataset_recipes WHERE recipe_key = ?",
            (recipe_key,),
        ).fetchone()

        if existing:
            return {
                "status": "duplicate",
                "id": existing["id"],
            }

        cursor = connection.execute("""
            INSERT INTO dataset_recipes (
                recipe_key, source_record_id, source_url,
                title, meal_type, confidence, needs_review,
                recipe_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            recipe_key,
            source_record_id,
            source_url or None,
            recipe.get("title") or "Untitled Recipe",
            prediction.get("meal_type"),
            prediction.get("confidence"),
            int(bool(prediction.get("needs_review"))),
            json.dumps(recipe, ensure_ascii=False),
            now,
            now,
        ))

        return {
            "status": "saved",
            "id": cursor.lastrowid,
        }


def get_dataset_recipe_stats():
    initialize_dataset_recipe_db()

    with get_connection() as connection:
        row = connection.execute("""
            SELECT
                COUNT(*) AS total_recipes,
                COALESCE(SUM(needs_review), 0) AS needs_review
            FROM dataset_recipes
        """).fetchone()

    return dict(row)


def list_dataset_recipes(limit: int = 100):
    initialize_dataset_recipe_db()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                source_record_id,
                source_url,
                title,
                meal_type,
                confidence,
                needs_review,
                created_at
            FROM dataset_recipes
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        {
            "id": row["id"],
            "source_record_id": row["source_record_id"],
            "source_url": row["source_url"],
            "title": row["title"],
            "meal_type": row["meal_type"],
            "confidence": row["confidence"],
            "needs_review": bool(row["needs_review"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def get_dataset_recipe_by_id(recipe_id: int):
    initialize_dataset_recipe_db()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                recipe_json,
                created_at,
                updated_at
            FROM dataset_recipes
            WHERE id = ?
            """,
            (recipe_id,),
        ).fetchone()

    if row is None:
        return None

    recipe = json.loads(row["recipe_json"])

    return {
        "id": row["id"],
        "recipe": recipe,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def initialize_video_recipe_db():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS video_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_hash TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                recipe_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def save_video_recipe(recipe: dict, video_hash: str):
    video_hash = video_hash.lower()

    if len(video_hash) != 64 or any(
        char not in "0123456789abcdef" for char in video_hash
    ):
        raise ValueError("Invalid video SHA-256 hash.")

    initialize_video_recipe_db()

    now = datetime.now(timezone.utc).isoformat()
    title = recipe.get("title") or "Untitled Video Recipe"

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM video_recipes WHERE video_hash = ?",
            (video_hash,),
        ).fetchone()

        if existing:
            return {
                "status": "duplicate",
                "id": existing["id"],
            }

        cursor = connection.execute(
            """
            INSERT INTO video_recipes (
                video_hash,
                title,
                recipe_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                video_hash,
                title,
                json.dumps(recipe, ensure_ascii=False),
                now,
                now,
            ),
        )

        return {
            "status": "saved",
            "id": cursor.lastrowid,
        }


def list_video_recipes():
    initialize_video_recipe_db()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                title,
                created_at,
                updated_at
            FROM video_recipes
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]

def get_video_recipe_by_id(recipe_id: int):
    initialize_video_recipe_db()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, recipe_json, created_at, updated_at
            FROM video_recipes
            WHERE id = ?
            """,
            (recipe_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "recipe": json.loads(row["recipe_json"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }

def normalize_video_url(url: str) -> str:
    """
    Convert supported YouTube and Instagram URLs
    into a consistent cache key.
    """
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()
    path = parsed.path.strip("/")
    parts = path.split("/")

    if host in ("youtube.com", "www.youtube.com", "m.youtube.com"):
        if path == "watch":
            from urllib.parse import parse_qs
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif parts[0] in ("shorts", "embed") and len(parts) > 1:
            video_id = parts[1]
        else:
            raise ValueError("Unsupported YouTube URL.")

        if not video_id:
            raise ValueError("Missing YouTube video ID.")

        return f"youtube:{video_id}"

    if host == "youtu.be":
        if not path:
            raise ValueError("Missing YouTube video ID.")

        return f"youtube:{parts[0]}"

    if host in ("instagram.com", "www.instagram.com"):
        if len(parts) >= 2 and parts[0] in ("reel", "reels", "p", "tv"):
            return f"instagram:{parts[1]}"

        raise ValueError("Unsupported Instagram video URL.")

    raise ValueError("Unsupported video platform.")


def initialize_video_url_cache():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS video_url_cache (
                url_key TEXT PRIMARY KEY,
                video_recipe_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (video_recipe_id)
                    REFERENCES video_recipes(id)
            )
            """
        )


def get_cached_video_recipe(url: str):
    initialize_video_recipe_db()
    initialize_video_url_cache()

    url_key = normalize_video_url(url)

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                vr.id,
                vr.recipe_json
            FROM video_url_cache AS cache
            JOIN video_recipes AS vr
                ON vr.id = cache.video_recipe_id
            WHERE cache.url_key = ?
            """,
            (url_key,),
        ).fetchone()

    if row is None:
        return None

    recipe = json.loads(row["recipe_json"])

    recipe["storage"] = {
        "status": "cached",
        "id": row["id"],
    }

    recipe["source_url"] = url

    return recipe


def cache_video_url(url: str, recipe_id: int):
    initialize_video_recipe_db()
    initialize_video_url_cache()

    url_key = normalize_video_url(url)
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO video_url_cache (
                url_key,
                video_recipe_id,
                created_at
            )
            VALUES (?, ?, ?)
            ON CONFLICT(url_key) DO UPDATE SET
                video_recipe_id = excluded.video_recipe_id
            """,
            (url_key, recipe_id, now),
        )