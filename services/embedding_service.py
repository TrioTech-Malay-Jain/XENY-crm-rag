"""
Embedding service for document processing and vector storage
"""
import asyncio
from typing import List, Optional
from datetime import datetime

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from config import CHUNK_SIZE, CHUNK_OVERLAP, LLM_MODEL, get_google_api_keys
from db.chroma_manager import chroma_manager
from services.file_service import file_service
from models.schemas import BuildStatus, BuildStatusEnum


class EmbeddingService:
    """Service for processing documents and creating embeddings"""
    
    def __init__(self):
        self.api_keys = get_google_api_keys()
        self.current_key_index = 0
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self._rag_chains = {}  # Company-specific RAG chains
        self.build_statuses = {}  # Company-specific build statuses
    
    def get_current_llm(self) -> ChatGoogleGenerativeAI:
        """Get LLM with current API key"""
        if not self.api_keys:
            raise ValueError("No Google API keys available")
        
        api_key = self.api_keys[self.current_key_index]
        return ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            google_api_key=api_key
        )
    
    def rotate_api_key(self):
        """Rotate to next available API key"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        chroma_manager.rotate_api_key()  # Also rotate chroma manager key
    
    async def process_company_documents(self, company_id: str) -> BuildStatus:
        """Process all documents for a company and build vector store"""
        
        # Initialize build status
        self.build_statuses[company_id] = BuildStatus(
            status=BuildStatusEnum.BUILDING,
            message="Starting document processing...",
            company_id=company_id,
            timestamp=datetime.now(),
            progress=0.0
        )
        
        try:
            # Load documents
            self.build_statuses[company_id].message = "Loading documents..."
            self.build_statuses[company_id].progress = 0.1
            
            documents = file_service.load_documents_from_company(company_id)
            
            if not documents:
                self.build_statuses[company_id] = BuildStatus(
                    status=BuildStatusEnum.ERROR,
                    message="No documents found for processing",
                    company_id=company_id,
                    timestamp=datetime.now()
                )
                return self.build_statuses[company_id]
            
            # Split documents
            self.build_statuses[company_id].message = f"Splitting {len(documents)} documents into chunks..."
            self.build_statuses[company_id].progress = 0.3
            
            splits = self.text_splitter.split_documents(documents)
            
            # Create/update vector store
            self.build_statuses[company_id].message = f"Creating embeddings for {len(splits)} chunks..."
            self.build_statuses[company_id].progress = 0.6
            
            # Check if collection exists
            existing_collections = chroma_manager.list_company_collections()
            
            if company_id in existing_collections:
                # Delete existing collection
                chroma_manager.delete_company_collection(company_id)
            
            # Create new collection
            success = chroma_manager.create_company_collection(company_id, splits)
            
            if not success:
                self.build_statuses[company_id] = BuildStatus(
                    status=BuildStatusEnum.ERROR,
                    message="Failed to create vector store",
                    company_id=company_id,
                    timestamp=datetime.now()
                )
                return self.build_statuses[company_id]
            
            # Initialize RAG chain
            self.build_statuses[company_id].message = "Initializing RAG pipeline..."
            self.build_statuses[company_id].progress = 0.9
            
            rag_chain = await self._create_rag_chain(company_id)
            if rag_chain:
                self._rag_chains[company_id] = rag_chain
            
            # Complete
            self.build_statuses[company_id] = BuildStatus(
                status=BuildStatusEnum.COMPLETED,
                message=f"Successfully processed {len(documents)} documents into {len(splits)} chunks",
                company_id=company_id,
                timestamp=datetime.now(),
                progress=1.0
            )
            
            return self.build_statuses[company_id]
            
        except Exception as e:
            self.build_statuses[company_id] = BuildStatus(
                status=BuildStatusEnum.ERROR,
                message=f"Processing failed: {str(e)}",
                company_id=company_id,
                timestamp=datetime.now()
            )
            
            # Try rotating API key for next attempt
            self.rotate_api_key()
            
            return self.build_statuses[company_id]
    
    async def _create_rag_chain(self, company_id: str):
        """Create RAG chain for a specific company"""
        try:
            llm = self.get_current_llm()
            vectorstore = chroma_manager.get_company_vectorstore(company_id)
            retriever = vectorstore.as_retriever()
            
            # Context prompt
            contextualize_q_prompt = ChatPromptTemplate.from_messages([
                ("system", "Given a chat history and the latest user question which might reference context in the chat history, formulate a standalone question which can be understood without the chat history."),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}")
            ])
            
            history_aware_retriever = create_history_aware_retriever(
                llm, retriever, contextualize_q_prompt
            )
            
            # System prompt
            system_prompt = f"""You are an advanced AI assistant for company {company_id}. Always mention the company {company_id} in your responses.
