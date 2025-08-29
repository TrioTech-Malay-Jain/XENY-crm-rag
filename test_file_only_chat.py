#!/usr/bin/env python3
"""
Test script for file-only chat functionality.
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
COMPANY_ID = "test_company"

def list_files():
    """List files for the test company to get file IDs."""
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

def test_file_info_endpoint(file_id):
    """Test the new file-info endpoint that doesn't require company_id."""
    print(f"\n🔍 Testing file-info endpoint for file: {file_id}")
    
    response = requests.get(f"{BASE_URL}/api/v1/query/file-info/{file_id}")
    
    if response.status_code == 200:
        file_info = response.json()
        print("✅ File info retrieved successfully!")
        print(f"📄 File: {file_info['original_filename']}")
        print(f"🏢 Company: {file_info['company_id']}")
        print(f"📊 Size: {file_info['size']} bytes")
        return file_info
    else:
        print(f"❌ File info failed: {response.status_code}")
        print(f"Error: {response.text}")
        return None

def test_file_only_chat(file_id, filename):
    """Test the new file-only chat endpoint."""
    print(f"\n💬 Testing file-only chat with: {filename}")
    
    chat_data = {
        'query': 'Hello! Can you tell me what this document is about and summarize its main points?',
        'file_id': file_id
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/query/file-chat",
        json=chat_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ File-only chat successful!")
        print(f"🆔 Session ID: {result['session_id']}")
        print(f"🏢 Company: {result['company_id']}")
        if 'file_info' in result:
            print(f"📄 Chatting with: {result['file_info']['filename']}")
        print(f"💬 Response: {result['response'][:300]}...")
        
        return result['session_id']
    else:
        print(f"❌ File-only chat failed: {response.status_code}")
        print(f"Error: {response.text}")
        return None

def test_follow_up_chat(file_id, session_id):
    """Test follow-up chat in the same session."""
    print(f"\n🔄 Testing follow-up chat...")
    
    follow_up_data = {
        'query': 'Can you provide more specific details about the key topics mentioned?',
        'file_id': file_id,
        'session_id': session_id
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/query/file-chat",
        json=follow_up_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Follow-up chat successful!")
        print(f"💬 Follow-up response: {result['response'][:300]}...")
        return True
    else:
        print(f"❌ Follow-up chat failed: {response.status_code}")
        print(f"Error: {response.text}")
        return False

def test_chat_history(session_id):
    """Test retrieving chat history."""
    print(f"\n📚 Testing chat history retrieval...")
    
    response = requests.get(f"{BASE_URL}/api/v1/query/chat/{session_id}")
    
    if response.status_code == 200:
        history = response.json()
        print(f"✅ Chat history retrieved successfully!")
        print(f"📝 Messages in session: {len(history)}")
        for i, msg in enumerate(history, 1):
            sender = msg['sender']
            content = msg['message'][:100] + "..." if len(msg['message']) > 100 else msg['message']
            print(f"  {i}. {sender.upper()}: {content}")
        return True
    else:
        print(f"❌ Chat history failed: {response.status_code}")
        return False

def compare_old_vs_new_chat(file_id, filename):
    """Compare the old chat method vs new file-only chat method."""
    print(f"\n🔬 Comparing old vs new chat methods for: {filename}")
    
    # Test old method (with company_id)
    print("\n📊 Old method (with company_id):")
    old_chat_data = {
        'query': 'What are the main topics in this document?',
        'company_id': COMPANY_ID,
        'file_id': file_id
    }
    
    old_response = requests.post(
        f"{BASE_URL}/api/v1/query/chat",
        json=old_chat_data
    )
    
    if old_response.status_code == 200:
        print("✅ Old method successful")
    else:
        print(f"❌ Old method failed: {old_response.status_code}")
    
    # Test new method (file_id only)
    print("\n🆕 New method (file_id only):")
    new_chat_data = {
        'query': 'What are the main topics in this document?',
        'file_id': file_id
    }
    
    new_response = requests.post(
        f"{BASE_URL}/api/v1/query/file-chat",
        json=new_chat_data
    )
    
    if new_response.status_code == 200:
        print("✅ New method successful")
        return True
    else:
        print(f"❌ New method failed: {new_response.status_code}")
        return False

def main():
    print("🚀 Testing File-Only Chat Functionality")
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
    
    # Test with the first file
    file_id = files[0]['file_id']
    filename = files[0]['original_filename']
    
    # Test file info endpoint
    file_info = test_file_info_endpoint(file_id)
    if not file_info:
        print("❌ File info test failed")
        return
    
    # Test file-only chat
    session_id = test_file_only_chat(file_id, filename)
    if not session_id:
        print("❌ File-only chat test failed")
        return
    
    # Test follow-up chat
    if not test_follow_up_chat(file_id, session_id):
        print("❌ Follow-up chat test failed")
        return
    
    # Test chat history
    if not test_chat_history(session_id):
        print("❌ Chat history test failed")
        return
    
    # Compare old vs new methods
    if not compare_old_vs_new_chat(file_id, filename):
        print("❌ Comparison test failed")
        return
    
    print("\n🎉 All file-only chat tests passed!")
    print("\n📋 Summary of new endpoints:")
    print("  - POST /api/v1/query/file-chat - Chat with file using only file_id")
    print("  - GET /api/v1/query/file-info/{file_id} - Get file info without company_id")
    print("\n💡 Benefits:")
    print("  - Simplified API: Only file_id required for chat")
    print("  - Automatic company detection")
    print("  - Same functionality as before but easier to use")

if __name__ == "__main__":
    main()
