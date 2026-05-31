"""
Module 5 -- Assignment 02: Structure a Recipe API

Demonstrates: folder structure, multiple routers, Pydantic schemas,
in-memory storage, requirements.txt.

Run with: uvicorn main:app --reload
Visit:     http://localhost:8000/docs
"""
import sys
sys.path.insert(0, ".")

from fastapi import FastAPI
from routers.recipes import router as recipes_router
from routers.ingredients import router as ingredients_router

app = FastAPI(
    title="Recipe API",
    description="A structured FastAPI application with multiple routers and Pydantic schemas.",
    version="0.1.0",
)

app.include_router(recipes_router)
app.include_router(ingredients_router)


@app.get("/")
def root():
    return {"message": "Recipe API is running", "docs": "/docs"}
