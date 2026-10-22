import pytest

from app.services.gemini_video_analyzer import validate_recipe_response


def valid_recipe():
    return {
        "title": "Cheesy Pasta",
        "ingredients": [
            {"name": "Pasta", "quantity": 200, "unit": "g"},
            {"name": "Cheese", "quantity": "1/2", "unit": "cup"},
        ],
        "instructions": [
            {
                "step_number": 1,
                "description": "Boil the pasta.",
                "timestamp_seconds": 5,
            }
        ],
        "uncertain_details": [],
    }


def test_valid_recipe():
    result = validate_recipe_response(valid_recipe())

    assert result["title"] == "Cheesy Pasta"
    assert len(result["ingredients"]) == 2
    assert len(result["instructions"]) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("title", ""),
        ("ingredients", "Pasta"),
        ("instructions", "Boil pasta"),
        ("uncertain_details", "Unknown quantity"),
    ],
)
def test_invalid_top_level_fields(field, value):
    recipe = valid_recipe()
    recipe[field] = value

    with pytest.raises(ValueError):
        validate_recipe_response(recipe)


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", None),
        ("quantity", {"amount": 2}),
        ("unit", ["grams"]),
    ],
)
def test_invalid_ingredient_fields(field, value):
    recipe = valid_recipe()
    recipe["ingredients"][0][field] = value

    with pytest.raises(ValueError):
        validate_recipe_response(recipe)


@pytest.mark.parametrize(
    "field,value",
    [
        ("description", None),
        ("step_number", "first"),
        ("timestamp_seconds", "five seconds"),
        ("timestamp_seconds", -1),
    ],
)
def test_invalid_instruction_fields(field, value):
    recipe = valid_recipe()
    recipe["instructions"][0][field] = value

    with pytest.raises(ValueError):
        validate_recipe_response(recipe)


def test_empty_ingredients_allowed():
    recipe = valid_recipe()
    recipe["ingredients"] = []

    result = validate_recipe_response(recipe)

    assert result["ingredients"] == []


def test_unknown_timestamp_allowed():
    recipe = valid_recipe()
    recipe["instructions"][0]["timestamp_seconds"] = None

    result = validate_recipe_response(recipe)

    assert result["instructions"][0]["timestamp_seconds"] is None
