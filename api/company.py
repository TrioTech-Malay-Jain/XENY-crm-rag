"""
Company management API endpoints
"""
from typing import List
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks

from models.schemas import CompanyInfo, CompanyCreate, BuildStatus
from services.file_service import file_service
from services.embedding_service import embedding_service
from db.chroma_manager import chroma_manager

router = APIRouter(prefix="/companies", tags=["companies"])

# router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("/", response_model=CompanyInfo)
async def create_company(company: CompanyCreate):
    """Create a new company (just creates the directory structure)"""
    
    try:
        # Create company directory
        company_dir = file_service.get_company_directory(company.company_id)
        
        # Create company info
        from datetime import datetime
        company_info = CompanyInfo(
            company_id=company.company_id,
            name=company.name,
            description=company.description,
            created_at=datetime.now(),
            file_count=0
        )
        
        return company_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create company: {str(e)}")

# @router.post("/", response_model=CompanyInfo)
# async def create_company(company: CompanyCreate):
#     """Create a new company (just creates the directory structure)"""
#     try:
#         # Create company directory
#         company_dir = file_service.get_company_directory(company.company_id)
#         # Create company info
#         from datetime import datetime
#         company_info = CompanyInfo(
#             company_id=company.company_id,
#             name=company.name,
#             description=company.description,
#             created_at=datetime.now(),
#             file_count=0
#         )
#         return company_info
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to create company: {str(e)}")


@router.get("/", response_model=List[CompanyInfo])
async def list_companies():
    """List all companies"""
    
    try:
        companies = []
        
        # Get companies from file system
        if file_service.base_dir.exists():
            for company_dir in file_service.base_dir.iterdir():
                if company_dir.is_dir():
                    company_id = company_dir.name
                    
                    # Get file stats
                    stats = file_service.get_company_file_stats(company_id)
                    
                    # Get collection stats (with error handling)
                    try:
                        collection_stats = chroma_manager.get_collection_stats(company_id)
                    except Exception as e:
                        print(f"Warning: Could not get collection stats for {company_id}: {e}")
                        collection_stats = {"exists": False, "document_count": 0}
                    
                    from datetime import datetime
                    company_info = CompanyInfo(
                        company_id=company_id,
                        name=company_id.replace('_', ' ').title(),  # Default name
                        description=f"Company with {stats['total_files']} files",
                        created_at=stats.get('last_updated', None) or datetime.now(),
                        file_count=stats['total_files'],
                        last_updated=stats.get('last_updated')
                    )
                    
                    companies.append(company_info)
        
        return companies
        
    except Exception as e:
        print(f"Error in list_companies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list companies: {str(e)}")

# @router.get("/", response_model=List[CompanyInfo])
# async def list_companies():
#     """List all companies"""
#     try:
#         companies = []
#         # Get companies from file system
#         if file_service.base_dir.exists():
#             for company_dir in file_service.base_dir.iterdir():
#                 if company_dir.is_dir():
#                     company_id = company_dir.name
#                     # Get file stats
#                     stats = file_service.get_company_file_stats(company_id)
#                     # Get collection stats (with error handling)
#                     try:
#                         collection_stats = chroma_manager.get_collection_stats(company_id)
#                     except Exception as e:
#                         print(f"Warning: Could not get collection stats for {company_id}: {e}")
#                         collection_stats = {"exists": False, "document_count": 0}
#                     from datetime import datetime
#                     company_info = CompanyInfo(
#                         company_id=company_id,
#                         name=company_id.replace('_', ' ').title(),  # Default name
#                         description=f"Company with {stats['total_files']} files",
#                         created_at=stats.get('last_updated', None) or datetime.now(),
#                         file_count=stats['total_files'],
#                         last_updated=stats.get('last_updated')
#                     )
#                     companies.append(company_info)
#         return companies
#     except Exception as e:
#         print(f"Error in list_companies: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to list companies: {str(e)}")


@router.get("/{company_id}", response_model=CompanyInfo)
async def get_company(company_id: str):
    """Get company information"""
    
    try:
        # Check if company exists
        company_dir = file_service.get_company_directory(company_id)
        
        if not company_dir.exists():
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
        
        # Get file stats
        stats = file_service.get_company_file_stats(company_id)
        
        from datetime import datetime
        company_info = CompanyInfo(
            company_id=company_id,
            name=company_id.replace('_', ' ').title(),
            description=f"Company with {stats['total_files']} files",
            created_at=stats.get('last_updated', None) or datetime.now(),
            file_count=stats['total_files'],
            last_updated=stats.get('last_updated')
        )
        
        return company_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get company: {str(e)}")

