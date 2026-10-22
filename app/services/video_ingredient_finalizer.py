def finalize_video_ingredients(ingredient_analysis: dict) -> list[dict]:
    """
    Build a clean ingredient list from the existing
    ingredient analysis results.

    Preserve timestamps and review statuses.
    """

    ingredients = []

    for item in ingredient_analysis.get("matched_ingredients", []):
        ingredients.append({
            "name": item["name"].strip(),
            "quantity": None,
            "unit": None,
            "first_seen_seconds": item.get("first_seen_seconds"),
            "status": "matched",
            "match_type": item.get("match_type"),
        })

    for item in ingredient_analysis.get("review_candidates", []):
        ingredients.append({
            "name": item["text"].strip(),
            "quantity": None,
            "unit": None,
            "first_seen_seconds": item.get("first_seen_seconds"),
            "status": "needs_review",
            "match_type": None,
        })

    # Sort ingredients by their first appearance in the video.
    ingredients.sort(
        key=lambda item: (
            item["first_seen_seconds"] is None,
            item["first_seen_seconds"]
            if item["first_seen_seconds"] is not None
            else float("inf"),
        )
    )

    return ingredients