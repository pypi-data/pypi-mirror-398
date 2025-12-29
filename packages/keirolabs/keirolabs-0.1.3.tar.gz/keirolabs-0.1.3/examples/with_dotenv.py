"""
Example using environment variables with python-dotenv
"""
import os
from dotenv import load_dotenv
from keirolabs import Keiro

# Load environment variables from .env file
load_dotenv()

def main():
    # Get configuration from environment variables
    api_key = os.getenv("KEIRO_API_KEY")
    base_url = os.getenv("KEIRO_BASE_URL", "http://localhost:8000/api")
    
    if not api_key:
        print("❌ Error: KEIRO_API_KEY not found in environment variables")
        print("\nCreate a .env file with:")
        print("KEIRO_API_KEY=your-api-key-here")
        print("KEIRO_BASE_URL=http://localhost:8000/api")
        return
    
    # Initialize client
    client = Keiro(api_key=api_key, base_url=base_url)
    
    print("=" * 60)
    print("KEIRO SDK - Environment Variables Example")
    print("=" * 60)
    print(f"\nBase URL: {base_url}")
    print(f"API Key: {api_key[:10]}...")
    
    try:
        # Test the connection
        health = client.health_check()
        print(f"\n✓ Connection successful!")
        print(f"Health check: {health}")
        
        # Perform a search
        result = client.search("test query")
        print(f"\n✓ Search successful!")
        print(f"Credits remaining: {result.get('creditsRemaining')}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
