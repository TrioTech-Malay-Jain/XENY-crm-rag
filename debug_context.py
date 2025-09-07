#!/usr/bin/env python3
"""
Debug script to see what context is actually being passed to the AI
"""
import asyncio
from services.embedding_service import embedding_service
from db.pinecone_manager import pinecone_manager

async def debug_context():
    """Debug what context is being retrieved and passed to the AI"""

    company_id = "UrbanPiper"
    query = "What is UrbanPiper?"

    print("🔍 Debugging context retrieval...")
    print("=" * 60)

    # Get the retriever
    retriever = embedding_service._create_rag_chain(company_id)
    if not retriever:
        print("❌ Could not create RAG chain")
        return

    # Get the retriever directly
    from services.embedding_service import PineconeRetriever

    pinecone_retriever = PineconeRetriever(
        company_id=company_id,
        pinecone_manager=pinecone_manager
    )

    # Get documents directly
    documents = pinecone_retriever._get_relevant_documents(query)

    print(f"Retrieved {len(documents)} documents:")
    print("-" * 40)

    total_content = ""
    for i, doc in enumerate(documents):
        content = doc.page_content
        total_content += content + "\n\n"

        print(f"Document {i+1}:")
        print(f"Length: {len(content)} characters")
        print(f"Content preview: {content[:300]}...")
        print(f"Metadata: {doc.metadata}")
        print("-" * 30)

    print("\n📝 Full context that would be passed to AI:")
    print("=" * 60)
    print(total_content[:2000] + "..." if len(total_content) > 2000 else total_content)

    # Now let's see what the system prompt looks like
    system_prompt = embedding_service._get_system_prompt(company_id)
    print("\n🤖 System Prompt:")
    print("=" * 60)
    print(system_prompt[:1000] + "..." if len(system_prompt) > 1000 else system_prompt)

if __name__ == "__main__":
    asyncio.run(debug_context())
