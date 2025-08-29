#!/usr/bin/env python3
"""
Test script to verify file-specific querying functionality.
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
COMPANY_ID = "test_company"

def list_files():
    """List files for the test company."""
    print("📁 Listing files for test_company...")
    
    response = requests.get(
        f"{BASE_URL}/api/v1/files/list",
        params={'company_id': COMPANY_ID}
    )
    
    if response.status_code == 200:
        files = response.json()
        print(f"✅ Found {len(files)} files:")
        for file_info in files:
            print(f"  - {file_info['original_filename']} (ID: {file_info['file_id']})")
        return files
    else:
        print(f"❌ Failed to list files: {response.status_code}")
        return []

def test_general_query():
    """Test querying all company documents."""
    print("\n🔍 Testing general query (all documents)...")
    
    query_data = {
        'query': 'What services does the company provide?',
        'company_id': COMPANY_ID
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/query/",
        json=query_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ General query successful!")
        print(f"📄 Sources: {len(result.get('sources', []))} documents")
        print(f"💬 Answer: {result['response'][:200]}...")
        return True
    else:
        print(f"❌ General query failed: {response.status_code}")
        print(f"Error: {response.text}")
        return False

def test_file_specific_query(file_id, filename):
    """Test querying a specific file."""
    print(f"\n🎯 Testing file-specific query for: {filename}")
    
    query_data = {
        'query': 'What is this document about? Summarize its contents.',
        'company_id': COMPANY_ID,
        'file_id': file_id
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/query/",
        json=query_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ File-specific query successful!")
        if 'file_info' in result:
            print(f"📄 Queried file: {result['file_info']['filename']}")
        print(f"📄 Sources: {len(result.get('sources', []))} documents")
        print(f"💬 Answer: {result['response'][:200]}...")
        return True
    else:
        print(f"❌ File-specific query failed: {response.status_code}")
        print(f"Error: {response.text}")
        return False

def test_chat_functionality():
    """Test the chat endpoint with file-specific querying."""
    print("\n💬 Testing chat functionality...")
    
    # First, list files to get a file ID
    files = list_files()
    if not files:
        print("❌ No files available for chat testing")
        return False
    
    file_id = files[0]['file_id']
    filename = files[0]['original_filename']
    
    # Test chat with specific file
    chat_data = {
        'query': 'Hello! Can you tell me what this document is about?',
        'company_id': COMPANY_ID,
        'file_id': file_id
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/query/chat",
        json=chat_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Chat with {filename} successful!")
        print(f"🆔 Session ID: {result['session_id']}")
        if 'file_info' in result:
            print(f"📄 Chatting with: {result['file_info']['filename']}")
        print(f"💬 Response: {result['response'][:200]}...")
        
        # Test follow-up question
        follow_up_data = {
            'query': 'Can you provide more details?',
            'company_id': COMPANY_ID,
            'file_id': file_id,
            'session_id': result['session_id']
        }
        
        follow_up_response = requests.post(
            f"{BASE_URL}/api/v1/query/chat",
            json=follow_up_data
        )
        
        if follow_up_response.status_code == 200:
            follow_up_result = follow_up_response.json()
            print("✅ Follow-up chat successful!")
            print(f"💬 Follow-up response: {follow_up_result['response'][:200]}...")
            return True
        else:
            print(f"❌ Follow-up chat failed: {follow_up_response.status_code}")
            return False
    else:
        print(f"❌ Chat failed: {response.status_code}")
        print(f"Error: {response.text}")
        return False

def main():
    print("🚀 Testing File-Specific Querying Functionality")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Server is not running or not responding")
            return
        print("✅ Server is running")
    except requests.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on localhost:8000")
        return
    
    # List available files
    files = list_files()
    if not files:
        print("❌ No files available for testing")
        return
    
    # Test general query
    if not test_general_query():
        print("❌ General query test failed")
        return
    
    # Test file-specific queries for each file
    success_count = 0
    for file_info in files:
        if test_file_specific_query(file_info['file_id'], file_info['original_filename']):
            success_count += 1
    
    print(f"\n📊 File-specific query results: {success_count}/{len(files)} successful")
    
    # Test chat functionality
    if test_chat_functionality():
        print("✅ Chat functionality test passed")
    else:
        print("❌ Chat functionality test failed")
    
    print("\n🎉 Testing completed!")
    print(f"📈 Overall success rate: {(success_count + 1)}/{len(files) + 1} tests passed")

if __name__ == "__main__":
    main()
