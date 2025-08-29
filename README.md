# CCD-AI Multi-Organization RAG System

A production-ready Retrieval Augmented Generation (RAG) system supporting multiple organizations, built with FastAPI, LangChain, ChromaDB, and Google Generative AI.

---

## Features
- **Multi-organization isolation**: Each company has its own files and vector DB collection
- **Automatic vector database building**: Vector DB is automatically built when files are uploaded
- **File upload, listing, deletion**: Per-company file management
- **Build status monitoring**: Check the status of vector database building process
- **Vector search and chat**: Query and chat endpoints scoped to company
- **File-specific querying**: Query individual documents by file_id for targeted responses
- **Scalable and modular**: Easily add new companies and files
- **Modern stack**: FastAPI, LangChain, ChromaDB, Google Gemini

---

## Project Structure
```
CCD-AI/
├── main_multi_org.py         # Main FastAPI app (multi-org)
├── api/
│   ├── files.py              # File endpoints (multi-org)
│   ├── query.py              # Query/chat endpoints (multi-org)
│   └── __init__.py           # Router registration
├── services/
│   ├── file_service.py       # File management per company
│   └── embedding_service.py  # Embedding & RAG chain per company
├── db/
│   └── chroma_manager.py     # ChromaDB collection management
├── models/
│   └── schemas.py            # Pydantic models
├── config.py                 # Centralized config
├── requirements.txt          # Dependencies
├── .env                      # Environment variables
├── knowledge_base/           # Company files
├── chroma_db/                # Vector DB collections
├── import_existing_files.py  # Utility: import files into system
├── create_test_files.py      # Utility: generate test files
├── archive/                  # Legacy/unused files
└── README.md                 # This documentation
```

---

## Installation & Setup

### Prerequisites
- Python 3.8+
- Google API Key(s) for Gemini

### 1. Clone the repository
```bash
git clone https://github.com/TrioTech-Malay-Jain/CCD-AI.git
cd CCD-AI
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/macOS
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the root directory:
```
GOOGLE_API_KEY_1="your_google_api_key"
SECRET_KEY="your_secret_key"
```
Add more `GOOGLE_API_KEY_N` as needed for rate limiting.

### 5. Prepare knowledge base
- Add your company files to `knowledge_base/{company_id}/`
- Supported formats: `.txt`, `.pdf`, `.docx`, `.json`
- Optionally, run `python create_test_files.py` to generate sample data

### 6. Import existing files (if needed)
```bash
python import_existing_files.py
```

### 7. Start the server
```bash
python main_multi_org.py
```
Visit [http://localhost:8000/docs](http://localhost:8000/docs) for API documentation.

---

## API Endpoints (Multi-Org)

> **Note:** Company management endpoints are currently commented out and not exposed. Only file and query endpoints are active.

- `POST /api/v1/files/upload` — Upload file (requires `company_id`) and automatically builds vector DB
- `GET /api/v1/files/build-status/{company_id}` — Check vector DB build status
- `GET /api/v1/files/list?company_id=...` — List files for a company
- `GET /api/v1/files/{file_id}?company_id=...` — Get file info
- `DELETE /api/v1/files/{file_id}?company_id=...` — Delete file
- `POST /api/v1/query` — Query documents (requires `company_id`, optional `file_id`)
- `POST /api/v1/chat` — Chat with company documents (supports file-specific chat)
- `POST /api/v1/query/file-chat` — Chat with specific file (only requires `file_id`)
- `GET /api/v1/query/file-info/{file_id}` — Get file info without company_id

---

## Example Usage

### Upload a file (automatically builds vector DB)
```python
import requests
with open('mydoc.pdf', 'rb') as f:
    r = requests.post('http://localhost:8000/api/v1/files/upload',
                     files={'file': f},
                     data={'company_id': 'company1'})
    print(r.json())
    # The vector database will be automatically built in the background
```

### Check build status
```python
import requests
r = requests.get('http://localhost:8000/api/v1/files/build-status/company1')
print(r.json())  # {'status': 'completed', 'message': 'Vector database ready'}
```

### Query all documents
```python
import requests
r = requests.post('http://localhost:8000/api/v1/query', json={
    'query': 'What technologies does this company use?',
    'company_id': 'company1'
})
print(r.json())
```

### Query a specific file
```python
import requests
r = requests.post('http://localhost:8000/api/v1/query', json={
    'query': 'What is this document about?',
    'company_id': 'company1',
    'file_id': 'your-file-id-here'
})
print(r.json())
```

### Chat with specific file (simplified)
```python
import requests
r = requests.post('http://localhost:8000/api/v1/query/file-chat', json={
    'query': 'Hello! Can you tell me about this document?',
    'file_id': 'your-file-id-here'  # Only file_id needed!
})
print(r.json())
```

### Get file info without company_id
```python
import requests
r = requests.get('http://localhost:8000/api/v1/query/file-info/your-file-id-here')
print(r.json())  # Automatically finds company and returns file details
```

---

## Notes
- All endpoints require `company_id` for isolation
- Each company’s files and vector DB are kept separate
- Legacy files are archived in `/archive` for migration/reference
- Company management endpoints are preserved in code for future migration, but not active

---

## License
MIT License

---

## Author
Malay Jain (TrioTech)

---

**For more details, see the API docs at `/docs` after starting the server.**

