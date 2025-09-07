# GitHub Copilot Instructions for Multi-Organizational RAG System

## System Overview

This is a **multi-tenant RAG (Retrieval-Augmented Generation) system** built with FastAPI that provides company-scoped document processing and querying capabilities. The system supports multiple organizations with complete data isolation, background document processing, and intelligent chat interfaces.

### Core Architecture

**Technology Stack:**
- **Backend:** FastAPI (Python 3.8+)
- **Vector Database:** ChromaDB with company-scoped collections
- **LLM Integration:** Azure OpenAI (primary) with HuggingFace embeddings fallback
- **Document Processing:** LangChain with support for PDF, DOCX, TXT, JSON
- **Frontend:** Jinja2 templates with static assets

**Key Design Patterns:**
- **Multi-Tenant Isolation:** All data is scoped by `company_id` with separate directories and vector collections
- **Background Processing:** File uploads trigger async document processing and vector building
- **Cached RAG Chains:** Company-specific RAG chains cached in memory for performance
- **Fuzzy Name Matching:** Intelligent company name resolution for user-friendly queries

## Development Workflow Patterns

### 1. Company Management Flow
```python
# Always sanitize company_id for filesystem safety
company_id = company_id.replace(' ', '_').replace('-', '_').lower()

# Create company directory structure
company_dir = file_service.get_company_directory(company_id)

# Build vector database asynchronously
background_tasks.add_task(embedding_service.process_company_documents, company_id)
```

### 2. File Upload and Processing Flow
```python
# Validate file type against ALLOWED_EXTENSIONS
if file_extension not in ALLOWED_EXTENSIONS:
    raise ValueError(f"File type {file_extension} not allowed")

# Generate UUID-based filename but preserve extension
file_id = str(uuid.uuid4())
saved_filename = f"{file_id}{file_extension}"

# Save file with metadata
file_info = FileInfo(...)
await file_service.save_file_metadata(file_info)

# Trigger background vector building
background_tasks.add_task(embedding_service.process_company_documents, company_id)
```

### 3. Query Processing Flow
```python
# Always scope queries by company_id
result = await embedding_service.query_company(
    company_id=request.company_id,
    query=request.query,
    chat_history=request.history or []
)

# Use cached RAG chain if available
if company_id in self._rag_chains:
    rag_chain = self._rag_chains[company_id]
```

## Critical Implementation Rules

### Company ID Handling
- **Always sanitize company_id:** Replace spaces with underscores, convert to lowercase
- **Filesystem Safe:** Use `company_id.replace(' ', '_').replace('-', '_').lower()`
- **Consistent Naming:** Apply same sanitization across all services

### Vector Database Operations
- **Collection Naming:** Use `f"company_{company_id}"` pattern
- **Error Handling:** Always check if collection exists before operations
- **Cleanup:** Delete collections when companies are removed

### Background Task Management
- **Status Tracking:** Use `embedding_service.build_statuses` dictionary
- **Progress Updates:** Update progress from 0.0 to 1.0 during processing
- **Error Recovery:** Handle failures gracefully and update status

### File Management Patterns
- **Metadata Storage:** Store file metadata in `company_dir/metadata.json`
- **Unique File IDs:** Generate UUIDs for file identification
- **Path Resolution:** Use `file_service.get_file_path(company_id, filename)`

## API Endpoint Patterns

### Company Management
```python
@router.post("/companies/", response_model=CompanyInfo)
@router.get("/companies/", response_model=List[CompanyInfo])
@router.get("/companies/{company_id}", response_model=CompanyInfo)
@router.delete("/companies/{company_id}")
@router.post("/companies/{company_id}/build", response_model=BuildStatus)
@router.get("/companies/{company_id}/build-status", response_model=BuildStatus)
```

### File Operations
```python
@router.post("/files/upload", response_model=FileInfo)
@router.get("/files/{company_id}", response_model=List[FileInfo])
@router.delete("/files/{company_id}/{file_id}")
```

### Query Operations
```python
@router.post("/query/", response_model=QueryResponse)  # Company-wide query
@router.post("/query/chat", response_model=QueryResponse)  # With chat history
@router.post("/query/file-chat", response_model=QueryResponse)  # File-specific chat
```

## Service Layer Architecture

### FileService Responsibilities
- Company directory management
- File upload and validation
- Metadata persistence (JSON-based)
- Document loading with LangChain
- File type detection and processing

