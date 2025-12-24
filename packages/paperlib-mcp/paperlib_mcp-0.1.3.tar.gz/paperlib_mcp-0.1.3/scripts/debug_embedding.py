#!/usr/bin/env python3
"""Embedding pipeline diagnostic script"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def check_settings():
    """Check if settings are loaded correctly"""
    print("=" * 60)
    print("Step 1: Checking Settings")
    print("=" * 60)
    
    from paperlib_mcp.settings import get_settings
    settings = get_settings()
    
    print(f"  OpenRouter API Key: {'[SET]' if settings.openrouter_api_key else '[NOT SET ❌]'}")
    if settings.openrouter_api_key:
        print(f"    Key starts with: {settings.openrouter_api_key[:10]}...")
    print(f"  OpenRouter Base URL: {settings.openrouter_base_url}")
    print(f"  Embedding Model: {settings.embedding_model}")
    print(f"  Embedding Batch Size: {settings.embedding_batch_size}")
    print()
    
    return settings.openrouter_api_key != ""


def check_direct_api():
    """Test a direct API call to OpenRouter embeddings endpoint"""
    print("=" * 60)
    print("Step 2: Testing Direct API Call")
    print("=" * 60)
    
    from paperlib_mcp.settings import get_settings
    import httpx
    
    settings = get_settings()
    
    if not settings.openrouter_api_key:
        print("  ❌ Cannot test - API key not set")
        return False
    
    url = f"{settings.openrouter_base_url}/embeddings"
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": settings.embedding_model,
        "input": ["This is a test text for embedding"],
    }
    
    print(f"  URL: {url}")
    print(f"  Model: {settings.embedding_model}")
    print(f"  Sending request...")
    
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload, headers=headers)
            print(f"  Status Code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"  ❌ Error Response: {response.text}")
                return False
            
            data = response.json()
            
            if "data" not in data:
                print(f"  ❌ Missing 'data' field: {data}")
                return False
            
            embedding = data["data"][0]["embedding"]
            print(f"  ✅ Success! Got embedding with {len(embedding)} dimensions")
            print(f"  First few values: {embedding[:5]}")
            return True
            
    except Exception as e:
        print(f"  ❌ Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_embedding_module():
    """Test the embeddings module functions"""
    print("=" * 60)
    print("Step 3: Testing embeddings.py module")
    print("=" * 60)
    
    try:
        from paperlib_mcp.embeddings import get_embedding, check_embeddings_api
        
        # First check API availability
        api_status = check_embeddings_api()
        print(f"  API Check Result: {api_status}")
        
        if not api_status.get("available"):
            print(f"  ❌ API not available: {api_status.get('error')}")
            return False
        
        # Test single embedding
        test_text = "This is a test text"
        print(f"  Testing get_embedding('{test_text}')")
        
        embedding = get_embedding(test_text)
        print(f"  ✅ Got embedding with {len(embedding)} dimensions")
        return True
        
    except Exception as e:
        print(f"  ❌ Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def check_async_embedding():
    """Test async embedding functions"""
    print("=" * 60)
    print("Step 4: Testing async embeddings")
    print("=" * 60)
    
    try:
        from paperlib_mcp.embeddings import aget_embeddings_batch, aget_embeddings_chunked
        
        test_texts = ["Text one", "Text two", "Text three"]
        print(f"  Testing aget_embeddings_batch with {len(test_texts)} texts")
        
        embeddings = await aget_embeddings_batch(test_texts)
        print(f"  ✅ Got {len(embeddings)} embeddings")
        
        # Test chunked
        many_texts = [f"Text number {i}" for i in range(10)]
        print(f"  Testing aget_embeddings_chunked with {len(many_texts)} texts")
        
        embeddings = await aget_embeddings_chunked(many_texts, batch_size=3)
        print(f"  ✅ Got {len(embeddings)} embeddings (chunked)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_database_connection():
    """Check database connectivity"""
    print("=" * 60)
    print("Step 5: Checking Database Connection")
    print("=" * 60)
    
    try:
        from paperlib_mcp.db import query_one
        
        result = query_one("SELECT 1 as test")
        print(f"  ✅ Database connection OK: {result}")
        
        # Check for documents and chunks
        doc_count = query_one("SELECT COUNT(*) as count FROM documents")
        chunk_count = query_one("SELECT COUNT(*) as count FROM chunks")
        embed_count = query_one("SELECT COUNT(*) as count FROM chunk_embeddings")
        
        print(f"  Documents: {doc_count['count']}")
        print(f"  Chunks: {chunk_count['count']}")
        print(f"  Embeddings: {embed_count['count']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_import_pdf_flow():
    """Check the import_pdf code path"""
    print("=" * 60)
    print("Step 6: Checking import_pdf code path")
    print("=" * 60)
    
    try:
        from paperlib_mcp.tools.import_pdf import import_pdf_run, IngestStage
        
        print("  ✅ import_pdf_run imported successfully")
        print(f"  IngestStage values: {[s.value for s in IngestStage]}")
        
        # Check if aget_embeddings_chunked is imported correctly
        from paperlib_mcp.embeddings import aget_embeddings_chunked
        print("  ✅ aget_embeddings_chunked is available")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("\n" + "=" * 60)
    print("EMBEDDING PIPELINE DIAGNOSTIC")
    print("=" * 60 + "\n")
    
    results = []
    
    # Step 1: Settings
    results.append(("Settings", check_settings()))
    
    if not results[-1][1]:
        print("\n⚠️  CRITICAL: OpenRouter API key not configured!")
        print("   Please set OPENROUTER_API_KEY in your .env file")
        return
    
    # Step 2: Direct API
    results.append(("Direct API", check_direct_api()))
    
    # Step 3: Embedding module
    results.append(("Embedding Module", check_embedding_module()))
    
    # Step 4: Async embedding
    results.append(("Async Embedding", await check_async_embedding()))
    
    # Step 5: Database
    results.append(("Database", check_database_connection()))
    
    # Step 6: Import flow
    results.append(("Import Flow", check_import_pdf_flow()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
    
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n✅ All checks passed! The embedding pipeline should be working.")
        print("   If documents still aren't embedding, check if they already exist")
        print("   with complete embeddings (use force=True to re-import).")
    else:
        print("\n❌ Some checks failed. Review the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
