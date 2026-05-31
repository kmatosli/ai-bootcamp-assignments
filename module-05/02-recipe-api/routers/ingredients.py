"""
routers/ingredients.py -- In-memory ingredient CRUD.
"""
from fastapi import APIRouter, HTTPException
from schemas.ingredient import IngredientCreate, IngredientResponse

router = APIRouter(prefix="/ingredients", tags=["Ingredients"])

_db: dict[int, dict] = {}
_next_id = 1


@router.post("", response_model=IngredientResponse, status_code=201)
def create_ingredient(payload: IngredientCreate):
    global _next_id
    ingredient = {"id": _next_id, **payload.model_dump()}
    _db[_next_id] = ingredient
    _next_id += 1
    return ingredient


@router.get("", response_model=list[IngredientResponse])
def list_ingredients():
    return list(_db.values())


@router.get("/{ingredient_id}", response_model=IngredientResponse)
def get_ingredient(ingredient_id: int):
    if ingredient_id not in _db:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return _db[ingredient_id]
