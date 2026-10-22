import hashlib

import pytest

from app.services import recipe_store


@pytest.fixture
def isolated_database(tmp_path, monkeypatch):
    test_database = tmp_path / "test_recipes.db"

    monkeypatch.setattr(
        recipe_store,
        "DATABASE_PATH",
        test_database,
    )

    return test_database


def make_recipe(title="Cheesy Pasta"):
    return {
        "source_type": "video",
        "title": title,
        "ingredients": [
            {"name": "Cheese", "quantity": 100, "unit": "g"}
        ],
        "instructions": [
            {"step_number": 1, "description": "Add cheese."}
        ],
    }


def make_hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def test_save_video_recipe(isolated_database):
    result = recipe_store.save_video_recipe(
        make_recipe(),
        make_hash("video-one"),
    )

    assert result["status"] == "saved"
    assert isinstance(result["id"], int)
    assert isolated_database.exists()


def test_duplicate_video_recipe(isolated_database):
    video_hash = make_hash("same-video")

    first = recipe_store.save_video_recipe(
        make_recipe(),
        video_hash,
    )

    second = recipe_store.save_video_recipe(
        make_recipe("Different Title"),
        video_hash,
    )

    assert first["status"] == "saved"
    assert second["status"] == "duplicate"
    assert second["id"] == first["id"]
    assert len(recipe_store.list_video_recipes()) == 1


def test_list_video_recipes(isolated_database):
    recipe_store.save_video_recipe(
        make_recipe("Pasta"),
        make_hash("video-a"),
    )

    recipe_store.save_video_recipe(
        make_recipe("Pizza"),
        make_hash("video-b"),
    )

    recipes = recipe_store.list_video_recipes()

    assert len(recipes) == 2
    assert {item["title"] for item in recipes} == {
        "Pasta",
        "Pizza",
    }


def test_get_video_recipe_by_id(isolated_database):
    original = make_recipe()

    saved = recipe_store.save_video_recipe(
        original,
        make_hash("video-detail"),
    )

    result = recipe_store.get_video_recipe_by_id(
        saved["id"]
    )

    assert result["id"] == saved["id"]
    assert result["recipe"] == original


def test_missing_video_recipe(isolated_database):
    result = recipe_store.get_video_recipe_by_id(99999)

    assert result is None


@pytest.mark.parametrize(
    "invalid_hash",
    [
        "abc",
        "not-a-valid-hash",
        "z" * 64,
    ],
)
def test_reject_invalid_hash(isolated_database, invalid_hash):
    with pytest.raises(ValueError, match="Invalid video SHA-256 hash"):
        recipe_store.save_video_recipe(
            make_recipe(),
            invalid_hash,
        )
