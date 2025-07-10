import openai
import json
import re

def extract_with_openai(raw_text, api_key):
    prompt = f"""
You are an intelligent document parsing assistant.

The following is the unstructured text extracted from a document:
\"\"\"{raw_text}\"\"\"

Your task:
1. Identify the type of document (e.g., resume, invoice, medical report).
2. Extract all relevant structured fields from the document.
3. Organize fields logically under keys like personal_info, education, skills, contact, etc., depending on content.
4. Return ONLY a valid JSON object with your findings. No explanations or markdown.
"""

    client = openai.OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a document extraction assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content.strip()

        # 🧹 Strip markdown ```json ... ``` block
        if content.startswith("```json"):
            content = re.sub(r"^```json\s*|\s*```$", "", content.strip(), flags=re.DOTALL)

        print("🧠 Cleaned GPT content:\n", content)
        return json.loads(content)

    except json.JSONDecodeError as je:
        print("❌ GPT response was not valid JSON. Returning raw text.")
        return {"raw_text": raw_text}

    except Exception as e:
        print(f"❌ GPT Fallback failed: {str(e)}")
        return {"raw_text": raw_text}
