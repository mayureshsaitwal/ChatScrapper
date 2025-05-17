from dotenv import load_dotenv

import json
# import os
# import re
# import shutil
# import requests
# from bs4 import BeautifulSoup
# import html2text
from prompt import ai_prompt
from pathlib import Path

from langchain.text_splitter import MarkdownTextSplitter
from langchain.schema import Document
from langchain.chains import ConversationalRetrievalChain
from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_community.vectorstores.chroma import Chroma
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.prompts.prompt import PromptTemplate
from langchain_community.llms import Ollama

folder_path = './chroma'
load_dotenv()

def text_to_docs(text, metadata):
    doc_chunks = []
    text_splitter = MarkdownTextSplitter(chunk_size=2048, chunk_overlap=128)
    chunks = text_splitter.split_text(text)
    for i, chunk in enumerate(chunks):
        doc = Document(page_content=chunk, metadata=metadata)
        doc_chunks.append(doc)
    return doc_chunks

def get_doc_chunks(text, metadata):
    doc_chunks = text_to_docs(text, metadata)
    return doc_chunks

def get_chroma_client():
    embedding_function  = OllamaEmbeddings(model='nomic-embed-text', base_url="http://localhost:11434")
    return Chroma(
        collection_name="batch",
        embedding_function=embedding_function,
        persist_directory="data/chroma")

def store_docs():
    meta_dir = Path("./data/metadata")
    html_dir = Path("./data/html")
    for meta_file,html_file in zip(meta_dir.iterdir(),html_dir.iterdir()):
        if meta_file.is_file() and html_file.is_file():
            with open(meta_file, 'r', encoding='utf-8') as meta:
                metadata = json.load(meta)

            with open(html_file, 'r', encoding='utf-8') as html:
                text = html.read()

            # text, metadata = get_data_from_website(url)
            docs = get_doc_chunks(text, metadata)
            vector_store = get_chroma_client()
            vector_store.add_documents(docs)
    # vector_store.persist()


# system_prompt = ai_prompt
system_prompt = """You are a helpful, friendly, and intelligent AI assistant.

- If the user greets you or engages in casual conversation (e.g., "Hi", "How are you?", "Thanks"), respond naturally and politely.
- If the user asks a factual or topic-specific question, first check the provided knowledge base.
- Use only the provided context to answer. If relevant information is found, respond clearly and concisely.
- If no relevant information is found in the tool calls, respond with: "Sorry, I don't know."

----------------

{context}
{chat_history}
Follow up question:"""

# system_prompt = """You are a helpful assistant. Check your knowledge base before answering any questions.
#     if no relevant information is found in the tool calls, respond, "Sorry, I don't know."
#
# ----------------
#
# {context}
# {chat_history}
# Follow up question: """


def get_prompt():
    prompt = ChatPromptTemplate(
        input_variables=['context', 'question', 'chat_history',],
        messages=[
            SystemMessagePromptTemplate(
                prompt=PromptTemplate(
                    input_variables=['context', 'question', 'chat_history',],
                    template=system_prompt, template_format='f-string',
                    validate_template=True
                ), additional_kwargs={}
            ),
            HumanMessagePromptTemplate(
                prompt=PromptTemplate(
                    input_variables=['question'],
                    template='{question}\nHelpful Answer:', template_format='f-string',
                    validate_template=True
                ), additional_kwargs={}
            )
        ]
    )
    return prompt

def make_chain():

    model=Ollama(model="gemma3")
    vector_store = get_chroma_client()
    prompt = get_prompt()

    # retriever = vector_store.as_retriever(search_type="mmr", verbose=True)
    retriever = vector_store.as_retriever(search_type="mmr", verbose=False)

    chain = ConversationalRetrievalChain.from_llm(
        model,
        retriever=retriever,
        return_source_documents=True,
        combine_docs_chain_kwargs=dict(prompt=prompt),
        # verbose=True,
        verbose=False,
        rephrase_question=False,
    )
    return chain

def get_response(question):
    chat_history = ""
    chain = make_chain()
    response = chain.invoke({"question": question, "chat_history": chat_history})
    return response['answer']


# def store_multiple_urls(file_path):
#     with open(file_path, 'r') as file:
#         urls = [line.strip() for line in file if line.strip()]
#
#     for url in urls:
#         print(f"Processing URL: {url}")
#         try:
#             store_docs(url)
#         except Exception as e:
#             print(f"Error processing {url}: {e}")

# mainurl = "https://www.coeptech.ac.in/about-us/about-university/"
# store_docs(mainurl)
# store_multiple_urls("urls.txt")
store_docs()
print("Website Scraped and Stored for RAG")
