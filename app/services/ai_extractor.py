
import json
from ollama import chat
from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    name: str
    quantity: str | None = None


class RecipeExtraction(BaseModel):
    ingredients: list[Ingredient] = Field(default_factory=list)


def extract_ingredients(text: str) -> dict:
    response = chat(
        model="qwen2.5:0.5b",
        
messages=[
    {
        "role": "system",
        "content": (
            "You are an ingredient extraction assistant. "
            "Extract EVERY ingredient from the user's text. "
            "Return an ingredients array containing objects "
            "with name and quantity fields. "
            "The ingredient name must not include its quantity. "
            "Keep preparation details in parentheses. "
            "For example, '1 chopped onion' becomes "
            "{'name': 'Onion (chopped)', 'quantity': '1'}. "
            "For '100g paneer', return "
            "{'name': 'Paneer', 'quantity': '100 g'}. "
            "Never return an empty ingredients array when "
            "ingredients are clearly present. "
            "Never invent missing quantities."
        ),
    },
    {
        "role": "user",
        "content": (
            "Extract all ingredients from this text:\n"
            f"{text}"
        ),
    },
],
        format=RecipeExtraction.model_json_schema(),
        options={"temperature": 0},
    )

    result = RecipeExtraction.model_validate_json(
        response.message.content
    )

    return result.model_dump()


import re


def extract_ingredients_rules(text: str) -> dict:
    ingredients = []

    units = (
        r"cups?|tbsp|tablespoons?|tsp|teaspoons?|"
        r"grams?|g|kg|ml|liters?|l|pieces?|slices?"
    )

    pattern = re.compile(
        rf"^\s*(\d+(?:\.\d+)?(?:/\d+)?)\s*"
        rf"({units})?\b\s*(.+)$",
        re.IGNORECASE
    )

    preparation_words = [
        "chopped", "sliced", "diced",
        "grated", "minced", "mashed"
    ]

    for item in text.split(","):
        item = item.strip()
        match = pattern.match(item)

        if not match:
            ingredients.append({
                "name": item.title(),
                "quantity": None
            })
            continue

        amount, unit, name = match.groups()
        quantity = f"{amount} {unit}".strip() if unit else amount

        preparation = []

        for word in preparation_words:
            if re.search(rf"\b{word}\b", name, re.I):
                preparation.append(word)
                name = re.sub(
                    rf"\b{word}\b", "", name, flags=re.I
                ).strip()

        name = name.title()

        if preparation:
            name += f" ({', '.join(preparation)})"

        ingredients.append({
            "name": name,
            "quantity": quantity
        })

    return {"ingredients": ingredients}



if __name__ == "__main__":
    sample = "2 cups rice, 1 chopped onion, 100g paneer"

    print("RULE-BASED EXTRACTION:")
    print(json.dumps(
        extract_ingredients_rules(sample),
        indent=2
    ))
