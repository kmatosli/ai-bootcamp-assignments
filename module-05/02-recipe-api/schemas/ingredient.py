"""
schemas/ingredient.py -- Pydantic schemas for the Ingredient resource.
"""
from pydantic import BaseModel


class IngredientCreate(BaseModel):
    name: str
    quantity: str
    unit: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Revenue growth rate",
                "quantity": "15",
                "unit": "percent",
            }
        }
    }


class IngredientResponse(IngredientCreate):
    id: int
