"""
SanTOK Embedding Generator

Converts SanTOK TokenRecord objects into dense vector embeddings
suitable for ML inference and similarity search.
"""

import numpy as np
from typing import List, Dict, Optional, Union
import hashlib
import warnings
import os
from multiprocessing import Pool, cpu_count
from functools import partial

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    # Warning removed - handled by user choice in comprehensive example

try:
    from .semantic_trainer import SanTOKSemanticTrainer
    SEMANTIC_TRAINER_AVAILABLE = True
except ImportError:
    try:
        from semantic_trainer import SanTOKSemanticTrainer
        SEMANTIC_TRAINER_AVAILABLE = True
    except ImportError:
        SEMANTIC_TRAINER_AVAILABLE = False


# ============================================================================
# STANDALONE FUNCTIONS FOR MULTIPROCESSING (must be at module level)
# ============================================================================

def _int64_to_bytes_standalone(value: int) -> List[float]:
    """Convert 64-bit integer to 8 normalized bytes (standalone for multiprocessing)."""
    if value is None:
        value = 0
    try:
        value = int(value)
        bytes_val = value.to_bytes(8, byteorder='big', signed=False)
        return [b / 255.0 for b in bytes_val]
    except (ValueError, OverflowError, TypeError):
        return [0.0] * 8


def _stream_to_onehot_standalone(stream_name: str) -> np.ndarray:
    """Convert stream name to one-hot encoding (standalone for multiprocessing)."""
    streams = [
        "space", "word", "char", "grammar", "subword",
        "subword_bpe", "subword_syllable", "subword_frequency", "byte"
    ]
    onehot = np.zeros(len(streams), dtype=np.float32)
    if stream_name in streams:
        onehot[streams.index(stream_name)] = 1.0
    return onehot


def _extract_features_standalone(token):
    """Standalone feature extraction function for multiprocessing."""
    features = []
    
    # UID
    uid = getattr(token, 'uid', 0)
    uid_bytes = _int64_to_bytes_standalone(uid)
    features.extend(uid_bytes)
    
    # Frontend
    frontend_onehot = np.zeros(9, dtype=np.float32)
    frontend = getattr(token, 'frontend', 0)
    if 1 <= frontend <= 9:
        frontend_onehot[frontend - 1] = 1.0
    features.extend(frontend_onehot)
    
    # Backend huge
    backend_huge = getattr(token, 'backend_huge', 0)
    backend_bytes = _int64_to_bytes_standalone(backend_huge)
    features.extend(backend_bytes)
    
    # Content ID
    content_id = getattr(token, 'content_id', 0)
    content_id_norm = float(content_id) / 150000.0
    features.append(content_id_norm)
    
    # Global ID
    global_id = getattr(token, 'global_id', 0)
    global_bytes = _int64_to_bytes_standalone(global_id)
    features.extend(global_bytes)
    
    # Neighbor UIDs
    prev_uid = getattr(token, 'prev_uid', None)
    next_uid = getattr(token, 'next_uid', None)
    prev_bytes = _int64_to_bytes_standalone(prev_uid if prev_uid is not None else 0)
    next_bytes = _int64_to_bytes_standalone(next_uid if next_uid is not None else 0)
    features.extend(prev_bytes)
    features.extend(next_bytes)
    
    # Index
    index = getattr(token, 'index', 0)
    index_norm = float(index) / 10000.0
    features.append(index_norm)
    
    # Stream
    stream = getattr(token, 'stream', 'word')
    stream_onehot = _stream_to_onehot_standalone(stream)
    features.extend(stream_onehot)
    
    return np.array(features, dtype=np.float32)


def _extract_features_batch_worker(args):
    """
    Worker function for multiprocessing - extracts features and saves to disk.
    Returns file path instead of large array to avoid memory issues.
    """
    tokens_chunk, temp_file = args
    features_list = []
    for token in tokens_chunk:
        features = _extract_features_standalone(token)
        features_list.append(features)
    # Ensure float32 and save to disk immediately
    result = np.array(features_list, dtype=np.float32)
    # Save to temp file to avoid pickling large arrays
    np.save(temp_file, result)
    return temp_file  # Return file path instead of array


