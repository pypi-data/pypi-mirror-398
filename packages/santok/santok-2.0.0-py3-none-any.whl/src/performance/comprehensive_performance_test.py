#!/usr/bin/env python3
"""
Comprehensive Performance Test for SanTOK
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.core.core_tokenizer import (
    tokenize_space,
    tokenize_word,
    tokenize_char,
    tokenize_grammar,
    tokenize_subword,
    tokenize_bytes,
    reconstruct_from_tokens
)
import time
import random
import string

def generate_test_data():
    """Generate comprehensive test datasets"""
    
    # Small dataset (1KB)
    small_text = "Hello, world! This is a test. " * 2500  # ~1KB
    
    # Medium dataset (10KB)
    medium_text = "The quick brown fox jumps over the lazy dog. " * 200  # ~10KB
    
    # Large dataset (100KB)
    large_text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 2000  # ~100KB
    
    # Very large dataset (1MB)
    very_large_text = "This is a very large text for performance testing. " * 20000  # ~300KB
    
    # Unicode dataset
    unicode_text = "你好世界 🌍 Hello 世界 🌟 Test 测试 🚀 " * 100  # ~5KB
    
    # Technical dataset
    technical_text = """
    def tokenize_text(text, tokenizer_type):
        if tokenizer_type == 'word':
            return text.split()
        elif tokenizer_type == 'char':
            return list(text)
        # ... more code
    """ * 5  # ~10KB
    
    return {
        'small': small_text,
        'medium': medium_text,
        'large': large_text,
        'very_large': very_large_text,
        'unicode': unicode_text,
        'technical': technical_text
    }

def test_tokenizer_performance(text, tokenizer_type, iterations=10):
    """Test performance of a specific tokenizer"""
    
    # Warm up
    for _ in range(5):
        if tokenizer_type == 'space':
            tokens = tokenize_space(text)
        elif tokenizer_type == 'word':
            tokens = tokenize_word(text)
        elif tokenizer_type == 'char':
            tokens = tokenize_char(text)
        elif tokenizer_type == 'grammar':
            tokens = tokenize_grammar(text)
        elif tokenizer_type == 'subword':
            tokens = tokenize_subword(text, 3, 'fixed')
        elif tokenizer_type == 'bpe':
            tokens = tokenize_subword(text, 3, 'bpe')
        elif tokenizer_type == 'syllable':
            tokens = tokenize_subword(text, 3, 'syllable')
        elif tokenizer_type == 'frequency':
            tokens = tokenize_subword(text, 3, 'frequency')
        elif tokenizer_type == 'byte':
            tokens = tokenize_bytes(text)
    
    # Time tokenization
    start_time = time.time()
    for _ in range(iterations):
        if tokenizer_type == 'space':
            tokens = tokenize_space(text)
        elif tokenizer_type == 'word':
            tokens = tokenize_word(text)
        elif tokenizer_type == 'char':
            tokens = tokenize_char(text)
        elif tokenizer_type == 'grammar':
            tokens = tokenize_grammar(text)
        elif tokenizer_type == 'subword':
            tokens = tokenize_subword(text, 3, 'fixed')
        elif tokenizer_type == 'bpe':
            tokens = tokenize_subword(text, 3, 'bpe')
        elif tokenizer_type == 'syllable':
            tokens = tokenize_subword(text, 3, 'syllable')
        elif tokenizer_type == 'frequency':
            tokens = tokenize_subword(text, 3, 'frequency')
        elif tokenizer_type == 'byte':
            tokens = tokenize_bytes(text)
    end_time = time.time()
    
    # Calculate metrics
    total_time = end_time - start_time
    avg_time = total_time / iterations
    chars_per_sec = len(text) / avg_time
    tokens_count = len(tokens)
    
    return {
        'avg_time_ms': avg_time * 1000,
        'chars_per_sec': chars_per_sec,
        'tokens_count': tokens_count,
        'chars_per_token': len(text) / tokens_count if tokens_count > 0 else 0
    }

def test_reconstruction_performance(text, tokenizer_type, iterations=10):
    """Test reconstruction performance"""
    
    # Tokenize first
    if tokenizer_type == 'space':
        tokens = tokenize_space(text)
    elif tokenizer_type == 'word':
        tokens = tokenize_word(text)
    elif tokenizer_type == 'char':
        tokens = tokenize_char(text)
    elif tokenizer_type == 'grammar':
        tokens = tokenize_grammar(text)
    elif tokenizer_type == 'subword':
        tokens = tokenize_subword(text, 3, 'fixed')
    elif tokenizer_type == 'bpe':
        tokens = tokenize_subword(text, 3, 'bpe')
    elif tokenizer_type == 'syllable':
        tokens = tokenize_subword(text, 3, 'syllable')
    elif tokenizer_type == 'frequency':
        tokens = tokenize_subword(text, 3, 'frequency')
    elif tokenizer_type == 'byte':
        tokens = tokenize_bytes(text)
    
    # Warm up
    for _ in range(5):
        reconstructed = reconstruct_from_tokens(tokens, tokenizer_type)
    
    # Time reconstruction
    start_time = time.time()
    for _ in range(iterations):
        reconstructed = reconstruct_from_tokens(tokens, tokenizer_type)
    end_time = time.time()
    
    # Calculate metrics
    total_time = end_time - start_time
    avg_time = total_time / iterations
    chars_per_sec = len(text) / avg_time
    
    return {
        'avg_time_ms': avg_time * 1000,
        'chars_per_sec': chars_per_sec,
        'perfect_reconstruction': text == reconstructed
    }

def comprehensive_performance_test():
    """Run comprehensive performance tests"""
    
    print("[START] SanTOK Comprehensive Performance Test")
    print("=" * 80)
    
    # Generate test data
    datasets = generate_test_data()
    tokenizers = ['space', 'word', 'char', 'grammar', 'subword', 'bpe', 'syllable', 'frequency', 'byte']
    
    # Results storage
    results = {}
    
    for dataset_name, text in datasets.items():
        print(f"\n📊 Testing {dataset_name.upper()} dataset ({len(text):,} characters)")
        print("-" * 60)
        
        results[dataset_name] = {}
        
        for tokenizer_type in tokenizers:
            print(f"\n🔧 {tokenizer_type.upper()} tokenization:")
            
            # Reduce iterations for very large datasets to prevent timeout
            iterations = 5 if dataset_name == "VERY_LARGE" else 20
            
            # Test tokenization performance
            tokenization_results = test_tokenizer_performance(text, tokenizer_type, iterations=iterations)
            
            # Test reconstruction performance
            reconstruction_results = test_reconstruction_performance(text, tokenizer_type, iterations=iterations)
            
            # Store results
            results[dataset_name][tokenizer_type] = {
                'tokenization': tokenization_results,
                'reconstruction': reconstruction_results
            }
            
            # Display results
            print(f"  Tokenization: {tokenization_results['chars_per_sec']:,.0f} chars/sec ({tokenization_results['avg_time_ms']:.2f}ms)")
            print(f"  Reconstruction: {reconstruction_results['chars_per_sec']:,.0f} chars/sec ({reconstruction_results['avg_time_ms']:.2f}ms)")
            print(f"  Tokens: {tokenization_results['tokens_count']:,} ({tokenization_results['chars_per_token']:.1f} chars/token)")
            print(f"  Perfect: {'✅' if reconstruction_results['perfect_reconstruction'] else '❌'}")
    
    # Summary analysis
    print("\n" + "=" * 80)
    print("📈 PERFORMANCE SUMMARY")
    print("=" * 80)
    
    # Calculate averages across all datasets
    avg_speeds = {}
    for tokenizer_type in tokenizers:
        speeds = []
        for dataset_name in datasets.keys():
            if dataset_name in results and tokenizer_type in results[dataset_name]:
                speeds.append(results[dataset_name][tokenizer_type]['tokenization']['chars_per_sec'])
        avg_speeds[tokenizer_type] = sum(speeds) / len(speeds) if speeds else 0
    
    # Sort by performance
    sorted_tokenizers = sorted(avg_speeds.items(), key=lambda x: x[1], reverse=True)
    
    print("\n🏆 Average Performance Ranking:")
    for i, (tokenizer_type, avg_speed) in enumerate(sorted_tokenizers, 1):
        print(f"  {i:2d}. {tokenizer_type.upper():12} {avg_speed:8,.0f} chars/sec")
    
    # Memory efficiency analysis
    print("\n💾 Memory Efficiency (chars per token):")
    for tokenizer_type in tokenizers:
        ratios = []
        for dataset_name in datasets.keys():
            if dataset_name in results and tokenizer_type in results[dataset_name]:
                ratios.append(results[dataset_name][tokenizer_type]['tokenization']['chars_per_token'])
        avg_ratio = sum(ratios) / len(ratios) if ratios else 0
        print(f"  {tokenizer_type.upper():12} {avg_ratio:6.1f} chars/token")
    
    # Scalability analysis
    print("\n📊 Scalability Analysis:")
    for tokenizer_type in tokenizers:
        print(f"\n{tokenizer_type.upper()}:")
        for dataset_name in ['small', 'medium', 'large', 'very_large']:
            if dataset_name in results and tokenizer_type in results[dataset_name]:
                text_len = len(datasets[dataset_name])
                speed = results[dataset_name][tokenizer_type]['tokenization']['chars_per_sec']
                print(f"  {dataset_name:12} {text_len:8,} chars -> {speed:8,.0f} chars/sec")
    
    return results

if __name__ == "__main__":
    results = comprehensive_performance_test()
    
    print("\n" + "=" * 80)
    print("✅ COMPREHENSIVE TEST COMPLETE")
    print("=" * 80)