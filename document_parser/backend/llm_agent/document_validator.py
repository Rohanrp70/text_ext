import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def validate_document_fields(data):
    prompt =  f"""
    You are a document validation assistant.

    This document has the following extracted fields:
    {data}

    Your tasks:
    1. Try to infer what type of document this is (e.g., invoice, contract, resume, report).
    2. Summarize its key contents.
    3. Identify if any expected fields for that type are missing (like signature, total, email, etc.).
    4. Suggest corrections or enhancements if any.

    Respond in a helpful, structured way.
   """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    return response['choices'][0]['message']['content']