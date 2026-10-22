import csv
import re
from pathlib import Path


DATASET_PATH = Path("data/raw/IndianFoodDatasetCSV.csv")

UNITS = (
    r"tablespoons?|tbsp|teaspoons?|tsp|"
    r"cups?|grams?|g|kg|ml|litres?|liters?|"
    r"pieces?|pinch|sprigs?|cloves?|"
    r"बड़ा\s+चम्मच|बड़ा\s+चमच्च|बड़े\s+चम्मच|"
    r"छोटा\s+चम्मच|छोटे\s+चम्मच|"
    r"चम्मच|चमच्च|कप|ग्राम|किलो|"
    r"मिलीलीटर|लीटर"
)

QUANTITY = r"\d+(?:\s*[-/]\s*\d+)*(?:\.\d+)?"


def clean_ingredient(text):
    # Remove stray punctuation and symbols at the beginning.
    text = re.sub(r"^[^\w]+", "", text).strip()

    # Remove preparation instructions.
    text = text.split(" - ")[0].strip()

    # Remove quantities at the beginning.
    text = re.sub(
        rf"^\s*{QUANTITY}\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Remove measurement units at the beginning.
    text = re.sub(
        rf"^(?:{UNITS})\b\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Remove parenthetical descriptions.
    text = re.sub(r"\([^)]*\)", "", text)

    return re.sub(r"\s+", " ", text).strip(" ,-")


def load_ingredient_vocabulary():
    vocabulary = set()

    with DATASET_PATH.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            for column in ("Ingredients", "TranslatedIngredients"):
                value = row.get(column, "")

                for ingredient in value.split(","):
                    name = clean_ingredient(ingredient)

                    if len(name) >= 3:
                        vocabulary.add(name)

    return sorted(vocabulary, key=str.casefold)