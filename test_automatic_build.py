#!/usr/bin/env python3
"""
Test script to verify automatic vector database building on file upload.
"""

import requests
import time
import os

# Configuration
BASE_URL = "http://localhost:8000"
COMPANY_ID = "test_company"
TEST_FILE_CONTENT = """
This is a test document for automatic vector database building.

Our company provides innovative AI solutions including:
- Natural Language Processing (NLP)
- Computer Vision systems
- Machine Learning models
- Data analytics platforms

We specialize in helping businesses automate their processes and make data-driven decisions.
Our team consists of experienced data scientists and software engineers.

Contact us at info@testcompany.com for more information.
"""

def create_test_file():
    """Create a test text file."""
    test_file_path = "test_document.txt"
    with open(test_file_path, 'w') as f:
        f.write(TEST_FILE_CONTENT)
    return test_file_path

def upload_file(file_path):
    """Upload a file to the API."""
    print(f"Uploading file: {file_path}")
    
    with open(file_path, 'rb') as f:
        response = requests.post(
            f"{BASE_URL}/api/v1/files/upload",
            files={'file': f},
            data={'company_id': COMPANY_ID}
        )
    
    if response.status_code == 200:
        print("✅ File uploaded successfully")
        print(f"Response: {response.json()}")
        return True
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(f"Error: {response.text}")
        return False

def check_build_status():
    """Check the vector database build status."""
    print("\nChecking build status...")
    
    response = requests.get(
        f"{BASE_URL}/api/v1/files/build-status/{COMPANY_ID}"
    )
    
    if response.status_code == 200:
        status_data = response.json()
        print(f"Build Status: {status_data}")
        return status_data.get('status')
    else:
        print(f"❌ Status check failed: {response.status_code}")
        print(f"Error details: {response.text}")
        return None

def wait_for_build_completion(max_wait=60):
    """Wait for the vector database build to complete."""
    print("\nWaiting for vector database build to complete...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        status = check_build_status()
        
        if status == 'completed':
            print("✅ Vector database build completed!")
            return True
        elif status == 'failed':
            print("❌ Vector database build failed!")
            return False
        elif status in ['building', 'pending']:
            print(f"⏳ Build status: {status}, waiting...")
            time.sleep(5)
        else:
            print(f"❓ Unknown status: {status}")
            time.sleep(5)
    
    print("⏰ Timeout waiting for build completion")
    return False

def test_query():
    """Test querying the documents after build completion."""
    print("\nTesting document query...")
    
    query_data = {
        'query': 'What services does the company provide?',
        'company_id': COMPANY_ID
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/query",
        json=query_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Query successful!")
        print(f"Full response: {result}")
        answer = result.get('response', result.get('answer', 'No answer received'))
        print(f"Answer: {answer}")
        return True
    else:
        print(f"❌ Query failed: {response.status_code}")
        print(f"Error: {response.text}")
        return False

def cleanup_test_file(file_path):
    """Clean up the test file."""
    try:
        os.remove(file_path)
        print(f"🧹 Cleaned up test file: {file_path}")
    except FileNotFoundError:
        pass

def main():
    print("🚀 Testing Automatic Vector Database Building")
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
    
    # Create test file
    test_file = create_test_file()
    
    try:
        # Upload file (should trigger automatic build)
        if not upload_file(test_file):
            return
        
        # Wait for build to complete
        if not wait_for_build_completion():
            print("❌ Test failed: Build did not complete in time")
            return
        
        # Test querying
        if not test_query():
            print("❌ Test failed: Query unsuccessful")
            return
        
        print("\n🎉 All tests passed! Automatic vector database building is working correctly.")
        
    finally:
        # Clean up
        cleanup_test_file(test_file)

if __name__ == "__main__":
    main()
