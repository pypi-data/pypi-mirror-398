"""
SanTOK Inference Pipeline

End-to-end pipeline for processing text through SanTOK,
generating embeddings, and performing inference/search.
"""

import numpy as np
from typing import List, Dict, Optional, Union
import sys
import os

# Try different import paths for TextTokenizer
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
try:
    from src.core.core_tokenizer import TextTokenizer
except ImportError:
    try:
        from core.core_tokenizer import TextTokenizer
    except ImportError:
        # Fallback - TextTokenizer may not exist, use tokenize_text instead
        from src.core.core_tokenizer import tokenize_text
        class TextTokenizer:
            def tokenize(self, text):
                return tokenize_text(text, 'space')

from .embedding_generator import SanTOKEmbeddingGenerator
from .vector_store import SanTOKVectorStore


class SanTOKInferencePipeline:
    """
    Complete inference pipeline using SanTOK embeddings.
    
    Flow:
    1. Tokenize text with SanTOK
    2. Generate embeddings for tokens
    3. Store in vector database
    4. Enable similarity search and retrieval
    """
    
    def __init__(
        self,
        embedding_generator: SanTOKEmbeddingGenerator,
        vector_store: SanTOKVectorStore,
        tokenizer: Optional[TextTokenizer] = None,
        tokenizer_seed: int = 42,
        embedding_bit: bool = False
    ):
        """
        Initialize inference pipeline.
        
        Args:
            embedding_generator: SanTOKEmbeddingGenerator instance
            vector_store: SanTOKVectorStore instance
            tokenizer: Optional TextTokenizer (creates new if None)
            tokenizer_seed: Seed for tokenizer
            embedding_bit: Embedding bit flag for tokenizer
        """
        self.embedding_generator = embedding_generator
        self.vector_store = vector_store
        
        if tokenizer is None:
            self.tokenizer = TextTokenizer(
                seed=tokenizer_seed,
                embedding_bit=embedding_bit
            )
        else:
            self.tokenizer = tokenizer
    
    def process_text(
        self,
        text: str,
        store: bool = True,
        stream_type: Optional[str] = None
    ) -> Dict:
        """
        Process text through complete pipeline.
        
        Args:
            text: Input text to process
            store: Whether to store in vector database
            stream_type: Specific tokenization stream to use (None = all)
        
        Returns:
            Dictionary with tokens, embeddings, and metadata
        """
        # Step 1: Tokenize with SanTOK
        streams = self.tokenizer.build(text)
        
        # Step 2: Collect tokens (from all streams or specific one)
        all_tokens = []
        if stream_type:
            if stream_type in streams:
                all_tokens = streams[stream_type].tokens
            else:
                raise ValueError(f"Stream type '{stream_type}' not found")
        else:
            # Collect from all streams
            for stream_name, token_stream in streams.items():
                all_tokens.extend(token_stream.tokens)
        
        if not all_tokens:
            return {
                "tokens": [],
                "embeddings": np.array([]),
                "streams": {},
                "text": text
            }
        
        # Step 3: Generate embeddings
        embeddings = self.embedding_generator.generate_batch(all_tokens)
        
        # Step 4: Store in vector database if requested
        if store:
            self.vector_store.add_tokens(all_tokens, embeddings)
        
        return {
            "tokens": all_tokens,
            "embeddings": embeddings,
            "streams": {name: len(stream.tokens) for name, stream in streams.items()},
            "text": text,
            "num_tokens": len(all_tokens)
        }
    
    def similarity_search(
        self,
        query_text: str,
        top_k: int = 10,
        stream_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for similar tokens using query text.
        
        Args:
            query_text: Query text to search for
            top_k: Number of results to return
            stream_type: Specific stream to use for query (None = all)
        
        Returns:
            List of similar tokens with distances
        """
        # Tokenize query
        query_streams = self.tokenizer.build(query_text)
        
        # Collect query tokens
        query_tokens = []
        if stream_type:
            if stream_type in query_streams:
                query_tokens = query_streams[stream_type].tokens
            else:
                return []
        else:
            for stream_name, token_stream in query_streams.items():
                query_tokens.extend(token_stream.tokens)
        
        if not query_tokens:
            return []
        
        # Generate query embeddings
        query_embeddings = self.embedding_generator.generate_batch(query_tokens)
        
        # Average query embeddings to get single query vector
        query_embedding = np.mean(query_embeddings, axis=0)
        
        # Search vector database
        results = self.vector_store.search(query_embedding, top_k=top_k)
        
        return results
    
    def get_document_embedding(
        self,
        text: str,
        method: str = "mean"
    ) -> np.ndarray:
        """
        Get document-level embedding from text.
        
        Args:
            text: Input text
            method: Aggregation method ("mean", "max", "sum", "first")
        
        Returns:
            Document embedding vector
        """
        result = self.process_text(text, store=False)
        
        if len(result["embeddings"]) == 0:
            return np.zeros(self.embedding_generator.embedding_dim)
        
        embeddings = result["embeddings"]
        
        if method == "mean":
            return np.mean(embeddings, axis=0)
        elif method == "max":
            return np.max(embeddings, axis=0)
        elif method == "sum":
            return np.sum(embeddings, axis=0)
        elif method == "first":
            return embeddings[0]
        else:
            raise ValueError(f"Unknown aggregation method: {method}")
    
    def batch_process(
        self,
        texts: List[str],
        store: bool = True,
        show_progress: bool = False
    ) -> List[Dict]:
        """
        Process multiple texts in batch.
        
        Args:
            texts: List of texts to process
            store: Whether to store in vector database
            show_progress: Show progress bar
        
        Returns:
            List of processing results
        """
        results = []
        for i, text in enumerate(texts):
            if show_progress:
                print(f"Processing {i+1}/{len(texts)}: {text[:50]}...")
            result = self.process_text(text, store=store)
            results.append(result)
        return results
    
    def find_similar_documents(
        self,
        query_text: str,
        document_texts: List[str],
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find similar documents from a list.
        
        Args:
            query_text: Query text
            document_texts: List of documents to search
            top_k: Number of results
        
        Returns:
            List of similar documents with scores
        """
        # Get query embedding
        query_emb = self.get_document_embedding(query_text)
        
        # Get document embeddings
        doc_embeddings = []
        for doc_text in document_texts:
            doc_emb = self.get_document_embedding(doc_text)
            doc_embeddings.append(doc_emb)
        
        doc_embeddings = np.array(doc_embeddings)
        
        # Compute similarities (cosine similarity)
        query_norm = query_emb / (np.linalg.norm(query_emb) + 1e-8)
        doc_norms = doc_embeddings / (np.linalg.norm(doc_embeddings, axis=1, keepdims=True) + 1e-8)
        similarities = doc_norms @ query_norm
        
        # Get top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                "document": document_texts[idx],
                "similarity": float(similarities[idx]),
                "index": int(idx)
            })
        
        return results