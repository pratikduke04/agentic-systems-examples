import streamlit as st
import requests
from autogen import AssistantAgent, UserProxyAgent
import groq

# Step 1: Set up the Groq client with the new hardcoded API key.
# This config will be used by the AutoGen agent.
llm_config = {
    "config_list": [
        {
            "model": "openai/gpt-oss-20b",
            # NOTE: "openai/gpt-oss-20b" is not a valid model on Groq.
            # For this script to run, replace it with a valid model like "llama3-70b-8192".
            "api_key": "REPLACE_WITH_YOUR_GROQ_API_KEY",
            "base_url": "https://api.groq.com/openai/v1"
        }
    ],
    "temperature": 0.7,
}

# Step 2: Define the function to fetch weather data using the OpenWeatherMap API
def get_weather(city: str) -> str:
    """Fetches the current weather for a given city from an external API."""
    # Note: For simplicity, the API key is hardcoded here.
    # In a real application, this should be stored securely.
    api_key = "d3c8f97ae904bda385f51c42dd996d05"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        temperature = data['main']['temp']
        weather_description = data['weather'][0]['description']
        return f"The current temperature in {city} is {temperature}°C with {weather_description}."
    except requests.exceptions.RequestException as e:
        return f"Unable to fetch weather data. Error: {e}"

# Step 3: Define the Tool-Using Agent using AutoGen
weather_agent = AssistantAgent(
    name="Weather_Agent",
    llm_config=llm_config,
    system_message="You are a helpful assistant that can provide weather forecasts.",
)

user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={"work_dir": "web"},
    # Register the get_weather function with the agent
    function_map={"get_weather": get_weather}
)

# Step 4: Streamlit UI
def main():
    st.title("Tool-Using Weather Agent")
    st.markdown("Enter the name of a city to get current weather information from a live API.")

    city = st.text_input("Enter City Name:")

    if city and st.button("Get Weather"):
        # The user proxy agent initiates the chat and calls the tool
        user_proxy.initiate_chat(
            weather_agent,
            message=f"What is the weather like in {city}?"
        )
        # We need to get the last message from the chat history
        chat_history = user_proxy.chat_messages[weather_agent]
        last_message = chat_history[-1]['content']
        st.write(last_message)


# Step 5: Run the Streamlit app
if __name__ == "__main__":
    main()