# @router.get("/{company_id}", response_model=CompanyInfo)
# async def get_company(company_id: str):
#     """Get company information"""
#     try:
#         # Check if company exists
#         company_dir = file_service.get_company_directory(company_id)
#         if not company_dir.exists():
#             raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
#         # Get file stats
#         stats = file_service.get_company_file_stats(company_id)
#         from datetime import datetime
#         company_info = CompanyInfo(
#             company_id=company_id,
#             name=company_id.replace('_', ' ').title(),
#             description=f"Company with {stats['total_files']} files",
#             created_at=stats.get('last_updated', None) or datetime.now(),
#             file_count=stats['total_files'],
#             last_updated=stats.get('last_updated')
#         )
#         return company_info
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to get company: {str(e)}")


@router.delete("/{company_id}")
async def delete_company(company_id: str):
    """Delete a company and all its data"""
    
    try:
        # Delete vector store collection
        chroma_manager.delete_company_collection(company_id)
        
        # Delete file directory
        company_dir = file_service.get_company_directory(company_id)
        if company_dir.exists():
            import shutil
            shutil.rmtree(company_dir)
        
        # Clean up build status
        if company_id in embedding_service.build_statuses:
            del embedding_service.build_statuses[company_id]
        
        # Clean up RAG chains
        if company_id in embedding_service._rag_chains:
            del embedding_service._rag_chains[company_id]
        
        return {"message": f"Company {company_id} deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete company: {str(e)}")

# @router.delete("/{company_id}")
# async def delete_company(company_id: str):
#     """Delete a company and all its data"""
#     try:
#         # Delete vector store collection
#         chroma_manager.delete_company_collection(company_id)
#         # Delete file directory
#         company_dir = file_service.get_company_directory(company_id)
#         if company_dir.exists():
#             import shutil
#             shutil.rmtree(company_dir)
#         # Clean up build status
#         if company_id in embedding_service.build_statuses:
#             del embedding_service.build_statuses[company_id]
#         # Clean up RAG chains
#         if company_id in embedding_service._rag_chains:
#             del embedding_service._rag_chains[company_id]
#         return {"message": f"Company {company_id} deleted successfully"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to delete company: {str(e)}")


