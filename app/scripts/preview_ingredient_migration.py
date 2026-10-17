
import json
import sqlite3
from pathlib import Path

from app.services.ingredient_normalizer import normalize_ingredients


DATABASE = Path("data/recipe_feedback.db")


def main():
    if not DATABASE.is_file():
        raise FileNotFoundError(
            f"Database not found: {DATABASE.resolve()}"
        )

    with sqlite3.connect(DATABASE) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT id, recipe_json
            FROM dataset_recipes
            ORDER BY id
            """
        ).fetchall()

    print(f"Found {len(rows)} saved dataset recipes.")

    changed_recipes = 0

    for row in rows:
        recipe = json.loads(row["recipe_json"])
        ingredients = recipe.get("ingredients", [])

        if not isinstance(ingredients, list):
            print(f"Recipe {row['id']}: invalid ingredients format")
            continue

        if not all(isinstance(item, dict) for item in ingredients):
            print(f"Recipe {row['id']}: unsupported ingredient format")
            continue

        normalized = normalize_ingredients(ingredients)

        if normalized != ingredients:
            changed_recipes += 1

            print(
                f"\nRecipe {row['id']}: "
                f"{recipe.get('title', 'Untitled')}"
            )

            for old, new in zip(ingredients, normalized):
                if old != new:
                    print(" BEFORE:", old)
                    print(" AFTER: ", new)
                    break

    print("\nMigration preview complete.")
    print("Recipes requiring updates:", changed_recipes)
    print("No database records were modified.")


if __name__ == "__main__":
    main()
