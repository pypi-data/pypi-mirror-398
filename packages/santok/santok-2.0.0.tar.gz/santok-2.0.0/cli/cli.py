#!/usr/bin/env python3
"""
Command Line Interface for TextTokenizationEngine
"""

import argparse
import json
import sys
from typing import Dict, Any, List
from .santok import TextTokenizationEngine

def main() -> None:
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='SanTOK - Comprehensive Text Tokenization Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  santok "Hello World" --method whitespace
  santok "Hello World" --method word --features
  santok "Hello World" --analyze --output results.json
  santok --file input.txt --method character
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('text', nargs='?', help='Text to tokenize')
    input_group.add_argument('--file', '-f', help='File containing text to tokenize')
    
    # Tokenization options
    parser.add_argument('--method', '-m', default='whitespace',
                       choices=['whitespace', 'word', 'character', 'subword'],
                       help='Tokenization method to perform')
    parser.add_argument('--chunk-size', '-c', type=int, default=3,
                       help='Chunk size for subword tokenization')
    
    # Configuration options
    parser.add_argument('--random-seed', '-s', type=int, default=12345,
                       help='Random seed for deterministic results')
    parser.add_argument('--embedding-bit', action='store_true',
                       help='Use embedding bit for extra variation')
    parser.add_argument('--no-normalize-case', action='store_true',
                       help='Do not normalize case to lowercase')
    parser.add_argument('--remove-punctuation', action='store_true',
                       help='Remove punctuation and special characters')
    parser.add_argument('--collapse-repetitions', type=int, default=0,
                       help='Collapse repeated letters (0=no collapse, 1=run-aware, N=collapse to N)')
    
    # Output options
    parser.add_argument('--features', action='store_true',
                       help='Calculate and display features')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze with all tokenization types')
    parser.add_argument('--output', '-o', help='Output file (JSON format)')
    parser.add_argument('--format', choices=['json', 'pretty'], default='pretty',
                       help='Output format')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Quiet mode (minimal output)')
    
    args = parser.parse_args()
    
    # Get input text
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        text = args.text
    
    if not text:
        print("Error: No text provided", file=sys.stderr)
        sys.exit(1)
    
    # Create tokenization engine
    tokenization_engine = TextTokenizationEngine(
        random_seed=args.random_seed,
        embedding_bit=args.embedding_bit,
        normalize_case=not args.no_normalize_case,
        remove_punctuation=args.remove_punctuation,
        collapse_repetitions=args.collapse_repetitions
    )
    
    # Perform analysis
    if args.analyze:
        results = tokenization_engine.analyze_text(text)
    else:
        results = {args.method: tokenization_engine.tokenize(text, args.method, args.features)}
    
    # Format output
    if args.format == 'json':
        output = json.dumps(results, indent=2, ensure_ascii=False)
    else:
        output = format_results(results, args.quiet)
    
    # Output results
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            if not args.quiet:
                print(f"Results saved to {args.output}")
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output)

def format_results(results: Dict[str, Dict[str, Any]], quiet: bool = False) -> str:
    """
    Format results for pretty printing
    
    Args:
        results: Dictionary containing tokenization results
        quiet: If True, suppress detailed output
        
    Returns:
        Formatted string representation of results
    """
    if not isinstance(results, dict):
        raise TypeError(f"results must be dict, got {type(results).__name__}")
    
    output: List[str] = []
    
    if not quiet:
        output.append("SanTOK Results")
        output.append("=" * 50)
    
    for tokenization_method, result in results.items():
        if not quiet:
            output.append(f"\n{tokenization_method.upper()} TOKENIZATION:")
            output.append("-" * 30)
        
        output.append(f"Original Text: {result['original_text']}")
        output.append(f"Preprocessed Text: {result['preprocessed_text']}")
        output.append(f"Tokenized Units: {result['tokens']}")
        output.append(f"Unit Count: {len(result['tokens'])}")
        output.append(f"Frontend Digit Values: {result['frontend_digits']}")
        
        if result['features']:
            features = result['features']
            output.append(f"Statistical Features:")
            output.append(f"  - Length Factor: {features['length_factor']}")
            output.append(f"  - Balance Index: {features['balance_index']}")
            output.append(f"  - Entropy Index: {features['entropy_index']}")
            if not quiet:
                output.append(f"  - Mean: {features['mean']:.2f}")
                output.append(f"  - Variance: {features['variance']:.2f}")
    
    return "\n".join(output)

if __name__ == "__main__":
    main()