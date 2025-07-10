import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

load_dotenv()

VECTORSTORE_DIR = "backend/rag_chatbot/vector_store"


def load_vectorstore():
    embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
    return FAISS.load_local(VECTORSTORE_DIR, embeddings, allow_dangerous_deserialization=True)


def list_documents():
    vectorstore = load_vectorstore()
    return sorted(set(doc.metadata.get("filename", "") for doc in vectorstore.docstore._dict.values()))


def query_chatbot(question, selected_filename=None):
    vectorstore = load_vectorstore()

    if selected_filename:
        # Simulate filtering manually
        filtered_docs = [doc for doc in vectorstore.docstore._dict.values() if doc.metadata.get("filename") == selected_filename]
        if not filtered_docs:
            return f"No content found for document: {selected_filename}"

        # Create a new temporary FAISS index
        embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        vectorstore = FAISS.from_documents(filtered_docs, embeddings)

    retriever = vectorstore.as_retriever(search_type="similarity", k=3)
    llm = ChatOpenAI(model="gpt-4o", openai_api_key=os.getenv("OPENAI_API_KEY"))

    prompt_template = """You are a helpful assistant. Use the context to answer the question.
If you don’t find an answer in the context, say \"Not found.\"

Context:
{context}

Question: {question}
"""
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={
            "prompt": PromptTemplate.from_template(prompt_template)
        }
    )

    result = qa_chain({"query": question})
    return result["result"]