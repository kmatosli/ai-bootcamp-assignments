"""
schemas/recipe.py -- Pydantic schemas for the Recipe resource.
Applied to Caduceus: recipes map to investment decisions.
"""
from pydantic import BaseModel


class RecipeCreate(BaseModel):
    name: str
    description: str | None = None
    prep_time_minutes: int
    servings: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Keytruda Revenue Model",
                "description": "Drug-level revenue analysis for MRK Keytruda",
                "prep_time_minutes": 30,
                "servings": 4,
            }
        }
    }


class RecipeResponse(RecipeCreate):
    id: int
