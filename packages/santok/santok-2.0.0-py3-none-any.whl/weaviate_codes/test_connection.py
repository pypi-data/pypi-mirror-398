"""
Simple test script to verify Weaviate connection works.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test basic connection first
try:
    import weaviate
    from weaviate.classes.init import Auth
    
    weaviate_url = os.getenv("WEAVIATE_URL")
    weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
    
    if not weaviate_url:
        print("❌ WEAVIATE_URL not found in .env file")
        sys.exit(1)
    
    if not weaviate_api_key:
        print("❌ WEAVIATE_API_KEY not found in .env file")
        sys.exit(1)
    
    print(f"🔗 Connecting to Weaviate at: {weaviate_url}")
    
    # Connect
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key),
    )
    
    try:
        if client.is_ready():
            print("✅ Connection successful!")
            print(f"✅ Weaviate is ready")
        else:
            print("❌ Connection failed - Weaviate not ready")
    finally:
        client.close()
        print("✅ Connection closed properly")
        
except ImportError:
    print("❌ weaviate-client not installed")
    print("   Install with: pip install weaviate-client")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)