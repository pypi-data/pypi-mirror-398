"""
Parallel Processing Module for SanTOK
Supports multi-threading and multi-processing for large text tokenization
"""

import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
from typing import List, Dict, Any, Callable

def chunk_text(text: str, chunk_size: int = 50000) -> List[str]:
    """Split text into chunks for parallel processing"""
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks

def process_chunk_sequential(chunk_data: tuple) -> List[Dict[str, Any]]:
    """Process a single chunk sequentially"""
    chunk_text, tokenizer_func, tokenizer_type, chunk_index = chunk_data
    
    # Import here to avoid circular imports
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from src.core.core_tokenizer import (
        tokenize_space, tokenize_word, tokenize_char, tokenize_grammar,
        tokenize_subword, tokenize_bytes, reconstruct_from_tokens
    )
    
    tokenizer_map = {
        'space': tokenize_space,
        'word': tokenize_word,
        'char': tokenize_char,
        'grammar': tokenize_grammar,
        'subword': lambda x: tokenize_subword(x, 3, 'fixed'),
        'bpe': lambda x: tokenize_subword(x, 3, 'bpe'),
        'syllable': lambda x: tokenize_subword(x, 3, 'syllable'),
        'frequency': lambda x: tokenize_subword(x, 3, 'frequency'),
        'byte': tokenize_bytes
    }
    
    tokenizer_func = tokenizer_map.get(tokenizer_type, tokenize_word)
    tokens = tokenizer_func(chunk_text)
    
    # Adjust token IDs to be unique across chunks
    for token in tokens:
        token['id'] += chunk_index * 1000000  # Offset by chunk index
    
    return tokens

def tokenize_parallel_threaded(text: str, tokenizer_type: str = 'word', 
                              max_workers: int = None, chunk_size: int = 50000) -> List[Dict[str, Any]]:
    """Tokenize text using multiple threads"""
    if len(text) <= chunk_size:
        # Use sequential processing for small texts
        return process_chunk_sequential((text, None, tokenizer_type, 0))
    
    chunks = chunk_text(text, chunk_size)
    chunk_data = [(chunk, None, tokenizer_type, i) for i, chunk in enumerate(chunks)]
    
    if max_workers is None:
        max_workers = min(len(chunks), multiprocessing.cpu_count())
    
    all_tokens = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_chunk_sequential, data) for data in chunk_data]
        
        for future in futures:
            chunk_tokens = future.result()
            all_tokens.extend(chunk_tokens)
    
    return all_tokens

def tokenize_parallel_multiprocess(text: str, tokenizer_type: str = 'word', 
                                  max_workers: int = None, chunk_size: int = 50000) -> List[Dict[str, Any]]:
    """Tokenize text using multiple processes"""
    if len(text) <= chunk_size:
        # Use sequential processing for small texts
        return process_chunk_sequential((text, None, tokenizer_type, 0))
    
    chunks = chunk_text(text, chunk_size)
    chunk_data = [(chunk, None, tokenizer_type, i) for i, chunk in enumerate(chunks)]
    
    if max_workers is None:
        max_workers = min(len(chunks), multiprocessing.cpu_count())
    
    all_tokens = []
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_chunk_sequential, data) for data in chunk_data]
        
        for future in futures:
            chunk_tokens = future.result()
            all_tokens.extend(chunk_tokens)
    
    return all_tokens

def benchmark_parallel_performance(text: str, tokenizer_type: str = 'word', 
                                 chunk_size: int = 50000) -> Dict[str, Any]:
    """Benchmark parallel vs sequential performance"""
    results = {}
    
    # Sequential processing
    start_time = time.time()
    sequential_tokens = process_chunk_sequential((text, None, tokenizer_type, 0))
    sequential_time = time.time() - start_time
    
    # Threaded processing
    start_time = time.time()
    threaded_tokens = tokenize_parallel_threaded(text, tokenizer_type, chunk_size=chunk_size)
    threaded_time = time.time() - start_time
    
    # Multi-process processing
    start_time = time.time()
    multiprocess_tokens = tokenize_parallel_multiprocess(text, tokenizer_type, chunk_size=chunk_size)
    multiprocess_time = time.time() - start_time
    
    results = {
        'text_length': len(text),
        'chunk_size': chunk_size,
        'sequential_time': sequential_time,
        'threaded_time': threaded_time,
        'multiprocess_time': multiprocess_time,
        'sequential_speed': len(text) / sequential_time if sequential_time > 0 else 0,
        'threaded_speed': len(text) / threaded_time if threaded_time > 0 else 0,
        'multiprocess_speed': len(text) / multiprocess_time if multiprocess_time > 0 else 0,
        'threaded_speedup': sequential_time / threaded_time if threaded_time > 0 else 0,
        'multiprocess_speedup': sequential_time / multiprocess_time if multiprocess_time > 0 else 0,
        'token_count': len(sequential_tokens)
    }
    
    return results

def auto_parallel_tokenize(text: str, tokenizer_type: str = 'word', 
                          threshold: int = 100000) -> List[Dict[str, Any]]:
    """Automatically choose between sequential and parallel processing based on text size"""
    if len(text) <= threshold:
        # Use sequential processing for small texts
        return process_chunk_sequential((text, None, tokenizer_type, 0))
    else:
        # Use parallel processing for large texts
        return tokenize_parallel_threaded(text, tokenizer_type)

# Language-specific parallel processing
def tokenize_multilang_parallel(text: str, tokenizer_type: str = 'word', 
                               language: str = None, max_workers: int = None) -> List[Dict[str, Any]]:
    """Tokenize multilingual text with parallel processing"""
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    # detect_language may not exist - provide fallback
    try:
        from src.core.core_tokenizer import detect_language
    except ImportError:
        def detect_language(text):
            # Simple language detection placeholder
            return 'en'
    
    if language is None:
        language = detect_language(text)
    
    # For CJK languages, use character-based tokenization for better parallelization
    if language == "cjk" and tokenizer_type == "word":
        tokenizer_type = "char"
    
    return auto_parallel_tokenize(text, tokenizer_type)