
import re


def normalize_time(value):
    if not value:
        return None

    match = re.fullmatch(
        r"P(?:T(?:(\d+)H)?(?:(\d+)M)?)",
        str(value),
        re.IGNORECASE
    )

    if not match:
        return value

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)

    parts = []

    if hours:
        parts.append(
            f"{hours} hour{'s' if hours != 1 else ''}"
        )

    if minutes:
        parts.append(
            f"{minutes} minute{'s' if minutes != 1 else ''}"
        )

    return " ".join(parts) or "0 minutes"


def normalize_servings(value):
    if value is None:
        return {"value": None, "unit": None, "raw": None}

    raw = str(value)
    match = re.search(r"\d+", raw)

    if not match:
        return {"value": None, "unit": None, "raw": raw}

    number = int(match.group())

    if "makes" in raw.lower():
        unit = "items"
    elif "serv" in raw.lower():
        unit = "servings"
    else:
        unit = None

    return {
        "value": number,
        "unit": unit,
        "raw": raw
    }


def normalize_ingredient(ingredient):
    raw_name = ingredient.get("name", "").strip()
    quantity = ingredient.get("quantity")

    optional = bool(
        re.search(r"\boptional\b", raw_name, re.I)
    )

    name = re.sub(
        r"\s*\(?optional\)?\s*",
        " ",
        raw_name,
        flags=re.I
    ).strip()

    note = None

    if re.search(r"\bto serve\b", name, re.I):
        note = "to serve"
        name = re.sub(
            r"\bto serve\b", "", name, flags=re.I
        ).strip()

    if quantity:
        quantity = re.sub(
            r"(\d)\s*(g|kg|ml|l)\b",
            r"\1 \2",
            str(quantity),
            flags=re.I
        )

    return {
        "name": name,
        "quantity": quantity,
        "optional": optional,
        "note": note,
        "original_name": raw_name
    }


def normalize_recipe(recipe):
    return {
        **recipe,
        "prep_time": normalize_time(
            recipe.get("prep_time")
        ),
        "cook_time": normalize_time(
            recipe.get("cook_time")
        ),
        "total_time": normalize_time(
            recipe.get("total_time")
        ),
        "servings": normalize_servings(
            recipe.get("servings")
        ),
        "ingredients": [
            normalize_ingredient(item)
            for item in recipe.get("ingredients", [])
        ]
    }
