"""
routers/recipes.py -- In-memory recipe CRUD.
"""
from fastapi import APIRouter, HTTPException
from schemas.recipe import RecipeCreate, RecipeResponse

router = APIRouter(prefix="/recipes", tags=["Recipes"])

_db: dict[int, dict] = {}
_next_id = 1


@router.post("", response_model=RecipeResponse, status_code=201)
def create_recipe(payload: RecipeCreate):
    global _next_id
    recipe = {"id": _next_id, **payload.model_dump()}
    _db[_next_id] = recipe
    _next_id += 1
    return recipe


@router.get("", response_model=list[RecipeResponse])
def list_recipes():
    return list(_db.values())


@router.get("/{recipe_id}", response_model=RecipeResponse)
def get_recipe(recipe_id: int):
    if recipe_id not in _db:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return _db[recipe_id]


@router.delete("/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: int):
    if recipe_id not in _db:
        raise HTTPException(status_code=404, detail="Recipe not found")
    del _db[recipe_id]
