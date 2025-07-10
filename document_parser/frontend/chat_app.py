import streamlit as st
import os
import sys
import json
import boto3

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.llm_agent.chat_agent import ask_question_about_document

st.set_page_config(page_title="📚 Document Chatbot", layout="wide")
st.title("💬 Document Intelligence Chatbot")

# Connect to DynamoDB
try:
    session = boto3.Session(profile_name='terraform-rohan')
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table('DocumentMetadata')
except Exception as e:
    st.error(f"Failed to connect to DynamoDB: {e}")
    st.stop()

# Load documents
try:
    response = table.scan()
    items = response.get("Items", [])
except Exception as e:
    st.error(f"Failed to fetch documents: {e}")
    st.stop()

if not items:
    st.warning("No documents found.")
else:
    selected_doc = st.selectbox("Choose a document", [item['filename'] for item in items])
    doc_data = next(item for item in items if item['filename'] == selected_doc)

    # Chat interface
    st.subheader("Ask a question about the document")
    question = st.text_input("Your question:")
    if st.button("Ask"):
        with st.spinner("Thinking..."):
            answer = ask_question_about_document(question, doc_data)
            st.markdown("**Answer:**")
            st.write(answer)
