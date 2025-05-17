from dotenv import load_dotenv

import os
import re
import shutil
import requests
from bs4 import BeautifulSoup
import html2text
from prompt import ai_prompt

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

def preload():
    folder_path = './data'
    load_dotenv()

    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        shutil.rmtree(folder_path)
        print(f"Removed existing folder: {folder_path}")
    else:
        print(f"No folder found at: {folder_path}")
# shutil.rmtree('./data')

def get_data_from_website(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' +
                      'AppleWebKit/537.36 (KHTML, like Gecko) ' +
                      'Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    response = requests.get(url,headers=headers)
    if response.status_code == 500:
        print("Server error")
        return
    soup = BeautifulSoup(response.content, 'html.parser')

    for script in soup(["script", "style","a"]):
        script.extract()

    # Extract text in markdown format
    html = str(soup)
    html2text_instance = html2text.HTML2Text()
    html2text_instance.images_to_alt = True
    html2text_instance.body_width = 0
    html2text_instance.single_line_break = True
    text = html2text_instance.handle(html)

    # Extract page metadata
    try:
        page_title = soup.title.string.strip()
    except:
        page_title = url.path[1:].replace("/", "-")
    meta_description = soup.find("meta", attrs={"name": "description"})
    meta_keywords = soup.find("meta", attrs={"name": "keywords"})
    if meta_description:
        description = meta_description.get("content")
    else:
        description = page_title
    if meta_keywords:
        meta_keywords = meta_description.get("content")
    else:
        meta_keywords = ""

    metadata = {'title': page_title,
                'url': url,
                'description': description,
                'keywords': meta_keywords}

    return text, metadata


def merge_hyphenated_words(text):
    return re.sub(r"(\w)-\n(\w)", r"\1\2", text)


def fix_newlines(text):
    return re.sub(r"(?<!\n)\n(?!\n)", " ", text)


def remove_multiple_newlines(text):
    return re.sub(r"\n{2,}", "\n", text)

def clean_text(text):
    cleaning_functions = [merge_hyphenated_words, fix_newlines, remove_multiple_newlines]
    for cleaning_function in cleaning_functions:
        text = cleaning_function(text)
    return text

def text_to_docs(text, metadata):
    doc_chunks = []
    text_splitter = MarkdownTextSplitter(chunk_size=2048, chunk_overlap=128)
    chunks = text_splitter.split_text(text)
    for i, chunk in enumerate(chunks):
        doc = Document(page_content=chunk, metadata=metadata)
        doc_chunks.append(doc)
    return doc_chunks

def get_doc_chunks(text, metadata):
    text = clean_text(text)
    doc_chunks = text_to_docs(text, metadata)
    return doc_chunks

def get_chroma_client():
    embedding_function  = OllamaEmbeddings(model='nomic-embed-text', base_url="http://localhost:11434")
    return Chroma(
        collection_name="website_data",
        embedding_function=embedding_function,
        persist_directory="data/chroma")

def store_docs(url):
    text, metadata = get_data_from_website(url)
    print(metadata)
    title = metadata["title"].split()
    file_name = ''.join(title[:2])
    with open(f"./{file_name}.txt","w")  as f:
        f.write(text)
    docs = get_doc_chunks(text, metadata)
    vector_store = get_chroma_client()
    vector_store.add_documents(docs)
    # vector_store.persist()


# system_prompt = ai_prompt
system_prompt = """
Answer the question based only on the following context:

{context}
{chat_history}

---

Answer the question based on the above context: {question}
"""
# system_prompt = """You are a helpful, friendly, and intelligent AI assistant.
#
# - If the user greets you or engages in casual conversation (e.g., "Hi", "How are you?", "Thanks"), respond naturally and politely.
# - If the user asks a factual or topic-specific question, first check the provided knowledge base.
# - Use only the provided context to answer. If relevant information is found, respond clearly and concisely.
# - If no relevant information is found in the tool calls, respond with: "Sorry, I don't know."
#
# ----------------
#
# {context}
# {chat_history}
# Follow up question:"""

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

    model=Ollama(model="mistral")
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


def store_multiple_urls(file_path):
    with open(file_path, 'r') as file:
        urls = [line.strip() for line in file if line.strip()]

    for url in urls:
        print(f"Processing URL: {url}")
        try:
            store_docs(url)
        except Exception as e:
            print(f"Error processing {url}: {e}")

# mainurl = "https://www.coeptech.ac.in/about-us/about-university/"
# store_docs(mainurl)
if __name__ == "__main__":
    preload()
    store_multiple_urls("urls.txt")
    print("Website Scraped and Stored for RAG")
