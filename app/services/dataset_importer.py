
import csv
import io
import re
from app.ml.recipe_classifier import predict_meal_type
from app.services.ingredient_normalizer import normalize_ingredients


def clean_text(value):
    return str(value or "").strip()


def get_value(row, *columns):
    for column in columns:
        value = clean_text(row.get(column))
        if value:
            return value
    return ""



def parse_ingredients(text):
    if not text:
        return []

    ingredients = []

    # Matches quantities such as:
    # 6 Karela
    # 1/2 teaspoon cumin
    # 2-1/2 cups rice
    # 3 tablespoon gram flour
    
    quantity_pattern = re.compile(
        r"^\s*(?P<amount>"
        r"\d+\s*-\s*\d+\s*/\s*\d+"
        r"|\d+\s+\d+\s*/\s*\d+"
        r"|\d+\s*/\s*\d+"
        r"|\d+(?:\.\d+)?"
        r")\s*"
        r"(?P<unit>"
        r"cups?|tablespoons?|tbsp|teaspoons?|tsp|"
        r"grams?|g|kg|ml|litres?|liters?|"
        r"pieces?|pinches?"
        r")?"
        r"\s+(?P<name>.+)$",
        flags=re.IGNORECASE,
    )


    for part in text.split(","):
        part = re.sub(r"\s+", " ", part).strip()

        if not part:
            continue

        match = quantity_pattern.match(part)

        if match:
            amount = match.group("amount")
            unit = match.group("unit") or ""
            name = match.group("name").strip()

            ingredients.append({
                "name": name,
                "quantity": f"{amount} {unit}".strip(),
            })
        else:
            ingredients.append({
                "name": part,
                "quantity": None,
            })

    return ingredients




def parse_instructions(text):
    if not text:
        return []

    # Normalize unusual spaces and line breaks.
    text = text.replace("\xa0", " ").strip()
    text = re.sub(r"\s+", " ", text)

    # Split sentences even when the source omits
    # a space, e.g. "Keep aside.Heat oil".
    steps = re.split(
        r"(?<=[.!?])\s*(?=[A-Z])",
        text,
    )

    return [
        step.strip()
        for step in steps
        if step.strip()
    ]



def parse_integer(value):
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None

 
def convert_dataset_row(row):
    title = get_value(
        row,
        "TranslatedRecipeName",
        "RecipeName",
        "title",
    )

    ingredients_text = get_value(
        row,
        "TranslatedIngredients",
        "Ingredients",
        "ingredients",
    )

    instructions_text = get_value(
        row,
        "TranslatedInstructions",
        "Instructions",
        "instructions",
    )

    if not title:
        raise ValueError("Missing recipe title.")

    
    if not ingredients_text:
        raise ValueError("Missing ingredients.")

    # Step 1: Extract ingredients from the CSV text.
    ingredients = parse_ingredients(ingredients_text)

    # Step 2: Separate quantities and units.
    normalized_ingredients = normalize_ingredients(ingredients)

    recipe = {

            "title": title,
            "ingredients": normalized_ingredients,
            "instructions": parse_instructions(instructions_text),
            "prep_time_minutes": parse_integer(
                get_value(row, "PrepTimeInMins")
            ),
            "cook_time_minutes": parse_integer(
                get_value(row, "CookTimeInMins")
            ),
            "total_time_minutes": parse_integer(
                get_value(row, "TotalTimeInMins")
            ),
            "servings": parse_integer(
                get_value(row, "Servings")
            ),
            "cuisine": get_value(row, "Cuisine"),
            "course": get_value(row, "Course"),
            "diet": get_value(row, "Diet"),
            "source_url": get_value(row, "URL", "source_url"),
            "source_record_id": get_value(row, "Srno", "recipe_id"),
            "raw_ingredients": ingredients_text,
            "raw_instructions": instructions_text,
        }

    return recipe


def import_dataset_csv(content):
    text = content.decode("utf-8-sig")

    reader = csv.DictReader(io.StringIO(text, newline=""))

    if not reader.fieldnames:
        raise ValueError("CSV is empty or missing headers.")

    results = []

    for row_number, row in enumerate(reader, start=2):
        
        try:
            recipe = convert_dataset_row(row)

            # Predict meal type using our trained ML model.
            recipe["ml_prediction"] = predict_meal_type(recipe)

            results.append({
                "row": row_number,
                "status": "success",
                "recipe": recipe,
            })


        except ValueError as exc:
            results.append({
                "row": row_number,
                "status": "error",
                "error": str(exc),
            })

    return {
        "total": len(results),
        "successful": sum(
            item["status"] == "success"
            for item in results
        ),
        "failed": sum(
            item["status"] == "error"
            for item in results
        ),
        "results": results,
    }
