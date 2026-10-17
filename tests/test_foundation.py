from app.models.recipe import Recipe

def test_recipe_defaults():
    recipe = Recipe(recipe_id="test-1", title="Tomato Salad")
    assert recipe.nutrition.calories_kcal is None
    assert recipe.processing_status.value == "Needs Review"
    assert recipe.confidence == 0.0
