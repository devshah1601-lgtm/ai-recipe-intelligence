
from pathlib import Path
import pandas as pd

INPUT_PATH = Path("data/raw/IndianFoodDatasetCSV.csv")
OUTPUT_PATH = Path("data/processed/meal_training.csv")

COURSE_MAPPING = {
    "Lunch": "Lunch",
    "Dinner": "Dinner",
    "Snack": "Snack",
    "Dessert": "Dessert",
    "South Indian Breakfast": "Breakfast",
    "World Breakfast": "Breakfast",
    "North Indian Breakfast": "Breakfast",
    "Indian Breakfast": "Breakfast",
}

df = pd.read_csv(INPUT_PATH, low_memory=False)

# Keep only recipes with unambiguous target labels
df["Course"] = df["Course"].astype(str).str.strip()
df = df[df["Course"].isin(COURSE_MAPPING)].copy()

df["meal_type"] = df["Course"].map(COURSE_MAPPING)

# Combine recipe title and ingredients
df["title"] = df["TranslatedRecipeName"].fillna("").astype(str)
df["ingredients"] = df["TranslatedIngredients"].fillna("").astype(str)

df["text"] = (
    df["title"].str.strip() + " " +
    df["ingredients"].str.strip()
).str.strip()

# Remove incomplete records
df = df[df["text"].str.len() >= 10].copy()

# Remove duplicate recipes using normalized title
df["title_key"] = (
    df["title"]
    .str.lower()
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

df = df[df["title_key"] != ""]
df = df.drop_duplicates(subset=["title_key"])

# Save the cleaned training data
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

df[["title", "ingredients", "text", "meal_type"]].to_csv(
    OUTPUT_PATH,
    index=False
)

print("\nDataset prepared successfully!")
print("Total cleaned recipes:", len(df))

print("\nMeal type distribution:")
print(df["meal_type"].value_counts())

print("\nSaved to:", OUTPUT_PATH)
