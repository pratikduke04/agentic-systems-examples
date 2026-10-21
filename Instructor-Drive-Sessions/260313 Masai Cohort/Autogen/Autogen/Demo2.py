import autogen
import streamlit as st
import groq

# Step 1: Set up the Groq client with a hardcoded API key.
client = groq.Groq(
    api_key="REPLACE_WITH_YOUR_GROQ_API_KEY",
)

# Step 2: Define an IT Support chatbot that remembers past issues
class ITSupportBot(autogen.AssistantAgent):
    def __init__(self, name, memory=None, model="openai/gpt-oss-20b"):
        super().__init__(name=name)
        self.memory = memory if memory is not None else {}  # Stores past user issues
        
        # NOTE: "openai/gpt-oss-20b" is not a valid model on Groq. 
        # For this script to run, replace it with a valid model like "llama3-70b-8192".
        self.model = model  # Specifies the LLM model

    def generate_reply(self, message, sender, **kwargs):
        """
        Step 3: Generates a response based on user input and past issues.
        - Retrieves past issues if available
        - Stores the latest issue in memory
        - Calls the Groq LLM to generate a response
        """
        context = self.memory.get(sender, "")  # Retrieves past issue if available
        self.memory[sender] = message  # Stores latest issue in memory
        
        response = self._get_groq_response(message, context)  # Calls Groq for reply
        return response
    
    def _get_groq_response(self, message, context):
        """
        Step 4: Calls Groq's LLM to generate a response with past issue history.
        - Constructs a prompt including past conversation history
        - Sends the prompt to the specified model
        - Returns the generated response
        """
        prompt = f"User's previous issue: {context}\nNew issue: {message}\nIT Support Response:"
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful IT support assistant providing troubleshooting steps."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()

# Step 5: Streamlit UI for real-time chatbot interaction
st.title(" IT Support Chatbot")
st.write("Ask me about your IT issues, and I'll provide troubleshooting steps!")

# Initialize chatbot
if "chatbot" not in st.session_state:
    st.session_state.chatbot = ITSupportBot(name="HelpDeskBot")

# Input field for user query
user_input = st.text_input("You:", "")

if st.button("Send"):
    if user_input:
        response = st.session_state.chatbot.generate_reply(user_input, "User1")
        st.write(f"**HelpDeskBot:** {response}")
