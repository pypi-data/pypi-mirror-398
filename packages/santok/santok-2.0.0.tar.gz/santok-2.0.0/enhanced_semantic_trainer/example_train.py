"""
Example: Train Enhanced Semantic Embeddings
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from enhanced_semantic_trainer import EnhancedSanTOKSemanticTrainer
from src.core.core_tokenizer import TextTokenizer

def main():
    # Sample corpus
    corpus = """
    SanTOK is a universal tokenization system that works on any file type.
    It generates multiple tokenization streams simultaneously.
    Each token has a deterministic UID that never changes.
    The system supports images, videos, audio, and any other file format.
    """
    
    print("Tokenizing corpus...")
    tokenizer = TextTokenizer(seed=42, embedding_bit=16)
    streams = tokenizer.build(corpus)
    
    print(f"Generated {len(streams)} streams:")
    for name, stream in streams.items():
        print(f"  {name}: {len(stream.tokens)} tokens")
    
    # Prepare token streams dict
    token_streams = {name: stream.tokens for name, stream in streams.items()}
    
    print("\nTraining enhanced semantic embeddings...")
    trainer = EnhancedSanTOKSemanticTrainer(
        embedding_dim=768,
        window_size=5,
        epochs=10,
        learning_rate=0.01,
        use_multi_stream=True,
        use_temporal=True,
        use_content_id_clustering=True,
        use_math_properties=True,
        use_cross_stream_alignment=True,
        use_deterministic_graph=True,
        use_source_aware=True
    )
    
    trainer.train(token_streams)
    
    print("\nSaving model...")
    trainer.save("enhanced_model.pkl")
    
    print("\nTraining stats:")
    for key, value in trainer.training_stats.items():
        print(f"  {key}: {value}")
    
    print("\nTesting embeddings...")
    # Get a sample UID
    if streams.get('word') and streams['word'].tokens:
        sample_token = streams['word'].tokens[0]
        sample_uid = getattr(sample_token, 'uid', None)
        if sample_uid:
            embedding = trainer.get_embedding(sample_uid)
            if embedding is not None:
                print(f"  Sample UID {sample_uid}: embedding shape {embedding.shape}")
    
    print("\nDone!")

if __name__ == "__main__":
    main()