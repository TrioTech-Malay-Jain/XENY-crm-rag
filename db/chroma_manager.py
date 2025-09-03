"""
Chroma DB utilities for multi-organizational document storage
"""
import os
import shutil
from typing import List, Dict, Any

from langchain_chroma import Chroma
from langchain_openai import AzureOpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document

from config import (
    CHROMA_DB_PATH,
    COLLECTION_PREFIX,
    openai_api_key,
    openai_api_version,
    openai_deployment,
    openai_endpoint,
    openai_embedding_deployment,
    USE_HF_EMBEDDINGS,
    HF_EMBEDDING_MODEL,
)


class ChromaManager:
    """Manages Chroma DB operations for multi-organizational setup"""

    def __init__(self):
        self.db_path = CHROMA_DB_PATH
        self._embeddings = None

        # Ensure DB directory exists
        os.makedirs(self.db_path, exist_ok=True)

    def get_embeddings(self) -> HuggingFaceEmbeddings | AzureOpenAIEmbeddings:
        """Get embeddings using Hugging Face or Azure OpenAI"""
        if self._embeddings is None:
            if USE_HF_EMBEDDINGS:
                print("⚡ Using Hugging Face embeddings")
                self._embeddings = HuggingFaceEmbeddings(model_name=HF_EMBEDDING_MODEL)
            else:
                print("⚡ Using Azure OpenAI embeddings")
                self._embeddings = AzureOpenAIEmbeddings(
                    deployment=openai_embedding_deployment,
                    openai_api_key=openai_api_key,
                    openai_api_version=openai_api_version,
                    azure_endpoint=openai_endpoint,
                )
        return self._embeddings

    def sanitize_company_name(self, company_id: str) -> str:
        """Sanitize company name to be valid for ChromaDB collection name"""
        sanitized = company_id.replace(" ", "_").replace("-", "_")
        sanitized = "".join(c for c in sanitized if c.isalnum() or c in "._")
        sanitized = sanitized.strip("._")
        if len(sanitized) < 3:
            sanitized = f"company_{sanitized}"
        return sanitized

    def get_collection_name(self, company_id: str) -> str:
        sanitized_id = self.sanitize_company_name(company_id)
        return f"{COLLECTION_PREFIX}{sanitized_id}"

    def get_file_collection_name(self, company_id: str, file_id: str) -> str:
        sanitized_company = self.sanitize_company_name(company_id)
        file_short_id = file_id.replace("-", "")[:8]
        return f"{COLLECTION_PREFIX}{sanitized_company}_file_{file_short_id}"

    def get_company_vectorstore(self, company_id: str) -> Chroma:
        collection_name = self.get_collection_name(company_id)
        embeddings = self.get_embeddings()
        return Chroma(
            collection_name=collection_name,
            persist_directory=str(self.db_path),
            embedding_function=embeddings,
        )

    def get_file_vectorstore(self, company_id: str, file_id: str) -> Chroma:
        collection_name = self.get_file_collection_name(company_id, file_id)
        embeddings = self.get_embeddings()
        return Chroma(
            collection_name=collection_name,
            persist_directory=str(self.db_path),
            embedding_function=embeddings,
        )

    def create_company_collection(self, company_id: str, documents: List[Document]) -> bool:
        try:
            collection_name = self.get_collection_name(company_id)
            embeddings = self.get_embeddings()
            Chroma.from_documents(
                documents=documents,
                embedding=embeddings,
                collection_name=collection_name,
                persist_directory=str(self.db_path),
            )
            return True
        except Exception as e:
            print(f"Error creating collection for company {company_id}: {e}")
            return False

    def create_file_collection(self, company_id: str, file_id: str, documents: List[Document]) -> bool:
        try:
            collection_name = self.get_file_collection_name(company_id, file_id)
            embeddings = self.get_embeddings()
            Chroma.from_documents(
                documents,
                embeddings,
                collection_name=collection_name,
                persist_directory=str(self.db_path),
            )
            return True
        except Exception as e:
            print(f"Error creating file collection for {company_id}/{file_id}: {e}")
            return False

    def add_documents_to_company(self, company_id: str, documents: List[Document]) -> bool:
        try:
            vectorstore = self.get_company_vectorstore(company_id)
            vectorstore.add_documents(documents)
            return True
        except Exception as e:
            print(f"Error adding documents to company {company_id}: {e}")
            return False

    def query_company_documents(self, company_id: str, query: str, k: int = 5) -> List[Document]:
        try:
            vectorstore = self.get_company_vectorstore(company_id)
            retriever = vectorstore.as_retriever(search_kwargs={"k": k})
            docs = retriever.get_relevant_documents(query)
            return docs
        except Exception as e:
            print(f"Error querying company {company_id}: {e}")
            return []

    def delete_company_collection(self, company_id: str) -> bool:
        try:
            collection_name = self.get_collection_name(company_id)
            embeddings = self.get_embeddings()
            vectorstore = Chroma(
                collection_name=collection_name,
                persist_directory=str(self.db_path),
                embedding_function=embeddings,
            )
            vectorstore.delete_collection()
            return True
        except Exception as e:
            print(f"Error deleting collection for company {company_id}: {e}")
            return False

    def delete_documents_from_company(self, company_id: str, document_ids: List[str]) -> bool:
        try:
            vectorstore = self.get_company_vectorstore(company_id)
            vectorstore.delete(ids=document_ids)
            return True
        except Exception as e:
            print(f"Error deleting documents from company {company_id}: {e}")
            return False

    def list_company_collections(self) -> List[str]:
        try:
            embeddings = self.get_embeddings()
            temp_vectorstore = Chroma(
                persist_directory=str(self.db_path),
                embedding_function=embeddings,
            )
            collections = temp_vectorstore._client.list_collections()
            company_collections = [
                col.name.replace(COLLECTION_PREFIX, "")
                for col in collections
                if col.name.startswith(COLLECTION_PREFIX)
            ]
            return company_collections
        except Exception as e:
            print(f"Error listing collections: {e}")
            return []

    def get_collection_stats(self, company_id: str) -> Dict[str, Any]:
        try:
            collection_name = self.get_collection_name(company_id)
            embeddings = self.get_embeddings()
            vectorstore = Chroma(
                collection_name=collection_name,
                persist_directory=str(self.db_path),
                embedding_function=embeddings,
            )
            collection = vectorstore._collection
            count = collection.count()
            return {
                "company_id": company_id,
                "collection_name": collection_name,
                "document_count": count,
                "exists": True,
            }
        except Exception as e:
            print(f"Error getting stats for company {company_id}: {e}")
            return {
                "company_id": company_id,
                "collection_name": self.get_collection_name(company_id),
                "document_count": 0,
                "exists": False,
                "error": str(e),
            }

    def reset_all_collections(self) -> bool:
        try:
            if os.path.exists(self.db_path):
                shutil.rmtree(self.db_path)
                os.makedirs(self.db_path, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error resetting collections: {e}")
            return False


# Global instance
chroma_manager = ChromaManager()
