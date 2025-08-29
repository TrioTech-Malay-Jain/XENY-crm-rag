"""
Chroma DB utilities for multi-organizational document storage
"""
import os
import shutil
from typing import List, Optional, Dict, Any
from pathlib import Path

from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.schema import Document

from config import CHROMA_DB_PATH, COLLECTION_PREFIX, EMBEDDING_MODEL, get_google_api_keys


class ChromaManager:
    """Manages Chroma DB operations for multi-organizational setup"""
    
    def __init__(self):
        self.db_path = CHROMA_DB_PATH
        self.api_keys = get_google_api_keys()
        self.current_key_index = 0
        self._embeddings = None
        
        # Ensure DB directory exists
        os.makedirs(self.db_path, exist_ok=True)
    
    def get_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """Get embeddings function with API key rotation"""
        if not self.api_keys:
            raise ValueError("No Google API keys available")
        
        if self._embeddings is None:
            api_key = self.api_keys[self.current_key_index]
            self._embeddings = GoogleGenerativeAIEmbeddings(
                model=EMBEDDING_MODEL,
                google_api_key=api_key
            )
        
        return self._embeddings
    
    def rotate_api_key(self):
        """Rotate to next API key"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self._embeddings = None  # Reset to use new key
    
    def sanitize_company_name(self, company_id: str) -> str:
        """Sanitize company name to be valid for ChromaDB collection name"""
        # Replace spaces with underscores and remove invalid characters
        sanitized = company_id.replace(" ", "_").replace("-", "_")
        # Keep only alphanumeric, dots, and underscores
        sanitized = "".join(c for c in sanitized if c.isalnum() or c in "._")
        # Ensure it starts and ends with alphanumeric
        sanitized = sanitized.strip("._")
        # Ensure minimum length
        if len(sanitized) < 3:
            sanitized = f"company_{sanitized}"
        return sanitized
    
    def get_collection_name(self, company_id: str) -> str:
        """Generate collection name for company"""
        sanitized_id = self.sanitize_company_name(company_id)
        return f"{COLLECTION_PREFIX}{sanitized_id}"
    
    def get_file_collection_name(self, company_id: str, file_id: str) -> str:
        """Generate collection name for a specific file within a company"""
        sanitized_company = self.sanitize_company_name(company_id)
        # Use first 8 characters of file_id for collection name
        file_short_id = file_id.replace("-", "")[:8]
        return f"{COLLECTION_PREFIX}{sanitized_company}_file_{file_short_id}"
    
    def get_company_vectorstore(self, company_id: str) -> Chroma:
        """Get or create vector store for a specific company"""
        collection_name = self.get_collection_name(company_id)
        embeddings = self.get_embeddings()
        
        return Chroma(
            collection_name=collection_name,
            persist_directory=str(self.db_path),
            embedding_function=embeddings
        )
    
    def get_file_vectorstore(self, company_id: str, file_id: str) -> Chroma:
        """Get or create vector store for a specific file within a company"""
        collection_name = self.get_file_collection_name(company_id, file_id)
        embeddings = self.get_embeddings()
        
        return Chroma(
            collection_name=collection_name,
            persist_directory=str(self.db_path),
            embedding_function=embeddings
        )
    
    def create_company_collection(self, company_id: str, documents: List[Document]) -> bool:
        """Create a new collection for a company with documents"""
        try:
            collection_name = self.get_collection_name(company_id)
            embeddings = self.get_embeddings()
            
            # Create vector store with documents
            vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=embeddings,
                collection_name=collection_name,
                persist_directory=str(self.db_path)
            )
            
            return True
            
        except Exception as e:
            print(f"Error creating collection for company {company_id}: {e}")
            # Try rotating API key
            self.rotate_api_key()
            return False
    
    def create_file_collection(self, company_id: str, file_id: str, documents: List[Document]) -> bool:
        """Create a new collection for a specific file with documents"""
        try:
            collection_name = self.get_file_collection_name(company_id, file_id)
            embeddings = self.get_embeddings()
            
            # Create vector store with documents
            vectorstore = Chroma.from_documents(
                documents,
                embeddings,
                collection_name=collection_name,
                persist_directory=str(self.db_path)
            )
            
            return True
            
        except Exception as e:
            print(f"Error creating file collection for {company_id}/{file_id}: {e}")
            # Try rotating API key
            self.rotate_api_key()
            return False
    
    def add_documents_to_company(self, company_id: str, documents: List[Document]) -> bool:
        """Add documents to existing company collection"""
        try:
            vectorstore = self.get_company_vectorstore(company_id)
            vectorstore.add_documents(documents)
            return True
            
        except Exception as e:
            print(f"Error adding documents to company {company_id}: {e}")
            self.rotate_api_key()
            return False
    
    def query_company_documents(self, company_id: str, query: str, k: int = 5) -> List[Document]:
        """Query documents for a specific company"""
        try:
            vectorstore = self.get_company_vectorstore(company_id)
            retriever = vectorstore.as_retriever(search_kwargs={"k": k})
            docs = retriever.get_relevant_documents(query)
            return docs
            
        except Exception as e:
            print(f"Error querying company {company_id}: {e}")
            self.rotate_api_key()
            return []
    
    def delete_company_collection(self, company_id: str) -> bool:
        """Delete entire collection for a company"""
        try:
            collection_name = self.get_collection_name(company_id)
            
            # Get the client and delete collection
            embeddings = self.get_embeddings()
            vectorstore = Chroma(
                collection_name=collection_name,
                persist_directory=str(self.db_path),
                embedding_function=embeddings
            )
            
            # Delete the collection
            vectorstore.delete_collection()
            return True
            
        except Exception as e:
            print(f"Error deleting collection for company {company_id}: {e}")
            return False
    
    def delete_documents_from_company(self, company_id: str, document_ids: List[str]) -> bool:
        """Delete specific documents from company collection"""
        try:
            vectorstore = self.get_company_vectorstore(company_id)
            vectorstore.delete(ids=document_ids)
            return True
            
        except Exception as e:
            print(f"Error deleting documents from company {company_id}: {e}")
            return False
    
    def list_company_collections(self) -> List[str]:
        """List all company collections"""
        try:
            embeddings = self.get_embeddings()
            # Create a temporary vectorstore to access client
            temp_vectorstore = Chroma(
                persist_directory=str(self.db_path),
                embedding_function=embeddings
            )
            
            # Get all collections
            collections = temp_vectorstore._client.list_collections()
            
            # Filter for company collections
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
        """Get statistics for a company collection"""
        try:
            collection_name = self.get_collection_name(company_id)
            embeddings = self.get_embeddings()
            
            vectorstore = Chroma(
                collection_name=collection_name,
                persist_directory=str(self.db_path),
                embedding_function=embeddings
            )
            
            # Get collection info
            collection = vectorstore._collection
            count = collection.count()
            
            return {
                "company_id": company_id,
                "collection_name": collection_name,
                "document_count": count,
                "exists": True
            }
            
        except Exception as e:
            print(f"Error getting stats for company {company_id}: {e}")
            return {
                "company_id": company_id,
                "collection_name": self.get_collection_name(company_id),
                "document_count": 0,
                "exists": False,
                "error": str(e)
            }
    
    def reset_all_collections(self) -> bool:
        """Reset all collections (for testing/development)"""
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