class SanTOKEmbeddingGenerator:
    """
    Generates embeddings from SanTOK TokenRecord objects.
    
    Supports multiple strategies:
    - feature_based: Deterministic embedding from SanTOK features
    - semantic: Self-trained semantic embeddings (NLP-understandable, NO pretrained models)
    - hybrid: Combines text embeddings with SanTOK features
    - hash: Fast hash-based embedding
    """
    
    def __init__(
        self,
        strategy: str = "feature_based",
        embedding_dim: int = 768,
        text_model: Optional[str] = None,
        feature_weights: Optional[Dict[str, float]] = None,
        random_seed: int = 42,
        semantic_model_path: Optional[str] = None,
        source_tag: Optional[str] = None,
        enable_source_tagging: bool = True
    ):
        """
        Initialize embedding generator.
        
        Args:
            strategy: One of ["feature_based", "semantic", "hybrid", "hash"]
            embedding_dim: Target embedding dimension (default: 768)
            text_model: Model name for text embeddings (required for hybrid)
            feature_weights: Custom weights for feature combination (hybrid only)
            random_seed: Random seed for reproducibility
            semantic_model_path: Path to trained semantic model (for semantic strategy)
            source_tag: Optional source tag for source map integration (e.g., "wikipedia", "arxiv")
            enable_source_tagging: Whether to enable source tagging in embeddings
        """
        self.strategy = strategy
        self.embedding_dim = embedding_dim
        self.text_model = text_model
        self.random_seed = random_seed
        self.source_tag = source_tag
        self.enable_source_tagging = enable_source_tagging
        np.random.seed(random_seed)
        
        # Initialize source map if source tagging is enabled
        if self.enable_source_tagging and self.source_tag:
            try:
                from src.santok_sources import get_source_map
                self.source_map = get_source_map()
                self.source_metadata = self.source_map.get_source_metadata(self.source_tag)
                if not self.source_metadata:
                    print(f"Warning: Source tag '{self.source_tag}' not found, disabling source tagging")
                    self.enable_source_tagging = False
                    self.source_map = None
                    self.source_metadata = None
            except ImportError:
                self.enable_source_tagging = False
                self.source_map = None
                self.source_metadata = None
        else:
            self.source_map = None
            self.source_metadata = None
        
        # Default feature weights for hybrid strategy
        self.feature_weights = feature_weights or {
            "text": 0.7,
            "features": 0.3
        }
        
        # Initialize semantic trainer if semantic strategy
        if strategy == "semantic":
            if not SEMANTIC_TRAINER_AVAILABLE:
                raise ImportError(
                    "Semantic trainer not available. "
                    "Make sure semantic_trainer.py is in the embeddings module."
                )
            self.semantic_trainer = SanTOKSemanticTrainer(embedding_dim=embedding_dim)
            if semantic_model_path and os.path.exists(semantic_model_path):
                self.semantic_trainer.load(semantic_model_path)
                print(f"✅ Loaded semantic model from {semantic_model_path}")
            else:
                print("⚠️  Semantic model not loaded. Train a model first or use feature_based strategy.")
        else:
            self.semantic_trainer = None
        
        # Initialize text model if hybrid strategy
        if strategy == "hybrid":
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise ImportError(
                    "sentence-transformers required for hybrid strategy. "
                    "Install with: pip install sentence-transformers"
                )
            if text_model is None:
                text_model = "sentence-transformers/all-MiniLM-L6-v2"
            self.text_embedder = SentenceTransformer(text_model)
            self.text_embedding_dim = self.text_embedder.get_sentence_embedding_dimension()
        else:
            self.text_embedder = None
            self.text_embedding_dim = None
        
        # Initialize projection matrix for feature-based embeddings
        self._projection_matrix = None
        self._feature_dim = None
    
    def generate(self, token_record, return_metadata: bool = False):
        """
        Generate embedding for a single token.
        
        Args:
            token_record: TokenRecord object from SanTOK or token dictionary
            return_metadata: If True, return dict with embedding and source metadata
            
        Returns:
            numpy array of shape (embedding_dim,) or dict with 'embedding' and 'source_metadata'
        """
        # Generate embedding based on strategy (always return float32 for memory efficiency)
        if self.strategy == "feature_based":
            embedding = self._feature_based_embedding(token_record).astype(np.float32)
        elif self.strategy == "semantic":
            embedding = self._semantic_embedding(token_record).astype(np.float32)
        elif self.strategy == "hybrid":
            embedding = self._hybrid_embedding(token_record).astype(np.float32)
        elif self.strategy == "hash":
            embedding = self._hash_embedding(token_record).astype(np.float32)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
        
        # Return with source metadata if requested and available
        if return_metadata and self.enable_source_tagging and self.source_metadata:
            return {
                "embedding": embedding,
                "source_metadata": self._get_source_metadata_dict()
            }
        
        return embedding
    
    def _get_source_metadata_dict(self):
        """
        Get source metadata dictionary for embedding results.
        
        Returns:
            Dictionary with source metadata
        """
        if not self.enable_source_tagging or not self.source_metadata:
            return None
        
        from datetime import datetime, timezone
        algorithm_id = f"{self.strategy}_embedding"
        
        return {
            "source_id": self.source_metadata.source_id,
            "source_tag": self.source_tag,
            "algorithm_id": algorithm_id,
            "strategy": self.strategy,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "weight": self.source_metadata.weight,
            "priority": self.source_metadata.priority,
            "category": self.source_metadata.category
        }
    
    def generate_batch(self, token_records: List, batch_size: int = 10000, return_metadata: bool = False):
        """
        Generate embeddings for multiple tokens in batches to avoid memory issues.
        
        Args:
            token_records: List of TokenRecord objects
            batch_size: Number of tokens to process at once (default: 10000)
            return_metadata: If True, return dict with embeddings and source metadata
            
        Returns:
            numpy array of shape (len(token_records), embedding_dim) as float32,
            or dict with 'embeddings' and 'source_metadata'
        """
        # Process in batches to avoid memory issues for large datasets
        # batch_size is already a parameter with default value
        
        if self.strategy == "hybrid" and self.text_embedder:
            # For hybrid, process in batches
            embeddings_list = []
            total = len(token_records)
            
            for i in range(0, total, batch_size):
                batch = token_records[i:i + batch_size]
                texts = [getattr(token, 'text', '') for token in batch]
                text_embeddings = self.text_embedder.encode(
                    texts,
                    convert_to_numpy=True,
                    show_progress_bar=False
                ).astype(np.float32)
                
                # Generate feature embeddings
                feature_embeddings = np.array([
                    self._feature_based_embedding(token)
                    for token in batch
                ], dtype=np.float32)
                
                # Combine
                combined = (
                    self.feature_weights["text"] * text_embeddings +
                    self.feature_weights["features"] * feature_embeddings
                ).astype(np.float32)
                
                # Normalize and project if needed
                if combined.shape[1] != self.embedding_dim:
                    combined = self._project_to_dim(combined, self.embedding_dim)
                
                embeddings_list.append(self._normalize_batch(combined))
                
                # Progress update for large batches
                if total > 100000 and (i + batch_size) % 100000 == 0:
                    print(f"  Processed {min(i + batch_size, total):,}/{total:,} tokens...")
            
            embeddings = np.vstack(embeddings_list)
            
            # Return with source metadata if requested
            if return_metadata and self.enable_source_tagging and self.source_metadata:
                return {
                    "embeddings": embeddings,
                    "source_metadata": self._get_source_metadata_dict()
                }
            
            return embeddings
        else:
            # VECTORIZED PROCESSING for speed - process features in batches!
            total = len(token_records)
            if total == 0:
                return np.array([], dtype=np.float32).reshape(0, self.embedding_dim)
            
            # For feature_based strategy, use vectorized batch processing
            if self.strategy == "feature_based":
                result = self._generate_batch_vectorized(token_records, batch_size, return_metadata)
            else:
                # For other strategies, use optimized sequential processing
                result = self._generate_batch_optimized(token_records, batch_size, return_metadata)
            
            # Return result (already includes metadata if requested)
            return result
    
    def _generate_batch_vectorized(self, token_records: List, batch_size: int, return_metadata: bool = False):
        """Vectorized batch processing for feature_based embeddings - MUCH faster!"""
        total = len(token_records)
        
        # Initialize projection matrix if needed (do this once)
        if self._projection_matrix is None:
            # Extract features from first token to get feature dimension
            sample_features = self._extract_features(token_records[0])
            self._feature_dim = len(sample_features)
            self._projection_matrix = np.random.randn(
                self._feature_dim, self.embedding_dim
            ).astype(np.float32)
            self._projection_matrix = self._projection_matrix / np.sqrt(self._feature_dim)
        
        # Process in large batches with vectorized operations
        embeddings_list = []
        processed = 0
        
        # Use multiprocessing for parallel feature extraction
        num_workers = min(cpu_count() - 1, 10)
        
        # Process in MUCH smaller chunks to avoid memory issues in multiprocessing
        # Multiprocessing pickles arrays when returning, so we need small chunks
        # Each chunk will be ~10k tokens max to avoid pickling large arrays
        chunk_size = min(10000, max(5000, total // (num_workers * 20)))  # Very small chunks to avoid pickling issues
        chunks = []
        temp_files = []
        import tempfile
        
        # Create temp files for each chunk
        for i in range(0, total, chunk_size):
            chunk = token_records[i:i + chunk_size]
            temp_file = os.path.join(tempfile.gettempdir(), f"santok_features_{i}_{os.getpid()}.npy")
            chunks.append((chunk, temp_file))
            temp_files.append(temp_file)
        
        print(f"  Using {num_workers} CPU cores, processing {len(chunks)} chunks...")
        print(f"  Chunk size: {chunk_size:,} tokens (to avoid memory issues in multiprocessing)")
        
        # Process chunks in parallel using module-level worker function
        # Ensure projection matrix is float32 before multiprocessing
        projection_matrix = self._projection_matrix.astype(np.float32)
        
        with Pool(processes=num_workers) as pool:
            for i, features_file in enumerate(pool.imap(_extract_features_batch_worker, chunks)):
                try:
                    # Load features from disk (saved by worker)
                    features_batch = np.load(features_file).astype(np.float32)
                    
                    # Vectorized projection: (batch_size, feature_dim) @ (feature_dim, embedding_dim)
                    embeddings_batch = features_batch @ projection_matrix
                    
                    # Ensure result is float32 (matrix multiplication might promote to float64)
                    embeddings_batch = embeddings_batch.astype(np.float32)
                    
                    # Vectorized normalization
                    norms = np.linalg.norm(embeddings_batch, axis=1, keepdims=True).astype(np.float32)
                    norms = np.where(norms > 1e-8, norms, 1.0).astype(np.float32)
                    embeddings_batch = (embeddings_batch / norms).astype(np.float32)
                    
                    embeddings_list.append(embeddings_batch)
                    processed += len(features_batch)
                    
                    # Progress update
                    if (i + 1) % 2 == 0 or i == len(chunks) - 1:
                        print(f"  Processed {processed:,}/{total:,} tokens ({(processed/total*100):.1f}%)...")
                    
                    # Cleanup
                    del features_batch
                    # Delete temp file
                    try:
                        os.remove(features_file)
                    except Exception:
                        pass
                    
                    if (i + 1) % 10 == 0:
                        import gc
                        gc.collect()
                except Exception as e:
                    print(f"  ⚠️  Error processing chunk {i+1}: {e}")
                    # Cleanup temp file
                    try:
                        if os.path.exists(features_file):
                            os.remove(features_file)
                    except Exception:
                        pass
                    continue
        
        # Cleanup any remaining temp files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass
        
        if len(embeddings_list) == 0:
            raise RuntimeError("No embeddings were generated. All chunks failed.")
        
        # Concatenate all results
        embeddings = np.vstack(embeddings_list)
        
        # Return with source metadata if requested
        if return_metadata and self.enable_source_tagging and self.source_metadata:
            return {
                "embeddings": embeddings,
                "source_metadata": self._get_source_metadata_dict()
            }
        
        return embeddings
    
    def _generate_batch_optimized(self, token_records: List, batch_size: int, return_metadata: bool = False):
        """Optimized batch processing for non-feature_based strategies"""
        total = len(token_records)
        embeddings_list = []
        
        # Process in batches
        for i in range(0, total, batch_size):
            batch = token_records[i:min(i + batch_size, total)]
            batch_embeddings = np.array(
                [self.generate(token, return_metadata=False) for token in batch],
                dtype=np.float32
            )
            embeddings_list.append(batch_embeddings)
            
            # Progress update
            if total > 100000 and (i + batch_size) % 100000 == 0:
                print(f"  Processed {min(i + batch_size, total):,}/{total:,} tokens...")
        
        embeddings = np.vstack(embeddings_list)
        
        # Return with source metadata if requested
        if return_metadata and self.enable_source_tagging and self.source_metadata:
            return {
                "embeddings": embeddings,
                "source_metadata": self._get_source_metadata_dict()
            }
        
        return embeddings
    
    def _feature_based_embedding(self, token) -> np.ndarray:
        """Generate embedding from SanTOK features only."""
        features = self._extract_features(token)
        
        # Project to target dimension
        if self._projection_matrix is None:
            self._feature_dim = len(features)
            self._projection_matrix = np.random.randn(
                self._feature_dim, self.embedding_dim
            ).astype(np.float32)
            # Normalize projection matrix
            self._projection_matrix = self._projection_matrix / np.sqrt(self._feature_dim)
        
        embedding = (features @ self._projection_matrix).astype(np.float32)
        
        return self._normalize(embedding)
    
    def _semantic_embedding(self, token) -> np.ndarray:
        """
        Generate semantic embedding from trained model.
        
        Uses self-trained semantic model that learned from SanTOK's structure.
        NO pretrained models - learns semantic relationships from co-occurrence.
        """
        if self.semantic_trainer is None:
            raise ValueError("Semantic trainer not initialized. Train a model first.")
        
        uid = getattr(token, 'uid', 0)
        embedding = self.semantic_trainer.get_embedding(uid)
        
        if embedding is None:
            # Fallback to feature-based if token not in vocabulary
            print(f"⚠️  Token UID {uid} not in semantic vocabulary, using feature-based fallback")
            return self._feature_based_embedding(token)
        
        return embedding
    
    def _hybrid_embedding(self, token) -> np.ndarray:
        """Generate hybrid embedding (text + features)."""
        # Get text embedding
        text = getattr(token, 'text', '')
        text_emb = self.text_embedder.encode(
            text,
            convert_to_numpy=True
        )
        
        # Get feature embedding
        feature_emb = self._feature_based_embedding(token)
        
        # Ensure same dimension
        if text_emb.shape[0] != feature_emb.shape[0]:
            # Project feature embedding to text embedding dimension
            if not hasattr(self, '_feature_to_text_projection'):
                self._feature_to_text_projection = np.random.randn(
                    feature_emb.shape[0], text_emb.shape[0]
                ).astype(np.float32)
            feature_emb = feature_emb @ self._feature_to_text_projection
            feature_emb = self._normalize(feature_emb)
        
        # Combine with weights
        combined = (
            self.feature_weights["text"] * text_emb +
            self.feature_weights["features"] * feature_emb
        )
        
        # Project to target dimension if needed
        if combined.shape[0] != self.embedding_dim:
            combined = self._project_to_dim(combined.reshape(1, -1), self.embedding_dim)[0]
        
        return self._normalize(combined)
    
    def _hash_embedding(self, token) -> np.ndarray:
        """Generate hash-based embedding."""
        # Create hash string from all features (use getattr for safety)
        text = getattr(token, 'text', '')
        uid = getattr(token, 'uid', 0)
        frontend = getattr(token, 'frontend', 0)
        backend_huge = getattr(token, 'backend_huge', 0)
        content_id = getattr(token, 'content_id', 0)
        global_id = getattr(token, 'global_id', 0)
        
        hash_string = (
            f"{text}_{uid}_{frontend}_"
            f"{backend_huge}_{content_id}_{global_id}"
        )
        
        # Hash to fixed size
        hash_bytes = hashlib.sha256(hash_string.encode()).digest()
        
        # Convert to embedding vector
        # Use hash bytes multiple times to fill embedding_dim
        embedding = np.zeros(self.embedding_dim, dtype=np.float32)
        for i in range(self.embedding_dim):
            byte_idx = i % len(hash_bytes)
            embedding[i] = hash_bytes[byte_idx] / 255.0
        
        return self._normalize(embedding)
    
    def _extract_features(self, token) -> np.ndarray:
        """Extract numerical features from TokenRecord."""
        features = []
        
        # UID (64-bit → 8 bytes, normalized to [0, 1])
        uid = getattr(token, 'uid', 0)
        uid_bytes = self._int64_to_bytes(uid)
        features.extend(uid_bytes)
        
        # Frontend (1-9 → one-hot encoded)
        frontend_onehot = np.zeros(9, dtype=np.float32)
        frontend = getattr(token, 'frontend', 0)
        if 1 <= frontend <= 9:
            frontend_onehot[frontend - 1] = 1.0
        features.extend(frontend_onehot)
        
        # Backend huge (64-bit → 8 bytes)
        backend_huge = getattr(token, 'backend_huge', 0)
        backend_bytes = self._int64_to_bytes(backend_huge)
        features.extend(backend_bytes)
        
        # Content ID (normalized to [0, 1])
        content_id = getattr(token, 'content_id', 0)
        content_id_norm = float(content_id) / 150000.0
        features.append(content_id_norm)
        
        # Global ID (64-bit → 8 bytes)
        global_id = getattr(token, 'global_id', 0)
        global_bytes = self._int64_to_bytes(global_id)
        features.extend(global_bytes)
        
        # Neighbor UIDs (context)
        prev_uid = getattr(token, 'prev_uid', None)
        next_uid = getattr(token, 'next_uid', None)
        prev_bytes = self._int64_to_bytes(prev_uid if prev_uid is not None else 0)
        next_bytes = self._int64_to_bytes(next_uid if next_uid is not None else 0)
        features.extend(prev_bytes)
        features.extend(next_bytes)
        
        # Index (normalized, assuming max 10k tokens per document)
        index = getattr(token, 'index', 0)
        index_norm = float(index) / 10000.0
        features.append(index_norm)
        
        # Stream (one-hot: 9 tokenization strategies)
        stream = getattr(token, 'stream', 'word')
        stream_onehot = self._stream_to_onehot(stream)
        features.extend(stream_onehot)
        
        return np.array(features, dtype=np.float32)
    
    def _int64_to_bytes(self, value: int) -> List[float]:
        """Convert 64-bit integer to 8 normalized bytes."""
        # Handle None or invalid values
        if value is None:
            value = 0
        try:
            # Ensure it's an integer
            value = int(value)
            # Convert to bytes
            bytes_val = value.to_bytes(8, byteorder='big', signed=False)
            # Normalize to [0, 1]
            return [b / 255.0 for b in bytes_val]
        except (ValueError, OverflowError, TypeError):
            # Fallback: return zeros
            return [0.0] * 8
    
    def _stream_to_onehot(self, stream_name: str) -> np.ndarray:
        """Convert stream name to one-hot encoding."""
        streams = [
            "space", "word", "char", "grammar", "subword",
            "subword_bpe", "subword_syllable", "subword_frequency", "byte"
        ]
        onehot = np.zeros(len(streams), dtype=np.float32)
        if stream_name in streams:
            onehot[streams.index(stream_name)] = 1.0
        return onehot
    
    def _project_to_dim(self, embeddings: np.ndarray, target_dim: int) -> np.ndarray:
        """Project embeddings to target dimension."""
        if embeddings.shape[1] == target_dim:
            return embeddings
        
        if not hasattr(self, f'_projection_{embeddings.shape[1]}_to_{target_dim}'):
            proj_name = f'_projection_{embeddings.shape[1]}_to_{target_dim}'
            setattr(
                self,
                proj_name,
                np.random.randn(embeddings.shape[1], target_dim).astype(np.float32)
                / np.sqrt(embeddings.shape[1])
            )
        
        proj = getattr(self, f'_projection_{embeddings.shape[1]}_to_{target_dim}')
        return embeddings @ proj
    
    def _normalize(self, embedding: np.ndarray) -> np.ndarray:
        """L2 normalize embedding (returns float32 for memory efficiency)."""
        embedding = embedding.astype(np.float32)
        norm = np.linalg.norm(embedding)
        if norm > 1e-8:
            return (embedding / norm).astype(np.float32)
        return embedding.astype(np.float32)
    
    def _normalize_batch(self, embeddings: np.ndarray) -> np.ndarray:
        """L2 normalize batch of embeddings (returns float32 for memory efficiency)."""
        embeddings = embeddings.astype(np.float32)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms > 1e-8, norms, 1.0)
        return (embeddings / norms).astype(np.float32)