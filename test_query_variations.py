#!/usr/bin/env python3
"""
Test script to try different query variations and analyze responses
"""
import asyncio
import json
from services.embedding_service import embedding_service
from services.file_service import file_service

async def test_query_variations():
    """Test different query variations to see which ones work better"""

    company_id = "UrbanPiper"

    # Test queries with different variations
    test_queries = [
        # Basic queries
        "What is UrbanPiper?",
        "What is Urban Piper?",
        "Tell me about UrbanPiper",
        "What does UrbanPiper do?",

        # Variations with different spacing/case
        "what is urban piper?",
        "URBAN PIPER",
        "urbanpiper",

        # More specific queries that might be in the document
        "What services does UrbanPiper provide?",
        "What is UrbanPiper's business model?",
        "Tell me about UrbanPiper's platform",
        "What industries does UrbanPiper serve?",

        # Very specific queries
        "What is the UP knowledge base?",
        "What information is in the knowledge base?",
        "Can you summarize the document?",

        # Generic queries
        "What is this company?",
        "Give me an overview",
        "What do you know about this organization?"
    ]

    print("🧪 Testing different query variations for UrbanPiper...")
    print("=" * 60)

    results = []

    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}/{len(test_queries)}: '{query}'")
        print("-" * 40)

        try:
            # Test the query
            result = await embedding_service.query_company(
                company_id=company_id,
                query=query,
                chat_history=[]
            )

            response = result.get("response", "")
            sources = result.get("sources", [])

            print(f"Response: {response}")
            print(f"Sources: {sources}")

            # Analyze the response
            is_available = "This information is currently not available" not in response
            has_content = len(response.strip()) > 0 and response != "I couldn't find an answer to that."

            results.append({
                "query": query,
                "response": response,
                "sources": sources,
                "is_available": is_available,
                "has_content": has_content,
                "response_length": len(response)
            })

            # Color coding for quick visual feedback
            if is_available and has_content:
                print("✅ SUCCESS: Got meaningful response")
            elif has_content:
                print("⚠️  PARTIAL: Got response but marked as unavailable")
            else:
                print("❌ FAILED: No meaningful response")

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results.append({
                "query": query,
                "error": str(e),
                "is_available": False,
                "has_content": False
            })

    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    successful_queries = [r for r in results if r.get("is_available", False) and r.get("has_content", False)]
    partial_queries = [r for r in results if r.get("has_content", False) and not r.get("is_available", False)]
    failed_queries = [r for r in results if not r.get("has_content", False)]

    print(f"✅ Successful queries: {len(successful_queries)}/{len(results)}")
    print(f"⚠️  Partial queries: {len(partial_queries)}/{len(results)}")
    print(f"❌ Failed queries: {len(failed_queries)}/{len(results)}")

    if successful_queries:
        print("\n🎯 Successful queries:")
        for r in successful_queries:
            print(f"  • '{r['query']}' → {len(r['response'])} chars")

    if partial_queries:
        print("\n⚠️  Partial queries (got content but marked unavailable):")
        for r in partial_queries:
            print(f"  • '{r['query']}' → {len(r['response'])} chars")

    # Save detailed results
    with open("query_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n📄 Detailed results saved to query_test_results.json")
    return results

async def analyze_document_content():
    """Analyze what content is actually in the documents"""
    print("\n🔍 Analyzing document content...")
    print("=" * 60)

    company_id = "UrbanPiper"

    try:
        # Get file info
        files = file_service.list_company_files(company_id)
        print(f"Files for {company_id}: {len(files)}")

        for file_info in files:
            print(f"\n📄 File: {file_info.original_filename}")
            print(f"   ID: {file_info.file_id}")
            print(f"   Size: {file_info.size} bytes")
            print(f"   Created: {file_info.created_at}")

            # Try to load and preview document content
            try:
                file_path = file_service.get_file_path(company_id, file_info.filename)
                documents = file_service.load_document(file_path)

                if documents:
                    print(f"   Loaded {len(documents)} document chunks")

                    # Show first few chunks (first 500 chars each)
                    for i, doc in enumerate(documents[:3]):
                        content_preview = doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content
                        print(f"\n   Chunk {i+1} preview:")
                        print(f"   {content_preview}")
                        print(f"   (Metadata: {doc.metadata})")
                else:
                    print("   ❌ Could not load document content")

            except Exception as e:
                print(f"   ❌ Error loading document: {e}")

    except Exception as e:
        print(f"❌ Error analyzing documents: {e}")

async def test_pinecone_directly():
    """Test Pinecone directly to see what it returns"""
    print("\n🔍 Testing Pinecone directly...")
    print("=" * 60)

    from db.pinecone_manager import pinecone_manager

    test_queries = [
        "What is UrbanPiper?",
        "UrbanPiper",
        "company overview",
        "business model"
    ]

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            results = pinecone_manager.query_company_documents(
                company_id="UrbanPiper",
                query=query,
                k=5
            )

            print(f"Found {len(results)} results:")
            for i, result in enumerate(results):
                score = result.get("score", 0)
                text_preview = result.get("text", "")[:200] + "..." if len(result.get("text", "")) > 200 else result.get("text", "")
                metadata = result.get("metadata", {})

                print(f"  {i+1}. Score: {score:.3f}")
                print(f"     Text: {text_preview}")
                print(f"     Metadata: {metadata}")

        except Exception as e:
            print(f"❌ Error: {e}")

async def main():
    """Main test function"""
    print("🚀 Starting comprehensive query testing...")
    print("=" * 60)

    # Test 1: Analyze document content
    await analyze_document_content()

    # Test 2: Test Pinecone directly
    await test_pinecone_directly()

    # Test 3: Test different query variations
    await test_query_variations()

    print("\n🎉 Testing complete!")

if __name__ == "__main__":
    asyncio.run(main())
