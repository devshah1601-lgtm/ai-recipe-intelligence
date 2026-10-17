
from pathlib import Path
import json

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = PROJECT_ROOT / "data" / "processed" / "meal_training.csv"

MODEL_PATH = Path(__file__).parent / "meal_classifier.joblib"

REPORT_PATH = Path(__file__).parent / "evaluation.json"


def train_model():
    print("\nLoading cleaned recipe dataset...")

    df = pd.read_csv(DATA_PATH)

    df = df.dropna(subset=["text", "meal_type"])

    X = df["text"].astype(str)
    y = df["meal_type"].astype(str)

    print("Total recipes:", len(df))
    print("\nCategories:")
    print(y.value_counts())

    # Reserve 20% for evaluation
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
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

    print("\nTraining model...")
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    print("\n===== MODEL EVALUATION =====")
    print(f"Accuracy: {accuracy:.2%}")

    report_text = classification_report(
        y_test,
        predictions,
        zero_division=0,
    )

    print("\nClassification report:")
    print(report_text)

    labels = sorted(y.unique())

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=labels,
    )

    print("\nConfusion matrix:")
    print("Labels:", labels)
    print(matrix)

    report = {
        "total_recipes": len(df),
        "training_samples": len(X_train),
        "testing_samples": len(X_test),
        "accuracy": float(accuracy),
        "classification_report": classification_report(
            y_test,
            predictions,
            output_dict=True,
            zero_division=0,
        ),
        "labels": labels,
        "confusion_matrix": matrix.tolist(),
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Save the model only after evaluation completes
    joblib.dump(model, MODEL_PATH)

    print("\nModel saved to:", MODEL_PATH)
    print("Evaluation saved to:", REPORT_PATH)


if __name__ == "__main__":
    train_model()
