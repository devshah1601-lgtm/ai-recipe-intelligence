
import json
import sqlite3
from collections import Counter
from pathlib import Path


DATABASE = Path("data/recipe_feedback.db")


def analyze_ingredient_quality():
    if not DATABASE.is_file():
        raise FileNotFoundError(
            f"Database not found: {DATABASE.resolve()}"
        )

    with sqlite3.connect(DATABASE) as connection:
        rows = connection.execute(
            "SELECT recipe_json FROM dataset_recipes"
        ).fetchall()

    total_recipes = len(rows)
    total_ingredients = 0
    with_quantity = 0
    with_unit = 0
    without_quantity = 0

    unit_counts = Counter()
    missing_quantity_examples = []

    for row in rows:
        recipe = json.loads(row[0])

        for ingredient in recipe.get("ingredients", []):
            if not isinstance(ingredient, dict):
                continue

            total_ingredients += 1

            quantity = ingredient.get("quantity")
            unit = ingredient.get("unit")
            name = ingredient.get("name", "")

            if quantity is not None and str(quantity).strip():
                with_quantity += 1
            else:
                without_quantity += 1

                if len(missing_quantity_examples) < 10:
                    missing_quantity_examples.append(name)

            if unit:
                with_unit += 1
                unit_counts[str(unit).lower()] += 1

    quantity_rate = (
        with_quantity / total_ingredients * 100
        if total_ingredients else 0
    )

    unit_rate = (
        with_unit / total_ingredients * 100
        if total_ingredients else 0
    )

    print("\n=== INGREDIENT QUALITY REPORT ===")
    print("Recipes analyzed:", total_recipes)
    print("Ingredients analyzed:", total_ingredients)
    print("With quantity:", with_quantity)
    print("With unit:", with_unit)
    print("Without quantity:", without_quantity)
    print(f"Quantity extraction rate: {quantity_rate:.2f}%")
    print(f"Unit extraction rate: {unit_rate:.2f}%")

    print("\nMost common units:")
    for unit, count in unit_counts.most_common(10):
        print(f"  {unit}: {count}")

    print("\nExamples without quantities:")
    for name in missing_quantity_examples:
        print(" -", name)

    print("\nAnalysis complete. No database changes made.")


if __name__ == "__main__":
    analyze_ingredient_quality()
