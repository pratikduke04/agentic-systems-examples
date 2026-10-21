# Step 1: Set Up API Key
# This script is configured to use a hardcoded Groq API key.

import autogen

# The config_list tells autogen how to connect to the LLM.
# We are pointing it to Groq's API endpoint.
config_list = [
    {
        # NOTE: "openai/gpt-oss-20b" is not a valid model on Groq. 
        # For this script to run, replace it with a valid model like "llama3-70b-8192".
        "model": "openai/gpt-oss-20b",
        "api_key": "REPLACE_WITH_YOUR_GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1" 
    }
]


# Step 2: Define Customer and Support Agents
# Creating a customer agent that represents a user seeking support.
customer_agent = autogen.UserProxyAgent(
    name="customer",
    human_input_mode="ALWAYS",  # Allows manual input for demonstration purposes.
    code_execution_config={"use_docker": False},
    max_consecutive_auto_reply=5
)

# Creating a support agent that will respond to customer queries using the Groq LLM.
support_agent = autogen.AssistantAgent(
    name="support_agent",
    llm_config={
        "config_list": config_list,
        "temperature": 0.7,
    },
    system_message="You are a helpful AI support agent. Answer customer queries clearly and professionally.",
    code_execution_config={'use_docker': False},
    max_consecutive_auto_reply=5
)

# Step 3: Running a Simulated Customer Interaction
# The customer initiates a conversation with the support agent.
# The user will be prompted in the terminal to provide input for the 'customer' agent.
customer_agent.initiate_chat(support_agent, message="I need help tracking my order.")

