#!/usr/bin/env python3
"""
Script to import existing files into the multi-organizational system
"""
import requests
import json

def import_files_for_all_companies():
    """Import existing files for all test companies"""
    
    base_url = "http://localhost:8000"
    companies = ["company1", "company2", "company3"]
    
    print("🔄 Importing existing files into the multi-org system...")
    
    for company_id in companies:
        print(f"\n📁 Processing {company_id}...")
        
        try:
            # Call the import endpoint
            response = requests.post(f"{base_url}/api/v1/companies/{company_id}/import-files")
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ {result['message']}")
                
                for file_info in result['files']:
                    print(f"    - {file_info['original_filename']} ({file_info['extension']})")
            else:
                print(f"  ❌ Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n🔍 Checking results...")
    
    # Verify by listing companies
    try:
        response = requests.get(f"{base_url}/api/v1/companies/")
        if response.status_code == 200:
            companies_data = response.json()
            print("\n📊 Updated company stats:")
            
            for company in companies_data:
                print(f"  - {company['company_id']}: {company['file_count']} files")
        else:
            print(f"❌ Failed to get companies: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking results: {e}")

if __name__ == "__main__":
    import_files_for_all_companies()
