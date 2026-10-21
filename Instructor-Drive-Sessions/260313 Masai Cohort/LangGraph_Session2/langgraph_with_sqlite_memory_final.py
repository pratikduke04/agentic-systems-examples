import groq
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
import streamlit as st
import matplotlib.pyplot as plt
import networkx as nx
import sqlite3
import uuid

# Groq API setup with the hardcoded key
client = groq.Groq(
    api_key="REPLACE_WITH_YOUR_GROQ_API_KEY",
)

# Graph state definition
class State(TypedDict):
    product_name: str
    basic_description: str
    features_benefits: str
    marketing_message: str
    final_description: str

# Step 3: Generate a basic product description
def generate_basic_description(state):
    """Generate a basic description for the product."""
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates brief product descriptions."},
            {"role": "user", "content": f"Write a brief description of a product named '{state['product_name']}'."}
        ]
    )
    basic_description = response.choices[0].message.content
    return {"basic_description": basic_description}

# Step 4: Add key features and benefits to the product description
def add_features_benefits(state: State):
    """Add features and benefits to the product description."""
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": f"List key features and benefits of the product: {state['basic_description']}"}]
    )
    features_benefits = response.choices[0].message.content
    return {"features_benefits": features_benefits}

# Step 5: Create a compelling marketing message based on the product's features
def create_marketing_message(state: State):
    """Create a marketing message for the product."""
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": f"Create a compelling marketing message for the product: {state['features_benefits']}"}]
    )
    marketing_message = response.choices[0].message.content
    return {"marketing_message": marketing_message}

# Step 6: Final polish and completion of the product description
def polish_final_description(state: State):
    """Polish and finalize the product description."""
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": f"Polish and finalize the product description, incorporating the marketing message: {state['marketing_message']}"}]
    )
    final_description = response.choices[0].message.content
    return {"final_description": final_description}


# Step 7: Function to build the workflow (Separate from Streamlit logic)
def build_workflow(memory):
    """Build and compile the workflow steps using LangGraph."""
    # Build the workflow for generating the product description
    workflow = StateGraph(State)
    
    # Add nodes to the workflow (steps in the process)
    workflow.add_node("generate_basic_description", generate_basic_description)
    workflow.add_node("add_features_benefits", add_features_benefits)
    workflow.add_node("create_marketing_message", create_marketing_message)
    workflow.add_node("polish_final_description", polish_final_description)

    # Add edges to connect the nodes (steps in order)
    workflow.add_edge(START, "generate_basic_description")
    workflow.add_edge("generate_basic_description", "add_features_benefits")
    workflow.add_edge("add_features_benefits", "create_marketing_message")
    workflow.add_edge("create_marketing_message", "polish_final_description")
    workflow.add_edge("polish_final_description", END)

    
    # Compile the workflow into a chain of actions
    chain = workflow.compile(checkpointer=memory)

    return chain

# Step 8: Function to visualize the workflow (saved as an image)
def visualize_workflow():
    """Visualize and save the workflow as an image."""

    graph = nx.DiGraph()
    edges = [
    ("START", "generate_basic_description"), 
    ("generate_basic_description", "add_features_benefits"),
    ("add_features_benefits", "create_marketing_message"),
    ("create_marketing_message", "polish_final_description"),
    ("polish_final_description", "END")]

    graph.add_edges_from(edges)

    plt.figure(figsize=(10, 6))
    pos = nx.spring_layout(graph, seed=42)
    nx.draw(graph, pos, with_labels=True, node_color='skyblue', node_size=2500, edge_color='gray', font_size=10, font_weight='bold', arrowsize=20)
    plt.title("Product Description Generation Workflow")
    plt.savefig("workflow.png")

# Main Streamlit function
def run_streamlit_app():
    """Handles the entire app logic: input, workflow, and output."""
    # Title for the app
    st.title("Product Description Generator with LangGraph & Groq")

    # Initialize SQLite Checkpointer and Thread ID in session state
    if "memory" not in st.session_state:
        # check_same_thread=False is required for Streamlit's threading model
        conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
        st.session_state.memory = SqliteSaver(conn)
        
    st.sidebar.header("Resume Session")
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
        
    # Expose Thread ID so user can copy it, restart app, and paste it to resume
    st.session_state.thread_id = st.sidebar.text_input(
        "Thread ID (Save this to resume later):", 
        value=st.session_state.thread_id
    )

    # Build workflow and config globally so we can check state without generating
    chain = build_workflow(st.session_state.memory)
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    if st.sidebar.button("Load Saved State"):
        saved_state = chain.get_state(config)
        if saved_state.values:
            st.sidebar.success("Found saved memory!")
            st.sidebar.json(saved_state.values)
        else:
            st.sidebar.warning("No memory found for this Thread ID.")

    # Step 1: Take product name as input from the user
    product_name = st.text_input("Enter the product name:", placeholder="e.g., Smart Water Bottle")

    # Step 2: Button to generate product description
    if st.button("Generate Product Description"):
        if not product_name:
            st.warning("Please enter a product name.")
        else:
            with st.spinner("Generating description..."):
                # Create the initial state with product name and empty fields for description steps
                initial_state = {
                    "product_name": product_name, 
                    "basic_description": "", 
                    "features_benefits": "", 
                    "marketing_message": "", 
                    "final_description": ""
                }

                # Run the workflow and get the results (chain and config are now defined above)
                result = chain.invoke(initial_state, config=config)

                # Display the results in Streamlit
                st.subheader("Basic Description:")
                st.write(result["basic_description"])

                st.subheader("Features and Benefits:")
                st.write(result["features_benefits"])

                st.subheader("Marketing Message:")
                st.write(result["marketing_message"])

                st.subheader("Final Description:")
                st.write(result["final_description"])

                # Step 3: Visualize the workflow and save it as an image
                visualize_workflow()
                st.image("workflow.png", caption="Product Description Workflow")

if __name__ == "__main__":
    run_streamlit_app()