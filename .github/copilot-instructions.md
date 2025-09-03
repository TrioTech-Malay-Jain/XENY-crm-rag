# AI Coding Assistant Instructions for CCD-AI Multi-Organization RAG System

## Project Overview
This is a production-ready Retrieval Augmented Generation (RAG) system supporting multiple organizations with complete data isolation. Built with FastAPI, LangChain, ChromaDB, and Google Generative AI.

## Architecture & Data Flow

### Core Components
- **`run.py`**: Main FastAPI application with lifespan management
- **`api/`**: REST endpoints (`files.py`, `query.py`) for file operations and queries
- **`services/`**: Business logic (`embedding_service.py`, `file_service.py`)
- **`db/chroma_manager.py`**: ChromaDB operations with company isolation
- **`models/schemas.py`**: Pydantic data models
- **`config.py`**: Centralized configuration management

### Data Isolation Pattern
Each company gets:
- Separate directory: `knowledge_base/{company_id}/`
- Dedicated ChromaDB collection: `company_{sanitized_company_id}`
- File metadata in `metadata.json` per company directory
- Independent RAG pipelines and chat sessions

### File Processing Flow
```
File Upload → Save to knowledge_base/{company_id}/ → Background Vector DB Build → Query/Chat Ready
```

## Critical Developer Workflows

### Starting the Application
```bash
# Always use run.py (not main.py which is archived)
python run.py
# Server starts on http://localhost:8000 with auto-reload in debug mode
```

### File Upload & Processing
- Files are saved as `{uuid}{extension}` (e.g., `a1b2c3d4-e5f6.txt`)
- Original filename stored in metadata
- Automatic background vector DB building triggers on upload
- Supports: `.txt`, `.pdf`, `.docx`, `.json`

### API Key Management
```python
# Multiple keys for rate limiting
GOOGLE_API_KEY_1="key1"
GOOGLE_API_KEY_2="key2"
# System rotates keys automatically on quota/rate limit errors
```

## Project-Specific Patterns & Conventions

### Company Isolation Implementation
```python
# Always include company_id in operations
@router.post("/upload")
async def upload_file(company_id: str = Form(...), file: UploadFile = File(...)):
    file_info = await file_service.save_uploaded_file(company_id, file)
    # Background tasks for vector DB building
    background_tasks.add_task(embedding_service.process_company_documents, company_id)
```

### File Metadata Management
```python
# Files stored as UUIDs, metadata tracks original names
file_id = str(uuid.uuid4())
saved_filename = f"{file_id}{extension}"
metadata[file_id] = FileInfo(
    file_id=file_id,
    filename=saved_filename,
    original_filename=file.filename,
    # ... other fields
)
```

### Vector Database Collections
```python
# Company collections: company_{sanitized_id}
# File collections: company_{sanitized_id}_file_{file_id[:8]}
collection_name = f"{COLLECTION_PREFIX}{sanitized_company_id}"
```

### Error Handling & API Key Rotation
```python
try:
    response = llm.invoke(query)
except Exception as e:
    if "quota" in str(e).lower():
        self.rotate_api_key()  # Switch to next API key
        # Retry operation
```

## Integration Points & Dependencies

### External Services
- **Google Generative AI**: Embeddings (`models/embedding-001`) and LLM (`gemini-1.5-flash`)
- **ChromaDB**: Persistent vector storage with collection isolation
- **LangChain**: RAG pipeline with history-aware retrieval

### File Processing Libraries
- **PyPDFLoader**: PDF document processing
- **Docx2txtLoader**: Word document processing
- **TextLoader**: Plain text files
- Custom JSON handling for structured data

## Common Development Tasks

### Adding New File Types
1. Add extension to `ALLOWED_EXTENSIONS` in `config.py`
2. Implement loader in `file_service.py` `_load_document_by_type()`
3. Update metadata handling if needed

### Adding New API Endpoints
1. Define Pydantic models in `models/schemas.py`
2. Implement business logic in appropriate service
3. Add router in `api/` with proper error handling
4. Include router in `run.py` app setup

### Testing File Upload Flow
```python
# Use test_automatic_build.py for end-to-end testing
python test_automatic_build.py
```

### Debugging Vector DB Issues
```python
# Check collection stats
stats = chroma_manager.get_collection_stats(company_id)
# Check build status
status = embedding_service.get_build_status(company_id)
```

## Code Quality Guidelines

### Naming Conventions
- Company IDs: `{company_id}` (e.g., `acme_corp`)
- File IDs: UUID strings (e.g., `a1b2c3d4-e5f6-7890-abcd-ef1234567890`)
- Collections: `company_{sanitized_id}` or `company_{id}_file_{short_file_id}`

### Error Handling
- Use specific exceptions (`ValueError`, `HTTPException`)
- Include company_id in error messages for debugging
- Log errors with context for troubleshooting

### Async/Await Usage
- Use `async` for I/O operations (file processing, API calls)
- Background tasks for long-running operations (vector DB building)
- Proper error handling in async contexts

## Deployment Considerations

### Environment Variables
```bash
# Required
GOOGLE_API_KEY_1="your_key"
SECRET_KEY="your_secret"

# Optional
DEBUG=true  # Enables auto-reload
HOST=0.0.0.0
PORT=8000
```

### Production Setup
- Mount `knowledge_base/` and `chroma_db/` as persistent volumes
- Configure CORS appropriately for frontend domains
- Set up proper logging and monitoring
- Consider Redis for chat session persistence

## Troubleshooting Common Issues

### "RAG system not initialized"
- Check if vector DB exists for the company
- Verify API keys are configured
- Run build process manually if needed

### File upload fails
- Check file extension is in `ALLOWED_EXTENSIONS`
- Verify company directory permissions
- Check available disk space

### Query returns no results
- Ensure vector DB is built (`build-status` endpoint)
- Check if documents were properly processed
- Verify company_id is correct in request

This system emphasizes **company-level data isolation**, **automatic processing pipelines**, and **scalable multi-tenant architecture**. Always consider the company context in all operations and maintain the isolation boundaries.</content>
<parameter name="filePath">c:\Users\int10281\Desktop\Github\CCD-AI\.github\copilot-instructions.md
