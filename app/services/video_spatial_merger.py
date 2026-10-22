def get_bounds(bbox):
    xs = [point[0] for point in bbox]
    ys = [point[1] for point in bbox]

    return min(xs), min(ys), max(xs), max(ys)


def merge_spatial_ocr(ocr_results):
    """
    Merge neighboring OCR text boxes on the same line.

    Keeps original detections and adds merged detections.
    """
    frames = {}

    for item in ocr_results:
        frames.setdefault(item["frame"], []).append(item)

    merged_results = list(ocr_results)
    seen = {
        (item["frame"], item["text"].casefold().strip())
        for item in ocr_results
    }

    for frame, items in frames.items():
        positioned = [
            item for item in items
            if item.get("bbox")
        ]

        # Sort by vertical position first, then horizontal position.
# Round vertical positions into approximate text lines.
        positioned.sort(
            key=lambda item: (
                round(get_bounds(item["bbox"])[1] / 30),
                get_bounds(item["bbox"])[0],
            )
        )

        for i in range(len(positioned) - 1):
            left = positioned[i]
            right = positioned[i + 1]

            x1, y1, x2, y2 = get_bounds(left["bbox"])
            rx1, ry1, rx2, ry2 = get_bounds(right["bbox"])

            left_height = y2 - y1
            right_height = ry2 - ry1

            if left_height <= 0 or right_height <= 0:
                continue

            vertical_overlap = max(
                0,
                min(y2, ry2) - max(y1, ry1)
            )

            overlap_ratio = vertical_overlap / min(
                left_height, right_height
            )

            horizontal_gap = rx1 - x2

            # Require strong vertical alignment and a small gap.
            if overlap_ratio < 0.6:
                continue

            if not (0 <= horizontal_gap <= max(left_height, right_height)):
                continue

            combined_text = (
                left["text"].strip()
                + " "
                + right["text"].strip()
            )

            key = (frame, combined_text.casefold())

            if key in seen:
                continue

            seen.add(key)

            merged_results.append({
                "frame": frame,
                "timestamp_seconds": min(
                    left["timestamp_seconds"],
                    right["timestamp_seconds"]
                ),
                "text": combined_text,
                "confidence": round(
                    min(left["confidence"], right["confidence"]),
                    3
                ),
                "bbox": [
                    [min(x1, rx1), min(y1, ry1)],
                    [max(x2, rx2), min(y1, ry1)],
                    [max(x2, rx2), max(y2, ry2)],
                    [min(x1, rx1), max(y2, ry2)],
                ],
                "source": "spatial_merge",
            })

    return merged_results