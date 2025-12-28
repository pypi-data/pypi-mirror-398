#!/usr/bin/env python3
"""
Test SanTOK reconstruction accuracy
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

def test_reconstruction_accuracy():
    """Test reconstruction accuracy for all tokenizer types"""
    
    # Test texts
    test_texts = [
        'Hello, world!',
        'This is a test.',
        'Special chars: @#$%^&*()',
        'Numbers: 12345.67890',
        'Unicode: 你好世界 🌍'
    ]

    # Available tokenizers
    tokenizers = ['space', 'word', 'char', 'grammar', 'subword', 'bpe', 'syllable', 'frequency', 'byte']

    print('Testing SanTOK reconstruction accuracy...')
    print('=' * 60)

    results = {}

    for tokenizer_type in tokenizers:
        print(f'\nTesting {tokenizer_type.upper()} tokenization:')
        print('-' * 30)
        
        perfect_count = 0
        total_tests = len(test_texts)
        errors = []
        
        for i, text in enumerate(test_texts):
            try:
                # Tokenize
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
                
                # Reconstruct
                reconstructed = reconstruct_from_tokens(tokens, tokenizer_type)
                
                # Check if perfect
                is_perfect = (text == reconstructed)
                if is_perfect:
                    perfect_count += 1
                else:
                    errors.append({
                        'text': text,
                        'reconstructed': reconstructed,
                        'original_len': len(text),
                        'reconstructed_len': len(reconstructed)
                    })
                
                status = "[OK] PERFECT" if is_perfect else "[FAIL] IMPERFECT"
                print(f'  {i+1}. {status}: "{text[:20]}{"..." if len(text) > 20 else ""}"')
                
            except Exception as e:
                print(f'  {i+1}. ERROR: {e}')
                errors.append({'text': text, 'error': str(e)})
        
        accuracy = (perfect_count / total_tests) * 100
        results[tokenizer_type] = {
            'accuracy': accuracy,
            'perfect_count': perfect_count,
            'total_tests': total_tests,
            'errors': errors
        }
        
        print(f'  Accuracy: {accuracy:.1f}% ({perfect_count}/{total_tests})')
        
        # Show errors if any
        if errors:
            print(f'  Errors found:')
            for error in errors:
                if 'error' in error:
                    print(f'    - {error["text"]}: {error["error"]}')
                else:
                    print(f'    - "{error["text"]}" -> "{error["reconstructed"]}"')
                    print(f'      Length: {error["original_len"]} vs {error["reconstructed_len"]}')

    # Summary
    print('\n' + '=' * 60)
    print('SUMMARY:')
    print('=' * 60)
    
    all_perfect = True
    for tokenizer_type, result in results.items():
        accuracy = result['accuracy']
        status = "[OK] PERFECT" if accuracy == 100.0 else "[FAIL] IMPERFECT"
        print(f'{tokenizer_type.upper():12} {accuracy:6.1f}% {status}')
        if accuracy != 100.0:
            all_perfect = False
    
    print(f'\nOverall: {"[OK] ALL PERFECT" if all_perfect else "[FAIL] SOME IMPERFECT"}')
    
    return results

def test_performance():
    """Test performance benchmarks"""
    
    print('\n' + '=' * 60)
    print('PERFORMANCE TESTING:')
    print('=' * 60)
    
    # Test text
    test_text = "Hello, world! This is a performance test. " * 100  # ~4KB
    tokenizers = ['space', 'word', 'char', 'byte']
    
    for tokenizer_type in tokenizers:
        print(f'\nTesting {tokenizer_type.upper()} performance:')
        
        # Warm up
        for _ in range(10):
            if tokenizer_type == 'space':
                tokens = tokenize_space(test_text)
            elif tokenizer_type == 'word':
                tokens = tokenize_word(test_text)
            elif tokenizer_type == 'char':
                tokens = tokenize_char(test_text)
            elif tokenizer_type == 'byte':
                tokens = tokenize_bytes(test_text)
        
        # Time tokenization
        start_time = time.time()
        for _ in range(100):
            if tokenizer_type == 'space':
                tokens = tokenize_space(test_text)
            elif tokenizer_type == 'word':
                tokens = tokenize_word(test_text)
            elif tokenizer_type == 'char':
                tokens = tokenize_char(test_text)
            elif tokenizer_type == 'byte':
                tokens = tokenize_bytes(test_text)
        end_time = time.time()
        
        # Calculate speed
        total_time = end_time - start_time
        avg_time = total_time / 100
        chars_per_sec = len(test_text) / avg_time
        
        print(f'  Text length: {len(test_text)} characters')
        print(f'  Average time: {avg_time*1000:.2f}ms')
        print(f'  Speed: {chars_per_sec:,.0f} chars/sec')
        print(f'  Tokens: {len(tokens)}')

if __name__ == "__main__":
    # Test accuracy
    results = test_reconstruction_accuracy()
    
    # Test performance
    test_performance()
    
    print('\n' + '=' * 60)
    print('TEST COMPLETE')
    print('=' * 60)