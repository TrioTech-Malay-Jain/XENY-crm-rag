#!/usr/bin/env python3
"""
Script to check Pinecone index for company documents
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.pinecone_manager import pinecone_manager

def check_company_documents(company_id: str):
    """Check if documents exist for a company in Pinecone"""
    print(f"🔍 Checking documents for company: {company_id}")

    # Get current stats (this might be inaccurate)
    stats = pinecone_manager.get_company_stats(company_id)
    print(f"📊 Current stats: {stats}")

    # Try to list company documents
    try:
        docs = pinecone_manager.list_company_docs(company_id)
        print(f"📄 Listed documents: {docs}")
    except Exception as e:
        print(f"❌ Error listing documents: {e}")

    # Try a test query to see if we get results
    try:
        results = pinecone_manager.query_company_documents(
            company_id=company_id,
            query="test query",
            k=1
        )
        print(f"🔎 Test query results: {len(results)} matches")
        if results:
            print(f"   First result metadata: {results[0].get('metadata', {})}")
    except Exception as e:
        print(f"❌ Error querying documents: {e}")

    # Check index stats directly
    try:
        index_stats = pinecone_manager.index.describe_index_stats()
        print(f"📈 Full index stats: {index_stats}")
    except Exception as e:
        print(f"❌ Error getting index stats: {e}")

if __name__ == "__main__":
    company_id = "urbanpiper"
    check_company_documents(company_id)
