import re
from difflib import SequenceMatcher


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


FUZZY_THRESHOLD = 0.88


def normalize_ingredient(name: str) -> str:
    normalized = re.sub(
        r"\s+",
        " ",
        name.strip().lower()
    )

    return ALIASES.get(normalized, normalized)


def ingredient_similarity(a: str, b: str) -> float:
    return SequenceMatcher(
        None,
        normalize_ingredient(a),
        normalize_ingredient(b)
    ).ratio()


def compare_ingredients(
    gemini_ingredients: list[dict],
    ocr_ingredients: list[dict],
) -> list[dict]:

    results = []

    for ingredient in gemini_ingredients:
        gemini_name = ingredient["name"]
        normalized_gemini = normalize_ingredient(gemini_name)

        exact_matches = []
        fuzzy_matches = []

        for ocr_ingredient in ocr_ingredients:
            ocr_name = ocr_ingredient["name"]
            normalized_ocr = normalize_ingredient(ocr_name)

            if normalized_gemini == normalized_ocr:
                exact_matches.append(ocr_ingredient)
                continue

            similarity = ingredient_similarity(
                gemini_name,
                ocr_name
            )

            if similarity >= FUZZY_THRESHOLD:
                fuzzy_matches.append(ocr_ingredient)

        if exact_matches:
            matches = exact_matches
            match_type = "exact"

        elif fuzzy_matches:
            matches = fuzzy_matches
            match_type = "fuzzy"

        else:
            matches = []
            match_type = None

        timestamps = [
            match["first_seen_seconds"]
            for match in matches
            if match.get("first_seen_seconds") is not None
        ]

        results.append({
            "name": gemini_name,
            "quantity": ingredient.get("quantity"),
            "unit": ingredient.get("unit"),
            "ocr_confirmed": bool(matches),
            "ocr_first_seen_seconds": (
                min(timestamps)
                if timestamps
                else None
            ),
            "verification_status": (
            "text_corroborated"
            if match_type == "exact"
            else "possible_text_match"
            if match_type == "fuzzy"
            else "needs_visual_review"
        ),
            "match_type": match_type,
            "ocr_source_status": (
    matches[0].get("status")
    if matches
    else None
),
        })

    return results