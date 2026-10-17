
import csv
from collections import Counter
from pathlib import Path

from app.services.dataset_importer import parse_ingredients
from app.services.ingredient_normalizer import normalize_ingredients


DATASET = Path("data/raw/IndianFoodDatasetCSV.csv")


def main():
    if not DATASET.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET.resolve()}"
        )

    total_recipes = 0
    total_ingredients = 0
    with_quantity = 0
    with_unit = 0
    missing_examples = []
    units = Counter()

    with DATASET.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            raw_text = (
                row.get("TranslatedIngredients")
                or row.get("Ingredients")
                or ""
            )

            if not raw_text.strip():
                continue

            total_recipes += 1

            parsed = parse_ingredients(raw_text)
            normalized = normalize_ingredients(parsed)

            for ingredient in normalized:
                total_ingredients += 1

                quantity = ingredient.get("quantity")
                unit = ingredient.get("unit")

                if quantity is not None and str(quantity).strip():
                    with_quantity += 1
                elif len(missing_examples) < 15:
                    missing_examples.append(
                        ingredient.get("name", "")
                    )

                if unit:
                    with_unit += 1
                    units[unit] += 1

    quantity_rate = (
        100 * with_quantity / total_ingredients
        if total_ingredients else 0
    )

    unit_rate = (
        100 * with_unit / total_ingredients
        if total_ingredients else 0
    )

    print("\n=== FULL DATASET INGREDIENT ANALYSIS ===")
    print("Recipes analyzed:", total_recipes)
    print("Ingredients analyzed:", total_ingredients)
    print("With quantity:", with_quantity)
    print("With unit:", with_unit)
    print(f"Quantity coverage: {quantity_rate:.2f}%")
    print(f"Unit coverage: {unit_rate:.2f}%")

    print("\nTop measurement units:")
    for unit, count in units.most_common(10):
        print(f"  {unit}: {count}")

    print("\nExamples without quantities:")
    for example in missing_examples:
        print(" -", example)

    print("\nRead-only analysis completed.")


if __name__ == "__main__":
    main()
