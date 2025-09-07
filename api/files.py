"""
File upload and management API endpoints
"""
from typing import List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import logging
from pathlib import Path

from models.schemas import FileInfo, FileUploadRequest, BuildStatus
from services.file_service import file_service
from services.embedding_service import embedding_service
from config import KNOWLEDGE_BASE_DIR

router = APIRouter(prefix="/files", tags=["files"])

logger = logging.getLogger(__name__)


@router.post("/upload", response_model=FileInfo)
async def upload_file(
    background_tasks: BackgroundTasks,
    company_id: str = Form(..., description="Company ID for file isolation"),
    file: UploadFile = File(..., description="File to upload")
):
    """Upload a file for a specific company and automatically build vector database"""
    
    try:
        # Save file
        file_info = await file_service.save_uploaded_file(company_id, file)
        
        # Check if company directory exists
        company_dir = file_service.get_company_directory(company_id)
        if not company_dir.exists():
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
        
        # Check if already building
        current_status = embedding_service.get_build_status(company_id)
        if current_status.status != "building":
            # Start build process in background for the entire company
            background_tasks.add_task(
                embedding_service.process_company_documents, 
                company_id
            )
        
        # Also create file-specific collection for targeted querying
        background_tasks.add_task(
            embedding_service.create_file_specific_collection,
            company_id,
            file_info.file_id
        )
        
        # Also add the individual document processing as fallback
        background_tasks.add_task(
            embedding_service.add_document_to_company, 
            company_id, 
            file_info.file_id
        )
        
        return file_info
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/list", response_model=List[FileInfo])
async def list_files(company_id: str):
    """List all files for a specific company"""
    
    try:
        files = file_service.list_company_files(company_id)
        return files
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.get("/{file_id}", response_model=FileInfo)
async def get_file_info(company_id: str, file_id: str):
    """Get information about a specific file"""
    
    file_info = file_service.get_file_info(company_id, file_id)
    
    if not file_info:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found for company {company_id}")
    
    return file_info


@router.delete("/{file_id}")
async def delete_file(company_id: str, file_id: str):
    """Delete a specific file"""
    
    try:
        # Delete from file system
        success = file_service.delete_file(company_id, file_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        
        # Delete from vector store
        from db.pinecone_manager import pinecone_manager
        pinecone_manager.delete_company_documents(company_id, file_id=file_id)
        
        return {"message": f"File {file_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@router.get("/stats/{company_id}")
async def get_file_stats(company_id: str):
    """Get file statistics for a company"""
    
    try:
        stats = file_service.get_company_file_stats(company_id)
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file stats: {str(e)}")


@router.get("/build-status/{company_id}", response_model=BuildStatus)
async def get_build_status(company_id: str):
    """Get build status for a company's vector database"""

    try:
        logger.info(f"Getting build status for company: {company_id}")

        # Sanitize company_id for filesystem safety
        sanitized_company_id = company_id.replace(' ', '_').replace('-', '_').lower()

        # Validate company exists
        company_dir = file_service.get_company_directory(sanitized_company_id)
        if not company_dir.exists():
            logger.warning(f"Company not found: {company_id}")
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")

        # Get build status from service
        build_status = embedding_service.get_build_status(sanitized_company_id)

        # Add additional metadata if status is completed
        if build_status.status == "completed":
            try:
                # Get company stats for additional context
                company_stats = file_service.get_company_file_stats(sanitized_company_id)
                if company_stats:
                    build_status.message = f"{build_status.message} ({company_stats['total_files']} files, {company_stats.get('total_size_mb', 0):.1f} MB)"
                    logger.info(f"Enhanced build status with stats for {company_id}: {company_stats['total_files']} files")
            except Exception as e:
                # Don't fail the request if stats retrieval fails
                logger.warning(f"Could not get company stats for {sanitized_company_id}: {e}")

        logger.info(f"Build status for {company_id}: {build_status.status} - {build_status.message}")
        return build_status

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid company ID format for {company_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid company ID format: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to get build status for {company_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get build status: {str(e)}")
    
@router.get("/file-paths/{company_id}")
async def get_company_file_paths(company_id: str):
    """Get static file paths for all files in a company for frontend viewing"""
    
    try:
        company_dir = KNOWLEDGE_BASE_DIR / company_id
        
        if not company_dir.exists():
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
        
        file_paths = []
        
        # Get all files in the company directory
        for file_path in company_dir.iterdir():
            if file_path.is_file() and file_path.name != "metadata.json":
                # Create static URL for the file
                static_url = f"/files/{company_id}/{file_path.name}"
                
                file_info = {
                    "filename": file_path.name,
                    "static_url": static_url,
                    "file_size": file_path.stat().st_size,
                    "file_extension": file_path.suffix.lower()
                }
                file_paths.append(file_info)
        
        return {
            "company_id": company_id,
            "total_files": len(file_paths),
            "files": file_paths
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file paths: {str(e)}")


@router.get("/file-url/{company_id}/{filename}")
async def get_file_url(company_id: str, filename: str):
    """Get static URL for a specific file"""
    
    try:
        file_path = KNOWLEDGE_BASE_DIR / company_id / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File {filename} not found in company {company_id}")
        
        static_url = f"/files/{company_id}/{filename}"
        
        return {
            "company_id": company_id,
            "filename": filename,
            "static_url": static_url,
            "file_size": file_path.stat().st_size,
            "file_extension": file_path.suffix.lower()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file URL: {str(e)}")


@router.get("/all-file-paths")
async def get_all_file_paths():
    """Get static file paths for all files across all companies"""
    
    try:
        all_files = {}
        
        if not KNOWLEDGE_BASE_DIR.exists():
            return {"companies": {}, "total_companies": 0, "total_files": 0}
        
        total_files = 0
        
        # Iterate through all company directories
        for company_dir in KNOWLEDGE_BASE_DIR.iterdir():
            if company_dir.is_dir():
                company_id = company_dir.name
                file_paths = []
                
                for file_path in company_dir.iterdir():
                    if file_path.is_file() and file_path.name != "metadata.json":
                        static_url = f"/files/{company_id}/{file_path.name}"
                        
                        file_info = {
                            "filename": file_path.name,
                            "static_url": static_url,
                            "file_size": file_path.stat().st_size,
                            "file_extension": file_path.suffix.lower()
                        }
                        file_paths.append(file_info)
                        total_files += 1
                
                all_files[company_id] = {
                    "file_count": len(file_paths),
                    "files": file_paths
                }
        
        return {
            "companies": all_files,
            "total_companies": len(all_files),
            "total_files": total_files
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get all file paths: {str(e)}")
