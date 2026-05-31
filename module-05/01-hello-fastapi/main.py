"""
Module 5 -- Assignment 01: Hello FastAPI

Four endpoints demonstrating basic FastAPI concepts.
Run with: uvicorn main:app --reload
Visit:     http://localhost:8000/docs
"""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Hello FastAPI", version="0.1.0")


@app.get("/")
def root():
    """Root endpoint -- confirms the server is running."""
    return {"message": "Welcome to my first FastAPI application!"}


@app.get("/about")
def about():
    """About this API and its developer."""
    return {
        "developer": "Kathy Matosli",
        "module": "Module 5 -- FastAPI Development",
        "project": "Caduceus Healthcare Equity Decision-Support Platform",
        "bootcamp": "Coding Temple AI Bootcamp",
    }


@app.get("/greet/{name}")
def greet(name: str):
    """Return a personalized greeting using a path parameter."""
    return {"message": f"Hello, {name}! Welcome to Caduceus."}


class EchoRequest(BaseModel):
    message: str
    shout: bool = False


@app.post("/echo")
def echo(payload: EchoRequest):
    """Echo the message back. If shout=True, return it in UPPERCASE."""
    msg = payload.message.upper() if payload.shout else payload.message
    return {"message": msg, "shout": payload.shout}
