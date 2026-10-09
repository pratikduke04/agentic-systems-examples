import streamlit as st
import autogen
import groq

# Step 1: Set up the Groq client with the new hardcoded API key.
client = groq.Groq(
    api_key="REPLACE_WITH_YOUR_GROQ_API_KEY",
)

# Step 2: Define the Diagnostic Agent
class DiagnosticAgent(autogen.AssistantAgent):
    def __init__(self, name="DiagnosticAgent", model="openai/gpt-oss-20b"):
        super().__init__(name=name)
        # NOTE: "openai/gpt-oss-20b" is not a valid model on Groq.
        # For this script to run, replace it with a valid model like "llama3-70b-8192".
        self.model = model
    
    def diagnose_issue(self, message):
        """
        The Diagnostic Agent analyzes the issue and determines possible causes.
        """
        prompt = f"""
        The user has reported an IT issue: "{message}".
        As the Diagnostic Agent, analyze the problem and list possible causes.
        """
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an IT diagnostic expert."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()

# Step 3: Define the Resolution Agent
class ResolutionAgent(autogen.AssistantAgent):
    def __init__(self, name="ResolutionAgent", model="openai/gpt-oss-20b"):
        super().__init__(name=name)
        # NOTE: "openai/gpt-oss-20b" is not a valid model on Groq.
        # For this script to run, replace it with a valid model like "llama3-70b-8192".
        self.model = model
    
    def provide_solution(self, diagnosis):
        """
        The Resolution Agent suggests a fix based on the diagnosis from the Diagnostic Agent.
        """
        prompt = f"""
        The Diagnostic Agent has identified the following possible causes:
        "{diagnosis}".
        As the Resolution Agent, suggest step-by-step troubleshooting solutions.
        """
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an IT troubleshooting expert."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()

# Step 5: Deploy via Streamlit
st.title("AutoGen IT Support Chatbot - Agent Collaboration")
st.write("An AI-powered chatbot where agents collaborate to diagnose and resolve IT issues.")

# User Input
user_input = st.text_area("Describe your IT issue:")
if st.button("Get Support"):
    if user_input.strip():
        # Initialize both agents
        diagnostic_agent = DiagnosticAgent()
        resolution_agent = ResolutionAgent()
        
        # Agent Collaboration: The output of one agent becomes the input for the next
        diagnosis = diagnostic_agent.diagnose_issue(user_input)
        solution = resolution_agent.provide_solution(diagnosis)
        
        st.subheader("Diagnosis:")
        st.write(diagnosis)
        
        st.subheader("Suggested Solution:")
        st.write(solution)
    else:
        st.warning("Please enter a valid IT issue.")

