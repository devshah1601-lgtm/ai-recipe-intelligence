from app.services.ingredient_matcher import normalize


def find_unmatched_ocr_texts(ocr_results, matched_ingredients):
    """
    Preserve OCR text that is not covered by a matched
    ingredient, without claiming it is an ingredient.
    """

    matched_names = {
        normalize(item["name"])
        for item in matched_ingredients
    }

    unmatched = []
    seen = set()

    for detection in ocr_results:
        text = detection["text"].strip()
        normalized = normalize(text)

        if not normalized or normalized in seen:
            continue

        # Ignore detections already covered by a matched ingredient.
        # Word-level comparison avoids matching 'oil' inside 'boil'.
        detected_words = normalized.split()

        is_covered = any(
            all(word in matched.split() for word in detected_words)
            for matched in matched_names
        )

        if is_covered:
            continue

        seen.add(normalized)

        unmatched.append({
            "text": text,
            "first_seen_seconds": detection.get("timestamp_seconds"),
            "status": "needs_review",
        })

    return unmatched

import re


SOCIAL_CAPTION_PATTERNS = [
    r"\bsubscribe\b",
    r"\bfollow\s+(?:me|us|for)\b",
    r"\blike\s+(?:and|this|the)\b",
    r"\bshare\s+(?:this|the|with)\b",
    r"\bcomment\s+(?:below|for)\b",
    r"\blink\s+in\s+bio\b",
]


def filter_unmatched_candidates(unmatched):
    """
    Separate likely non-recipe social captions from
    OCR text that still needs ingredient review.
    """

    candidates = []
    ignored = []

    for item in unmatched:
        text = item["text"].strip()

        is_social_caption = any(
            re.search(pattern, text, flags=re.IGNORECASE)
            for pattern in SOCIAL_CAPTION_PATTERNS
        )

        if is_social_caption:
            ignored.append({
                **item,
                "status": "ignored",
                "reason": "social_media_caption",
            })
        else:
            candidates.append({
                **item,
                "status": "needs_review",
            })

    return {
        "candidates": candidates,
        "ignored": ignored,
    }