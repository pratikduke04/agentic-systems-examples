import streamlit as st
import autogen
import groq

# Step 1: Set up the Groq client with the new hardcoded API key.
client = groq.Groq(
    api_key="REPLACE_WITH_YOUR_GROQ_API_KEY",
)

# Step 2: Define the Diagnostic Agent
class DiagnosticAgent(autogen.AssistantAgent):
    def __init__(self, name="DiagnosticAgent"):
        super().__init__(name=name)

    def analyze_issue(self, issue):
        """Analyzes the issue and decides whether to resolve or escalate."""
        if any(keyword in issue.lower() for keyword in ["password", "slow internet", "software update"]):
            return "simple"
        elif any(keyword in issue.lower() for keyword in ["network failure", "hardware crash", "security breach"]):
            return "critical"
        else:
            return "complex"

# Step 3: Define the Resolution Agent
class ResolutionAgent(autogen.AssistantAgent):
    def __init__(self, name="ResolutionAgent", model="openai/gpt-oss-20b"):
        super().__init__(name=name)
        # NOTE: "openai/gpt-oss-20b" is not a valid model on Groq.
        # For this script to run, replace it with a valid model like "llama3-70b-8192".
        self.model = model

    def resolve_issue(self, issue):
        """Uses Groq's LLM to troubleshoot complex problems."""
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an IT support specialist providing solutions to technical problems."},
                {"role": "user", "content": f"Troubleshoot the following IT issue: {issue}"}
            ]
        )
        return response.choices[0].message.content.strip()

# Step 4: Define the Escalation Agent
class EscalationAgent(autogen.AssistantAgent):
    def __init__(self, name="EscalationAgent"):
        super().__init__(name=name)

    def escalate_issue(self, issue):
        """Escalates the issue to human IT support."""
        return f"The issue '{issue}' is critical and requires human intervention. Escalating to the IT support team immediately."

# Step 5: Streamlit UI
st.title("Multi-Agent IT Support System")
st.write("AI-powered IT support with multi-agent interaction and escalation.")

# User Input
user_issue = st.text_area("Describe your IT issue:")

if st.button("Get Support"):
    if user_issue.strip():
        # Initialize all agents
        diagnostic_agent = DiagnosticAgent()
        resolution_agent = ResolutionAgent()
        escalation_agent = EscalationAgent()

        # Let the Diagnostic Agent analyze the issue first
        issue_type = diagnostic_agent.analyze_issue(user_issue)

        # Route the issue based on the diagnosis
        if issue_type == "simple":
            st.success("This seems to be a common issue. It has been resolved with basic troubleshooting. Please check our FAQ for more details.")
        elif issue_type == "complex":
            response = resolution_agent.resolve_issue(user_issue)
            st.subheader("Resolution Agent Response:")
            st.write(response)
        else: # 'critical'
            response = escalation_agent.escalate_issue(user_issue)
            st.subheader("Escalation Agent Response:")
            st.warning(response)
    else:
        st.warning("Please enter a valid IT issue.")
