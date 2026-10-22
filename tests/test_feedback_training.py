
import pandas as pd
import pytest

from app.ml.feedback_training import feedback_to_dataframe


def make_feedback(
    title="Masala Omelette",
    meal_type="Breakfast",
    ingredients=None,
):
    return {
        "recipe_title": title,
        "corrected_meal_type": meal_type,
        "ingredients": (
            [{"name": "Eggs"}, {"name": "Onion"}]
            if ingredients is None
            else ingredients
        ),
    }


def test_valid_feedback():
    result = feedback_to_dataframe([make_feedback()])

    assert len(result) == 1
    assert result.iloc[0]["text"] == "Masala Omelette Eggs Onion"
    assert result.iloc[0]["meal_type"] == "Breakfast"


def test_empty_feedback():
    result = feedback_to_dataframe([])

    assert result.empty
    assert list(result.columns) == ["text", "meal_type"]


def test_duplicate_feedback():
    feedback = make_feedback()

    result = feedback_to_dataframe([feedback, feedback])

    assert len(result) == 1


def test_invalid_category():
    result = feedback_to_dataframe([
        make_feedback(meal_type="Brunch")
    ])

    assert result.empty


@pytest.mark.parametrize("title", ["", "   ", None])
def test_invalid_title(title):
    result = feedback_to_dataframe([
        make_feedback(title=title)
    ])

    assert result.empty


def test_string_ingredients():
    result = feedback_to_dataframe([
        make_feedback(ingredients=["Eggs", "Onion"])
    ])

    assert result.iloc[0]["text"] == "Masala Omelette Eggs Onion"


def test_invalid_ingredients():
    result = feedback_to_dataframe([
        make_feedback(ingredients="Eggs, Onion")
    ])

    assert result.empty


def test_mixed_ingredient_formats():
    result = feedback_to_dataframe([
        make_feedback(
            ingredients=[
                {"name": "Eggs"},
                "Onion",
                {"name": ""},
                123,
                None,
            ]
        )
    ])

    assert result.iloc[0]["text"] == "Masala Omelette Eggs Onion"


def test_whitespace_normalization():
    result = feedback_to_dataframe([
        make_feedback(
            title="  Masala   Omelette  ",
            ingredients=["  Eggs  ", " Onion "],
        )
    ])

    assert result.iloc[0]["text"] == "Masala Omelette Eggs Onion"


def test_multiple_categories():
    result = feedback_to_dataframe([
        make_feedback("Omelette", "Breakfast"),
        make_feedback("Chocolate Cake", "Dessert"),
        make_feedback("Paneer Curry", "Dinner"),
    ])

    assert len(result) == 3
    assert set(result["meal_type"]) == {
        "Breakfast",
        "Dessert",
        "Dinner",
    }


def test_returns_dataframe():
    result = feedback_to_dataframe([make_feedback()])

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["text", "meal_type"]


from app.ml.feedback_training import merge_training_feedback


def make_training_data():
    return pd.DataFrame({
        "text": [
            "Pancakes eggs milk",
            "Chocolate cake cocoa",
            "Chicken curry rice",
            "Vegetable sandwich",
            "Roasted peanuts",
        ],
        "meal_type": [
            "Breakfast",
            "Dessert",
            "Dinner",
            "Lunch",
            "Snack",
        ],
    })


def test_merge_valid_feedback():
    training = make_training_data()
    feedback = pd.DataFrame({
        "text": ["Masala omelette onion"],
        "meal_type": ["Breakfast"],
    })

    result = merge_training_feedback(
        training, feedback, max_feedback_ratio=0.20
    )

    assert len(result) == 6
    assert "Masala omelette onion" in result["text"].values


def test_merge_empty_feedback():
    training = make_training_data()
    feedback = pd.DataFrame(columns=["text", "meal_type"])

    result = merge_training_feedback(training, feedback)

    pd.testing.assert_frame_equal(
        result.reset_index(drop=True),
        training.reset_index(drop=True),
    )


def test_merge_excludes_existing_recipe():
    training = make_training_data()
    feedback = pd.DataFrame({
        "text": ["Pancakes eggs milk"],
        "meal_type": ["Dinner"],
    })

    result = merge_training_feedback(training, feedback)

    assert len(result) == len(training)


def test_merge_case_insensitive_duplicates():
    training = make_training_data()
    feedback = pd.DataFrame({
        "text": ["  PANCAKES   EGGS MILK  "],
        "meal_type": ["Breakfast"],
    })

    result = merge_training_feedback(training, feedback)

    assert len(result) == len(training)


def test_merge_conflicting_feedback():
    training = make_training_data()
    feedback = pd.DataFrame({
        "text": [
            "Masala omelette onion",
            "Masala omelette onion",
        ],
        "meal_type": ["Breakfast", "Dinner"],
    })

    result = merge_training_feedback(training, feedback)

    assert len(result) == len(training)


def test_merge_duplicate_feedback():
    training = make_training_data()
    feedback = pd.DataFrame({
        "text": [
            "Masala omelette onion",
            "MASALA OMELETTE ONION",
        ],
        "meal_type": ["Breakfast", "Breakfast"],
    })

    result = merge_training_feedback(training, feedback)

    assert len(result) == 6


def test_merge_feedback_limit():
    training = make_training_data()
    feedback = pd.DataFrame({
        "text": [
            "New recipe one",
            "New recipe two",
            "New recipe three",
        ],
        "meal_type": [
            "Breakfast",
            "Lunch",
            "Dinner",
        ],
    })

    result = merge_training_feedback(
        training, feedback, max_feedback_ratio=0.20
    )

    assert len(result) == 6


