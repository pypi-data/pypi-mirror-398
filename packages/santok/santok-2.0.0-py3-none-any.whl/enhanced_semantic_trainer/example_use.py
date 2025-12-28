"""
Example: Use Trained Enhanced Semantic Embeddings
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from enhanced_semantic_trainer import EnhancedSanTOKSemanticTrainer
from src.core.core_tokenizer import TextTokenizer
import numpy as np

def main():
    model_path = "enhanced_model.pkl"
    
    if not os.path.exists(model_path):
        print(f"Model not found: {model_path}")
        print("Please train a model first using example_train.py")
        return
    
    print(f"Loading model from {model_path}...")
    trainer = EnhancedSanTOKSemanticTrainer()
    trainer.load(model_path)
    
    print(f"Model loaded:")
    print(f"  Vocab size: {trainer.vocab_size}")
    print(f"  Embedding dim: {trainer.embedding_dim}")
    print(f"  Streams: {list(trainer.stream_vocabs.keys())}")
    
    # Tokenize new text
    text = "SanTOK generates deterministic UIDs for every token."
    print(f"\nTokenizing: {text}")
    
    tokenizer = TextTokenizer(seed=42, embedding_bit=16)
    streams = tokenizer.build(text)
    
    # Get embeddings for tokens
    print("\nGetting embeddings:")
    if streams.get('word') and streams['word'].tokens:
        for i, token in enumerate(streams['word'].tokens[:5]):  # First 5 tokens
            uid = getattr(token, 'uid', None)
            if uid:
                embedding = trainer.get_embedding(uid)
                if embedding is not None:
                    print(f"  Token {i}: '{token.text}' (UID: {uid})")
                    print(f"    Embedding shape: {embedding.shape}")
                    print(f"    Embedding norm: {np.linalg.norm(embedding):.4f}")
    
    # Find similar tokens (simple cosine similarity)
    print("\nFinding similar tokens:")
    if streams.get('word') and streams['word'].tokens:
        sample_token = streams['word'].tokens[0]
        sample_uid = getattr(sample_token, 'uid', None)
        if sample_uid:
            sample_emb = trainer.get_embedding(sample_uid)
            if sample_emb is not None:
                similarities = []
                for uid, idx in list(trainer.vocab.items())[:100]:  # Check first 100
                    if uid == sample_uid:
                        continue
                    emb = trainer.get_embedding(uid)
                    if emb is not None:
                        # Cosine similarity
                        sim = np.dot(sample_emb, emb) / (
                            np.linalg.norm(sample_emb) * np.linalg.norm(emb)
                        )
                        similarities.append((uid, sim))
                
                # Sort by similarity
                similarities.sort(key=lambda x: x[1], reverse=True)
                print(f"  Most similar to UID {sample_uid}:")
                for uid, sim in similarities[:5]:
                    print(f"    UID {uid}: similarity {sim:.4f}")

if __name__ == "__main__":
    main()