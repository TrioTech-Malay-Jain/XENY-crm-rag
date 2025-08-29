"""
File operations service for multi-organizational file management
"""
import os
import json
import uuid
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from fastapi import UploadFile
from langchain.schema import Document
from langchain_community.document_loaders import (
    TextLoader, 
    PyPDFLoader, 
    Docx2txtLoader
)

from config import KNOWLEDGE_BASE_DIR, ALLOWED_EXTENSIONS
from models.schemas import FileInfo, FileStatus


class FileOperationsService:
    """Service for handling file operations with company isolation"""
    
    def __init__(self):
        self.base_dir = KNOWLEDGE_BASE_DIR
        os.makedirs(self.base_dir, exist_ok=True)
    
    def get_company_directory(self, company_id: str) -> Path:
        """Get company-specific directory"""
        company_dir = self.base_dir / company_id
        os.makedirs(company_dir, exist_ok=True)
        return company_dir
    
    def generate_file_id(self) -> str:
        """Generate unique file ID"""
        return str(uuid.uuid4())
    
    async def save_uploaded_file(self, company_id: str, file: UploadFile) -> FileInfo:
        """Save uploaded file to company directory"""
        
        # Validate file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise ValueError(f"File type {file_extension} not allowed")
        
        # Validate JSON files
        if file_extension == ".json":
            content = await file.read()
            try:
                json.loads(content.decode('utf-8'))
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format")
            await file.seek(0)  # Reset file pointer
        
        # Generate file info
        file_id = self.generate_file_id()
        company_dir = self.get_company_directory(company_id)
        
        # Save with file_id as filename but keep extension
        saved_filename = f"{file_id}{file_extension}"
        file_path = company_dir / saved_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create file info
        file_info = FileInfo(
            file_id=file_id,
            filename=saved_filename,
            original_filename=file.filename,
            company_id=company_id,
            size=file_size,
            extension=file_extension,
            created_at=datetime.now(),
            metadata={
                "status": FileStatus.UPLOADED,
                "content_type": file.content_type
            }
        )
        
        # Save metadata
        await self.save_file_metadata(file_info)
        
        return file_info
    
    async def save_file_metadata(self, file_info: FileInfo):
        """Save file metadata to JSON file"""
        company_dir = self.get_company_directory(file_info.company_id)
        metadata_file = company_dir / "metadata.json"
        
        # Load existing metadata
        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        
        # Add new file metadata
        metadata[file_info.file_id] = file_info.dict()
        
        # Save metadata
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)
    
    def load_file_metadata(self, company_id: str) -> Dict[str, FileInfo]:
        """Load file metadata for a company"""
        company_dir = self.get_company_directory(company_id)
        metadata_file = company_dir / "metadata.json"
        
        if not metadata_file.exists():
            return {}
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Convert to FileInfo objects
            file_infos = {}
            for file_id, data in metadata.items():
                # Handle datetime strings
                if isinstance(data.get('created_at'), str):
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                
                file_infos[file_id] = FileInfo(**data)
            
            return file_infos
            
        except Exception as e:
            print(f"Error loading metadata for company {company_id}: {e}")
            return {}
    
    def list_company_files(self, company_id: str) -> List[FileInfo]:
        """List all files for a company"""
        metadata = self.load_file_metadata(company_id)
        return list(metadata.values())
    
    def get_file_info(self, company_id: str, file_id: str) -> Optional[FileInfo]:
        """Get specific file info"""
        metadata = self.load_file_metadata(company_id)
        return metadata.get(file_id)
    
    def get_file_path(self, company_id: str, filename: str) -> Path:
        """Get the full path to a file"""
        company_dir = self.get_company_directory(company_id)
        return company_dir / filename
    
    def find_company_by_file_id(self, file_id: str) -> Optional[str]:
        """Find which company a file belongs to by searching all companies"""
        try:
            # List all company directories
            for company_dir in self.base_dir.iterdir():
                if company_dir.is_dir():
                    company_id = company_dir.name
                    
                    # Check if this company has the file
                    file_info = self.get_file_info(company_id, file_id)
                    if file_info:
                        return company_id
            
            return None
            
        except Exception as e:
            print(f"Error finding company for file {file_id}: {e}")
            return None
    
    def delete_file(self, company_id: str, file_id: str) -> bool:
        """Delete a file and its metadata"""
        try:
            # Get file info
            file_info = self.get_file_info(company_id, file_id)
            if not file_info:
                return False
            
            # Delete physical file
            company_dir = self.get_company_directory(company_id)
            file_path = company_dir / file_info.filename
            
            if file_path.exists():
                os.remove(file_path)
            
            # Update metadata
            metadata = self.load_file_metadata(company_id)
            if file_id in metadata:
                del metadata[file_id]
                
                # Save updated metadata
                metadata_file = company_dir / "metadata.json"
                metadata_dict = {k: v.dict() for k, v in metadata.items()}
                
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata_dict, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            print(f"Error deleting file {file_id} for company {company_id}: {e}")
            return False
    
    def load_documents_from_company(self, company_id: str) -> List[Document]:
        """Load all documents for a company as LangChain Documents"""
        documents = []
        company_dir = self.get_company_directory(company_id)
        file_metadata = self.load_file_metadata(company_id)
        
        for file_id, file_info in file_metadata.items():
            file_path = company_dir / file_info.filename
            
            if not file_path.exists():
                continue
            
            try:
                # Load document based on file type
                docs = self._load_document_by_type(file_path, file_info.extension)
                
                # Add metadata to documents
                for doc in docs:
                    doc.metadata.update({
                        'file_id': file_id,
                        'company_id': company_id,
                        'original_filename': file_info.original_filename,
                        'file_type': file_info.extension.replace('.', ''),
                        'created_at': file_info.created_at.isoformat()
                    })
                
                documents.extend(docs)
                
            except Exception as e:
                print(f"Error loading document {file_path}: {e}")
                continue
        
        return documents
    
    def load_document(self, file_path: Path) -> List[Document]:
        """Load a single document as LangChain Documents"""
        if not file_path.exists():
            raise ValueError(f"File does not exist: {file_path}")
        
        # Determine file extension
        extension = file_path.suffix.lower()
        
        try:
            # Load document based on file type
            docs = self._load_document_by_type(file_path, extension)
            
            # Add basic metadata
            for doc in docs:
                doc.metadata.update({
                    'source': str(file_path),
                    'file_type': extension.replace('.', ''),
                    'filename': file_path.name
                })
            
            return docs
            
        except Exception as e:
            raise ValueError(f"Error loading document {file_path}: {e}")
    
    def _load_document_by_type(self, file_path: Path, extension: str) -> List[Document]:
        """Load document using appropriate loader based on file type"""
        
        if extension == '.txt':
            loader = TextLoader(str(file_path), encoding='utf-8')
            return loader.load()
        
        elif extension == '.pdf':
            loader = PyPDFLoader(str(file_path))
            return loader.load()
        
        elif extension == '.docx':
            loader = Docx2txtLoader(str(file_path))
            return loader.load()
        
        elif extension == '.json':
            # Handle JSON files
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Convert JSON to text
            if isinstance(json_data, dict):
                text_content = json.dumps(json_data, indent=2, ensure_ascii=False)
            elif isinstance(json_data, list):
                text_content = '\n'.join([
                    json.dumps(item, indent=2, ensure_ascii=False) 
                    if isinstance(item, (dict, list)) 
                    else str(item) 
                    for item in json_data
                ])
            else:
                text_content = str(json_data)
            
            # Create document
            doc = Document(
                page_content=text_content,
                metadata={
                    'source': str(file_path),
                    'file_type': 'json'
                }
            )
            return [doc]
        
        else:
            raise ValueError(f"Unsupported file type: {extension}")
    
    def get_company_file_stats(self, company_id: str) -> Dict[str, Any]:
        """Get file statistics for a company"""
        # First try to get files from metadata
        files = self.list_company_files(company_id)
        
        # If no metadata, count actual files in directory
        if not files:
            company_dir = self.get_company_directory(company_id)
            actual_files = []
            
            for file_path in company_dir.iterdir():
                if file_path.is_file() and file_path.name != "metadata.json":
                    # Check if it's a supported file type
                    extension = file_path.suffix.lower()
                    if extension in ALLOWED_EXTENSIONS:
                        actual_files.append({
                            'name': file_path.name,
                            'size': file_path.stat().st_size,
                            'extension': extension,
                            'created_at': datetime.fromtimestamp(file_path.stat().st_mtime)
                        })
            
            # Calculate stats from actual files
            total_size = sum(f['size'] for f in actual_files)
            file_types = {}
            
            for file_info in actual_files:
                ext = file_info['extension']
                file_types[ext] = file_types.get(ext, 0) + 1
            
            return {
                "company_id": company_id,
                "total_files": len(actual_files),
                "total_size": total_size,
                "file_types": file_types,
                "last_updated": max((f['created_at'] for f in actual_files), default=None)
            }
        
        # Use metadata files
        total_size = sum(f.size for f in files)
        file_types = {}
        
        for file_info in files:
            ext = file_info.extension
            file_types[ext] = file_types.get(ext, 0) + 1
        
        return {
            "company_id": company_id,
            "total_files": len(files),
            "total_size": total_size,
            "file_types": file_types,
            "last_updated": max((f.created_at for f in files), default=None)
        }


# Global instance
file_service = FileOperationsService()
