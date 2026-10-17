from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class ProcessingStatus(str, Enum):
    PROCESSED = "Processed"
    NEEDS_REVIEW = "Needs Review"
    FAILED = "Failed"
    DUPLICATE = "Duplicate"

class Ingredient(BaseModel):
    name: str
    quantity: str | None = None

class Nutrition(BaseModel):
    protein_g: float | None = None
    fat_g: float | None = None
    carbs_g: float | None = None
    calories_kcal: float | None = None

class Recipe(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recipe_id: str
    title: str
    dietary_labels: list[str] = Field(default_factory=list)
    time_required: str | None = None
    serving_size: int | str | None = None
    age_group: str | None = None
    nutrition: Nutrition = Field(default_factory=Nutrition)
    ingredients: list[Ingredient] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)
    source_url: str | None = None
    processing_status: ProcessingStatus = ProcessingStatus.NEEDS_REVIEW
    confidence: float = Field(default=0.0, ge=0, le=1)
    # Extensions below are explicitly documented, not part of the minimum sample output.
    filters: dict[str, list[str]] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    evidence: list[dict] = Field(default_factory=list)
    raw_source: dict = Field(default_factory=dict)
