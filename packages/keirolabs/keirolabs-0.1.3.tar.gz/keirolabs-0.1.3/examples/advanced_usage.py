"""
Advanced usage examples for KEIRO SDK
"""
import os
from keirolabs import Keiro
from keirolabs.exceptions import (
    KeiroAuthError,
    KeiroRateLimitError,
    KeiroConnectionError,
    KeiroValidationError,
)

def example_error_handling():
    """Demonstrate proper error handling"""
    print("\n🛡️  Error Handling Example")
    print("-" * 60)
    
    client = Keiro(
        api_key=os.getenv("KEIRO_API_KEY", "your-key"),
        base_url="http://localhost:8000/api"
    )
    
    try:
        result = client.search("test query")
        print(f"✓ Search successful: {result}")
        
    except KeiroAuthError:
        print("❌ Authentication failed - Invalid API key")
        
    except KeiroRateLimitError:
        print("❌ Out of credits - Please add more credits")
        
    except KeiroValidationError as e:
        print(f"❌ Validation error: {e}")
        
    except KeiroConnectionError as e:
        print(f"❌ Connection failed: {e}")
        print("  → Is the server running on localhost:8000?")

def example_context_manager():
    """Demonstrate context manager usage"""
    print("\n🔧 Context Manager Example")
    print("-" * 60)
    
    with Keiro(
        api_key=os.getenv("KEIRO_API_KEY"),
        base_url="http://localhost:8000/api"
    ) as client:
        result = client.search("context manager test")
        print(f"✓ Search completed: {result}")
    
    print("✓ Session automatically closed")

def example_environment_switching():
    """Demonstrate switching between environments"""
    print("\n🌍 Environment Switching Example")
    print("-" * 60)
    
    client = Keiro(
        api_key=os.getenv("KEIRO_API_KEY"),
        base_url="http://localhost:8000/api"
    )
    
    print(f"Current base URL: {client.base_url}")
    
    # Switch to production
    client.set_base_url("https://api.keiro.com/api")
    print(f"Updated base URL: {client.base_url}")
    
    # Switch back to development
    client.set_base_url("http://localhost:8000/api")
    print(f"Back to dev URL: {client.base_url}")

def example_batch_operations():
    """Demonstrate batch operations"""
    print("\n📦 Batch Operations Example")
    print("-" * 60)
    
    client = Keiro(
        api_key=os.getenv("KEIRO_API_KEY"),
        base_url="http://localhost:8000/api"
    )
    
    queries = [
        "What is Python?",
        "What is JavaScript?",
        "What is TypeScript?",
    ]
    
    results = []
    
    try:
        for i, query in enumerate(queries, 1):
            print(f"\nProcessing query {i}/{len(queries)}: {query}")
            result = client.search(query)
            results.append(result)
            print(f"  ✓ Credits remaining: {result.get('creditsRemaining')}")
        
        print(f"\n✓ Successfully processed {len(results)} queries")
        
    except KeiroRateLimitError:
        print(f"\n❌ Ran out of credits after {len(results)} queries")
        print(f"  → Successfully processed: {results}")

def example_web_crawler():
    """Demonstrate web crawler usage"""
    print("\n🕷️  Web Crawler Example")
    print("-" * 60)
    
    client = Keiro(
        api_key=os.getenv("KEIRO_API_KEY"),
        base_url="http://localhost:8000/api"
    )
    
    url = "https://example.com"
    
    try:
        print(f"Crawling: {url}")
        result = client.web_crawler(url)
        print(f"✓ Crawl completed")
        print(f"  Data: {result}")
    except Exception as e:
        print(f"❌ Crawl failed: {e}")

def main():
    """Run all advanced examples"""
    print("=" * 60)
    print("KEIRO SDK - Advanced Examples")
    print("=" * 60)
    
    # Run examples
    example_error_handling()
    example_context_manager()
    example_environment_switching()
    example_batch_operations()
    example_web_crawler()
    
    print("\n" + "=" * 60)
    print("✅ All advanced examples completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
