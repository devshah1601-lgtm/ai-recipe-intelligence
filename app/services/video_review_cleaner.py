from difflib import SequenceMatcher

from app.services.ingredient_matcher import normalize


def consolidate_review_candidates(candidates):
    """
    Consolidate repeated or progressively appearing OCR text.

    Keep the most complete version and preserve the earliest
    timestamp of its related detections.
    """

    groups = []

    for item in sorted(
        candidates,
        key=lambda x: (
            x.get("first_seen_seconds") is None,
            x.get("first_seen_seconds") or 0,
        ),
    ):
        text = normalize(item["text"])
        timestamp = item.get("first_seen_seconds")

        if not text:
            continue

        found_group = None

        for group in groups:
            existing = normalize(group["text"])
            existing_time = group["last_seen_seconds"]

            # Avoid merging captions far apart in time.
            if (
                timestamp is not None
                and existing_time is not None
                and abs(timestamp - existing_time) > 2.0
            ):
                continue

            similarity = SequenceMatcher(
                None, text, existing
            ).ratio()

            # A shorter caption may be an incomplete version
            # of a longer caption.
            is_progressive = (
                len(text) >= 4
                and len(existing) >= 4
                and (
                    text.startswith(existing)
                    or existing.startswith(text)
                )
            )

            if similarity >= 0.85 or is_progressive:
                found_group = group
                break

        if found_group is None:
            groups.append({
                "text": item["text"],
                "first_seen_seconds": timestamp,
                "last_seen_seconds": timestamp,
                "status": "needs_review",
            })
        else:
            if len(text) > len(normalize(found_group["text"])):
                found_group["text"] = item["text"]

            if timestamp is not None:
                previous = found_group["first_seen_seconds"]

                if previous is None:
                    found_group["first_seen_seconds"] = timestamp
                else:
                    found_group["first_seen_seconds"] = min(
                        previous, timestamp
                    )

                found_group["last_seen_seconds"] = timestamp

    return [
        {
            "text": group["text"],
            "first_seen_seconds": group["first_seen_seconds"],
            "status": "needs_review",
        }
        for group in groups
    ]

def remove_redundant_fragments(candidates, time_window=2.0):
    """
    Remove short OCR fragments already represented by
    a longer nearby review candidate.
    """

    cleaned = []

    for index, item in enumerate(candidates):
        current_text = normalize(item["text"])
        current_time = item.get("first_seen_seconds")
        current_words = current_text.split()

        if not current_words:
            continue

        redundant = False

        for other_index, other in enumerate(candidates):
            if index == other_index:
                continue

            other_text = normalize(other["text"])
            other_time = other.get("first_seen_seconds")
            other_words = other_text.split()

            # Only remove fragments of a longer phrase.
            if len(other_text) <= len(current_text):
                continue

            # Don't compare unrelated or unknown timestamps.
            if current_time is None or other_time is None:
                continue

            if abs(current_time - other_time) > time_window:
                continue

            # Require complete word matches, not substrings.
            for start in range(
                len(other_words) - len(current_words) + 1
            ):
                if (
                    other_words[start:start + len(current_words)]
                    == current_words
                ):
                    redundant = True
                    break

            if redundant:
                break

        if not redundant:
            cleaned.append(item)

    return cleaned