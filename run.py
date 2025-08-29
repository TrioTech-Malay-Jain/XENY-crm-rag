"""
Multi-organizational RAG system - Main FastAPI application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime
import os

from config import KNOWLEDGE_BASE_DIR
from config import API_PREFIX, HOST, PORT, DEBUG, STATIC_DIR, TEMPLATES_DIR
from models.schemas import HealthCheck
from api import files_router, query_router  # Removed company_router import

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting Multi-Organizational RAG System...")
    
    # Create necessary directories
    from config import KNOWLEDGE_BASE_DIR, CHROMA_DB_PATH
    os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)
    
    # Check API keys
    from config import get_google_api_keys
    api_keys = get_google_api_keys()
    if not api_keys:
        print("⚠️  Warning: No Google API keys found. Set GOOGLE_API_KEY_1 environment variable.")
    else:
        print(f"✅ Loaded {len(api_keys)} Google API keys")
    
    # List existing companies
    from db.chroma_manager import chroma_manager
    companies = chroma_manager.list_company_collections()
    if companies:
        print(f"📊 Found {len(companies)} existing companies: {companies}")
    else:
        print("📁 No existing companies found")
    
    print("✅ Application startup complete!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Multi-Organizational RAG System...")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Multi-Organizational RAG System",
    description="A RAG system with company-level data isolation",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates (if they exist)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Mount knowledge_base as static files for file viewing
if KNOWLEDGE_BASE_DIR.exists():
    app.mount("/files", StaticFiles(directory=str(KNOWLEDGE_BASE_DIR)), name="files")

if TEMPLATES_DIR.exists():
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include API routers
app.include_router(files_router, prefix=API_PREFIX)
app.include_router(query_router, prefix=API_PREFIX)
# app.include_router(company_router, prefix=API_PREFIX)  # Commented out to disable company endpoints


@app.get("/health")
async def simple_health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main interface"""
    if TEMPLATES_DIR.exists() and (TEMPLATES_DIR / "index.html").exists():
        return templates.TemplateResponse("index.html", {"request": request})
    else:
        return HTMLResponse("""
        <html>
            <head><title>Multi-Organizational RAG System</title></head>
            <body>
                <h1>Multi-Organizational RAG System</h1>
                <p>API is running. Visit <a href="/docs">/docs</a> for API documentation.</p>
                <h2>Quick Start:</h2>
                <ol>
                    <li>Create a company: POST /api/v1/companies/</li>
                    <li>Upload files: POST /api/v1/files/upload</li>
                    <li>Build database: POST /api/v1/companies/{company_id}/build</li>
                    <li>Query documents: POST /api/v1/query/</li>
                </ol>
            </body>
        </html>
        """)


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """Serve the admin panel"""
    if TEMPLATES_DIR.exists() and (TEMPLATES_DIR / "admin.html").exists():
        return templates.TemplateResponse("admin.html", {"request": request})
    else:
        return HTMLResponse("""
        <html>
            <head><title>Admin Panel - Multi-Organizational RAG</title></head>
            <body>
                <h1>Admin Panel</h1>
                <p>Use the API endpoints at <a href="/docs">/docs</a> to manage the system.</p>
                <h2>Available Endpoints:</h2>
                <ul>
                    <li><strong>Companies:</strong> /api/v1/companies/</li>
                    <li><strong>Files:</strong> /api/v1/files/</li>
                    <li><strong>Query:</strong> /api/v1/query/</li>
                </ul>
            </body>
        </html>
        """)


@app.get("/api/v1/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    from config import get_google_api_keys
    from services.embedding_service import embedding_service
    from db.chroma_manager import chroma_manager
    
    api_keys = get_google_api_keys()
    companies = chroma_manager.list_company_collections()
    
    return HealthCheck(
        status="healthy",
        version="2.0.0",
        rag_initialized=len(embedding_service._rag_chains) > 0,
        companies_loaded=len(companies),
        api_keys_available=len(api_keys),
        timestamp=datetime.now()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "run:app",
        host=HOST,
        port=PORT,
        reload=DEBUG
    )
