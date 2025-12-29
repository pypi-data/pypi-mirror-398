"""
Basic usage example for KEIRO SDK
"""
import os
from dotenv import load_dotenv
from keirolabs import Keiro
from keirolabs.exceptions import KeiroError

# Load environment variables from .env file
load_dotenv()

def main():
    # Get API key from environment variable
    api_key = os.getenv("KEIRO_API_KEY", "your-api-key-here")
    
    # Initialize client for local development
    client = Keiro(
        api_key=api_key,
        base_url="http://localhost:8000/api"
    )
    
    print("=" * 60)
    print("KEIRO SDK - Basic Examples")
    print("=" * 60)
    
    try:
        # Example 1: Health Check
        print("\n1️⃣  Health Check")
        print("-" * 60)
        health = client.health_check()
        print(f"✓ API Status: {health}")
        
        # Example 2: Basic Search
        print("\n2️⃣  Basic Search (1 credit)")
        print("-" * 60)
        search_query = "What is machine learning?"
        result = client.search(search_query)
        print(f"Query: {search_query}")
        print(f"Results: {result.get('data', {})}")
        print(f"Credits Remaining: {result.get('creditsRemaining')}")
        
        # Example 3: Answer Generation
        print("\n3️⃣  Answer Generation (5 credits)")
        print("-" * 60)
        question = "Explain how neural networks work"
        answer = client.answer(question)
        print(f"Question: {question}")
        print(f"Answer: {answer.get('data', {})}")
        print(f"Credits Remaining: {answer.get('creditsRemaining')}")
        
        # Example 4: Research
        print("\n4️⃣  Research")
        print("-" * 60)
        topic = "Latest AI developments"
        research = client.research(topic)
        print(f"Topic: {topic}")
        print(f"Research Results: {research.get('data', {})}")
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
        
    except KeiroError as e:
        print(f"\n❌ Error: {e}")
        print("Make sure:")
        print("  1. Your API key is set correctly")
        print("  2. The server is running on localhost:8000")
        print("  3. You have sufficient credits")

if __name__ == "__main__":
    main()
