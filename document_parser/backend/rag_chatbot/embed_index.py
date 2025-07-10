import boto3
import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from dotenv import load_dotenv

load_dotenv()

VECTORSTORE_DIR = "backend/rag_chatbot/vector_store"


def fetch_raw_texts():
    dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
    table = dynamodb.Table("DocumentMetadata")
    response = table.scan()

    documents = []
    for item in response.get("Items", []):
        if "raw_text" in item and item["raw_text"].strip():
            doc = Document(
                page_content=item["raw_text"],
                metadata={"filename": item.get("filename", "unknown")}
            )
            documents.append(doc)
    return documents


def build_vector_store():
    documents = fetch_raw_texts()
    if not documents:
        print("⚠️ No documents found in DynamoDB.")
        return

    embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(VECTORSTORE_DIR)
    print("✅ Vector store created and saved!")


if __name__ == "__main__":
    build_vector_store()