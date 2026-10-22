
import pandas as pd

ALLOWED_MEAL_TYPES = {
    "Breakfast",
    "Lunch",
    "Dinner",
    "Snack",
    "Dessert",
}


def feedback_to_dataframe(feedback_records):
    """Convert recipe feedback into ML training rows."""

    rows = []
    seen = set()

    for record in feedback_records:
        meal_type = record.get("corrected_meal_type")
        title = record.get("recipe_title")
        ingredients = record.get("ingredients", [])

        if meal_type not in ALLOWED_MEAL_TYPES:
            continue

        if not isinstance(title, str) or not title.strip():
            continue

        if not isinstance(ingredients, list):
            continue

        ingredient_names = []

        for ingredient in ingredients:
            if isinstance(ingredient, str):
                name = ingredient
            elif isinstance(ingredient, dict):
                name = ingredient.get("name", "")
            else:
                continue

            if isinstance(name, str) and name.strip():
                ingredient_names.append(name.strip())

        text = " ".join([title.strip(), *ingredient_names])
        text = " ".join(text.split())

        # Prevent identical feedback records from being repeated.
        key = (text.casefold(), meal_type)

        if key in seen:
            continue

        seen.add(key)

        rows.append({
            "text": text,
            "meal_type": meal_type,
        })

    return pd.DataFrame(rows, columns=["text", "meal_type"])


def merge_training_feedback(
    training_df,
    feedback_df,
    max_feedback_ratio=0.20,
):
    """
    Merge feedback into training data safely.

    - Never modifies the original DataFrames.
    - Removes duplicate feedback texts.
    - Excludes feedback matching existing training texts.
    - Excludes feedback with conflicting labels.
    - Limits feedback to 20% of original training size.
    """

    if not 0 <= max_feedback_ratio <= 1:
        raise ValueError("max_feedback_ratio must be between 0 and 1")

    required_columns = {"text", "meal_type"}

    for name, df in [
        ("training_df", training_df),
        ("feedback_df", feedback_df),
    ]:
        if not required_columns.issubset(df.columns):
            raise ValueError(f"{name} is missing required columns")

    training = training_df[["text", "meal_type"]].copy()
    feedback = feedback_df[["text", "meal_type"]].copy()

    if feedback.empty:
        return training

    # Normalize text for duplicate detection.
    training["_key"] = (
        training["text"].astype(str)
        .str.split()
        .str.join(" ")
        .str.casefold()
    )

    feedback["_key"] = (
        feedback["text"].astype(str)
        .str.split()
        .str.join(" ")
        .str.casefold()
    )

    # Ignore ambiguous feedback where one recipe has
    # multiple different corrected categories.
    conflicting_keys = (
        feedback.groupby("_key")["meal_type"]
        .nunique()
    )

    conflicting_keys = set(
        conflicting_keys[conflicting_keys > 1].index
    )

    feedback = feedback[
        ~feedback["_key"].isin(conflicting_keys)
    ]

    # Avoid duplicates and potential overlap with
    # the original training data.
    feedback = feedback.drop_duplicates(subset=["_key"])

    feedback = feedback[
        ~feedback["_key"].isin(set(training["_key"]))
    ]

    max_rows = int(len(training) * max_feedback_ratio)

    feedback = feedback.head(max_rows)

    combined = pd.concat(
        [
            training[["text", "meal_type"]],
            feedback[["text", "meal_type"]],
        ],
        ignore_index=True,
    )

    return combined


def exclude_evaluation_overlap(feedback_df, evaluation_texts):
    """
    Remove feedback matching held-out evaluation recipes.

    Comparison ignores case and repeated whitespace.
    Does not modify the input DataFrame.
    """

    if not {"text", "meal_type"}.issubset(feedback_df.columns):
        raise ValueError("feedback_df is missing required columns")

    def normalize(value):
        return " ".join(str(value).split()).casefold()

    evaluation_keys = {
        normalize(text)
        for text in evaluation_texts
    }

    keep_mask = ~feedback_df["text"].map(
        normalize
    ).isin(evaluation_keys)

    return feedback_df.loc[
        keep_mask, ["text", "meal_type"]
    ].reset_index(drop=True)


def exclude_evaluation_title_overlap(
    feedback_records,
    evaluation_titles,
):
    """
    Exclude feedback whose recipe title appears in
    the held-out evaluation set.

    Does not modify the original records.
    """

    def normalize_title(value):
        if not isinstance(value, str):
            return ""
        return " ".join(value.split()).casefold()

    protected_titles = {
        normalize_title(title)
        for title in evaluation_titles
        if normalize_title(title)
    }

    safe_records = []

    for record in feedback_records:
        title = normalize_title(
            record.get("recipe_title")
        )

        if not title or title in protected_titles:
            continue

        safe_records.append(record.copy())

    return safe_records