### EmbeddingService Responsibilities
- RAG chain creation and caching
- Document processing and vector building
- Company-scoped query execution
- Background task management
- Build status tracking

### ChromaManager Responsibilities
- Vector database operations
- Collection management (create/delete)
- Document embedding and storage
- Similarity search execution
- Multi-provider embedding support

## Configuration Management

### Environment Variables
```python
# Required
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT=your_deployment

# Optional with fallbacks
HUGGINGFACE_API_KEY=your_key
EMBEDDING_PROVIDER=azure  # or huggingface
```

### Directory Structure
```
knowledge_base/
├── company_1/
│   ├── metadata.json
│   ├── file1.pdf
│   └── file2.txt
└── company_2/
    ├── metadata.json
    └── file3.docx

chroma_db/
└── company_company_1/
    ├── data_level0.bin
    └── header.bin
```

## Error Handling Patterns

### HTTP Exceptions
```python
# Company not found
raise HTTPException(status_code=404, detail=f"Company {company_id} not found")

# File validation errors
raise HTTPException(status_code=400, detail=f"File type {extension} not allowed")

# Processing errors
raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
```

### Service-Level Error Handling
```python
try:
    # Vector database operations
    collection_stats = chroma_manager.get_collection_stats(company_id)
except Exception as e:
    print(f"Warning: Could not get collection stats for {company_id}: {e}")
    collection_stats = {"exists": False, "document_count": 0}
```

## Testing Patterns

### Unit Test Structure
```python
def test_company_creation():
    # Test company directory creation
    # Test metadata initialization
    # Test vector collection setup

def test_file_upload():
    # Test file validation
    # Test metadata saving
    # Test background processing trigger

def test_query_execution():
    # Test company isolation
    # Test RAG chain caching
    # Test chat history integration
```

### Integration Test Patterns
```python
# Test complete upload-to-query workflow
# Test multi-company isolation
# Test background processing completion
# Test error recovery scenarios
```

## Deployment Considerations

### Docker Configuration
```dockerfile
FROM python:3.8-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Environment Variables
```bash
# Database
CHROMA_DB_PATH=/app/data/chroma_db
KNOWLEDGE_BASE_DIR=/app/data/knowledge_base

# Azure OpenAI
AZURE_OPENAI_API_KEY=production_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Application
DEBUG=false
WORKERS=4
```

## Common Development Tasks

### Adding New File Types
1. Add extension to `ALLOWED_EXTENSIONS` in config.py
2. Implement loader in `FileService._load_document_by_type()`
3. Update file validation logic
4. Test document processing pipeline

### Adding New Embedding Providers
1. Extend `ChromaManager` with new provider methods
2. Update configuration loading in config.py
3. Add provider selection logic in embedding service
4. Update requirements.txt with new dependencies

### Adding New Query Types
1. Create new Pydantic request/response models
2. Implement query method in `EmbeddingService`
3. Add API endpoint in appropriate router
4. Update OpenAPI documentation

## Code Quality Standards

### Naming Conventions
- **Company IDs:** `company_id` (snake_case for variables)
- **File IDs:** `file_id` (UUID strings)
- **Service Methods:** `process_company_documents()` (descriptive verbs)
- **API Endpoints:** `/companies/{company_id}/build` (RESTful patterns)

### Documentation Standards
- **Docstrings:** Use triple quotes with parameter descriptions
- **Type Hints:** Include for all function parameters and return values
- **Comments:** Explain complex business logic, not obvious code
- **API Docs:** Use FastAPI's automatic OpenAPI generation

### Logging Patterns
```python
# Info level for normal operations
logger.info(f"Processing documents for company {company_id}")

# Warning level for recoverable errors
logger.warning(f"Could not get collection stats for {company_id}: {e}")

# Error level for critical failures
logger.error(f"Failed to process documents for {company_id}: {e}")
```

## Security Considerations

### Data Isolation
- **Company Scoping:** All operations must include company_id validation
- **File Access:** Verify file ownership before operations
- **API Authentication:** Implement proper authentication middleware

### Input Validation
- **File Types:** Restrict to allowed extensions only
- **File Sizes:** Implement size limits to prevent abuse
- **Company IDs:** Sanitize and validate format
- **Query Input:** Sanitize user queries for safety

This comprehensive guide ensures AI coding agents can immediately understand and contribute effectively to the multi-organizational RAG system, maintaining consistency with established patterns and architectural decisions.</content>
<parameter name="filePath">e:\New folder\.github\copilot-instructions.md
