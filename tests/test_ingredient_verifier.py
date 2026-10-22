import pytest

from app.services.ingredient_verifier import (
    compare_ingredients,
    normalize_ingredient,
)


@pytest.mark.parametrize(
    "original,expected",
    [
        ("Tomatoes", "tomato"),
        ("Green Chillies", "green chilli"),
        ("Mozzarella Cheese", "mozzarella"),
        ("Spring Onions", "spring onion"),
        ("Potatoes", "potato"),
        ("Eggs", "egg"),
        ("  RED   CHILI POWDER  ", "red chilli powder"),
    ],
)
def test_ingredient_normalization(original, expected):
    assert normalize_ingredient(original) == expected


@pytest.mark.parametrize(
    "gemini_name,ocr_name,expected",
    [
        ("Tomato", "Tomatoes", True),
        ("Mozzarella", "Mozzarella Cheese", True),
        ("Green chilli", "Green Chillies", True),
        ("Butter", "Peanut butter", False),
        ("Red chilli powder", "Chilli powder", False),
    ],
)
def test_ingredient_matching(gemini_name, ocr_name, expected):
    gemini = [
        {"name": gemini_name, "quantity": 1, "unit": None}
    ]

    ocr = [
        {"name": ocr_name, "first_seen_seconds": 10}
    ]

    result = compare_ingredients(gemini, ocr)

    assert result[0]["ocr_confirmed"] is expected


def test_earliest_ocr_timestamp():
    gemini = [{"name": "Tomato"}]

    ocr = [
        {"name": "Tomatoes", "first_seen_seconds": 20},
        {"name": "Tomato", "first_seen_seconds": 5},
    ]

    result = compare_ingredients(gemini, ocr)

    assert result[0]["ocr_first_seen_seconds"] == 5


def test_missing_ocr_evidence():
    gemini = [{"name": "Cheese"}]

    result = compare_ingredients(gemini, [])

    assert result[0]["ocr_confirmed"] is False
    assert result[0]["ocr_first_seen_seconds"] is None
    assert result[0]["verification_status"] == "needs_visual_review"
