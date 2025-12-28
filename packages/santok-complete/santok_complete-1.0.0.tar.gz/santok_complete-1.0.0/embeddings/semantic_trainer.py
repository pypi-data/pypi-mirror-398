"""
SanTOK Semantic Embedding Trainer

Trains semantic embeddings from SanTOK tokens WITHOUT using pretrained models.
Uses self-supervised learning on SanTOK's mathematical features to capture
semantic relationships.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import pickle
import os

# Try to import sparse matrix support
try:
    from scipy import sparse
    SPARSE_AVAILABLE = True
except ImportError:
    SPARSE_AVAILABLE = False
    # Fallback: use dict-based sparse representation
    pass


class SanTOKSemanticTrainer:
    """
    Trains semantic embeddings from SanTOK tokens using:
    - Co-occurrence patterns (which tokens appear together)
    - Context windows (neighbor relationships)
    - Content similarity (content_id relationships)
    - Global patterns (global_id relationships)
    
    NO pretrained models - learns from SanTOK's structure itself.
    """
    
    def __init__(
        self,
        embedding_dim: int = 768,
        window_size: int = 5,
        min_count: int = 2,
        learning_rate: float = 0.01,
        epochs: int = 10,
        max_vocab_size: Optional[int] = None
    ):
        """
        Initialize semantic trainer.
        
        Args:
            embedding_dim: Target embedding dimension
            window_size: Context window size for co-occurrence
            min_count: Minimum token frequency to include
            learning_rate: Learning rate for training
            epochs: Number of training epochs
            max_vocab_size: Maximum vocabulary size (None = no limit)
        """
        self.embedding_dim = embedding_dim
        self.window_size = window_size
        self.min_count = min_count
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.max_vocab_size = max_vocab_size  # None = no limit
        
        # Vocabulary: token_uid -> index
        self.vocab: Dict[int, int] = {}
        self.reverse_vocab: Dict[int, int] = {}
        self.token_counts: Dict[int, int] = defaultdict(int)
        
        # Embedding matrices
        self.token_embeddings: Optional[np.ndarray] = None  # (vocab_size, embedding_dim)
        self.context_embeddings: Optional[np.ndarray] = None  # (vocab_size, embedding_dim)
        
        # Co-occurrence statistics
        # Use sparse representation for large vocabularies
        self.cooccurrence_matrix: Optional[np.ndarray] = None
        self.cooccurrence_dict: Optional[Dict[Tuple[int, int], float]] = None
        
    def build_vocab(self, token_streams: List) -> None:
        """
        Build vocabulary from token streams.
        
        Args:
            token_streams: List of TokenRecord objects
        """
        print("Building vocabulary from SanTOK tokens...")
        
        # Count token frequencies
        for token in token_streams:
            uid = getattr(token, 'uid', 0)
            if uid:
                self.token_counts[uid] += 1
        
        # Filter by min_count and create vocab
        filtered_tokens = {
            uid: count for uid, count in self.token_counts.items()
            if count >= self.min_count
        }
        
        # Sort by frequency and limit vocabulary size for semantic training
        sorted_tokens = sorted(filtered_tokens.items(), key=lambda x: x[1], reverse=True)
        
        # Limit to top N most frequent tokens to avoid memory issues (if max_vocab_size is set)
        if self.max_vocab_size is not None and len(sorted_tokens) > self.max_vocab_size:
            print(f"⚠️  Vocabulary size ({len(sorted_tokens):,}) exceeds limit ({self.max_vocab_size:,})")
            print(f"   Limiting to top {self.max_vocab_size:,} most frequent tokens for semantic training")
            sorted_tokens = sorted_tokens[:self.max_vocab_size]
        
        # Create vocabulary mapping
        for idx, (uid, count) in enumerate(sorted_tokens):
            self.vocab[uid] = idx
            self.reverse_vocab[idx] = uid
        
        vocab_size = len(self.vocab)
        print(f"Vocabulary size: {vocab_size:,} tokens")
        
        # Initialize embedding matrices
        self.token_embeddings = np.random.randn(vocab_size, self.embedding_dim).astype(np.float32) * 0.1
        self.context_embeddings = np.random.randn(vocab_size, self.embedding_dim).astype(np.float32) * 0.1
        
        # Normalize initial embeddings
        self.token_embeddings = self._normalize(self.token_embeddings)
        self.context_embeddings = self._normalize(self.context_embeddings)
    
    def build_cooccurrence(self, token_streams: List) -> None:
        """
        Build co-occurrence matrix from SanTOK's neighbor relationships.
        
        Uses:
        - prev_uid, next_uid (immediate neighbors)
        - content_id (semantic content similarity)
        - Same stream tokens (contextual relationships)
        
        For large vocabularies (>50k), uses sparse representation.
        """
        print("Building co-occurrence matrix from SanTOK features...")
        
        vocab_size = len(self.vocab)
        
        # For large vocabularies, use dict-based sparse representation
        if vocab_size > 50000:
            print(f"⚠️  Large vocabulary ({vocab_size:,}). Using sparse co-occurrence representation.")
            self.cooccurrence_dict = defaultdict(float)
            use_sparse = True
        else:
            # For smaller vocabularies, use dense matrix
            self.cooccurrence_matrix = np.zeros((vocab_size, vocab_size), dtype=np.float32)
            use_sparse = False
        
        # Group tokens by stream for context windows
        stream_tokens: Dict[str, List] = defaultdict(list)
        for token in token_streams:
            uid = getattr(token, 'uid', 0)
            stream = getattr(token, 'stream', 'word')
            if uid in self.vocab:
                stream_tokens[stream].append(token)
        
        # Build co-occurrence from SanTOK's neighbor structure
        for stream, tokens in stream_tokens.items():
            for i, token in enumerate(tokens):
                uid = getattr(token, 'uid', 0)
                if uid not in self.vocab:
                    continue
                
                token_idx = self.vocab[uid]
                
                # Immediate neighbors (prev_uid, next_uid)
                prev_uid = getattr(token, 'prev_uid', None)
                next_uid = getattr(token, 'next_uid', None)
                
                if prev_uid and prev_uid in self.vocab:
                    prev_idx = self.vocab[prev_uid]
                    if use_sparse:
                        self.cooccurrence_dict[(token_idx, prev_idx)] += 1.0
                        self.cooccurrence_dict[(prev_idx, token_idx)] += 1.0
                    else:
                        self.cooccurrence_matrix[token_idx, prev_idx] += 1.0
                        self.cooccurrence_matrix[prev_idx, token_idx] += 1.0
                
                if next_uid and next_uid in self.vocab:
                    next_idx = self.vocab[next_uid]
                    if use_sparse:
                        self.cooccurrence_dict[(token_idx, next_idx)] += 1.0
                        self.cooccurrence_dict[(next_idx, token_idx)] += 1.0
                    else:
                        self.cooccurrence_matrix[token_idx, next_idx] += 1.0
                        self.cooccurrence_matrix[next_idx, token_idx] += 1.0
                
                # Context window (using SanTOK's index) - limit for large vocabularies
                start = max(0, i - self.window_size)
                end = min(len(tokens), i + self.window_size + 1)
                
                # Limit context window processing for large vocabularies
                max_context_tokens = 100 if use_sparse else len(tokens)
                context_count = 0
                
                for j in range(start, end):
                    if i == j or context_count >= max_context_tokens:
                        continue
                    context_token = tokens[j]
                    context_uid = getattr(context_token, 'uid', 0)
                    if context_uid in self.vocab:
                        context_idx = self.vocab[context_uid]
                        # Weight by distance
                        distance = abs(i - j)
                        weight = 1.0 / distance
                        if use_sparse:
                            self.cooccurrence_dict[(token_idx, context_idx)] += weight
                        else:
                            self.cooccurrence_matrix[token_idx, context_idx] += weight
                        context_count += 1
                
                # Content-based similarity - skip for large vocabularies (too expensive)
                if not use_sparse:
                    content_id = getattr(token, 'content_id', 0)
                    for other_token in tokens[:100]:  # Limit to first 100 tokens
                        other_uid = getattr(other_token, 'uid', 0)
                        other_content_id = getattr(other_token, 'content_id', 0)
                        if other_uid in self.vocab and other_uid != uid:
                            # Similar content_id suggests semantic similarity
                            if abs(content_id - other_content_id) < 100:  # Threshold
                                other_idx = self.vocab[other_uid]
                                self.cooccurrence_matrix[token_idx, other_idx] += 0.5
        
        if use_sparse:
            # Normalize sparse co-occurrence dict
            row_sums = defaultdict(float)
            for (i, j), val in self.cooccurrence_dict.items():
                row_sums[i] += val
            
            # Normalize
            normalized_dict = {}
            for (i, j), val in self.cooccurrence_dict.items():
                if row_sums[i] > 0:
                    normalized_dict[(i, j)] = val / row_sums[i]
            self.cooccurrence_dict = normalized_dict
            print(f"Sparse co-occurrence dictionary built: {len(self.cooccurrence_dict):,} pairs")
        else:
            # Normalize co-occurrence matrix
            row_sums = self.cooccurrence_matrix.sum(axis=1, keepdims=True)
            row_sums[row_sums == 0] = 1  # Avoid division by zero
            self.cooccurrence_matrix = self.cooccurrence_matrix / row_sums
            print(f"Co-occurrence matrix built: {vocab_size}x{vocab_size}")
    
    def train(self, token_streams: List) -> None:
        """
        Train semantic embeddings using Skip-gram style learning.
        
        Learns from:
        - Co-occurrence patterns
        - SanTOK's neighbor structure
        - Content similarity
        """
        if self.token_embeddings is None:
            raise ValueError("Must call build_vocab() first")
        
        print(f"Training semantic embeddings (epochs={self.epochs})...")
        
        vocab_size = len(self.vocab)
        
        # Check if using sparse or dense co-occurrence
        use_sparse = self.cooccurrence_dict is not None
        
        for epoch in range(self.epochs):
            total_loss = 0.0
            num_updates = 0
            
            if use_sparse:
                # Train on sparse co-occurrence dict
                cooccurrence_pairs = list(self.cooccurrence_dict.items())
                # Sample a subset for training (to avoid too many iterations)
                max_pairs = min(100000, len(cooccurrence_pairs))
                if len(cooccurrence_pairs) > max_pairs:
                    import random
                    cooccurrence_pairs = random.sample(cooccurrence_pairs, max_pairs)
                
                for (i, j), weight in cooccurrence_pairs:
                    # Positive sample (co-occurring tokens)
                    loss = self._update_embeddings(i, j, positive=True)
                    total_loss += loss
                    num_updates += 1
                    
                    # Negative sampling (random non-co-occurring tokens)
                    for _ in range(5):  # 5 negative samples per positive
                        neg_j = np.random.randint(0, vocab_size)
                        if (i, neg_j) not in self.cooccurrence_dict:
                            self._update_embeddings(i, neg_j, positive=False)
            else:
                # Train on dense co-occurrence matrix
                for i in range(vocab_size):
                    for j in range(vocab_size):
                        if self.cooccurrence_matrix[i, j] > 0:
                            # Positive sample (co-occurring tokens)
                            loss = self._update_embeddings(i, j, positive=True)
                            total_loss += loss
                            num_updates += 1
                            
                            # Negative sampling (random non-co-occurring tokens)
                            for _ in range(5):  # 5 negative samples per positive
                                neg_j = np.random.randint(0, vocab_size)
                                if self.cooccurrence_matrix[i, neg_j] == 0:
                                    self._update_embeddings(i, neg_j, positive=False)
            
            avg_loss = total_loss / max(num_updates, 1)
            print(f"Epoch {epoch + 1}/{self.epochs}, Loss: {avg_loss:.4f}")
            
            # Normalize embeddings periodically
            if (epoch + 1) % 2 == 0:
                self.token_embeddings = self._normalize(self.token_embeddings)
                self.context_embeddings = self._normalize(self.context_embeddings)
        
        print("Training complete!")
    
    def _update_embeddings(self, token_idx: int, context_idx: int, positive: bool = True) -> float:
        """
        Update embeddings using gradient descent.
        
        Args:
            token_idx: Index of token
            context_idx: Index of context token
            positive: True if positive sample, False if negative
        """
        # Get embeddings
        token_emb = self.token_embeddings[token_idx]
        context_emb = self.context_embeddings[context_idx]
        
        # Compute similarity (dot product)
        similarity = np.dot(token_emb, context_emb)
        
        # Sigmoid activation
        sigmoid = 1.0 / (1.0 + np.exp(-similarity))
        
        # Compute loss and gradient
        if positive:
            target = 1.0
            loss = -np.log(sigmoid + 1e-10)
        else:
            target = 0.0
            loss = -np.log(1.0 - sigmoid + 1e-10)
        
        # Gradient
        error = target - sigmoid
        
        # Update embeddings
        token_grad = error * context_emb
        context_grad = error * token_emb
        
        self.token_embeddings[token_idx] += self.learning_rate * token_grad
        self.context_embeddings[context_idx] += self.learning_rate * context_grad
        
        return loss
    
    def _normalize(self, embeddings: np.ndarray) -> np.ndarray:
        """L2 normalize embeddings."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        return embeddings / norms
    
    def get_embedding(self, token_uid: int) -> Optional[np.ndarray]:
        """
        Get trained embedding for a token UID.
        
        Args:
            token_uid: SanTOK token UID
            
        Returns:
            Embedding vector or None if not in vocabulary
        """
        if token_uid not in self.vocab:
            return None
        
        idx = self.vocab[token_uid]
        # Use token_embeddings (can also average with context_embeddings)
        return self.token_embeddings[idx]
    
    def save(self, filepath: str) -> None:
        """Save trained model."""
        model_data = {
            'vocab': self.vocab,
            'reverse_vocab': self.reverse_vocab,
            'token_embeddings': self.token_embeddings,
            'context_embeddings': self.context_embeddings,
            'embedding_dim': self.embedding_dim,
            'token_counts': dict(self.token_counts)
        }
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"Model saved to {filepath}")
    
    def load(self, filepath: str) -> None:
        """Load trained model."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.vocab = model_data['vocab']
        self.reverse_vocab = model_data['reverse_vocab']
        self.token_embeddings = model_data['token_embeddings']
        self.context_embeddings = model_data['context_embeddings']
        self.embedding_dim = model_data['embedding_dim']
        self.token_counts = defaultdict(int, model_data['token_counts'])
        print(f"Model loaded from {filepath}")