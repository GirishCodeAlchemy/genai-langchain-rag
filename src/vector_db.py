import os
from typing import List

import genai_service as model
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.vectorstores import FAISS


def find_filename(path: str):
    if not path:
        return ""
    return os.path.basename(path)


class KnowledgeDB:

    def __init__(self, text: str, source: str):
        self.text = text
        self.source = source


class VectorDB:
    def search(self, query: str, model_provider: model.GenAIModels):
        raise Exception("Not implemented")

    @staticmethod
    def get_instance(model_provider: model.GenAIModels):
        return InMemory(model_provider)


class InMemory(VectorDB):

    # Initialize the vector store using FAISS
    def __init__(self, model_provider: model.GenAIModels):
        chunked_documents = [
            self.get_html_chunks(),
            self.get_pdf_chunks()
        ]
        
        # Use FAISS to create an in-memory vector store.
        # This calls LLM Gateway to generate embeddings
        if not os.path.exists("local_vector_db"):
            local_vector_db = FAISS.from_documents(
                documents=chunked_documents,
                embedding=model_provider.embedding_model()
            )
            local_vector_db.save_local("local_vector_db")

        # self.doc_retriever = FAISS.from_documents(
        #     documents=chunked_documents,
        #     embedding=model_provider.embedding_model()
        # ).as_retriever()

        self.doc_retriever = FAISS.load_local(folder_path="local_vector_db", embeddings=model_provider.embedding_model()).as_retriever()
        self.doc_retriever.search_kwargs["distance_metric"] = "cos"
        self.doc_retriever.search_kwargs["fetch_k"] = 100
        self.doc_retriever.search_kwargs["maximal_marginal_relevance"] = True
        self.doc_retriever.search_kwargs["k"] = 5

    def get_html_chunks(self):
        html_chunks = DirectoryLoader(
            'data/html',
            glob="**/*.html",
            loader_cls=TextLoader
        ).load()

        for html_chunk in html_chunks:
            html_chunk.metadata['page'] = find_filename(html_chunk.metadata['source'])

        return html_chunks

    def get_pdf_chunks(self):
        pdf_folder_path = "data/pdf"
        documents = []
        for file in os.listdir(pdf_folder_path):
            if file.endswith(".pdf"):
                pdf_path = os.path.join(pdf_folder_path, file)
                loader = PyPDFLoader(pdf_path)
                documents.extend(loader.load())

        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=10)
        pdf_chunks = text_splitter.split_documents(documents)

        return pdf_chunks

    # Search the provided query string and find the matching context
    def search(self, query: str):
        relevant_documents = self.doc_retriever.get_relevant_documents(query)
        documents = []
        for r in relevant_documents:
            documents.append(KnowledgeDB(r.page_content,
                                        '' if not r.metadata or 'source' not in r.metadata
                                        else r.metadata['source']))
        return documents