Your role is to answer user questions using the knowledge base context.

Guidelines:
1. Use only the knowledge base to generate answers. Do not mention or describe the documents or context explicitly.
2. Provide responses that are concise yet slightly expanded for clarity. 
3. Adapt answer style dynamically:
   - Use bullet points for lists, steps, or features.
   - Use short paragraphs for explanations or reasoning.
4. If the requested information is not available in the knowledge base, respond with:
   "This information is currently not available. For more details, please contact [insert company contact info if available]."
5. Maintain a friendly but professional tone.
6. Always tailor answers to company {company_id}, explicitly mentioning it when relevant.
7. Avoid filler phrases such as "the uploaded text says" or "the context provides."

Context:
{{context}}"""
            
            qa_prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}")
            ])
            
            question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
            rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
            
            return rag_chain
            
        except Exception as e:
            print(f"Error creating RAG chain for company {company_id}: {e}")
            self.rotate_api_key()
            return None
    
    async def query_company(self, company_id: str, query: str, chat_history: List[dict] = None) -> dict:
        """Query documents for a specific company"""
        
        # Check if RAG chain exists
        if company_id not in self._rag_chains:
            # Try to create RAG chain
            rag_chain = await self._create_rag_chain(company_id)
            if not rag_chain:
                raise ValueError(f"RAG system not available for company {company_id}")
            self._rag_chains[company_id] = rag_chain
        
        # Convert chat history to LangChain format
        chat_history_for_chain = []
        if chat_history:
            for msg in chat_history:
                content = msg.get('message', '')
                if msg.get('sender') == 'user':
                    chat_history_for_chain.append(HumanMessage(content=content))
                else:
                    chat_history_for_chain.append(AIMessage(content=content))
        
        try:
            # Query the RAG chain
            response = self._rag_chains[company_id].invoke({
                "input": query,
                "chat_history": chat_history_for_chain
            })
            
            # Extract sources
            sources = []
            if 'context' in response:
                for doc in response['context']:
                    if 'source' in doc.metadata:
                        sources.append(doc.metadata['source'])
            
            return {
                "response": response.get("answer", "I couldn't find an answer to that."),
                "sources": list(set(sources))  # Remove duplicates
            }
            
        except Exception as e:
            # Try rotating API key and retry once
            self.rotate_api_key()
            
            # Remove the failed RAG chain
            if company_id in self._rag_chains:
                del self._rag_chains[company_id]
            
            raise Exception(f"Query failed: {str(e)}")
    
    async def query_specific_file(self, company_id: str, file_id: str, query: str, chat_history: List[dict] = None) -> dict:
        """Query a specific file for a company"""
        
        from services.file_service import file_service
        from db.chroma_manager import chroma_manager
        
        # Get the file info
        file_info = file_service.get_file_info(company_id, file_id)
        if not file_info:
            raise ValueError(f"File {file_id} not found for company {company_id}")
        
        try:
            # Check if file-specific collection exists, if not create it
            file_vectorstore = chroma_manager.get_file_vectorstore(company_id, file_id)
            
            # Check if collection has documents
            try:
                collection = file_vectorstore._collection
                doc_count = collection.count()
                
                if doc_count == 0:
                    # Collection is empty, need to populate it
                    file_path = file_service.get_file_path(company_id, file_info.filename)
                    documents = file_service.load_document(file_path)
                    
                    if documents:
                        # Create the file collection with documents
                        success = chroma_manager.create_file_collection(company_id, file_id, documents)
                        if not success:
                            raise ValueError("Failed to create file collection")
                        
                        # Get the vectorstore again after creation
                        file_vectorstore = chroma_manager.get_file_vectorstore(company_id, file_id)
                    else:
                        raise ValueError(f"Could not load document: {file_path}")
                        
            except Exception as e:
                # If collection doesn't exist, create it
                file_path = file_service.get_file_path(company_id, file_info.filename)
                documents = file_service.load_document(file_path)
                
                if documents:
                    success = chroma_manager.create_file_collection(company_id, file_id, documents)
                    if not success:
                        raise ValueError("Failed to create file collection")
                    
                    file_vectorstore = chroma_manager.get_file_vectorstore(company_id, file_id)
                else:
                    raise ValueError(f"Could not load document: {file_path}")
            
            # Create a RAG chain for this file
            rag_chain = self._create_single_file_rag_chain(file_vectorstore, company_id)
            
            # Convert chat history to LangChain format
            chat_history_for_chain = []
            if chat_history:
                for msg in chat_history:
                    content = msg.get('message', '')
                    if msg.get('sender') == 'user':
                        chat_history_for_chain.append(HumanMessage(content=content))
                    else:
                        chat_history_for_chain.append(AIMessage(content=content))
            
            # Query the RAG chain
            response = rag_chain.invoke({
                "input": query,
                "chat_history": chat_history_for_chain
            })
            
            # Extract sources
            sources = [f"{company_id}/{file_info.filename}"]
            
            return {
                "response": response.get("answer", "I couldn't find an answer to that in the specified document."),
                "sources": sources,
                "file_id": file_id,
                "filename": file_info.original_filename or file_info.filename
            }
                
        except Exception as e:
            # Try rotating API key and retry once
            self.rotate_api_key()
            raise Exception(f"File-specific query failed: {str(e)}")
    
    async def create_file_specific_collection(self, company_id: str, file_id: str):
        """Create a file-specific collection for targeted querying"""
        try:
            from services.file_service import file_service
            from db.chroma_manager import chroma_manager
            
            # Get file info and load document
            file_info = file_service.get_file_info(company_id, file_id)
            if not file_info:
                print(f"File {file_id} not found for company {company_id}")
                return
            
            file_path = file_service.get_file_path(company_id, file_info.filename)
            documents = file_service.load_document(file_path)
            
            if documents:
                # Create file-specific collection
                success = chroma_manager.create_file_collection(company_id, file_id, documents)
                if success:
                    print(f"✅ Created file collection for {company_id}/{file_info.filename}")
                else:
                    print(f"❌ Failed to create file collection for {company_id}/{file_info.filename}")
            else:
                print(f"❌ No documents loaded from {file_path}")
                
        except Exception as e:
            print(f"Error creating file collection for {company_id}/{file_id}: {e}")
    
    def _create_single_file_rag_chain(self, vectorstore, company_id: str = None):
        """Create a RAG chain for a single file"""
        from langchain.chains import create_history_aware_retriever, create_retrieval_chain
        from langchain.chains.combine_documents import create_stuff_documents_chain
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Get current API key
        current_api_key = self.api_keys[self.current_key_index] if self.api_keys else None
        if not current_api_key:
            raise ValueError("No Google API key available")
        
        # Create LLM
        llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            google_api_key=current_api_key,
            temperature=0.3
        )
        
        # Create retriever
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        
        # History-aware retriever prompt
        contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""
        
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )
        
        # QA prompt with company context
        company_context = f" for company {company_id}" if company_id else ""
        qa_system_prompt = f"""You are an AI assistant{company_context}. \
