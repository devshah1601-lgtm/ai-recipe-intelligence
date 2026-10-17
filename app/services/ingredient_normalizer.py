
import re
from typing import Any


UNITS = [
    "tablespoons", "tablespoon",
    "teaspoons", "teaspoon",
    "kilograms", "kilogram",
    "grams", "gram",
    "litres", "litre",
    "liters", "liter",
    "cups", "cup",
    "ml", "kg", "g",
    "tbsp", "tsp",
    "pieces", "piece",
    "pinches", "pinch",
]


UNIT_ALIASES = {
    "cups": "cup",
    "tablespoons": "tablespoon",
    "tbsp": "tablespoon",
    "teaspoons": "teaspoon",
    "tsp": "teaspoon",
    "grams": "gram",
    "g": "gram",
    "kilograms": "kilogram",
    "kg": "kilogram",
    "litres": "liter",
    "litre": "liter",
    "liters": "liter",
    "pieces": "piece",
    "pinches": "pinch",
}

UNIT_PATTERN = "|".join(
    re.escape(unit)
    for unit in sorted(UNITS, key=len, reverse=True)
)


QUANTITY_PATTERN = re.compile(
    rf"^\s*(?P<amount>"
    rf"\d+\s*-\s*\d+\s*/\s*\d+"
    rf"|\d+\s+\d+\s*/\s*\d+"
    rf"|\d+\s*/\s*\d+"
    rf"|\d+(?:\.\d+)?"
    rf")\s*(?P<unit>{UNIT_PATTERN})\s*$",
    re.IGNORECASE,
)




def normalize_ingredient(
    ingredient: dict[str, Any],
) -> dict[str, Any]:
    result = ingredient.copy()
    original_quantity = ingredient.get("quantity")

    if original_quantity is None:
        result.setdefault("original_quantity", None)
        result.setdefault("unit", None)
        return result

    quantity_text = str(original_quantity).strip()

    # Preserve the original value if already normalized.
    result.setdefault("original_quantity", quantity_text)

    existing_unit = ingredient.get("unit")

    if existing_unit:
        raw_unit = str(existing_unit).strip().lower()
        result["quantity"] = quantity_text
        result["unit"] = UNIT_ALIASES.get(raw_unit, raw_unit)
        return result

    match = QUANTITY_PATTERN.fullmatch(quantity_text)

    if match:
        result["quantity"] = match.group("amount")
        raw_unit = match.group("unit").lower()
        result["unit"] = UNIT_ALIASES.get(raw_unit, raw_unit)
    else:
        result["quantity"] = quantity_text
        result["unit"] = None

    return result



def normalize_ingredients(
    ingredients: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        normalize_ingredient(ingredient)
        for ingredient in ingredients
    ]
