import streamlit as st
import pytesseract
from pdf2image import convert_from_path
from autogen import ConversableAgent, UserProxyAgent, GroupChat, GroupChatManager
import tempfile
import os
import groq

# Ensure Tesseract is correctly set up (update path if necessary)
# On Windows, you might need to set the path explicitly, e.g.:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Step 1: Set up the Groq client with the new hardcoded API key.
# This config will be shared by all AutoGen agents.
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
    "temperature": 0.3,
}

# Step 2: Function to extract text from a PDF using OCR
def extract_text_from_pdf(uploaded_file):
    """Extracts text from an uploaded PDF file using OCR."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name

        images = convert_from_path(temp_file_path)
        text = "\n".join(pytesseract.image_to_string(img, config="--psm 6") for img in images)
    except Exception as e:
        st.error(f"Error processing PDF: {e}")
        text = ""
    finally:
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
    return text

# Step 3: Define AutoGen Agents
user_agent = UserProxyAgent(name="User", code_execution_config={"use_docker": False})

doc_ingestor = ConversableAgent(
    name="Document_Ingestor",
    system_message="You are an expert at extracting key clauses from legal contract documents. Be concise and accurate.",
    llm_config=llm_config
)

compliance_checker = ConversableAgent(
    name="Compliance_Checker",
    system_message="You are a compliance officer. Review the contract for compliance with GDPR, corporate policies, and industry standards.",
    llm_config=llm_config
)

risk_assessor = ConversableAgent(
    name="Risk_Assessor",
    system_message="You are a risk assessment analyst. Analyze the contract and highlight potential risks, missing clauses, and ambiguities.",
    llm_config=llm_config
)

revision_recommender = ConversableAgent(
    name="Revision_Recommender",
    system_message="You are a legal counsel. Suggest contract modifications to improve clarity, reduce risks, and ensure compliance.",
    llm_config=llm_config
)

# Step 4: Create Streamlit UI
st.title("AutoGen-Powered Contract Review System")
st.write("Upload a contract PDF to have a team of AI agents analyze compliance, risks, and suggest revisions.")

# File Upload Mechanism
uploaded_file = st.file_uploader("Upload Contract PDF", type=["pdf"])

if uploaded_file:
    st.write("Extracting text from PDF...")
    contract_text = extract_text_from_pdf(uploaded_file)

    if contract_text:
        st.subheader("Extracted Contract Text")
        st.text_area("Contract Content", contract_text, height=200)

        if st.button("Analyze Contract"):
            with st.spinner("A team of AI agents is reviewing your contract..."):
                # Use a group chat to make the agents collaborate
                groupchat = GroupChat(
                    agents=[user_agent, doc_ingestor, compliance_checker, risk_assessor, revision_recommender],
                    messages=[],
                    max_round=15
                )
                manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)

                # Initiate the chat with a clear starting message
                user_agent.initiate_chat(
                    manager,
                    message=f"Please analyze the following contract text:\n\n{contract_text}"
                )

                # Display the full conversation history
                st.subheader("Full Agent Conversation")
                for msg in groupchat.messages:
                    st.text(f"{msg['name']}: {msg['content']}")

