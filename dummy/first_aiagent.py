import json
import asyncio
import aiohttp
import os
import serpapi
import urllib.parse

# This script now uses a real LLM (Gemini API), a real search API (SerpApi),
# and a new geocoding API (OpenCage) to power the agent's decisions and actions.
# Required libraries: 'aiohttp' and 'serpapi'.
# You can install them with 'pip install aiohttp serpapi'.

class SimpleAIAgent:
    """
    A foundational AI agent with a "memory" and "tools."
    This class demonstrates a basic agentic loop:
    1. Receive a user query.
    2. "Think" about the query to decide on an action.
    3. Execute an action (either use a tool or formulate a final response).
    4. Provide the final response to the user.
    """
    def __init__(self, name="Agent"):
        self.name = name
        self.memory = []
        # Define the tools the agent can use.
        # Each tool is a function that performs a specific task.
        # We'll use a dictionary to store tool names and their functions.
        self.tools = {
            "get_current_weather": self._get_current_weather,
            "get_search_results": self._get_search_results,
            "get_location_coords": self._get_location_coords,
        }
        # A description of the tools that the "LLM" (simulated here)
        # can read to understand how to use them.
        self.tool_descriptions = {
            "get_current_weather": {
                "description": "Get the current weather for a specified location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "The city and state, e.g. San Francisco, CA"},
                    },
                    "required": ["location"]
                }
            },
            "get_search_results": {
                "description": "Perform a web search for a given query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query string."},
                    },
                    "required": ["query"]
                }
            },
            "get_location_coords": {
                "description": "Get the latitude and longitude for a given location name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location_name": {"type": "string", "description": "The name of the city or location."},
                    },
                    "required": ["location_name"]
                }
            }
        }
        # The URL for the Gemini API.
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"
        # IMPORTANT: Replace "YOUR_API_KEY" with your actual API key.
        # It's best practice to use an environment variable for this.
        self.api_key = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY")
        # SerpApi key for web searches. Get one from https://serpapi.com/users/sign_up
        self.serpapi_key = os.getenv("SERPAPI_API_KEY", "YOUR_SERPAPI_KEY")
        # NEW: OpenCage Geocoding API key for converting location names to coordinates.
        # Get a free key from https://opencagedata.com/pricing
        self.opencage_api_key = os.getenv("OPENCAGE_API_KEY", "YOUR_OPENCAGE_API_KEY")

    async def _get_location_coords(self, location_name):
        """
        UPDATED tool: Fetches latitude and longitude for a given location using the OpenCage Geocoding API.
        """
        print(f"Agent is calling tool: 'get_location_coords' for location: {location_name}")

        if not self.opencage_api_key or self.opencage_api_key == "YOUR_OPENCAGE_API_KEY":
            return "Error: OpenCage API key is not set. Please get a free key from https://opencagedata.com/pricing and set the OPENCAGE_API_KEY environment variable or replace 'YOUR_OPENCAGE_API_KEY' in the code."

        # We need to URL-encode the location name
        encoded_location = urllib.parse.quote(location_name)
        base_url = f"https://api.opencagedata.com/geocode/v1/json?q={encoded_location}&key={self.opencage_api_key}"

        try:
            async with aiohttp.ClientSession() as session:
                # OpenCage does not require a special User-Agent.
                async with session.get(base_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Check if results were found
                        if data and data.get("results"):
                            first_result = data["results"][0]["geometry"]
                            lat = first_result["lat"]
                            lon = first_result["lng"]
                            return json.dumps({"latitude": lat, "longitude": lon})
                        else:
                            return f"Error: No coordinates found for location '{location_name}'."
                    else:
                        error_text = await response.text()
                        return f"Error: Failed to fetch coordinates. Status code: {response.status}. Details: {error_text}"
        except Exception as e:
            return f"An error occurred during the API call: {e}"

    async def _get_current_weather(self, location):
        """
        Fetches real-time weather data from Open-Meteo API using dynamic geocoding.
        This function now first calls the geocoding tool to get the coordinates.
        """
        print(f"Agent is calling tool: 'get_current_weather' for location: {location}")

        # First, call the geocoding tool to get the coordinates.
        coords_result = await self._get_location_coords(location)
        try:
            coords = json.loads(coords_result)
            lat = coords["latitude"]
            lon = coords["longitude"]
        except (json.JSONDecodeError, KeyError):
            # If geocoding failed, return the error message.
            return coords_result

        base_url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true" # Must be a string
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        current_weather = data.get("current_weather", {})
                        temperature = current_weather.get("temperature", "N/A")
                        windspeed = current_weather.get("windspeed", "N/A")

                        return f"The current weather in {location} is {temperature}°C with a wind speed of {windspeed} km/h."
                    else:
                        return f"Error: Failed to fetch weather data. Status code: {response.status}"
        except Exception as e:
            return f"An error occurred during the API call: {e}"

    async def _get_search_results(self, query):
        """
        Performs a real web search using SerpApi.
        This function is now updated to use the SerpApi library.
        """
        print(f"Agent is calling tool: 'get_search_results' for query: {query}")

        if not self.serpapi_key or self.serpapi_key == "YOUR_SERPAPI_KEY":
            return "Error: SerpApi key is not set. Please get a key from https://serpapi.com/users/sign_up and set the SERPAPI_API_KEY environment variable or replace 'YOUR_SERPAPI_KEY' in the code."

        try:
            # Note: The serpapi library handles the async nature, so we can
            # call it directly. The aiohttp is not needed here.
            search = serpapi.search(
                q=query,
                engine="google",
                api_key=self.serpapi_key
            )
            # The search object is a dictionary with the results.
            # We can return the full dictionary or a specific part of it.
            # For this example, let's just return the organic results.
            organic_results = search.get("organic_results", [])

            # Format the results into a readable string
            if not organic_results:
                return "No search results found."

            formatted_results = []
            for i, result in enumerate(organic_results[:5]): # Get top 5 results
                title = result.get("title", "No Title")
                link = result.get("link", "No Link")
                snippet = result.get("snippet", "No Snippet")
                formatted_results.append(f"{i+1}. {title}\n   Link: {link}\n   Snippet: {snippet}")

            return json.dumps(formatted_results)

        except Exception as e:
            return f"An error occurred during the SerpApi call: {e}"


    async def _get_llm_response_with_tools(self, prompt):
        """
        This is the new function that connects to a real LLM API.
        It sends the user's prompt and a description of the tools to the model.
        The model's response will either be a tool call or a final text response.
        """
        print(f"\n--- {self.name} is thinking with a real LLM... ---")

        chat_history = []
        chat_history.append({
            "role": "user",
            "parts": [
                {"text": prompt}
            ]
        })

        function_declarations = []
        for tool_name, tool_def in self.tool_descriptions.items():
            tool_declaration = {
                "name": tool_name,
                "description": tool_def["description"],
                "parameters": tool_def["parameters"]
            }
            function_declarations.append(tool_declaration)

        payload = {
            "contents": chat_history,
            "tools": [
                {
                    "function_declarations": function_declarations
                }
            ]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url + "?key=" + self.api_key,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        llm_output = await response.json()
                        content = llm_output["candidates"][0]["content"]["parts"][0]

                        if "functionCall" in content:
                            return json.dumps({
                                "action": "call_tool",
                                "tool_name": content["functionCall"]["name"],
                                "tool_args": content["functionCall"]["args"]
                            })
                        else:
                            return json.dumps({
                                "action": "final_response",
                                "response": content["text"]
                            })
                    else:
                        print(f"API Error: {await response.text()}")
                        return json.dumps({"action": "error", "response": "API call failed."})
        except Exception as e:
            print(f"Request failed: {e}")
            return json.dumps({"action": "error", "response": "Network request failed."})

    async def run(self, user_query):
        """
        The main agentic loop.
        This function handles the flow of the agent's interaction.
        Note: The `run` function is now async to support the API call.
        """
        try:
            self.memory.append({"role": "user", "content": user_query})

            llm_output_str = await self._get_llm_response_with_tools(user_query)
            llm_output = json.loads(llm_output_str)

            action = llm_output.get("action")

            if action == "call_tool":
                tool_name = llm_output.get("tool_name")
                tool_args = llm_output.get("tool_args", {})

                if tool_name in self.tools:
                    tool_func = self.tools[tool_name]

                    tool_result = await tool_func(**tool_args)
                    print(f"--- Tool call completed. Result: {tool_result} ---")

                    final_response_text = f"I used my tool to get the information. Here's what I found: {tool_result}"
                else:
                    final_response_text = f"Error: The requested tool '{tool_name}' does not exist."

            elif action == "final_response":
                final_response_text = llm_output.get("response")

            else:
                final_response_text = "I'm sorry, I'm unable to process that request."

            print(f"\n--- Final Response from {self.name} ---")
            print(final_response_text)
            self.memory.append({"role": "assistant", "content": final_response_text})

            return final_response_text

        except json.JSONDecodeError:
            print("Error: Failed to parse the LLM's response. It may not be in JSON format.")
            return "I encountered an internal error. Please try again."
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return "I'm sorry, an unexpected error occurred."

# --- Example Usage ---
async def main():
    my_agent = SimpleAIAgent()

    print("Agent started. What can I do for you?")
    print("Try asking about the weather or asking me to search for something.")

    # Example 1: A user asks about the weather, triggering a tool call.
    print("\n--- User Query 1: What is the weather like in New York? ---")
    await my_agent.run("What is the weather like in New York?")

    # Example 2: A user asks about the weather in another location.
    print("\n--- User Query 2: What's the temperature in Paris, France? ---")
    await my_agent.run("What's the temperature in Paris, France?")

    # Example 3: A user asks to perform a web search.
    print("\n--- User Query 3: Can you search for the latest AI news? ---")
    await my_agent.run("Can you search for the latest AI news?")

    # Example 4: A general query that does not require a tool.
    print("\n--- User Query 4: Hello, how are you? ---")
    await my_agent.run("Hello, how are you?")

if __name__ == "__main__":
    asyncio.run(main())
