from typing import List

import config_provider
import requests
from vector_db import KnowledgeDB
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.schema import Document


class GenAIModels:

    def embedding_model(self):
        raise Exception("Not implemented")

    def generate_embeddings(self, query: str):
        raise Exception("Not implemented")

    def ask(self, query: str, kb: List[KnowledgeDB]):
        raise Exception("Not implemented")

    @staticmethod
    def get_instance():
        return LLM()


class LLM(GenAIModels):
    def embedding_model(self):
        AzureOpenAIEmbeddings(
            openai_api_key=config_provider.OPENAI_API_KEY,
            model=config_provider.EMBEDDING_MODEL,
            api_version="2023-05-15",
            # azure_endpoint=config_provider.AZURE_ENDPOINT,
            # http_client=self.client,
        )

      