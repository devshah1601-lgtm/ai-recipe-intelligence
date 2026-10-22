import re


ALIASES = {
    "red chili powder": "red chilli powder",
    "chillies flakes": "chilli flakes",
    "chili flakes": "chilli flakes",
    "maggi masale": "maggi masala",
    "tomatoes": "tomato",
    "green chillies": "green chilli",
    "green chilies": "green chilli",
    "mozzarella cheese": "mozzarella",
    "spring onions": "spring onion",
    "potatoes": "potato",
    "eggs": "egg",
}


def normalize_ingredient(name: str) -> str:
    normalized = re.sub(r"\s+", " ", name.strip().lower())
    return ALIASES.get(normalized, normalized)


def compare_ingredients(
    gemini_ingredients: list[dict],
    ocr_ingredients: list[dict],
) -> list[dict]:

    ocr_lookup = {}

    for ingredient in ocr_ingredients:
        normalized = normalize_ingredient(ingredient["name"])
        ocr_lookup.setdefault(normalized, []).append(ingredient)

    results = []

    for ingredient in gemini_ingredients:
        normalized = normalize_ingredient(ingredient["name"])
        matches = ocr_lookup.get(normalized, [])

        results.append({
            "name": ingredient["name"],
            "quantity": ingredient.get("quantity"),
            "unit": ingredient.get("unit"),
            "ocr_confirmed": bool(matches),
            "ocr_first_seen_seconds": (
                min(
                    match["first_seen_seconds"]
                    for match in matches
                    if match.get("first_seen_seconds") is not None
                )
                if any(
                    match.get("first_seen_seconds") is not None
                    for match in matches
                )
                else None
            ),
            "verification_status": (
                "text_corroborated"
                if matches
                else "needs_visual_review"
            ),
        })

    return results