"""
SanTOK Vocabulary Builder
==========================

Builds 60K vocabulary from SanTOK tokenized text.
Uses ONLY SanTOK tokenization - NO external tokenizers.

This is the core of building a SanTOK-only language model.
"""

import numpy as np
from typing import List, Dict, Set, Tuple, Optional
from collections import Counter, defaultdict
from pathlib import Path
import json
import pickle
from tqdm import tqdm

# Import SanTOK components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.core_tokenizer import TextTokenizer, TokenRecord


class SanTOKVocabularyBuilder:
    """
    Build vocabulary from SanTOK tokens.
    
    This creates a 60K vocabulary using ONLY SanTOK's tokenization.
    No external models or algorithms.
    """
    
    def __init__(
        self,
        vocab_size: int = 60000,
        min_frequency: int = 2,
        tokenizer_seed: int = 42,
        embedding_bit: bool = False
    ):
        """
        Initialize vocabulary builder.
        
        Args:
            vocab_size: Target vocabulary size (default: 60K)
            min_frequency: Minimum token frequency to include
            tokenizer_seed: Seed for SanTOK tokenizer
            embedding_bit: Use embedding_bit mode
        """
        self.vocab_size = vocab_size
        self.min_frequency = min_frequency
        self.tokenizer = TextTokenizer(seed=tokenizer_seed, embedding_bit=embedding_bit)
        
        # Vocabulary storage
        self.token_counts: Counter = Counter()
        self.token_to_id: Dict[str, int] = {}
        self.id_to_token: Dict[int, str] = {}
        self.token_metadata: Dict[str, Dict] = {}  # Store token features
        
        # Special tokens (SanTOK style)
        self.special_tokens = {
            '<PAD>': 0,
            '<UNK>': 1,
            '<BOS>': 2,  # Beginning of sequence
            '<EOS>': 3,  # End of sequence
            '<MASK>': 4,  # Mask token for training
        }
        
        # Initialize with special tokens
        self.token_to_id.update(self.special_tokens)
        self.id_to_token = {v: k for k, v in self.special_tokens.items()}
        self.next_id = len(self.special_tokens)
    
    def tokenize_text(self, text: str) -> List[TokenRecord]:
        """
        Tokenize text using SanTOK.
        
        Returns:
            List of TokenRecord objects
        """
        streams = self.tokenizer.build(text)
        
        # Use word stream as primary (most meaningful tokens)
        word_stream = streams.get('word')
        if word_stream and hasattr(word_stream, 'tokens'):
            return word_stream.tokens
        
        # Fallback to first available stream
        if streams:
            first_stream = next(iter(streams.values()))
            if hasattr(first_stream, 'tokens'):
                return first_stream.tokens
        
        return []
    
    def build_vocabulary(self, text_file: Path, chunk_size: int = 1000000) -> Dict[str, int]:
        """
        Build vocabulary from text file.
        
        Args:
            text_file: Path to text file
            chunk_size: Process in chunks of this many characters
        
        Returns:
            Dictionary mapping tokens to IDs
        """
        print("\n" + "="*60)
        print("Building SanTOK Vocabulary (60K)")
        print("="*60)
        print(f"Reading: {text_file}")
        print(f"Target vocab size: {self.vocab_size:,}")
        print(f"Min frequency: {self.min_frequency}")
        
        # First pass: Count all tokens
        print("\n[Pass 1] Tokenizing text and counting vocabulary tokens...")
        print("  (This is NOT just tokenization - we're building a 60K vocabulary)")
        total_chars = text_file.stat().st_size
        processed_chars = 0
        
        with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
            chunk = ""
            for line in tqdm(f, total=total_chars // 100, desc="Building vocabulary from tokens"):
                chunk += line
                processed_chars += len(line)
                
                # Process chunk when it reaches size
                if len(chunk) >= chunk_size:
                    tokens = self.tokenize_text(chunk)
                    for token in tokens:
                        token_text = token.text
                        self.token_counts[token_text] += 1
                        
                        # Store metadata (first occurrence)
                        if token_text not in self.token_metadata:
                            self.token_metadata[token_text] = {
                                'uid': getattr(token, 'uid', 0),
                                'frontend': getattr(token, 'frontend', 0),
                                'stream': getattr(token, 'stream', 'word'),
                                'frequency': 0
                            }
                    
                    chunk = ""
            
            # Process remaining chunk
            if chunk:
                tokens = self.tokenize_text(chunk)
                for token in tokens:
                    token_text = token.text
                    self.token_counts[token_text] += 1
                    if token_text not in self.token_metadata:
                        self.token_metadata[token_text] = {
                            'uid': getattr(token, 'uid', 0),
                            'frontend': getattr(token, 'frontend', 0),
                            'stream': getattr(token, 'stream', 'word'),
                            'frequency': 0
                        }
        
        print(f"\n✓ Found {len(self.token_counts):,} unique tokens")
        print(f"  Total token occurrences: {sum(self.token_counts.values()):,}")
        
        # Filter by minimum frequency
        filtered_counts = {
            token: count 
            for token, count in self.token_counts.items() 
            if count >= self.min_frequency
        }
        
        print(f"  After filtering (min_freq={self.min_frequency}): {len(filtered_counts):,} tokens")
        
        # Second pass: Build vocabulary (top N tokens)
        print("\n[Pass 2] Creating 60K vocabulary from token frequencies...")
        print("  (Selecting top tokens and assigning IDs for language model)")
        
        # Sort by frequency (descending)
        sorted_tokens = sorted(
            filtered_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Take top vocab_size tokens
        top_tokens = sorted_tokens[:self.vocab_size - len(self.special_tokens)]
        
        # Assign IDs
        for token_text, count in tqdm(top_tokens, desc="Creating vocabulary (60K tokens)"):
            if token_text not in self.token_to_id:
                self.token_to_id[token_text] = self.next_id
                self.id_to_token[self.next_id] = token_text
                
                # Update metadata
                if token_text in self.token_metadata:
                    self.token_metadata[token_text]['frequency'] = count
                    self.token_metadata[token_text]['vocab_id'] = self.next_id
                
                self.next_id += 1
        
        print(f"\n✓ Vocabulary built!")
        print(f"  Total vocabulary size: {len(self.token_to_id):,}")
        print(f"  Special tokens: {len(self.special_tokens)}")
        print(f"  Regular tokens: {len(self.token_to_id) - len(self.special_tokens):,}")
        
        return self.token_to_id
    
    def encode(self, text: str) -> List[int]:
        """
        Encode text to token IDs.
        
        Args:
            text: Input text
        
        Returns:
            List of token IDs
        """
        tokens = self.tokenize_text(text)
        token_ids = []
        
        for token in tokens:
            token_text = token.text
            if token_text in self.token_to_id:
                token_ids.append(self.token_to_id[token_text])
            else:
                token_ids.append(self.token_to_id['<UNK>'])
        
        return token_ids
    
    def decode(self, token_ids: List[int]) -> str:
        """
        Decode token IDs to text.
        
        Args:
            token_ids: List of token IDs
        
        Returns:
            Decoded text
        """
        tokens = []
        for token_id in token_ids:
            if token_id in self.id_to_token:
                token_text = self.id_to_token[token_id]
                # Skip special tokens in output
                if token_text not in self.special_tokens:
                    tokens.append(token_text)
        
        return ' '.join(tokens)
    
    def save(self, output_path: Path):
        """Save vocabulary to disk."""
        vocab_data = {
            'token_to_id': self.token_to_id,
            'id_to_token': self.id_to_token,
            'token_metadata': self.token_metadata,
            'token_counts': dict(self.token_counts),
            'vocab_size': len(self.token_to_id),
            'special_tokens': self.special_tokens,
        }
        
        with open(output_path, 'wb') as f:
            pickle.dump(vocab_data, f)
        
        # Also save as JSON (human-readable)
        json_path = output_path.with_suffix('.json')
        json_data = {
            'token_to_id': self.token_to_id,
            'id_to_token': {str(k): v for k, v in self.id_to_token.items()},
            'vocab_size': len(self.token_to_id),
            'special_tokens': self.special_tokens,
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Vocabulary saved:")
        print(f"  Binary: {output_path}")
        print(f"  JSON: {json_path}")
    
    def load(self, input_path: Path):
        """Load vocabulary from disk."""
        with open(input_path, 'rb') as f:
            vocab_data = pickle.load(f)
        
        self.token_to_id = vocab_data['token_to_id']
        self.id_to_token = vocab_data['id_to_token']
        self.token_metadata = vocab_data.get('token_metadata', {})
        self.token_counts = Counter(vocab_data.get('token_counts', {}))
        self.special_tokens = vocab_data.get('special_tokens', {})
        self.next_id = len(self.token_to_id)
        
        print(f"✓ Vocabulary loaded: {len(self.token_to_id):,} tokens")


def main():
    """Example usage."""
    # Build vocabulary from dataset
    text_file = Path("training_data/combined_training_data.txt")
    
    if not text_file.exists():
        print(f"Error: Dataset not found: {text_file}")
        print("Run dataset_downloader.py first!")
        return
    
    builder = SanTOKVocabularyBuilder(vocab_size=60000, min_frequency=2)
    builder.build_vocabulary(text_file)
    
    # Save vocabulary
    vocab_path = Path("models/santok_60k_vocab.pkl")
    vocab_path.parent.mkdir(parents=True, exist_ok=True)
    builder.save(vocab_path)
    
    # Test encode/decode
    test_text = "Hello world! This is SanTOK tokenization."
    token_ids = builder.encode(test_text)
    decoded = builder.decode(token_ids)
    
    print(f"\nTest:")
    print(f"  Original: {test_text}")
    print(f"  Token IDs: {token_ids[:10]}...")
    print(f"  Decoded: {decoded}")


if __name__ == "__main__":
    main()