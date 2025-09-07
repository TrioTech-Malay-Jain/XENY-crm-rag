#!/usr/bin/env python3
"""
Tes        # Test different queries
        test_queries = [
            "Urban Piper",
            "What is Urban Piper?",
            "Tell me about Urban Piper",
            "UrbanPiper",
            "food delivery",
            "restaurant platform",
            "company information"
        ]

        print("\n🔍 Testing Different Query Variations...")
        for query in test_queries:
            results = pinecone_manager.query_company_documents(
                company_id="UrbanPiper",
                query=query,
                k=3
            )
            print(f"Query: '{query}' -> {len(results)} results")
            if results:
                print(f"  Top score: {results[0].get('score', 'N/A')}")
                print(f"  Sample text: {results[0].get('text', '')[:50]}...")
            print()ript to debug Pinecone integration and query issues
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Run all tests"""
    print("🚀 Starting Pinecone Debug Tests\n")

    try:
        from config import KNOWLEDGE_BASE_DIR
        from db.pinecone_manager import pinecone_manager
        from services.embedding_service import PineconeRetriever

        # Test 1: Connection
        print("🔍 Testing Pinecone Connection...")
        stats = pinecone_manager.get_company_stats("UrbanPiper")
        print(f"📊 Pinecone Index Stats: {stats}")

        # Test 2: Direct query
        print("\n🔍 Testing Direct Pinecone Query...")
        results = pinecone_manager.query_company_documents(
            company_id="UrbanPiper",
            query="Urban Piper",
            k=5
        )
        print(f"📊 Direct query results: {len(results)} matches")
        for i, result in enumerate(results[:3]):  # Show first 3 results
            print(f"  {i+1}. Score: {result.get('score', 'N/A')}")
            print(f"     Text: {result.get('text', '')[:100]}...")

        # Test 3: Retriever
        print("\n🔍 Testing PineconeRetriever...")
        retriever = PineconeRetriever(
            company_id="UrbanPiper",
            pinecone_manager=pinecone_manager
        )
        docs = retriever._get_relevant_documents("Urban Piper")
        # Test 4: Check document content
        print("\n� Checking Document Content in Pinecone...")
        # Get a sample document from Pinecone to see what content is actually stored
        sample_results = pinecone_manager.query_company_documents(
            company_id="UrbanPiper",
            query="Urban",  # Very broad query to get some content
            k=1
        )

        # Test 5: Simulate actual API query
        print("\n🔍 Testing Full RAG Chain Query...")
        try:
            from services.embedding_service import embedding_service

            # Test the same query that might be causing issues
            test_query = "What is Urban Piper?"  # Common query that should work

            print(f"Testing query: '{test_query}'")
            # Run async query in a new event loop
            import asyncio
            result = asyncio.run(embedding_service.query_company(
                company_id="UrbanPiper",
                query=test_query,
                chat_history=[]
            ))

            print(f"Response: {result.get('response', 'No response')}")
            print(f"Sources: {result.get('sources', [])}")

        except Exception as e:
            print(f"❌ RAG Chain test failed: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"❌ Debug test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
