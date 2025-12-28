#!/usr/bin/env python3
"""
Demonstration of Enhanced SanTOK Tokenizer Logic

This script demonstrates the enhanced space, byte, and sub-word tokenization
logic that has been added to the SanTOK Tokenizer system.
"""

# Import the enhanced tokenizer functions
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.core.core_tokenizer import (
    tokenize_space, tokenize_bytes, tokenize_subword,
    all_tokenizations
)
# Note: advanced_tokenization_analysis and tokenization_comparison 
# may need to be implemented or imported differently
def advanced_tokenization_analysis(text):
    return all_tokenizations(text)
def tokenization_comparison(text):
    return all_tokenizations(text)

def demo_space_tokenization():
    """Demonstrate enhanced space tokenization"""
    print("=== SPACE TOKENIZATION DEMO ===")
    text = "Hello    world!\nThis\tis\ta\ttest."
    
    tokens = tokenize_space(text)
    print(f"Input: '{text}'")
    print(f"Tokens: {len(tokens)}")
    
    for i, token in enumerate(tokens):
        token_type = token.get('type', 'unknown')
        if token_type == 'space':
            space_type = token.get('space_type', 'unknown')
            space_count = token.get('space_count', 0)
            print(f"  {i}: '{token['text']}' (type: {token_type}, space_type: {space_type}, count: {space_count})")
        else:
            print(f"  {i}: '{token['text']}' (type: {token_type})")
    print()

def demo_byte_tokenization():
    """Demonstrate enhanced byte tokenization"""
    print("=== BYTE TOKENIZATION DEMO ===")
    text = "Hello 世界"  # Mix of ASCII and Unicode
    
    tokens = tokenize_bytes(text)
    print(f"Input: '{text}'")
    print(f"Tokens: {len(tokens)}")
    
    # Group tokens by type for better display
    utf8_tokens = [t for t in tokens if t.get('type') == 'utf8_byte']
    codepoint_tokens = [t for t in tokens if t.get('type') == 'codepoint_digit']
    hex_tokens = [t for t in tokens if t.get('type') == 'hex_digit']
    
    print(f"UTF-8 bytes: {len(utf8_tokens)} tokens")
    for token in utf8_tokens[:5]:  # Show first 5
        print(f"  '{token['text']}' (char: {token['original_char']}, codepoint: {token['codepoint']})")
    
    print(f"Codepoint digits: {len(codepoint_tokens)} tokens")
    for token in codepoint_tokens[:5]:  # Show first 5
        print(f"  '{token['text']}' (char: {token['original_char']})")
    
    print(f"Hex digits: {len(hex_tokens)} tokens")
    for token in hex_tokens[:5]:  # Show first 5
        print(f"  '{token['text']}' (char: {token['original_char']})")
    print()

def demo_subword_tokenization():
    """Demonstrate enhanced sub-word tokenization"""
    print("=== SUB-WORD TOKENIZATION DEMO ===")
    text = "unbelievable running quickly"
    
    strategies = ["fixed", "bpe", "syllable", "frequency"]
    
    for strategy in strategies:
        tokens = tokenize_subword(text, chunk_len=3, strategy=strategy)
        print(f"Strategy '{strategy}': {len(tokens)} tokens")
        
        for i, token in enumerate(tokens[:8]):  # Show first 8 tokens
            token_type = token.get('type', 'unknown')
            parent_word = token.get('parent_word', '')
            print(f"  {i}: '{token['text']}' (type: {token_type}, parent: '{parent_word}')")
        print()

def demo_comprehensive_analysis():
    """Demonstrate comprehensive tokenization analysis"""
    print("=== COMPREHENSIVE ANALYSIS DEMO ===")
    text = "The quick brown fox jumps over the lazy dog."
    
    # Get analysis
    analysis = advanced_tokenization_analysis(text)
    
    print(f"Input: '{text}'")
    print(f"Text length: {len(text)} characters")
    print()
    
    for name, stats in analysis.items():
        print(f"{name.upper()}:")
        print(f"  Tokens: {stats['token_count']}")
        print(f"  Unique: {stats['unique_tokens']}")
        print(f"  Avg length: {stats['average_length']:.2f}")
        print(f"  Compression: {stats['compression_ratio']:.2f}")
        if stats['type_distribution']:
            print(f"  Types: {stats['type_distribution']}")
        print(f"  Sample: {stats['sample_tokens'][:5]}")
        print()

def demo_comparison():
    """Demonstrate tokenization comparison"""
    print("=== TOKENIZATION COMPARISON DEMO ===")
    text = "Hello world!"
    
    comparison = tokenization_comparison(text)
    
    print(f"Input: '{text}'")
    print(f"Text length: {comparison['text_length']}")
    print()
    
    for name, data in comparison['strategies'].items():
        print(f"{name}: {data['count']} tokens")
        print(f"  Tokens: {data['tokens']}")
        print(f"  Types: {data['metadata']}")
        print()

def main():
    """Run all demonstrations"""
    print("Enhanced SanTOK Tokenizer Logic Demonstration")
    print("=" * 50)
    print()
    
    demo_space_tokenization()
    demo_byte_tokenization()
    demo_subword_tokenization()
    demo_comprehensive_analysis()
    demo_comparison()
    
    print("=== SUMMARY ===")
    print("Enhanced tokenization features added:")
    print("1. Space tokenization: Preserves spacing information and classifies whitespace types")
    print("2. Byte tokenization: Multiple strategies (UTF-8, codepoint digits, hex)")
    print("3. Sub-word tokenization: Multiple algorithms (fixed, BPE-like, syllable, frequency)")
    print("4. Comprehensive analysis: Statistics and insights for all tokenization strategies")
    print("5. Comparison tools: Side-by-side analysis of different tokenization approaches")

if __name__ == "__main__":
    main()