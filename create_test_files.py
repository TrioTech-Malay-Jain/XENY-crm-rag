#!/usr/bin/env python3
"""
Test script to create sample files for multi-organizational RAG system
"""

import os
import json
from pathlib import Path

def create_test_files():
    """Create sample files for testing multi-organizational setup"""
    
    # Create test companies
    companies = {
        "company1": "TechCorp Solutions",
        "company2": "DataFlow Industries", 
        "company3": "AI Innovations Ltd"
    }
    
    for company_id, company_name in companies.items():
        print(f"📁 Creating test files for {company_name} ({company_id})...")
        
        # Ensure company directory exists
        company_dir = Path("knowledge_base") / company_id
        os.makedirs(company_dir, exist_ok=True)
        
        # Create company-specific text file
        with open(company_dir / "company_info.txt", "w", encoding="utf-8") as f:
            f.write(f"Company Name: {company_name}\n")
            f.write(f"Company ID: {company_id}\n")
            f.write(f"Industry: Technology Solutions\n")
            f.write(f"Founded: 202{companies.__len__() - list(companies.keys()).index(company_id)}\n")
            f.write(f"This is a test document for the multi-organizational RAG system.\n")
            f.write(f"Each company has isolated data storage and retrieval.\n")
        
        # Create company-specific JSON file
        company_data = {
            "company_id": company_id,
            "company_name": company_name,
            "departments": ["Engineering", "Sales", "Marketing", "HR"],
            "technologies": ["Python", "FastAPI", "LangChain", "ChromaDB"],
            "features": [
                "Multi-format document support",
                "Company-level data isolation", 
                "Vector-based search",
                "Chat interface"
            ],
            "supported_formats": [".txt", ".json", ".pdf", ".docx"],
            "employees": 50 + (list(companies.keys()).index(company_id) * 25)
        }
        
        with open(company_dir / "company_data.json", "w", encoding="utf-8") as f:
            json.dump(company_data, f, indent=2)
        
        # Create company-specific policy file
        with open(company_dir / "policies.txt", "w", encoding="utf-8") as f:
            f.write(f"COMPANY POLICIES - {company_name}\n")
            f.write("=" * 50 + "\n\n")
            f.write("1. Data Security Policy\n")
            f.write(f"   - All {company_name} data must be kept confidential\n")
            f.write("   - Access is restricted to authorized personnel only\n")
            f.write("   - Multi-factor authentication required\n\n")
            f.write("2. Remote Work Policy\n")
            f.write("   - Flexible working hours: 9 AM - 6 PM\n")
            f.write("   - Work from home: 3 days per week\n")
            f.write("   - Mandatory team meetings: Tuesdays and Thursdays\n\n")
            f.write("3. Technology Usage\n")
            f.write("   - All employees must use company-provided laptops\n")
            f.write("   - Personal devices require security approval\n")
            f.write("   - Cloud storage: Google Drive for Business\n")
        
        print(f"  ✅ Created files for {company_name}")
    
    print("\n📊 Summary:")
    print(f"  - Created {len(companies)} test companies")
    print("  - Each company has 3 test files (txt, json, policies)")
    print("  - Files are isolated by company ID")
    
    print("\n🚀 Next Steps:")
    print("1. Start the multi-org server: python main_multi_org.py")
    print("2. Visit http://localhost:8000/docs for API documentation")
    print("3. Test the API:")
    print("   - Create companies via POST /api/v1/companies/")
    print("   - Upload files via POST /api/v1/files/upload")
    print("   - Build databases via POST /api/v1/companies/{company_id}/build")
    print("   - Query documents via POST /api/v1/query/")
    
    print("\n📋 Example API calls:")
    print("   curl -X POST 'http://localhost:8000/api/v1/companies/' \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"company_id\":\"company1\",\"name\":\"TechCorp Solutions\"}'")

if __name__ == "__main__":
    create_test_files()
