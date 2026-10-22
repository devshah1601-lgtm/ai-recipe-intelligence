from app.services.ingredient_vocabulary import load_ingredient_vocabulary
from app.services.ingredient_matcher import match_ingredients
from app.services.ingredient_fallback import (
    find_unmatched_ocr_texts,
    filter_unmatched_candidates,
)
from app.services.video_spatial_merger import merge_spatial_ocr
from app.services.video_review_cleaner import (
    consolidate_review_candidates,
    remove_redundant_fragments,
)

def extract_video_ingredients(ocr_results):
    """
    Extract ingredient evidence from OCR detections,
    including spatially reconstructed text.
    """

    vocabulary = load_ingredient_vocabulary()

    # Reconstruct nearby OCR text fragments.
    enriched_results = merge_spatial_ocr(ocr_results)

    # Match against our ingredient vocabulary.
    matched = match_ingredients(
        enriched_results,
        vocabulary,
    )

    # Preserve unmatched text for review.
    unmatched = find_unmatched_ocr_texts(
        enriched_results,
        matched,
    )

    filtered = filter_unmatched_candidates(unmatched)
    review_candidates = consolidate_review_candidates(
        filtered["candidates"]
    )

    review_candidates = remove_redundant_fragments(
        review_candidates
    )

    return {
    "matched_ingredients": matched,
    "review_candidates": review_candidates,
    "ignored_captions": filtered["ignored"],
    "matched_count": len(matched),
    "review_count": len(review_candidates),
    "ignored_count": len(filtered["ignored"]),
    "spatial_merge_count": (
        len(enriched_results) - len(ocr_results)
    ),
}