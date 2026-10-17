
import json
import sqlite3
from pathlib import Path

from app.services.dataset_importer import parse_ingredients
from app.services.ingredient_normalizer import normalize_ingredients


DATABASE = Path("data/recipe_feedback.db")


def main():
    if not DATABASE.is_file():
        raise FileNotFoundError(
            f"Database not found: {DATABASE.resolve()}"
        )

    connection = sqlite3.connect(DATABASE)

    try:
        connection.row_factory = sqlite3.Row

        # Start an explicit transaction.
        connection.execute("BEGIN IMMEDIATE")

        rows = connection.execute(
            """
            SELECT id, recipe_json
            FROM dataset_recipes
            ORDER BY id
            """
        ).fetchall()

        print(f"Found {len(rows)} dataset recipes.")

        updated = 0
        skipped = 0

        for row in rows:
            recipe = json.loads(row["recipe_json"])

            raw_ingredients = recipe.get("raw_ingredients")

            if not isinstance(raw_ingredients, str) or not raw_ingredients.strip():
                print(
                    f"Skipping recipe {row['id']}: "
                    "missing raw ingredients"
                )
                skipped += 1
                continue

            parsed = parse_ingredients(raw_ingredients)
            normalized = normalize_ingredients(parsed)

            if not normalized:
                raise ValueError(
                    f"Recipe {row['id']} has no parsed ingredients."
                )

            if recipe.get("ingredients") == normalized:
                skipped += 1
                continue

            # Preserve all other recipe fields.
            recipe["ingredients"] = normalized

            connection.execute(
                """
                UPDATE dataset_recipes
                SET recipe_json = ?
                WHERE id = ?
                """,
                (
                    json.dumps(recipe, ensure_ascii=False),
                    row["id"],
                ),
            )

            updated += 1
            print(
                f"Updated recipe {row['id']}: "
                f"{recipe.get('title', 'Untitled')}"
            )

        connection.commit()

        print("\nMigration completed.")
        print("Updated:", updated)
        print("Skipped:", skipped)
        print("Total:", len(rows))

    except Exception:
        connection.rollback()
        print("Migration failed. Transaction rolled back.")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
