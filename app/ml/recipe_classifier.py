
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "meal_classifier.joblib"

# Small demonstration dataset.
# We will replace this with a larger verified dataset.
TRAINING_DATA = [
    ("pancakes with milk flour and eggs", "Breakfast"),
    ("scrambled eggs and toast", "Breakfast"),
    ("oatmeal with banana and honey", "Breakfast"),
    ("french toast with cinnamon", "Breakfast"),
    ("vegetable sandwich with cheese", "Lunch"),
    ("chicken salad with lettuce", "Lunch"),
    ("rice bowl with vegetables", "Lunch"),
    ("lentil soup with bread", "Lunch"),
    ("paneer butter masala with naan", "Dinner"),
    ("chicken curry with rice", "Dinner"),
    ("vegetable biryani with spices", "Dinner"),
    ("grilled fish with potatoes", "Dinner"),
    ("chocolate cake with frosting", "Dessert"),
    ("vanilla ice cream with chocolate", "Dessert"),
    ("brownies with cocoa and butter", "Dessert"),
    ("fruit custard with cream", "Dessert"),
    ("popcorn with salt and butter", "Snack"),
    ("potato chips with seasoning", "Snack"),
    ("roasted peanuts with spices", "Snack"),
    ("vegetable spring rolls", "Snack"),
]


def train_model():
    texts = [item[0] for item in TRAINING_DATA]
    labels = [item[1] for item in TRAINING_DATA]

    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
        ("classifier", LogisticRegression(max_iter=1000))
    ])

    model.fit(texts, labels)
    joblib.dump(model, MODEL_PATH)

    print("Model trained and saved successfully!")


def predict_meal_type(recipe):
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Model not trained. Run the training command first."
        )

    model = joblib.load(MODEL_PATH)

    text = " ".join([
        recipe.get("title") or "",
        recipe.get("description") or "",
        " ".join(
            item.get("name", "")
            for item in recipe.get("ingredients", [])
        )
    ])

    prediction = model.predict([text])[0]
    probabilities = model.predict_proba([text])[0]

    
    confidence = float(max(probabilities))

    # Threshold for showing a prediction as uncertain.
    # This is a provisional UI rule, not a calibrated
    # measure of prediction reliability.
    needs_review = confidence < 0.50

    return {
        "meal_type": prediction,
        "confidence": round(confidence, 3),
        "needs_review": needs_review,
        "message": (
            "Low-confidence prediction. Please verify the meal type."
            if needs_review
            else "Predicted meal category."
        )
    }



if __name__ == "__main__":
    train_model()
