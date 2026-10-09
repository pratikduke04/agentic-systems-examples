import streamlit as st
from typing import TypedDict
from autogen import AssistantAgent, UserProxyAgent
from langgraph.graph import StateGraph, START, END
import groq
import networkx as nx
import matplotlib.pyplot as plt
import io

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

# Define the state for LangGraph
class QueryState(TypedDict):
    user_input: str
    response: str

# Define AutoGen Assistant Agent
define_assistant = AssistantAgent(
    name="FAQ_Bot",
    llm_config=llm_config,
    system_message="You are a helpful assistant. You can answer FAQs and check order statuses. If you don't know the answer, say 'I am not sure'.",
    code_execution_config={'use_docker': False}
)

user_agent = UserProxyAgent(name="User", code_execution_config={'use_docker': False})

# Function to handle FAQs
def faq_handler(state: QueryState) -> QueryState:
    # A simplified interaction for the graph. The AutoGen agent generates a reply.
    initial_response = define_assistant.generate_reply(messages=[{"role": "user", "content": state["user_input"]}])
    return {"user_input": state["user_input"], "response": initial_response}

# Function to escalate complex queries
def escalate_to_human(state: QueryState) -> QueryState:
    return {"user_input": state["user_input"], "response": "I am unable to handle this request. Escalating to human support. Please wait."}

# Routing function to decide the next step
def route_decision(state: QueryState) -> str:
    # A simple keyword-based router to decide if the bot can handle the request.
    if "i am not sure" in state["response"].lower():
        # If the bot is unsure, escalate.
        return "Escalation"
    else:
        # If the bot provided a confident answer, end the workflow.
        return "end"

# Create LangGraph Workflow
graph = StateGraph(QueryState)
graph.add_node("FAQ_Handler", faq_handler)
graph.add_node("Escalation", escalate_to_human)

graph.set_entry_point("FAQ_Handler")

# Add a conditional edge for routing
graph.add_conditional_edges(
    "FAQ_Handler",
    route_decision,
    {
        "Escalation": "Escalation",
        "end": END # Route to the built-in END node
    }
)
graph.add_edge("Escalation", END) # Escalation also leads to the end

workflow = graph.compile()

# Function to visualize the workflow
def visualize_workflow():
    """Generates and returns a visualization of the LangGraph workflow."""
    G = nx.DiGraph()
    G.add_node("START", shape="diamond", style="filled", fillcolor="green")
    G.add_node("FAQ_Handler", shape="box", style="filled", fillcolor="lightblue")
    G.add_node("Escalation", shape="box", style="filled", fillcolor="orange")
    G.add_node("END", shape="diamond", style="filled", fillcolor="red")

    G.add_edge("START", "FAQ_Handler")
    G.add_edge("FAQ_Handler", "Escalation", label="Unsure")
    G.add_edge("FAQ_Handler", "END", label="Confident")
    G.add_edge("Escalation", "END")

    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(10, 6))
    nx.draw(G, pos, with_labels=True, node_size=3000, node_color=[G.nodes[n]['fillcolor'] for n in G.nodes], font_size=10, font_weight="bold", arrows=True)
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')
    
    # Save the plot to a BytesIO object to display in Streamlit
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    return buf


# Streamlit UI
st.title("Customer Support AI Chatbot")
st.write("Ask a question and let the AI assist you.")

user_input = st.text_input("Enter your query:")
if st.button("Submit"):
    if user_input:
        query = QueryState(user_input=user_input, response="")
        result = workflow.invoke(query)
        st.subheader("Response:")
        st.write(result.get("response"))
        
        # Display the workflow visualization
        st.subheader("Workflow Visualization:")
        graph_image = visualize_workflow()
        st.image(graph_image, caption="Customer Support Workflow Diagram")
    else:
        st.warning("Please enter a query.")

