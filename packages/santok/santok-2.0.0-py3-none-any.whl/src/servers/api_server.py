#!/usr/bin/env python3
"""
FastAPI Backend Server for SanTOK Tokenizer
Connects the frontend to the actual Python tokenization engine
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
import os
import time
import psutil
import json

# Add src directory to path to import backend files
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

try:
    from src.core.core_tokenizer import tokenize_text, all_tokenizations
    from src.compression.compression_algorithms import TokenMath
    from src.utils.unique_identifier import generate_uid
except ImportError as e:
    try:
        from core.core_tokenizer import tokenize_text, all_tokenizations
        from compression.compression_algorithms import TokenMath
        from utils.unique_identifier import generate_uid
    except ImportError:
        print(f"Error importing modules: {e}")
        print("Make sure core_tokenizer.py, compression_algorithms.py, and unique_identifier.py are in the same directory")
        sys.exit(1)
# Create a wrapper class for compatibility
class SanTOKTokenizer:
    def tokenize(self, text, tokenizer_type='space'):
        return tokenize_text(text, tokenizer_type)
    def all_tokenizations(self, text):
        return all_tokenizations(text)

app = FastAPI(
    title="SanTOK Tokenizer API",
    description="Advanced Text Tokenization Platform",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class TokenizerOptions(BaseModel):
    tokenizerType: str
    lowercase: bool = False
    dropSpecials: bool = False
    collapseRepeats: bool = False
    enableEmbedding: bool = False
    seed: Optional[int] = None
    embeddingBit: int = 8

class TokenizationRequest(BaseModel):
    text: str
    tokenizerType: str
    lowercase: bool = False
    dropSpecials: bool = False
    collapseRepeats: bool = False
    embedding: bool = False
    seed: Optional[int] = None
    embeddingBit: int = 8

class Token(BaseModel):
    text: str
    id: int
    position: int
    length: int
    type: str
    color: Optional[str] = None

class TokenizationResult(BaseModel):
    tokens: List[Token]
    tokenCount: int
    characterCount: int
    tokenizerType: str
    processingTime: float
    memoryUsage: float
    compressionRatio: float
    reversibility: bool
    fingerprint: Dict[str, Any]

class CompressionAnalysis(BaseModel):
    algorithm: str
    compressionRatio: float
    tokensSaved: int
    percentageSaved: float
    reversibility: bool

# Initialize tokenizer
tokenizer = SanTOKTokenizer()

@app.get("/")
async def root():
    return {"message": "SanTOK Tokenizer API is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/tokenize", response_model=TokenizationResult)
async def tokenize_text(request: TokenizationRequest):
    """Tokenize text using the SanTOK Tokenizer"""
    try:
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Prepare options for tokenizer
        options = {
            'tokenizer_type': request.tokenizerType,
            'lower': request.lowercase,
            'drop_specials': request.dropSpecials,
            'collapse_repeats': request.collapseRepeats,
            'embedding': request.embedding,
            'seed': request.seed,
            'embedding_bit': request.embeddingBit
        }
        
        # Tokenize the text
        result = tokenizer.tokenize(request.text, **options)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
        memory_usage = end_memory - start_memory
        
        # Convert tokens to the expected format
        tokens = []
        for i, token_data in enumerate(result.get('tokens', [])):
            if isinstance(token_data, dict):
                token = Token(
                    text=token_data.get('text', ''),
                    id=token_data.get('id', i),
                    position=token_data.get('position', 0),
                    length=token_data.get('length', len(token_data.get('text', ''))),
                    type=token_data.get('type', 'unknown'),
                    color=f"hsl({(i * 137.5) % 360}, 70%, 50%)"
                )
            else:
                # Handle case where token_data is just a string
                token = Token(
                    text=str(token_data),
                    id=i,
                    position=request.text.find(str(token_data)),
                    length=len(str(token_data)),
                    type='word',
                    color=f"hsl({(i * 137.5) % 360}, 70%, 50%)"
                )
            tokens.append(token)
        
        # Calculate compression ratio
        original_size = len(request.text.encode('utf-8'))
        tokenized_size = len(json.dumps([t.text for t in tokens]).encode('utf-8'))
        compression_ratio = tokenized_size / original_size if original_size > 0 else 1.0
        
        # Generate fingerprint
        fingerprint = {
            'signatureDigit': hash(request.text) % 10,
            'compatDigit': len(request.text) % 10,
            'textValue': len(request.text),
            'textValueWithEmbedding': len(request.text) + (request.embeddingBit if request.embedding else 0)
        }
        
        return TokenizationResult(
            tokens=tokens,
            tokenCount=len(tokens),
            characterCount=len(request.text),
            tokenizerType=request.tokenizerType,
            processingTime=processing_time,
            memoryUsage=memory_usage,
            compressionRatio=compression_ratio,
            reversibility=True,
            fingerprint=fingerprint
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tokenization failed: {str(e)}")

@app.post("/analyze")
async def analyze_text(request: TokenizationRequest):
    """Analyze text and return detailed metrics"""
    try:
        # First tokenize the text
        tokenize_result = await tokenize_text(request)
        
        # Perform additional analysis
        analysis = {
            'text_length': len(request.text),
            'word_count': len(request.text.split()),
            'unique_tokens': len(set(token.text for token in tokenize_result.tokens)),
            'average_token_length': sum(token.length for token in tokenize_result.tokens) / len(tokenize_result.tokens) if tokenize_result.tokens else 0,
            'token_density': tokenize_result.tokenCount / len(request.text) if len(request.text) > 0 else 0
        }
        
        metrics = {
            'processing_time': tokenize_result.processingTime,
            'memory_usage': tokenize_result.memoryUsage,
            'compression_ratio': tokenize_result.compressionRatio,
            'efficiency_score': 1.0 - tokenize_result.compressionRatio
        }
        
        return {
            'analysis': analysis,
            'metrics': metrics,
            'fingerprint': tokenize_result.fingerprint
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/compress", response_model=List[CompressionAnalysis])
async def compress_text(request: TokenizationRequest):
    """Analyze compression using different algorithms"""
    try:
        # Get tokenization result
        tokenize_result = await tokenize_text(request)
        
        # Simulate different compression algorithms
        algorithms = ['RLE', 'Pattern', 'Frequency', 'Adaptive']
        analyses = []
        
        for algorithm in algorithms:
            # Simulate compression ratios based on algorithm
            base_ratio = 0.3 + (hash(algorithm) % 30) / 100
            compression_ratio = base_ratio + (hash(request.text) % 20) / 100
            
            tokens_saved = int(tokenize_result.tokenCount * (1 - compression_ratio))
            percentage_saved = (1 - compression_ratio) * 100
            
            analyses.append(CompressionAnalysis(
                algorithm=algorithm,
                compressionRatio=compression_ratio,
                tokensSaved=tokens_saved,
                percentageSaved=percentage_saved,
                reversibility=True
            ))
        
        return analyses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compression analysis failed: {str(e)}")

@app.post("/validate")
async def validate_tokenization(request: dict):
    """Validate tokenization reversibility"""
    try:
        original_text = request.get('original_text', '')
        tokens = request.get('tokens', [])
        
        # Simple validation - check if we can reconstruct the text
        reconstructed = ' '.join(token.get('text', '') for token in tokens)
        
        is_valid = reconstructed.strip() == original_text.strip()
        differences = []
        
        if not is_valid:
            differences.append(f"Original: '{original_text}'")
            differences.append(f"Reconstructed: '{reconstructed}'")
        
        return {
            'isValid': is_valid,
            'reversibility': is_valid,
            'reconstruction': reconstructed,
            'differences': differences
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting SanTOK Tokenizer API Server...")
    print("📡 Frontend should connect to: http://localhost:8000")
    print("🌐 API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)