Use the following pieces of retrieved context to answer the question. \
If you don't know the answer, just say that you don't know. \
Keep the answer concise but comprehensive.{' Always mention the company ' + company_id + ' when relevant.' if company_id else ''}

{{context}}"""
        
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
        
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        
        return rag_chain
    
    def get_build_status(self, company_id: str) -> BuildStatus:
        """Get build status for a company"""
        return self.build_statuses.get(company_id, BuildStatus(
            status=BuildStatusEnum.IDLE,
            message="No build process started",
            company_id=company_id,
            timestamp=datetime.now()
        ))
    
    def get_all_build_statuses(self) -> dict:
        """Get all build statuses"""
        return self.build_statuses
    
    async def add_document_to_company(self, company_id: str, file_id: str) -> bool:
        """Add a single new document to existing company vector store"""
        try:
            # Load the specific document
            file_info = file_service.get_file_info(company_id, file_id)
            if not file_info:
                return False
            
            # Load document content
            company_dir = file_service.get_company_directory(company_id)
            file_path = company_dir / file_info.filename
            
            if not file_path.exists():
                return False
            
            docs = file_service._load_document_by_type(file_path, file_info.extension)
            
            # Add metadata
            for doc in docs:
                doc.metadata.update({
                    'file_id': file_id,
                    'company_id': company_id,
                    'original_filename': file_info.original_filename,
                    'file_type': file_info.extension.replace('.', ''),
                    'created_at': file_info.created_at.isoformat()
                })
            
            # Split documents
            splits = self.text_splitter.split_documents(docs)
            
            # Add to vector store
            success = chroma_manager.add_documents_to_company(company_id, splits)
            
            if success and company_id in self._rag_chains:
                # Refresh RAG chain
                del self._rag_chains[company_id]
            
            return success
            
        except Exception as e:
            print(f"Error adding document {file_id} to company {company_id}: {e}")
            return False


# Global instance
embedding_service = EmbeddingService()
