import json
import os
from textwrap import dedent
from dotenv import load_dotenv
import requests

from crewai import Agent, Crew, LLM, Task
from crewai.tools import tool

# --- 0. INITIALIZATION & SETUP ---
load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing. Please set it in your .env file.")

os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY


# --- 1. DEFINE TOOLS ---
@tool("Search the internet")
def search_internet(query: str) -> str:
    """Useful to search the internet about a given topic and return relevant results."""
    top_result_to_return = 4
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "content-type": "application/json",
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response_json = response.json()

        if "organic" not in response_json:
            return "Error: Could not retrieve search results. Please verify your Serper API key."

        results = response_json["organic"]
        string = []
        for result in results[:top_result_to_return]:
            string.append(
                "\n".join(
                    [
                        f"Title: {result.get('title', '')}",
                        f"Link: {result.get('link', '')}",
                        f"Snippet: {result.get('snippet', '')}",
                        "\n-----------------",
                    ]
                )
            )
        return "\n".join(string)
    except Exception as e:
        return f"Error performing search: {str(e)}"


@tool("Make a calculation")
def calculate(operation: str) -> str:
    """Performs basic arithmetic calculations."""
    try:
        return str(eval(operation))
    except Exception as e:
        return f"Error: Invalid mathematical expression - {str(e)}"


# --- 2. DEFINE GEMINI LLM ---
# Using gemini-2.0-flash as a stable endpoint for tool calling and multi-agent execution
gemini_llm = LLM(
    model="gemini/gemini-2.0-flash",
    api_key=GEMINI_API_KEY,
    temperature=0.2,
)


# --- 3. DEFINE AGENTS ---
expert_travel_agent = Agent(
    role="Expert Travel Agent",
    backstory="I am a seasoned expert in travel planning and logistics specializing in curated family trips.",
    goal="Plan a complete 4-day trip with day-by-day itineraries, including dining, packing tips, and safety.",
    tools=[search_internet, calculate],
    verbose=True,
    llm=gemini_llm,
)

city_selection_expert = Agent(
    role="City Selection Expert",
    backstory="A specialist at analyzing travel destinations for family celebrations.",
    goal="Evaluate destinations based on weather, local culture, and traveler preferences.",
    tools=[search_internet],
    verbose=True,
    llm=gemini_llm,
)

local_tour_guide = Agent(
    role="Local Tour Guide",
    backstory="A local guide knowledgeable about French Quarter heritage, beachside dining, and cultural landmarks.",
    goal="Provide cultural insights, aesthetic photo spots, and cafe recommendations.",
    tools=[search_internet],
    verbose=True,
    llm=gemini_llm,
)


def main():
    print("## Welcome to Trip Planner Crew")
    print("-------------------------------")

    origin = input("From where will you be traveling?\n")
    cities = input("What destination option are you considering?\n")
    date_range = input("What is your travel date range?\n")
    interests = input("What are your key interests/occasions?\n")

    destination_selection_task = Task(
        description=dedent(f"""Evaluate {cities} for travel from {origin} during {date_range} focusing on {interests}."""),
        expected_output="A detailed destination selection report recommending the best city.",
        agent=city_selection_expert,
    )

    city_guide_task = Task(
        description=dedent(f"""Compile a city guide for {cities} featuring top cafes, heritage spots, and birthday dining."""),
        expected_output="A city guide highlighting top attractions and cultural spots.",
        agent=local_tour_guide,
    )

    itinerary_task = Task(
        description=dedent(f"""Develop a day-by-day travel itinerary for {cities} from {date_range}."""),
        expected_output="A complete daily itinerary with hotel, dining, packing, and budget suggestions.",
        agent=expert_travel_agent,
    )

    travel_crew = Crew(
        agents=[city_selection_expert, local_tour_guide, expert_travel_agent],
        tasks=[destination_selection_task, city_guide_task, itinerary_task],
        verbose=True,
    )

    result = travel_crew.kickoff()

    print("\n\n########################")
    print("## Here is your Trip Plan")
    print("########################\n")
    print(result)


if __name__ == "__main__":
    main()