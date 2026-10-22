import re
from difflib import SequenceMatcher


def normalize_text(text):
    return re.sub(r"\s+", " ", text.strip()).lower()


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def clean_ocr_results(results):
    frames = {}

    for item in results:
        frames.setdefault(item["frame"], []).append(item)

    candidates = []

    for frame in sorted(frames):
        items = frames[frame]
        texts = [item["text"].strip() for item in items]

        # Keep OCR detections in frame order.
# Do not guess which words form an ingredient.
        candidates.extend(texts)

    # Group near-duplicates, preferring complete readings.
    unique = []

    for text in candidates:
        normalized = normalize_text(text)

        if len(normalized) < 3:
            continue

        match_index = None

        for i, existing in enumerate(unique):
            existing_normalized = normalize_text(existing)

            if (
                similarity(normalized, existing_normalized) >= 0.85
                or normalized in existing_normalized.split()
                or existing_normalized in normalized.split()
            ):
                match_index = i
                break

        if match_index is None:
            unique.append(text)
        elif len(text) > len(unique[match_index]):
            unique[match_index] = text

    # Remove fragments after all frames have been processed.
    cleaned = []

    for text in unique:
        normalized = normalize_text(text)
        is_fragment = False

        for other in unique:
            if text == other:
                continue

            other_normalized = normalize_text(other)

            if (
                len(normalized.split()) == 1
                and len(normalized) >= 4
                and any(
                    word.endswith(normalized)
                    for word in other_normalized.split()
                )
            ):
                is_fragment = True
                break

        if not is_fragment:
            cleaned.append(text)

    return cleaned