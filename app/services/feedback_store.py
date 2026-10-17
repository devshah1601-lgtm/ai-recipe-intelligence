
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "recipe_feedback.db"

ALLOWED_MEAL_TYPES = {
    "Breakfast",
    "Lunch",
    "Dinner",
    "Snack",
    "Dessert",
}


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_feedback_db():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS recipe_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_title TEXT NOT NULL,
                source_url TEXT NOT NULL,
                original_meal_type TEXT,
                corrected_meal_type TEXT NOT NULL,
                original_confidence REAL,
                ingredients_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def save_recipe_feedback(
    recipe_title,
    source_url,
    original_meal_type,
    corrected_meal_type,
    original_confidence,
    ingredients,
):
    if corrected_meal_type not in ALLOWED_MEAL_TYPES:
        raise ValueError("Invalid corrected meal type.")

    initialize_feedback_db()

    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO recipe_feedback (
                recipe_title,
                source_url,
                original_meal_type,
                corrected_meal_type,
                original_confidence,
                ingredients_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recipe_title,
                source_url,
                original_meal_type,
                corrected_meal_type,
                original_confidence,
                json.dumps(ingredients),
                created_at,
            ),
        )

        return {
            "id": cursor.lastrowid,
            "recipe_title": recipe_title,
            "original_meal_type": original_meal_type,
            "corrected_meal_type": corrected_meal_type,
            "created_at": created_at,
        }


def list_recipe_feedback():
    initialize_feedback_db()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM recipe_feedback
            ORDER BY id DESC
            """
        ).fetchall()

    results = []

    for row in rows:
        item = dict(row)
        item["ingredients"] = json.loads(item.pop("ingredients_json"))
        results.append(item)

    return results

def delete_recipe_feedback(feedback_id: int):
    initialize_feedback_db()

    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM recipe_feedback WHERE id = ?",
            (feedback_id,),
        )

        return cursor.rowcount > 0