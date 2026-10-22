import re
from difflib import SequenceMatcher


def normalize(text):
    text = text.casefold().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Normalize common ingredient spelling variations.
    replacements = {
        "chili": "chilli",
        "chilies": "chillies",
        "chile": "chilli",
    }

    words = text.split()
    words = [replacements.get(word, word) for word in words]

    return " ".join(words)

def canonical_name(text):
    words = normalize(text).split()

    canonical_words = []

    for word in words:
        if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]

        canonical_words.append(word)

    return " ".join(canonical_words)


def match_ingredients(ocr_texts, vocabulary):
    normalized_vocabulary = {}

    for name in vocabulary:
        normalized = normalize(name)

        if not normalized:
            continue

        # Keep one representative for each normalized ingredient.
        # Prefer the original name with fewer characters.
        if normalized not in normalized_vocabulary:
            normalized_vocabulary[normalized] = name
        elif len(name) < len(normalized_vocabulary[normalized]):
            normalized_vocabulary[normalized] = name

    frames = {}

    for item in ocr_texts:
        frames.setdefault(item["frame"], []).append(item)

    matches = []
    seen = set()

    for frame in sorted(frames):
        items = frames[frame]

        texts = [normalize(item["text"]) for item in items]
        detected_words = set(" ".join(texts).split())

        candidates = []

        for normalized_name, original_name in normalized_vocabulary.items():
            ingredient_words = normalized_name.split()

            # Exact matching must be supported by one OCR detection.
            # Do not combine unrelated words across the entire frame.
            exact_match = normalized_name in texts

            best_similarity = max(
                (
                    SequenceMatcher(None, normalized_name, text).ratio()
                    for text in texts
                ),
                default=0,
            )

            if exact_match or (
                best_similarity >= 0.88
                and len(normalized_name) >= 5
            ):
                candidates.append({
                    "name": original_name,
                    "normalized": normalized_name,
                    "score": 1.0 if exact_match else best_similarity,
                    "match_type": "exact" if exact_match else "fuzzy",
                })

        # Prefer complete ingredient names over shorter fragments.
        candidates.sort(
            key=lambda item: (
                item["score"],
                len(item["normalized"].split()),
                len(item["normalized"]),
            ),
            reverse=True,
        )

        selected = []

        for candidate in candidates:
            candidate_words = set(
                canonical_name(candidate["normalized"]).split()
            )

            overlaps = any(
                candidate_words.issubset(
                    set(canonical_name(existing["normalized"]).split())
                )
                or set(canonical_name(existing["normalized"]).split()).issubset(
                    candidate_words
                )
                for existing in selected
            )

            if not overlaps:
                selected.append(candidate)

        timestamps = [
            item["timestamp_seconds"]
            for item in items
            if item.get("timestamp_seconds") is not None
        ]

        first_seen = min(timestamps) if timestamps else None

        for candidate in selected:
            normalized_name = candidate["normalized"]

            if normalized_name in seen:
                continue

            matches.append({
                "name": candidate["name"],
                "first_seen_seconds": first_seen,
                "match_type": candidate["match_type"],
            })

            seen.add(normalized_name)

    return matches