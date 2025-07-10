import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from backend.rag_chatbot.chatbot import query_chatbot, list_documents

st.set_page_config(page_title="Document Q&A Chatbot", layout="wide")
st.title("🧠 Ask Questions From Your Documents")

question = st.text_input("Ask a question:")
selected_filename = st.selectbox("Select a document", ["(Search all docs)"] + list_documents())

if st.button("Ask"):
    if question.strip():
        with st.spinner("Thinking..."):
            filename = None if selected_filename == "(Search all docs)" else selected_filename
            answer = query_chatbot(question, selected_filename=filename)
            st.success(answer)
    else:
        st.warning("Please enter a question.")