@router.post("/{company_id}/build", response_model=BuildStatus)
async def build_company_database(company_id: str, background_tasks: BackgroundTasks):
    """Build/rebuild vector database for a company"""
    
    try:
        # Check if company exists
        company_dir = file_service.get_company_directory(company_id)
        if not company_dir.exists():
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
        
        # Check if already building
        current_status = embedding_service.get_build_status(company_id)
        if current_status.status == "building":
            return current_status
        
        # Start build process in background
        background_tasks.add_task(
            embedding_service.process_company_documents, 
            company_id
        )
        
        from datetime import datetime
        from models.schemas import BuildStatusEnum
        return BuildStatus(
            status=BuildStatusEnum.BUILDING,
            message="Vector database build started...",
            company_id=company_id,
            timestamp=datetime.now(),
            progress=0.0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start build: {str(e)}")

# @router.post("/{company_id}/build", response_model=BuildStatus)
# async def build_company_database(company_id: str, background_tasks: BackgroundTasks):
#     """Build/rebuild vector database for a company"""
#     try:
#         # Check if company exists
#         company_dir = file_service.get_company_directory(company_id)
#         if not company_dir.exists():
#             raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
#         # Check if already building
#         current_status = embedding_service.get_build_status(company_id)
#         if current_status.status == "building":
#             return current_status
#         # Start build process in background
#         background_tasks.add_task(
#             embedding_service.process_company_documents, 
#             company_id
#         )
#         from datetime import datetime
#         from models.schemas import BuildStatusEnum
#         return BuildStatus(
#             status=BuildStatusEnum.BUILDING,
#             message="Vector database build started...",
#             company_id=company_id,
#             timestamp=datetime.now(),
#             progress=0.0
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to start build: {str(e)}")


@router.get("/{company_id}/build-status", response_model=BuildStatus)
async def get_build_status(company_id: str):
    """Get build status for a company"""
    
    return embedding_service.get_build_status(company_id)

# @router.get("/{company_id}/build-status", response_model=BuildStatus)
# async def get_build_status(company_id: str):
#     """Get build status for a company"""
#     return embedding_service.get_build_status(company_id)


@router.post("/{company_id}/import-files")
async def import_existing_files(company_id: str):
    """Import existing files in company directory into metadata system"""
    
    try:
        company_dir = file_service.get_company_directory(company_id)
        if not company_dir.exists():
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
        
        imported_files = []
        
        for file_path in company_dir.iterdir():
            if file_path.is_file() and file_path.name != "metadata.json":
                extension = file_path.suffix.lower()
                
                # Check if it's a supported file type
                from config import ALLOWED_EXTENSIONS
                if extension in ALLOWED_EXTENSIONS:
                    # Create file info for existing file
                    file_id = file_service.generate_file_id()
                    file_size = file_path.stat().st_size
                    created_at = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    # Create file info
                    from models.schemas import FileInfo, FileStatus
                    file_info = FileInfo(
                        file_id=file_id,
                        filename=file_path.name,
                        original_filename=file_path.name,
                        company_id=company_id,
                        size=file_size,
                        extension=extension,
                        created_at=created_at,
                        metadata={
                            "status": FileStatus.UPLOADED,
                            "imported": True
                        }
                    )
                    
                    # Save metadata
                    await file_service.save_file_metadata(file_info)
                    imported_files.append(file_info.dict())
        
        return {
            "message": f"Imported {len(imported_files)} files for company {company_id}",
            "files": imported_files
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import files: {str(e)}")

# @router.post("/{company_id}/import-files")
# async def import_existing_files(company_id: str):
#     """Import existing files in company directory into metadata system"""
#     try:
#         company_dir = file_service.get_company_directory(company_id)
#         if not company_dir.exists():
#             raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
#         imported_files = []
#         for file_path in company_dir.iterdir():
#             if file_path.is_file() and file_path.name != "metadata.json":
#                 extension = file_path.suffix.lower()
#                 # Check if it's a supported file type
#                 from config import ALLOWED_EXTENSIONS
#                 if extension in ALLOWED_EXTENSIONS:
#                     # Create file info for existing file
#                     file_id = file_service.generate_file_id()
#                     file_size = file_path.stat().st_size
#                     created_at = datetime.fromtimestamp(file_path.stat().st_mtime)
#                     # Create file info
#                     from models.schemas import FileInfo, FileStatus
#                     file_info = FileInfo(
#                         file_id=file_id,
#                         filename=file_path.name,
#                         original_filename=file_path.name,
#                         company_id=company_id,
#                         size=file_size,
#                         extension=extension,
#                         created_at=created_at,
#                         metadata={
#                             "status": FileStatus.UPLOADED,
#                             "imported": True
#                         }
#                     )
#                     # Save metadata
#                     await file_service.save_file_metadata(file_info)
#                     imported_files.append(file_info.dict())
#         return {
#             "message": f"Imported {len(imported_files)} files for company {company_id}",
#             "files": imported_files
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to import files: {str(e)}")


@router.get("/{company_id}/stats")
async def get_company_stats(company_id: str):
    """Get comprehensive stats for a company"""
    
    try:
        # File stats
        file_stats = file_service.get_company_file_stats(company_id)
        
        # Collection stats
        collection_stats = chroma_manager.get_collection_stats(company_id)
        
        # Build status
        build_status = embedding_service.get_build_status(company_id)
        
        return {
            "company_id": company_id,
            "files": file_stats,
            "vector_store": collection_stats,
            "build_status": build_status.dict(),
            "rag_available": company_id in embedding_service._rag_chains
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get company stats: {str(e)}")

# @router.get("/{company_id}/stats")
# async def get_company_stats(company_id: str):
#     """Get comprehensive stats for a company"""
#     try:
#         # File stats
#         file_stats = file_service.get_company_file_stats(company_id)
#         # Collection stats
#         collection_stats = chroma_manager.get_collection_stats(company_id)
#         # Build status
#         build_status = embedding_service.get_build_status(company_id)
#         return {
#             "company_id": company_id,
#             "files": file_stats,
#             "vector_store": collection_stats,
#             "build_status": build_status.dict(),
#             "rag_available": company_id in embedding_service._rag_chains
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to get company stats: {str(e)}")
