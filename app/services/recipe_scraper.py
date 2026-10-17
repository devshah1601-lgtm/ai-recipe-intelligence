
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from ipaddress import ip_address
import socket

from app.services.ai_extractor import extract_ingredients_rules


def check_public_url(url):
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Invalid HTTP/HTTPS URL")

    hostname = parsed.hostname

    if hostname.lower() == "localhost":
        raise ValueError("Local addresses are not allowed")

    addresses = socket.getaddrinfo(
        hostname, None, type=socket.SOCK_STREAM
    )

    for address in addresses:
        ip = ip_address(address[4][0])

        if not ip.is_global:
            raise ValueError("Private or unsafe address")


def find_recipe(data):
    if isinstance(data, list):
        for item in data:
            result = find_recipe(item)
            if result:
                return result

    if isinstance(data, dict):
        recipe_type = data.get("@type", [])

        if isinstance(recipe_type, str):
            recipe_type = [recipe_type]

        if any(
            str(t).split("/")[-1].lower() == "recipe"
            for t in recipe_type
        ):
            return data

        for key in ("@graph", "mainEntity"):
            if key in data:
                result = find_recipe(data[key])
                if result:
                    return result

    return None


def clean_instructions(instructions):
    steps = []

    if isinstance(instructions, str):
        return [instructions.strip()]

    if isinstance(instructions, list):
        for item in instructions:
            if isinstance(item, str):
                steps.append(item.strip())

            elif isinstance(item, dict):
                if item.get("text"):
                    steps.append(item["text"].strip())

                elif item.get("itemListElement"):
                    steps.extend(
                        clean_instructions(item["itemListElement"])
                    )

    return steps


def scrape_recipe(url):
    check_public_url(url)

    response = requests.get(
        url,
        headers={
            "User-Agent": "RecipeResearchBot/1.0"
        },
        timeout=15,
        allow_redirects=False
    )

    if 300 <= response.status_code < 400:
        raise ValueError("Redirected URLs are not supported yet")

    response.raise_for_status()

    if "text/html" not in response.headers.get(
        "Content-Type", ""
    ).lower():
        raise ValueError("URL does not return HTML")

    soup = BeautifulSoup(response.text, "html.parser")

    recipe_data = None

    for script in soup.find_all(
        "script", type="application/ld+json"
    ):
        try:
            data = json.loads(script.string or script.get_text())
            recipe_data = find_recipe(data)

            if recipe_data:
                break

        except (json.JSONDecodeError, TypeError):
            continue

    if not recipe_data:
        raise ValueError(
            "No structured recipe data found on this webpage"
        )

    raw_ingredients = recipe_data.get(
        "recipeIngredient", []
    )

    if isinstance(raw_ingredients, str):
        raw_ingredients = [raw_ingredients]

    ingredients = []

    for item in raw_ingredients:
        if isinstance(item, str):
            parsed = extract_ingredients_rules(item)
            ingredients.extend(parsed["ingredients"])

    return {
        "title": recipe_data.get("name"),
        "description": recipe_data.get("description"),
        "prep_time": recipe_data.get("prepTime"),
        "cook_time": recipe_data.get("cookTime"),
        "total_time": recipe_data.get("totalTime"),
        "servings": recipe_data.get("recipeYield"),
        "ingredients": ingredients,
        "instructions": clean_instructions(
            recipe_data.get("recipeInstructions", [])
        ),
        "source_url": url
    }
