"""
Real-Time Data Interpretation System
=====================================

Uses YOUR Weaviate database (5.5M objects) with SanTOK's own embeddings.
NO pretrained models - 100% YOUR data and YOUR embeddings.

Example:
    Input: "Sales dropped 20% last month."
    Token clues: ["Sales", "dropped", "20%"]
    Searches YOUR Weaviate → finds related concepts from YOUR data
    Output: "Analyze customer behavior and marketing changes to find the cause."
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.core.core_tokenizer import TextTokenizer
    from src.embeddings.embedding_generator import SanTOKEmbeddingGenerator
    from src.embeddings.weaviate_vector_store import WeaviateVectorStore
except ImportError:
    from core.core_tokenizer import TextTokenizer
    from embeddings.embedding_generator import SanTOKEmbeddingGenerator
    from embeddings.weaviate_vector_store import WeaviateVectorStore


class DataInterpreter:
    """
    Real-time data interpretation system using SanTOK embeddings.
    
    Flow:
    1. Tokenize input text → extract key tokens
    2. Generate embeddings for tokens
    3. Search for related concepts in knowledge base
    4. Generate interpretation based on semantic relationships
    """
    
    def __init__(
        self,
        embedding_strategy: str = "feature_based",
        embedding_dim: int = 768,
        weaviate_url: Optional[str] = None,
        weaviate_api_key: Optional[str] = None,
        collection_name: str = "SanTOK_Token"
    ):
        """
        Initialize data interpreter using YOUR Weaviate database.
        
        Args:
            embedding_strategy: Strategy for embeddings ("feature_based", "semantic", "hybrid")
                               Uses SanTOK's own embeddings - NO pretrained models
            embedding_dim: Embedding dimension (must match your Weaviate collection)
            weaviate_url: Your Weaviate cluster URL (or from WEAVIATE_URL env var, or auto-detected)
            weaviate_api_key: Your Weaviate API key (or from WEAVIATE_API_KEY env var, or auto-detected)
            collection_name: Your Weaviate collection name (default: "SanTOK_Token")
        """
        self.embedding_strategy = embedding_strategy
        self.embedding_dim = embedding_dim
        
        # Initialize tokenizer (YOUR SanTOK tokenizer)
        self.tokenizer = TextTokenizer(seed=42, embedding_bit=False)
        
        # Initialize embedding generator (YOUR SanTOK embeddings - NO pretrained models)
        self.embedding_generator = SanTOKEmbeddingGenerator(
            strategy=embedding_strategy,  # Uses YOUR feature-based embeddings
            embedding_dim=embedding_dim
        )
        
        # Auto-detect Weaviate credentials from weaviate_codes/.env if not provided
        if not weaviate_url or not weaviate_api_key:
            # Try to load from weaviate_codes/.env file
            weaviate_env_path = Path(__file__).parent.parent.parent / "weaviate_codes" / ".env"
            if weaviate_env_path.exists():
                try:
                    from dotenv import load_dotenv
                    load_dotenv(weaviate_env_path)
                    if not weaviate_url:
                        weaviate_url = os.getenv("WEAVIATE_URL")
                    if not weaviate_api_key:
                        weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
                    if weaviate_url and weaviate_api_key:
                        print(f"✓ Loaded Weaviate credentials from {weaviate_env_path}")
                except ImportError:
                    pass
                except Exception as e:
                    print(f"⚠️  Could not load from weaviate_codes/.env: {e}")
        
        # Also try loading from root .env or environment variables
        if not weaviate_url:
            weaviate_url = os.getenv("WEAVIATE_URL")
        if not weaviate_api_key:
            weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
        
        # Connect to YOUR Weaviate database (5.5M objects)
        self.vector_store = WeaviateVectorStore(
            collection_name=collection_name,
            embedding_dim=embedding_dim,
            weaviate_url=weaviate_url,
            weaviate_api_key=weaviate_api_key,
            auto_load_env=True
        )
        
        print(f"✓ Connected to YOUR Weaviate database: {collection_name}")
        print(f"✓ Using YOUR SanTOK embeddings (strategy: {embedding_strategy})")
        print(f"✓ NO pretrained models - 100% YOUR data")
    
    def _extract_concepts_from_results(self, search_results: List[Dict[str, Any]]) -> List[str]:
        """
        Extract concept keywords from search results in YOUR Weaviate database.
        Uses the text and metadata from YOUR data to identify concepts.
        """
        concepts = []
        seen_texts = set()
        word_frequency = {}
        
        # Common stop words to filter out
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                     'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
                     'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who'}
        
        for result in search_results:
            text = result.get('text', '').strip()
            metadata = result.get('metadata', {})
            
            # Extract meaningful words from YOUR data
            if text and text not in seen_texts:
                seen_texts.add(text)
                
                # Tokenize the text to extract meaningful words
                text_lower = text.lower()
                
                # Split into words and filter
                words = text_lower.split()
                meaningful_words = []
                
                for word in words:
                    # Remove punctuation
                    word = word.strip('.,!?;:()[]{}"\'-')
                    # Filter out stop words and very short words
                    if word and len(word) > 2 and word not in stop_words:
                        # Check if it's a meaningful word (not just numbers)
                        if not word.isdigit():
                            meaningful_words.append(word)
                            word_frequency[word] = word_frequency.get(word, 0) + 1
                
                # Also check metadata for additional context
                if metadata:
                    for key, value in metadata.items():
                        if isinstance(value, str) and len(value) > 2:
                            value_lower = value.lower().strip('.,!?;:()[]{}"\'-')
                            if value_lower not in stop_words and not value_lower.isdigit():
                                meaningful_words.append(value_lower)
                                word_frequency[value_lower] = word_frequency.get(value_lower, 0) + 1
        
        # Get top meaningful words as concepts (most frequent, but diverse)
        # Sort by frequency, but also prioritize longer words
        scored_words = []
        for word, freq in word_frequency.items():
            score = freq * 10  # Frequency score
            score += len(word) * 2  # Longer words are more meaningful
            scored_words.append((score, word))
        
        # Sort by score and get top concepts
        scored_words.sort(reverse=True, key=lambda x: x[0])
        
        # Get top concepts (avoid duplicates and very similar words)
        for score, word in scored_words[:20]:  # Consider top 20
            # Skip if too similar to existing concepts
            is_duplicate = False
            for existing in concepts:
                if word in existing or existing in word:
                    is_duplicate = True
                    break
            if not is_duplicate:
                concepts.append(word)
                if len(concepts) >= 10:  # Limit to 10 concepts
                    break
        
        return concepts
    
    def extract_token_clues(self, text: str, top_n: int = 5) -> List[str]:
        """
        Extract key token clues from input text.
        
        Args:
            text: Input text
            top_n: Number of key tokens to extract
            
        Returns:
            List of key token strings
        """
        # Tokenize text
        streams = self.tokenizer.build(text)
        
        # Get tokens from word stream (most meaningful)
        word_stream = streams.get('word')
        if not word_stream:
            return []
        
        tokens = word_stream.tokens
        
        # Score tokens by importance (length, position, uniqueness)
        token_scores = []
        all_texts = [t.text.lower() for t in tokens]
        
        for i, token in enumerate(tokens):
            text_lower = token.text.lower()
            score = 0
            
            # Longer tokens are more important
            score += len(token.text) * 2
            
            # Early position tokens are more important
            score += (len(tokens) - i) / len(tokens) * 10
            
            # Unique tokens are more important
            if all_texts.count(text_lower) == 1:
                score += 5
            
            # Numbers and percentages are important
            if any(c.isdigit() for c in token.text) or '%' in token.text:
                score += 10
            
            # Action verbs are important
            action_words = ['drop', 'dropped', 'increase', 'decrease', 'change', 'improve', 'decline']
            if text_lower in action_words:
                score += 8
            
            token_scores.append((score, token.text))
        
        # Sort by score and get top N
        token_scores.sort(reverse=True, key=lambda x: x[0])
        top_tokens = [text for _, text in token_scores[:top_n]]
        
        return top_tokens
    
    def find_related_concepts(
        self,
        token_clues: List[str],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find related concepts by searching YOUR Weaviate database (5.5M objects).
        Uses YOUR SanTOK embeddings - NO pretrained models.
        
        Args:
            token_clues: List of key token strings
            top_k: Number of results to retrieve from YOUR database
            
        Returns:
            List of related concepts found in YOUR data
        """
        if not token_clues:
            return []
        
        # Tokenize clues using YOUR SanTOK tokenizer
        all_tokens = []
        for clue in token_clues:
            streams = self.tokenizer.build(clue)
            word_stream = streams.get('word')
            if word_stream:
                all_tokens.extend(word_stream.tokens)
        
        if not all_tokens:
            return []
        
        # Generate embeddings using YOUR SanTOK embedding generator
        # This uses YOUR feature-based embeddings - NO pretrained models
        clue_embeddings = self.embedding_generator.generate_batch(all_tokens)
        
        # Average embeddings to get single query vector
        query_embedding = np.mean(clue_embeddings, axis=0)
        
        # Search YOUR Weaviate database (5.5M objects)
        # This searches through YOUR existing data
        results = self.vector_store.search(query_embedding, top_k=top_k)
        
        # Extract concepts from YOUR search results
        concepts = self._extract_concepts_from_results(results)
        
        # Format results with YOUR data
        formatted_results = []
        seen_concepts = set()
        
        for i, result in enumerate(results):
            # Extract concept from result text
            text = result.get('text', '').strip()
            text_lower = text.lower() if text else ''
            
            # Try to identify concept from extracted concepts
            concept = None
            for c in concepts:
                if c not in seen_concepts and c in text_lower:
                    concept = c
                    seen_concepts.add(c)
                    break
            
            # If no concept matched, extract from text directly
            if not concept and text:
                # Get first meaningful word from text
                words = text_lower.split()
                for word in words:
                    word_clean = word.strip('.,!?;:()[]{}"\'-')
                    if (word_clean and len(word_clean) > 2 and 
                        not word_clean.isdigit() and 
                        word_clean not in {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from'}):
                        concept = word_clean
                        break
            
            # If still no concept, use a descriptive label
            if not concept:
                # Extract first few words as concept
                words = text.split()[:3]
                concept = ' '.join(words).lower()[:30] if words else 'concept'
            
            formatted_results.append({
                'concept': concept,
                'text': text,
                'metadata': result.get('metadata', {}),
                'distance': result.get('distance', 0.0)
            })
            
            if len(formatted_results) >= top_k:
                break
        
        return formatted_results
    
    def generate_interpretation(
        self,
        input_text: str,
        token_clues: List[str],
        related_concepts: List[Dict[str, Any]]
    ) -> str:
        """
        Generate interpretation based on YOUR Weaviate search results.
        Uses concepts found in YOUR data.
        
        Args:
            input_text: Original input text
            token_clues: Extracted token clues
            related_concepts: Related concepts from YOUR Weaviate database
            
        Returns:
            Generated interpretation string based on YOUR data
        """
        # Extract concept names from YOUR search results
        concept_names = [c.get('concept', '').lower() for c in related_concepts if c.get('concept')]
        
        # Get top texts from YOUR search results for context
        top_texts = [c.get('text', '') for c in related_concepts[:5] if c.get('text')]
        
        # Build interpretation from actual search results
        if not related_concepts:
            return "No related concepts found in your database. Try different keywords or expand your data."
        
        # Extract key themes from top results
        key_themes = []
        action_verbs = []
        
        # Analyze top concepts and texts
        for concept_detail in related_concepts[:5]:
            concept = concept_detail.get('concept', '').lower()
            text = concept_detail.get('text', '').lower()
            
            # Extract meaningful concepts
            if concept and concept not in key_themes:
                key_themes.append(concept)
            
            # Look for action words in text
            action_words = ['analyze', 'investigate', 'examine', 'review', 'study', 'explore',
                          'identify', 'understand', 'evaluate', 'assess', 'consider', 'examine']
            for action in action_words:
                if action in text and action not in action_verbs:
                    action_verbs.append(action)
        
        # Build interpretation dynamically
        interpretation_parts = []
        
        # Start with an action if found
        if action_verbs:
            interpretation_parts.append(action_verbs[0].capitalize())
        else:
            interpretation_parts.append("Review")
        
        # Add key themes
        if key_themes:
            # Use top 2-3 themes
            themes_to_use = key_themes[:3]
            if len(themes_to_use) == 1:
                interpretation_parts.append(f"the {themes_to_use[0]}")
            elif len(themes_to_use) == 2:
                interpretation_parts.append(f"the {themes_to_use[0]} and {themes_to_use[1]}")
            else:
                themes_str = ", ".join(themes_to_use[:-1]) + f", and {themes_to_use[-1]}"
                interpretation_parts.append(f"the {themes_str}")
        
        # Add context from input
        input_lower = input_text.lower()
        if any(word in input_lower for word in ['drop', 'decrease', 'decline', 'fall']):
            interpretation_parts.append("to identify the cause of the decline")
        elif any(word in input_lower for word in ['increase', 'grow', 'improve', 'rise']):
            interpretation_parts.append("to understand the growth factors")
        elif any(word in input_lower for word in ['what', 'how', 'why', 'explain']):
            interpretation_parts.append("to provide insights")
        else:
            interpretation_parts.append("to understand the context")
        
        # Combine into final interpretation
        interpretation = " ".join(interpretation_parts) + "."
        
        # Fallback if too generic
        if len(interpretation) < 30:
            # Use actual text from results
            if top_texts:
                first_result = top_texts[0][:100]
                interpretation = f"Based on your database: {first_result}..."
            else:
                interpretation = f"Review the related concepts ({', '.join(concept_names[:3])}) from your database to understand this topic."
        
        return interpretation
    
    def interpret(self, input_text: str, top_clues: int = 5, top_concepts: int = 5) -> Dict[str, Any]:
        """
        Complete interpretation pipeline.
        
        Args:
            input_text: Input text to interpret
            top_clues: Number of token clues to extract
            top_concepts: Number of related concepts to find
            
        Returns:
            Dictionary with interpretation results
        """
        # Step 1: Extract token clues
        token_clues = self.extract_token_clues(input_text, top_n=top_clues)
        
        # Step 2: Find related concepts
        related_concepts = self.find_related_concepts(token_clues, top_k=top_concepts)
        
        # Step 3: Generate interpretation
        interpretation = self.generate_interpretation(input_text, token_clues, related_concepts)
        
        return {
            "input": input_text,
            "token_clues": token_clues,
            "related_concepts": [c['concept'] for c in related_concepts],
            "concept_details": related_concepts,
            "interpretation": interpretation
        }


def main():
    """Example usage with YOUR Weaviate database"""
    print("=" * 80)
    print("Real-Time Data Interpretation System")
    print("Using YOUR Weaviate Database (5.5M objects)")
    print("Using YOUR SanTOK Embeddings - NO Pretrained Models")
    print("=" * 80)
    
    # Initialize interpreter with YOUR Weaviate
    # Credentials will be auto-loaded from weaviate_codes/.env
    print("\nConnecting to YOUR Weaviate database...")
    interpreter = DataInterpreter(
        embedding_strategy="feature_based",  # YOUR SanTOK embeddings
        embedding_dim=768,  # Must match your Weaviate collection
        collection_name="SanTOK_Token"  # YOUR collection name
    )
    
    # Example input
    input_text = "Sales dropped 20% last month."
    
    print(f"\nInput: {input_text}")
    print("\nSearching YOUR Weaviate database (5.5M objects)...")
    
    # Interpret using YOUR data
    result = interpreter.interpret(input_text)
    
    # Display results
    print("\n" + "=" * 80)
    print("RESULTS (from YOUR data)")
    print("=" * 80)
    print(f"\nToken Clues: {result['token_clues']}")
    print(f"\nRelated Concepts (from YOUR Weaviate): {result['related_concepts']}")
    print(f"\nTop Results from YOUR Database:")
    for i, detail in enumerate(result['concept_details'][:5], 1):
        print(f"  {i}. {detail.get('text', 'N/A')} (concept: {detail.get('concept', 'N/A')})")
    print(f"\nInterpretation (based on YOUR data):")
    print(f"  {result['interpretation']}")
    print("\n" + "=" * 80)
    
    return result


if __name__ == "__main__":
    main()