from difflib import SequenceMatcher

from app.services.video_ocr_cleaner import clean_ocr_results


def normalize_name(text):
    return " ".join(text.lower().split())


def build_video_recipe_data(ocr_results):
    cleaned = clean_ocr_results(ocr_results)

    ingredients = []

    for name in cleaned:
        normalized = normalize_name(name)
        matching_detections = []

        for detection in ocr_results:
            detected_text = normalize_name(detection["text"])

            score = SequenceMatcher(
                None,
                normalized,
                detected_text
            ).ratio()

            if score >= 0.85:
                matching_detections.append(detection)

        first_seen = None

        if matching_detections:
            first_seen = min(
                item.get("timestamp_seconds", 0)
                for item in matching_detections
            )

        ingredients.append({
            "name": name.strip().title(),
            "quantity": None,
            "unit": None,
            "first_seen_seconds": first_seen,
        })

    return {
        "source_type": "video",
        "extraction_method": "easyocr",
        "ingredients": ingredients,
        "ingredient_count": len(ingredients),
    }