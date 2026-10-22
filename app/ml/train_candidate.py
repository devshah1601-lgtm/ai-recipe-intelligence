
import json
from pathlib import Path

import joblib
import pandas as pd

from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from app.ml.feedback_training import (
    feedback_to_dataframe,
    merge_training_feedback,
    exclude_evaluation_overlap,
    exclude_evaluation_title_overlap,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = PROJECT_ROOT / "data/processed/meal_training.csv"

CANDIDATE_DIR = PROJECT_ROOT / "backups/ml/candidate"

CANDIDATE_MODEL_PATH = (
    CANDIDATE_DIR / "meal_classifier_candidate.joblib"
)

CANDIDATE_REPORT_PATH = (
    CANDIDATE_DIR / "candidate_evaluation.json"
)


def train_candidate(feedback_records=None):
    """
    Train and evaluate a separate candidate model.

    Never overwrites the active production model.
    """

    if feedback_records is None:
        feedback_records = []

    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["text", "meal_type"])

    X = df["text"].astype(str)
    y = df["meal_type"].astype(str)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    # Exclude feedback whose titles occur in evaluation data.
    safe_records = exclude_evaluation_title_overlap(
        feedback_records,
        df.loc[X_test.index, "title"].tolist(),
    )

    feedback_df = feedback_to_dataframe(safe_records)

    # Exclude feedback whose full text matches evaluation data.
    feedback_df = exclude_evaluation_overlap(
        feedback_df,
        X_test.tolist(),
    )

    # Add a limited number of feedback examples.
    combined = merge_training_feedback(
        pd.DataFrame({
            "text": X_train.tolist(),
            "meal_type": y_train.tolist(),
        }),
        feedback_df,
        max_feedback_ratio=0.20,
    )

    model = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                ngram_range=(1, 2),
                min_df=2,
                max_features=20000,
                sublinear_tf=True,
            ),
        ),
        (
            "classifier",
            LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
            ),
        ),
    ])

    print("Original training samples:", len(X_train))
    print("Accepted feedback samples:", len(combined) - len(X_train))
    print("Candidate training samples:", len(combined))

    model.fit(combined["text"], combined["meal_type"])

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    macro_f1 = f1_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0,
    )

    baseline = joblib.load(
        PROJECT_ROOT / "backups/ml/meal_classifier_baseline.joblib"
    )

    baseline_predictions = baseline.predict(X_test)

    baseline_accuracy = accuracy_score(
        y_test, baseline_predictions
    )

    baseline_macro_f1 = f1_score(
        y_test,
        baseline_predictions,
        average="macro",
        zero_division=0,
    )

    report = {
        "original_training_samples": len(X_train),
        "accepted_feedback_samples": len(combined) - len(X_train),
        "evaluation_samples": len(X_test),
        "baseline_accuracy": float(baseline_accuracy),
        "candidate_accuracy": float(accuracy),
        "baseline_macro_f1": float(baseline_macro_f1),
        "candidate_macro_f1": float(macro_f1),
        "accuracy_change": float(accuracy - baseline_accuracy),
        "macro_f1_change": float(macro_f1 - baseline_macro_f1),
    }

    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, CANDIDATE_MODEL_PATH)

    with open(
        CANDIDATE_REPORT_PATH, "w", encoding="utf-8"
    ) as file:
        json.dump(report, file, indent=2)

    print("\n===== CANDIDATE EVALUATION =====")
    print(json.dumps(report, indent=2))
    print("\nCandidate model saved:", CANDIDATE_MODEL_PATH)

    return report


if __name__ == "__main__":
    train_candidate()
