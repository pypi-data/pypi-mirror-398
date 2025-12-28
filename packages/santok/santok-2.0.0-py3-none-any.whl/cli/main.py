#!/usr/bin/env python3
"""
SanTOK CLI - Command Line Interface
"""

import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.core_tokenizer import tokenize_text, reconstruct_from_tokens

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description='SanTOK - Advanced Text Tokenization Framework')
    parser.add_argument('text', help='Text to tokenize')
    parser.add_argument('-t', '--tokenizer', default='word', 
                       choices=['space', 'word', 'char', 'grammar', 'subword', 'subword_bpe', 'subword_syllable', 'subword_frequency', 'byte'],
                       help='Tokenizer type to use')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-f', '--format', default='json', choices=['json', 'csv', 'txt', 'xml'],
                       help='Output format')
    parser.add_argument('--decode', action='store_true', help='Decode tokens back to text')
    parser.add_argument('--tokens', help='Tokens to decode (JSON format)')
    
    args = parser.parse_args()
    
    if args.decode:
        if not args.tokens:
            print("Error: --tokens required for decoding")
            sys.exit(1)
        
        # Decode tokens
        import json
        try:
            tokens = json.loads(args.tokens)
            reconstructed = reconstruct_from_tokens(tokens, args.tokenizer)
            print(f"Reconstructed text: {reconstructed}")
        except Exception as e:
            print(f"Error decoding tokens: {e}")
            sys.exit(1)
    else:
        # Tokenize text
        print(f"Tokenizing with {args.tokenizer} tokenizer...")
        tokens = tokenize_text(args.text, args.tokenizer)
        
        print(f"Generated {len(tokens)} tokens")
        
        if args.output:
            # Save to file
            save_tokens(tokens, args.output, args.format)
            print(f"Tokens saved to {args.output}")
        else:
            # Print to console
            if args.format == 'json':
                import json
                print(json.dumps(tokens, indent=2))
            elif args.format == 'csv':
                print("ID,Text,Position,Length,Type")
                for token in tokens:
                    print(f"{token['id']},{token['text']},{token.get('position', '')},{token.get('length', '')},{token.get('type', '')}")
            elif args.format == 'txt':
                print(' '.join([token['text'] for token in tokens]))
            elif args.format == 'xml':
                print('<?xml version="1.0" encoding="UTF-8"?>')
                print('<tokens>')
                for token in tokens:
                    print(f'  <token id="{token["id"]}" position="{token.get("position", "")}" length="{token.get("length", "")}" type="{token.get("type", "")}">{token["text"]}</token>')
                print('</tokens>')

def save_tokens(tokens, output_path, format_type):
    """Save tokens to file in specified format"""
    with open(output_path, 'w', encoding='utf-8') as f:
        if format_type == 'json':
            import json
            json.dump(tokens, f, indent=2)
        elif format_type == 'csv':
            f.write("ID,Text,Position,Length,Type\n")
            for token in tokens:
                f.write(f"{token['id']},{token['text']},{token.get('position', '')},{token.get('length', '')},{token.get('type', '')}\n")
        elif format_type == 'txt':
            f.write(' '.join([token['text'] for token in tokens]))
        elif format_type == 'xml':
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<tokens>\n')
            for token in tokens:
                f.write(f'  <token id="{token["id"]}" position="{token.get("position", "")}" length="{token.get("length", "")}" type="{token.get("type", "")}">{token["text"]}</token>\n')
            f.write('</tokens>\n')

if __name__ == "__main__":
    main()