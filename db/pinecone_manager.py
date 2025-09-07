"""
Enhanced Pinecone utilities for multi-organizational document storage
with file-level isolation + reset + listing helpers
"""
import os
import time
from typing import List, Dict, Any

from pinecone import Pinecone, ServerlessSpec
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document

from config import (
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    HF_EMBEDDING_MODEL,
)


class PineconeManager:
    """Manages Pinecone operations for multi-organizational setup"""

    def __init__(self):
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index_name = PINECONE_INDEX_NAME
        self._embeddings = None
        self.index = self.ensure_index()

    def get_embeddings(self) -> HuggingFaceEmbeddings:
        """Get embeddings using Hugging Face only"""
        if self._embeddings is None:
            print(f"⚡ Using Hugging Face embeddings: {HF_EMBEDDING_MODEL}")
            self._embeddings = HuggingFaceEmbeddings(model_name=HF_EMBEDDING_MODEL)
        return self._embeddings

    def ensure_index(self):
        """Ensure Pinecone index exists"""
        if self.index_name not in [i["name"] for i in self.pc.list_indexes()]:
            print(f"⏳ Creating index {self.index_name}...")
            self.pc.create_index(
                name=self.index_name,
                dimension=768,  # HuggingFace all-mpnet-base-v2 -> 768 dims
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            while not self.pc.describe_index(self.index_name).status["ready"]:
                time.sleep(2)
        return self.pc.Index(self.index_name)

    def reset_index(self) -> bool:
        """Delete and recreate index (⚠ destructive operation)"""
        try:
            if self.index_name in [i["name"] for i in self.pc.list_indexes()]:
                print(f"⚠ Resetting index {self.index_name}...")
                self.pc.delete_index(self.index_name)
                time.sleep(5)
            # Recreate
            self.index = self.ensure_index()
            return True
        except Exception as e:
            print(f"Error resetting index: {e}")
            return False

    def _build_id(
        self, company_id: str, doc_id: str, file_id: str, page: int, chunk_index: int
    ) -> str:
        return f"{company_id}::{doc_id}::{file_id}::p{page}::c{chunk_index}"

    def upsert_documents(
        self, company_id: str, doc_id: str, file_id: str, documents: List[Document]
    ) -> bool:
        """Upsert docs tied to a company + file (file-level isolation)"""
        try:
            embeddings = self.get_embeddings()
            vectors = []
            for i, doc in enumerate(documents):
                vec = embeddings.embed_query(doc.page_content)
                vector_id = self._build_id(
                    company_id, doc_id, file_id, doc.metadata.get("page", 0), i
                )
                vectors.append(
                    {
                        "id": vector_id,
                        "values": vec,
                        "metadata": {
                            "company_id": company_id,
                            "doc_id": doc_id,
                            "file_id": file_id,
                            "page": doc.metadata.get("page", 0),
                            "chunk_index": i,
                            "text": doc.page_content,
                            **{k: str(v) for k, v in doc.metadata.items()},
                        },
                    }
                )
            self.index.upsert(vectors=vectors, namespace="default")
            return True
        except Exception as e:
            print(f"Error upserting docs for {company_id}/{doc_id}/{file_id}: {e}")
            return False

    def query_company_documents(
        self, company_id: str, query: str, file_id: str = None, k: int = 5
    ) -> List[Dict[str, Any]]:
        """Query docs by company (optionally restricted to file)"""
        try:
            embeddings = self.get_embeddings()
            query_vec = embeddings.embed_query(query)

            filter_dict = {"company_id": {"$eq": company_id}}
            if file_id:
                filter_dict["file_id"] = {"$eq": file_id}

            results = self.index.query(
                vector=query_vec,
                top_k=k,
                include_metadata=True,
                namespace="default",
                filter=filter_dict,
            )
            return results.matches
        except Exception as e:
            print(f"Error querying company {company_id}: {e}")
            return []

    def delete_company_documents(
        self, company_id: str, doc_id: str = None, file_id: str = None
    ) -> bool:
        """Delete all docs for a company, or restrict to doc/file"""
        try:
            filter_dict = {"company_id": {"$eq": company_id}}
            if doc_id:
                filter_dict["doc_id"] = {"$eq": doc_id}
            if file_id:
                filter_dict["file_id"] = {"$eq": file_id}

            self.index.delete(namespace="default", filter=filter_dict)
            return True
        except Exception as e:
            print(f"Error deleting docs for {company_id}: {e}")
            return False

    def list_company_docs(self, company_id: str) -> Dict[str, List[str]]:
        """
        List all doc_ids and file_ids stored for a company
        Returns: {doc_id: [file_id1, file_id2, ...]}
        """
        try:
            stats = self.index.describe_index_stats()
            matches = {}
            namespace_stats = stats.get("namespaces", {}).get("default", {})
            if "vector_count" == 0 or "metadata_config" not in stats:
                return matches

            # NOTE: Pinecone does not expose direct metadata search listing.
            # Workaround: use filter queries per company.
            # Here we just return vector counts for the company.
            filter_dict = {"company_id": {"$eq": company_id}}
            results = self.index.query(
                vector=[0.0] * 768,  # dummy vector
                top_k=1,
                include_metadata=True,
                namespace="default",
                filter=filter_dict,
            )

            # Collect doc_ids and file_ids from metadata
            for match in results.matches:
                doc_id = match.metadata.get("doc_id")
                file_id = match.metadata.get("file_id")
                if doc_id:
                    matches.setdefault(doc_id, [])
                    if file_id and file_id not in matches[doc_id]:
                        matches[doc_id].append(file_id)
            return matches
        except Exception as e:
            print(f"Error listing docs for company {company_id}: {e}")
            return {}

    def get_company_stats(self, company_id: str) -> Dict[str, Any]:
        try:
            stats = self.index.describe_index_stats()
            total = stats.get("namespaces", {}).get("default", {}).get("vector_count", 0)
            return {
                "company_id": company_id,
                "index_name": self.index_name,
                "total_vectors": total,
                "exists": True,
            }
        except Exception as e:
            print(f"Error fetching stats: {e}")
            return {
                "company_id": company_id,
                "index_name": self.index_name,
                "total_vectors": 0,
                "exists": False,
                "error": str(e),
            }


# Global instance
pinecone_manager = PineconeManager()
