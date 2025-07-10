import openai
import os
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_question_about_document(question, doc_data):
    # Combine extracted_fields, tables, and raw_text
    fields = doc_data.get("extracted_fields", {})
    tables = doc_data.get("tables", [])
    raw_text = doc_data.get("raw_text", "")

    combined_context = f"""
Document Metadata:
Extracted Fields: {fields}
Tables: {tables}
Raw Text: {raw_text}
"""

    prompt = f"""
You are an AI assistant helping users understand document contents.

Context:
{combined_context}

User Question:
{question}

Answer the question clearly based on the document above.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Failed to get answer: {e}"
