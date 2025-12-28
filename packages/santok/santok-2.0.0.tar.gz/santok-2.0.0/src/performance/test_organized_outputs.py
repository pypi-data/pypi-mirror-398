#!/usr/bin/env python3
"""
Test script to verify the organized output system works correctly
"""

import os
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.core.core_tokenizer import tokenize_text

def test_organized_outputs():
    """Test the organized output system"""
    print("[INFO] Testing Organized Output System")
    print("=" * 50)
    
    # Test text
    test_text = "Hello world! This is a test."
    
    # Test all tokenizer types
    tokenizer_types = [
        "space", "word", "char", "grammar", "subword", 
        "subword_bpe", "subword_syllable", "subword_frequency", "byte"
    ]
    
    # Check if Outputs folder structure exists
    outputs_dir = "Outputs"
    if not os.path.exists(outputs_dir):
        print("❌ Outputs folder not found!")
        return False
    
    print(f"✅ Outputs folder exists: {outputs_dir}")
    
    # Check each tokenizer folder
    for tokenizer_type in tokenizer_types:
        tokenizer_dir = os.path.join(outputs_dir, tokenizer_type)
        if not os.path.exists(tokenizer_dir):
            print(f"❌ {tokenizer_type} folder not found!")
            return False
        
        # Check subfolders
        subfolders = ["JSON", "CSV", "TEXT", "XML"]
        for subfolder in subfolders:
            subfolder_path = os.path.join(tokenizer_dir, subfolder)
            if not os.path.exists(subfolder_path):
                print(f"❌ {tokenizer_type}/{subfolder} folder not found!")
                return False
        
        print(f"✅ {tokenizer_type} folder structure complete")
    
    print("\n📁 Folder Structure:")
    print("Outputs/")
    for tokenizer_type in tokenizer_types:
        print(f"├── {tokenizer_type}/")
        print(f"│   ├── JSON/")
        print(f"│   ├── CSV/")
        print(f"│   ├── TEXT/")
        print(f"│   └── XML/")
    
    print("\n🧪 Testing Tokenization...")
    
    # Test tokenization for each type
    for tokenizer_type in tokenizer_types:
        try:
            tokens = tokenize_text(test_text, tokenizer_type)
            print(f"✅ {tokenizer_type}: {len(tokens)} tokens")
        except Exception as e:
            print(f"❌ {tokenizer_type}: Error - {e}")
            return False
    
    print("\n🎉 All tests passed! Organized output system is working correctly.")
    return True

if __name__ == "__main__":
    test_organized_outputs()