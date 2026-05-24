"""
hello_fastapi.py -- Module 5 Assignment 1: Hello FastAPI

Standalone warmup. Run with:
    uvicorn hello_fastapi:app --reload

Test all four endpoints at http://localhost:8000/docs
"""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Hello FastAPI", version="0.1.0")


@app.get("/")
def root():
    """Root endpoint -- confirms the server is running."""
    return {"message": "Welcome to my first API"}


@app.get("/about")
def about():
    """About this API and its developer."""
    return {
        "name": "Kathy Matosli",
        "module": "Module 5 -- FastAPI Development",
        "fun_fact": "Building a healthcare equity platform for a Stockholm fund as a bootcamp capstone.",
    }


@app.get("/greet/{name}")
def greet(name: str):
    """Return a personalized greeting using the path parameter."""
    return {"message": f"Hello, {name}! Welcome to Caduceus."}


class EchoRequest(BaseModel):
    message: str
    shout: bool = False


@app.post("/echo")
def echo(payload: EchoRequest):
    """Echo the message back. If shout=True, return it in UPPERCASE."""
    msg = payload.message.upper() if payload.shout else payload.message
    return {"message": msg, "shout": payload.shout}
