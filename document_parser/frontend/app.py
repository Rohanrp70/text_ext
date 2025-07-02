import streamlit as st
import sys
import os
import boto3
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.llm_agent.document_validator import validate_document_fields

st.set_page_config(page_title="Document Intelligence Viewer", layout="wide")
st.title(" Document Intelligence Viewer")

# Initialize DynamoDB resource
try:
    session = boto3.Session(profile_name='terraform-rohan')  # replace with your actual profile name
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table('DocumentMetadata')
except Exception as e:
    st.error(f"Error initializing DynamoDB resource: {e}")
    st.stop()

# Fetch documents from DynamoDB
try:
    response = table.scan()
    items = response.get("Items", [])
except Exception as e:
    st.error(f"Error fetching documents from DynamoDB: {e}")
    st.stop()

if not items:
    st.warning("No documents found in the database.")
else:
    # Select document dropdown
    selected_doc = st.selectbox("Select a document", [item['filename'] for item in items])
    doc_data = next(item for item in items if item['filename'] == selected_doc)

    st.subheader(" Extracted Fields")
    st.json(doc_data.get('extracted_fields', {}))

    st.subheader(" Tables")
    tables = doc_data.get('tables', [])
    if tables:
        for idx, table_data in enumerate(tables):
            st.markdown(f"*Table {idx + 1}*")
            # Table data might be stored as JSON string or list of dicts
            # Try to parse if necessary
            if isinstance(table_data, str):
                try:
                    table_data = json.loads(table_data)
                except json.JSONDecodeError:
                    st.write(table_data)
                    continue
            st.table(table_data)
    else:
        st.info("No tables found in this document.")

    # Button to trigger validation
    if st.button(" Validate Document with LLM"):
        with st.spinner("Validating document fields..."):
            try:
                result = validate_document_fields(doc_data.get('extracted_fields', {}))
                st.success("Validation Complete!")
                st.markdown(result)
            except Exception as e:
                st.error(f"Error during validation: {e}")