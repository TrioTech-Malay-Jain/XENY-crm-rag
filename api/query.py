"""
Query and chat API endpoints
"""
import uuid
from typing import Dict, List
from datetime import datetime
from fastapi import APIRouter, HTTPException

from models.schemas import QueryRequest, QueryResponse, ChatMessage, FileChatRequest
from services.embedding_service import embedding_service
from services.file_service import file_service

router = APIRouter(prefix="/query", tags=["query"])

# In-memory chat sessions (in production, use Redis or database)
chat_sessions: Dict[str, List[ChatMessage]] = {}


@router.post("/", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query documents for a specific company"""
    
    try:
        # Query the embedding service
        result = await embedding_service.query_company(
            company_id=request.company_id,
            query=request.query,
            chat_history=request.history or []
        )
        
        session_id = request.session_id or str(uuid.uuid4())
        
        return QueryResponse(
            response=result["response"],
            company_id=request.company_id,
            session_id=session_id,
            timestamp=datetime.now(),
            sources=result.get("sources", [])
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/chat", response_model=QueryResponse)
async def chat_with_documents(request: QueryRequest):
    """Chat with documents for a specific company"""
    
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get existing chat history
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
        
        # Add user message to session
        user_message = ChatMessage(
            message=request.query,
            sender="user",
            timestamp=datetime.now(),
            session_id=session_id,
            company_id=request.company_id
        )
        chat_sessions[session_id].append(user_message)
        
        # Query the embedding service
        result = await embedding_service.query_company(
            company_id=request.company_id,
            query=request.query,
            chat_history=request.history or []
        )
        
        # Add bot response to session
        bot_message = ChatMessage(
            message=result["response"],
            sender="bot",
            timestamp=datetime.now(),
            session_id=session_id,
            company_id=request.company_id
        )
        chat_sessions[session_id].append(bot_message)
        
        return QueryResponse(
            response=result["response"],
            company_id=request.company_id,
            session_id=session_id,
            timestamp=datetime.now(),
            sources=result.get("sources", [])
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.post("/file-chat", response_model=QueryResponse)
async def chat_with_file(request: FileChatRequest):
    """Chat with a specific file (company_id is automatically determined from file_id)"""
    
    try:
        # Find the company_id from the file_id
        company_id = file_service.find_company_by_file_id(request.file_id)
        if not company_id:
            raise HTTPException(status_code=404, detail=f"File {request.file_id} not found")
        
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get existing chat history
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
        
        # Add user message to session
        user_message = ChatMessage(
            message=request.query,
            sender="user",
            timestamp=datetime.now(),
            session_id=session_id,
            company_id=company_id
        )
        chat_sessions[session_id].append(user_message)
        
        # Query the specific file
        result = await embedding_service.query_specific_file(
            company_id=company_id,
            file_id=request.file_id,
            query=request.query,
            chat_history=request.history or []
        )
        
        # Add bot response to session
        bot_message = ChatMessage(
            message=result["response"],
            sender="bot",
            timestamp=datetime.now(),
            session_id=session_id,
            company_id=company_id
        )
        chat_sessions[session_id].append(bot_message)
        
        # Prepare response
        response_data = {
            "response": result["response"],
            "company_id": company_id,
            "session_id": session_id,
            "timestamp": datetime.now(),
            "sources": result.get("sources", [])
        }
        
        # Add file information
        if "file_id" in result:
            response_data["file_info"] = {
                "file_id": result["file_id"],
                "filename": result.get("filename", "Unknown")
            }
        
        return QueryResponse(**response_data)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File chat failed: {str(e)}")


@router.get("/chat/{session_id}", response_model=List[ChatMessage])
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    
    return chat_sessions.get(session_id, [])


@router.delete("/chat/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear chat history for a session"""
    
    if session_id in chat_sessions:
        chat_sessions[session_id] = []
    
    return {"message": "Chat history cleared"}


@router.get("/file-info/{file_id}")
async def get_file_info_by_id(file_id: str):
    """Get file information by file_id (automatically finds company)"""
    
    try:
        # Find the company_id from the file_id
        company_id = file_service.find_company_by_file_id(file_id)
        if not company_id:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        
        # Get file info
        file_info = file_service.get_file_info(company_id, file_id)
        if not file_info:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        
        return {
            "file_id": file_id,
            "company_id": company_id,
            "filename": file_info.filename,
            "original_filename": file_info.original_filename,
            "size": file_info.size,
            "extension": file_info.extension,
            "created_at": file_info.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file info: {str(e)}")


@router.get("/sessions")
async def list_chat_sessions():
    """List all active chat sessions"""
    
    sessions = []
    for session_id, messages in chat_sessions.items():
        if messages:
            last_message = messages[-1]
            sessions.append({
                "session_id": session_id,
                "company_id": last_message.company_id,
                "last_activity": last_message.timestamp,
                "message_count": len(messages)
            })
    
    return sessions
