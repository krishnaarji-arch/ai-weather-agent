# fastapi_server.py
# Import necessary libraries
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import json
import os

# Import the new agent function from simple_agent.py
from simple_agent import _get_current_weather

# CRITICAL: This line initializes the FastAPI application.
app = FastAPI()

# Mount the static files directory (for serving HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

# Create a data model for the incoming request from the front-end
class WeatherQuery(BaseModel):
    city: str
    state: str

# Define the root endpoint to serve our HTML file
@app.get("/", response_class=HTMLResponse)
async def serve_frontend(request: Request):
    """
    Serves the main HTML page for the AI agent interface.
    """
    return templates.TemplateResponse("index.html", {"request": request})

# Define the API endpoint that will handle requests from the front-end
@app.post("/api/chat")
async def process_chat(query: WeatherQuery):
    """
    This endpoint receives a user query (city and state),
    calls the AI agent to get the temperature, and returns the response.
    """
    city = query.city
    state = query.state
    
    print(f"Received query for: {city}, {state}")

    # Call the new agent function to get the weather
    response = await _get_current_weather(city, state)

    return response

# This conditional block ensures that `uvicorn.run()` is only called
# when the script is executed directly.
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
