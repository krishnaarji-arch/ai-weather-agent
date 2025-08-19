# simple_agent.py
import httpx
import json

# --- Configuration for the Gemini API ---
# The API key is provided automatically by the Canvas environment.
API_KEY = "AIzaSyAVy96a4U4t_kI8q7nk4g7a3wipyQA2VRs"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key=" + API_KEY

async def _get_current_weather(city: str, state: str):
    """
    Calls the Gemini API to get the current temperature for a given city and state.
    Returns a formatted string or an error message.
    
    The underscore in the function name indicates that it's typically for internal use
    within a module, a common Python convention.
    """
    # The prompt for the AI model, asking for the temperature in a structured format.
    prompt = f"What is the current temperature in {city}, {state}? Please respond with only a single JSON object containing the city, state, and temperature. Do not include any other text."

    # The payload for the Gemini API call.
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "city": {"type": "STRING"},
                    "state": {"type": "STRING"},
                    "temperature": {"type": "STRING", "description": "The current temperature with units, e.g., '68°F'"}
                }
            }
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(API_URL, json=payload, timeout=30)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            
            api_response = response.json()
            response_text = api_response['candidates'][0]['content']['parts'][0]['text']
            
            parsed_json = json.loads(response_text)
            
            # Extract the temperature and format a user-friendly response.
            ai_response = f"The current temperature in {parsed_json['city']}, {parsed_json['state']} is {parsed_json['temperature']}."
            
            return {"response": ai_response}

    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        return {"response": f"An HTTP error occurred: {e.response.status_code}. Please try again later."}
    except KeyError as e:
        print(f"KeyError: Could not parse API response. Missing key: {e}")
        return {"response": f"I'm sorry, there was an issue parsing the API's response. Please try again."}
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: Could not decode JSON from API response. Error: {e}")
        return {"response": "I'm sorry, the API returned an invalid response. Please try again."}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {"response": "An unexpected server error occurred. Please try again later."}
