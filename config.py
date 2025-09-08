"""
Configuration settings for multi-organizational RAG system
"""
import os
from typing import List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
CHROMA_DB_PATH = BASE_DIR / "chroma_db"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# File handling
ALLOWED_EXTENSIONS = {".txt", ".json", ".pdf", ".docx"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Company settings
DEFAULT_COMPANY_ID = "default"

# Chroma DB settings
COLLECTION_PREFIX = "company_"

# API settings
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# # Google API settings
# def get_google_api_keys() -> List[str]:
#     """Load all available Google API keys from environment"""
#     api_keys = []
#     i = 1
#     while True:
#         key = os.getenv(f"GOOGLE_API_KEY_{i}")
#         if key:
#             api_keys.append(key)
#             i += 1
#         else:
#             break
    
#     # Fallback to single key
#     if not api_keys:
#         single_key = os.getenv("GOOGLE_API_KEY")
#         if single_key:
#             api_keys.append(single_key)
    
#     # Debug print
#     print(f"🔑 Found {len(api_keys)} Google API keys")
    
#     return api_keys

openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")

# Separate deployment for embeddings
openai_embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")

# Pinecone settings
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY_RAG")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME_RAG", "xeny-crm-rag")
PINECONE_DIMENSION = int(os.getenv("PINECONE_DIMENSION_RAG", "768"))
PINECONE_METRIC = os.getenv("PINECONE_METRIC_RAG", "cosine")
PINECONE_CLOUD = os.getenv("PINECONE_CLOUD_RAG", "aws")
PINECONE_REGION = os.getenv("PINECONE_REGION_RAG", "us-east-1")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE_RAG", "default")

# Embedding provider settings
USE_HF_EMBEDDINGS = os.getenv("USE_HF_EMBEDDINGS", "false").lower() == "true"
HF_EMBEDDING_MODEL = os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")

# Embedding model settings
EMBEDDING_MODEL = "models/embedding-001"
LLM_MODEL = "gemini-1.5-flash"

# Text splitting settings
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200

# Server settings
HOST = "0.0.0.0"
PORT = 8000
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