def test_merge_does_not_modify_inputs():
    training = make_training_data()
    feedback = pd.DataFrame({
        "text": ["Masala omelette onion"],
        "meal_type": ["Breakfast"],
    })

    original_training = training.copy(deep=True)
    original_feedback = feedback.copy(deep=True)

    merge_training_feedback(training, feedback)

    pd.testing.assert_frame_equal(training, original_training)
    pd.testing.assert_frame_equal(feedback, original_feedback)


@pytest.mark.parametrize("ratio", [-0.1, 1.1])
def test_merge_invalid_ratio(ratio):
    with pytest.raises(ValueError):
        merge_training_feedback(
            make_training_data(),
            pd.DataFrame(columns=["text", "meal_type"]),
            max_feedback_ratio=ratio,
        )


def test_merge_missing_columns():
    feedback = pd.DataFrame({"recipe": ["Omelette"]})

    with pytest.raises(ValueError):
        merge_training_feedback(make_training_data(), feedback)


from app.ml.feedback_training import exclude_evaluation_overlap


def test_excludes_evaluation_recipe():
    feedback = pd.DataFrame({
        "text": ["Pancakes eggs milk", "Masala omelette"],
        "meal_type": ["Breakfast", "Breakfast"],
    })

    result = exclude_evaluation_overlap(
        feedback,
        ["Pancakes eggs milk"],
    )

    assert len(result) == 1
    assert result.iloc[0]["text"] == "Masala omelette"


def test_evaluation_overlap_ignores_case_and_whitespace():
    feedback = pd.DataFrame({
        "text": ["  PANCAKES   EGGS MILK  "],
        "meal_type": ["Breakfast"],
    })

    result = exclude_evaluation_overlap(
        feedback,
        ["pancakes eggs milk"],
    )

    assert result.empty


def test_evaluation_filter_keeps_new_feedback():
    feedback = pd.DataFrame({
        "text": ["Masala omelette onion"],
        "meal_type": ["Breakfast"],
    })

    result = exclude_evaluation_overlap(
        feedback,
        ["Chocolate cake cocoa"],
    )

    assert len(result) == 1


def test_evaluation_filter_empty_feedback():
    feedback = pd.DataFrame(columns=["text", "meal_type"])

    result = exclude_evaluation_overlap(
        feedback,
        ["Pancakes eggs milk"],
    )

    assert result.empty
    assert list(result.columns) == ["text", "meal_type"]


def test_evaluation_filter_does_not_modify_input():
    feedback = pd.DataFrame({
        "text": ["Pancakes eggs milk", "Masala omelette"],
        "meal_type": ["Breakfast", "Breakfast"],
    })

    original = feedback.copy(deep=True)

    exclude_evaluation_overlap(
        feedback,
        ["Pancakes eggs milk"],
    )

    pd.testing.assert_frame_equal(feedback, original)


def test_evaluation_filter_removes_all_matches():
    feedback = pd.DataFrame({
        "text": ["Pancakes eggs milk", "Chocolate cake"],
        "meal_type": ["Breakfast", "Dessert"],
    })

    result = exclude_evaluation_overlap(
        feedback,
        ["Pancakes eggs milk", "Chocolate cake"],
    )

    assert result.empty


def test_evaluation_filter_missing_columns():
    feedback = pd.DataFrame({
        "recipe": ["Masala omelette"],
    })

    with pytest.raises(ValueError):
        exclude_evaluation_overlap(
            feedback,
            ["Pancakes eggs milk"],
        )

from app.ml.feedback_training import exclude_evaluation_title_overlap


def make_title_feedback(title):
    return {
        "recipe_title": title,
        "corrected_meal_type": "Breakfast",
        "ingredients": ["Eggs", "Onion"],
    }


def test_title_overlap_removes_matching_recipe():
    feedback = [
        make_title_feedback("Chocolate Cake"),
        make_title_feedback("Masala Omelette"),
    ]

    result = exclude_evaluation_title_overlap(
        feedback,
        ["Chocolate Cake"],
    )

    assert len(result) == 1
    assert result[0]["recipe_title"] == "Masala Omelette"


def test_title_overlap_ignores_case_and_whitespace():
    feedback = [
        make_title_feedback("  CHOCOLATE   CAKE  "),
    ]

    result = exclude_evaluation_title_overlap(
        feedback,
        ["chocolate cake"],
    )

    assert result == []


def test_title_overlap_keeps_new_recipe():
    feedback = [make_title_feedback("Masala Omelette")]

    result = exclude_evaluation_title_overlap(
        feedback,
        ["Chocolate Cake"],
    )

    assert len(result) == 1


def test_title_overlap_empty_feedback():
    result = exclude_evaluation_title_overlap(
        [],
        ["Chocolate Cake"],
    )

    assert result == []


def test_title_overlap_missing_title():
    feedback = [
        {
            "corrected_meal_type": "Breakfast",
            "ingredients": ["Eggs"],
        }
    ]

    result = exclude_evaluation_title_overlap(
        feedback,
        ["Chocolate Cake"],
    )

    assert result == []


def test_title_overlap_does_not_modify_original():
    feedback = [make_title_feedback("Masala Omelette")]
    original = [item.copy() for item in feedback]

    result = exclude_evaluation_title_overlap(
        feedback,
        ["Chocolate Cake"],
    )

    assert feedback == original
    assert result[0] is not feedback[0]


def test_title_overlap_removes_all_matching_titles():
    feedback = [
        make_title_feedback("Chocolate Cake"),
        make_title_feedback("Vegetable Biryani"),
    ]

    result = exclude_evaluation_title_overlap(
        feedback,
        ["Chocolate Cake", "Vegetable Biryani"],
    )

    assert result == []
