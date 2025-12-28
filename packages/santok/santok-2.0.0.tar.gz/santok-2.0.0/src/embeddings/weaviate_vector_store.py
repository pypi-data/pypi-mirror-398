"""
Weaviate Vector Store for SanTOK Embeddings

Cloud-based vector database integration using Weaviate.
Inherits from SanTOKVectorStore for consistency with other vector stores.
"""

import os
import numpy as np
from typing import List, Dict, Optional, Any
import warnings
import uuid
import sys

from .vector_store import SanTOKVectorStore

# Try importing weaviate (module-level check - may fail in some import contexts)
# Runtime check in __init__ is more reliable
try:
    if 'weaviate' in sys.modules:
        weaviate = sys.modules['weaviate']
        from weaviate.classes.init import Auth
        from dotenv import load_dotenv
        WEAVIATE_AVAILABLE = True
    else:
        import weaviate
        from weaviate.classes.init import Auth
        from dotenv import load_dotenv
        WEAVIATE_AVAILABLE = True
except (ImportError, AttributeError):
    WEAVIATE_AVAILABLE = False


class WeaviateVectorStore(SanTOKVectorStore):
    """
    Weaviate-based vector store for SanTOK.
    
    Advantages:
    - Cloud-based (accessible from anywhere)
    - Production-ready
    - Built-in GraphQL API
    - Good metadata filtering
    - Scalable
    """
    
    def __init__(
        self,
        collection_name: str = "SanTOK_Token",
        embedding_dim: int = 768,
        weaviate_url: Optional[str] = None,
        weaviate_api_key: Optional[str] = None,
        auto_load_env: bool = True,
        persist_directory: Optional[str] = None  # For compatibility with base class
    ):
        """
        Initialize Weaviate vector store.
        
        Args:
            collection_name: Name of the Weaviate class (collection)
            embedding_dim: Dimension of embeddings (default 768)
            weaviate_url: Weaviate cluster URL (or from env)
            weaviate_api_key: Weaviate API key (or from env)
            auto_load_env: Auto-load .env file for credentials
            persist_directory: Ignored (for compatibility with base class)
        """
        # Initialize base class
        super().__init__(
            backend="weaviate",
            collection_name=collection_name,
            embedding_dim=embedding_dim,
            persist_directory=persist_directory
        )
        
        # Check at runtime (more reliable than module-level check)
        try:
            if 'weaviate' in sys.modules:
                weaviate = sys.modules['weaviate']
                from weaviate.classes.init import Auth
            else:
                import weaviate
                from weaviate.classes.init import Auth
        except (ImportError, AttributeError):
            raise ImportError(
                "weaviate-client required. Install with: pip install weaviate-client"
            )
        
        # Load environment variables if requested
        if auto_load_env:
            load_dotenv()
        
        # Get credentials from args or environment
        self.weaviate_url = weaviate_url or os.getenv("WEAVIATE_URL")
        self.weaviate_api_key = weaviate_api_key or os.getenv("WEAVIATE_API_KEY")
        
        # Validate credentials
        if not self.weaviate_url:
            raise ValueError(
                "WEAVIATE_URL not provided. Set it as argument or in .env file."
            )
        if not self.weaviate_api_key:
            raise ValueError(
                "WEAVIATE_API_KEY not provided. Set it as argument or in .env file."
            )
        
        # Initialize connection
        self._init_weaviate()
        self._token_counter = 0
    
    def _init_weaviate(self):
        """Initialize Weaviate client and create/verify collection."""
        # Import here to ensure it's available (use sys.modules if already imported)
        import sys
        if 'weaviate' in sys.modules:
            weaviate = sys.modules['weaviate']
            from weaviate.classes.init import Auth
        else:
            import weaviate
            from weaviate.classes.init import Auth
        
        # Connect to Weaviate Cloud
        self.client = weaviate.connect_to_weaviate_cloud(
            cluster_url=self.weaviate_url,
            auth_credentials=Auth.api_key(self.weaviate_api_key),
        )
        
        # Check if ready
        if not self.client.is_ready():
            raise ConnectionError("Failed to connect to Weaviate")
        
        # Create or get collection (class in Weaviate)
        self._create_collection()
    
    def _create_collection(self):
        """Create Weaviate collection if it doesn't exist."""
        try:
            # Check if collection exists
            if self.client.collections.exists(self.collection_name):
                self.collection = self.client.collections.get(self.collection_name)
            else:
                # Create new collection
                from weaviate.classes.config import Configure, Property, DataType
                
                self.collection = self.client.collections.create(
                    name=self.collection_name,
                    vectorizer_config=Configure.Vectorizer.none(),  # We provide vectors
                    properties=[
                        Property(name="text", data_type=DataType.TEXT),
                        Property(name="stream", data_type=DataType.TEXT),
                        Property(name="uid", data_type=DataType.TEXT),
                        Property(name="frontend", data_type=DataType.TEXT),
                        Property(name="index", data_type=DataType.INT),
                        Property(name="content_id", data_type=DataType.TEXT),
                        Property(name="global_id", data_type=DataType.TEXT),
                    ]
                )
        except Exception as e:
            # If collection exists, just get it
            if "already exists" in str(e).lower() or "conflict" in str(e).lower():
                self.collection = self.client.collections.get(self.collection_name)
            else:
                raise
    
    def add_tokens(
        self,
        token_records: List,
        embeddings: np.ndarray,
        metadata: Optional[List[Dict]] = None,
        skip_duplicates: bool = True
    ):
        """
        Add tokens and embeddings to Weaviate.
        
        Args:
            token_records: List of token records
            embeddings: Numpy array of embeddings
            metadata: Optional list of metadata dicts
            skip_duplicates: If True, skip tokens that already exist (based on text+uid)
        """
        if len(token_records) != len(embeddings):
            raise ValueError("token_records and embeddings must have same length")
        
        # Prepare data for batch insert
        objects_to_insert = []
        skipped_count = 0
        
        # If skip_duplicates, check existing tokens first (batch query for efficiency)
        existing_uuids = set()
        if skip_duplicates:
            try:
                # Query for existing tokens by text+uid to find duplicates
                batch_size = 100
                for batch_start in range(0, len(token_records), batch_size):
                    batch_end = min(batch_start + batch_size, len(token_records))
                    batch_tokens = token_records[batch_start:batch_end]
                    
                    # Generate deterministic UUIDs for this batch
                    batch_uuids = []
                    for token in batch_tokens:
                        token_text = getattr(token, 'text', '')
                        token_uid = str(getattr(token, 'uid', ''))
                        unique_string = f"{token_text}_{token_uid}"
                        token_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, unique_string)
                        batch_uuids.append(str(token_uuid))
                    
                    # Check which UUIDs already exist
                    try:
                        existing = self.collection.data.get_many(ids=batch_uuids)
                        for obj in existing.objects:
                            existing_uuids.add(str(obj.uuid))
                    except Exception:
                        pass
            except Exception as e:
                print(f"[WARNING] Deduplication check failed: {e}. Continuing with insert.")
        
        for i, token in enumerate(token_records):
            token_text = getattr(token, 'text', '')
            token_uid = str(getattr(token, 'uid', ''))
            token_global_id = str(getattr(token, 'global_id', ''))
            
            # Generate deterministic UUID
            if skip_duplicates:
                unique_string = f"{token_text}_{token_uid}"
            else:
                unique_string = f"{token_text}_{token_uid}_{token_global_id}_{self._token_counter + i}"
            
            token_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, unique_string)
            uuid_str = str(token_uuid)
            
            # Skip if duplicate exists
            if skip_duplicates and uuid_str in existing_uuids:
                skipped_count += 1
                continue
            
            # Get embedding
            embedding = embeddings[i]
            if embedding.ndim > 1:
                embedding = embedding.reshape(-1)
            
            # Create metadata if not provided
            if metadata is None:
                token_metadata = {
                    "text": token_text,
                    "stream": getattr(token, 'stream', ''),
                    "uid": token_uid,
                    "frontend": str(getattr(token, 'frontend', '')),
                    "index": int(getattr(token, 'index', 0)),
                    "content_id": str(getattr(token, 'content_id', '')),
                    "global_id": token_global_id
                }
            else:
                token_metadata = metadata[i]
            
            # Create Weaviate object
            from weaviate.classes.data import DataObject
            
            objects_to_insert.append(
                DataObject(
                    uuid=uuid_str,
                    properties=token_metadata,
                    vector=embedding.tolist()
                )
            )
        
        # Batch insert
        if objects_to_insert:
            try:
                self.collection.data.insert_many(objects_to_insert)
                self._token_counter += len(objects_to_insert)
                if skipped_count > 0:
                    print(f"[INFO] Inserted {len(objects_to_insert):,} new tokens, skipped {skipped_count:,} duplicates")
            except Exception as e:
                # If batch insert fails, try individual inserts
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'conflict' in error_msg:
                    inserted = 0
                    for obj in objects_to_insert:
                        try:
                            self.collection.data.insert(obj)
                            inserted += 1
                        except Exception:
                            skipped_count += 1
                    self._token_counter += inserted
                    if skipped_count > 0:
                        print(f"[INFO] Inserted {inserted:,} new tokens, skipped {skipped_count:,} duplicates")
                else:
                    raise
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filter: Optional[Dict] = None
    ) -> List[Dict]:
        """Search Weaviate for similar tokens."""
        # Ensure query is 1D
        if query_embedding.ndim > 1:
            query_embedding = query_embedding.reshape(-1)
        
        # Convert filter to Weaviate format if provided
        weaviate_filter = None
        if filter:
            weaviate_filter = self._convert_filter(filter)
        
        # Perform search
        from weaviate.classes.query import MetadataQuery
        results = self.collection.query.near_vector(
            near_vector=query_embedding.tolist(),
            limit=top_k,
            return_metadata=MetadataQuery(distance=True)
        )
        
        # Format results
        formatted_results = []
        for obj in results.objects:
            formatted_results.append({
                "id": str(obj.uuid),
                "text": obj.properties.get("text", ""),
                "metadata": {
                    "stream": obj.properties.get("stream", ""),
                    "uid": obj.properties.get("uid", ""),
                    "frontend": obj.properties.get("frontend", ""),
                    "index": obj.properties.get("index", 0),
                    "content_id": obj.properties.get("content_id", ""),
                    "global_id": obj.properties.get("global_id", "")
                },
                "distance": obj.metadata.distance if obj.metadata else None
            })
        
        return formatted_results
    
    def _convert_filter(self, filter_dict: Dict) -> Optional[Any]:
        """Convert simple filter dict to Weaviate filter format."""
        # Basic filter conversion - can be extended
        return None
    
    def get_token_embedding(self, token_id: str) -> Optional[np.ndarray]:
        """Retrieve embedding by token ID."""
        try:
            obj = self.collection.data.fetch_by_id(token_id)
            if obj and hasattr(obj, 'vector'):
                return np.array(obj.vector)
        except Exception:
            pass
        return None
    
    def close(self):
        """Close Weaviate connection."""
        if hasattr(self, 'client') and self.client:
            self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection."""
        self.close()