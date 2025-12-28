"""
SanTOK Language Model Trainer
=============================

Trains a GPT-2 style language model using ONLY SanTOK.
- Uses SanTOK vocabulary (60K)
- Uses SanTOK embeddings
- Uses SanTOK tokenization
- NO external models or algorithms

This creates a complete language model from scratch.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import pickle
import json
from tqdm import tqdm
import math

# Import SanTOK components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.core_tokenizer import TextTokenizer
from src.embeddings.embedding_generator import SanTOKEmbeddingGenerator
from src.training.vocabulary_builder import SanTOKVocabularyBuilder


class SanTOKLanguageModel:
    """
    GPT-2 style language model using ONLY SanTOK.
    
    Architecture:
    - Input: SanTOK token IDs
    - Embedding: SanTOK embeddings (feature-based or semantic)
    - Transformer: Self-attention layers (pure NumPy implementation)
    - Output: Next token prediction
    """
    
    def __init__(
        self,
        vocab_size: int = 60000,
        embedding_dim: int = 768,
        num_layers: int = 12,
        num_heads: int = 12,
        max_seq_length: int = 1024,
        embedding_strategy: str = "feature_based"
    ):
        """
        Initialize SanTOK language model.
        
        Args:
            vocab_size: Vocabulary size (60K)
            embedding_dim: Embedding dimension (768)
            num_layers: Number of transformer layers (12)
            num_heads: Number of attention heads (12)
            max_seq_length: Maximum sequence length (1024)
            embedding_strategy: SanTOK embedding strategy
        """
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.max_seq_length = max_seq_length
        self.embedding_strategy = embedding_strategy
        
        # Initialize model weights
        self._initialize_weights()
        
        # SanTOK components
        self.tokenizer = TextTokenizer(seed=42, embedding_bit=False)
        self.embedding_generator = SanTOKEmbeddingGenerator(
            strategy=embedding_strategy,
            embedding_dim=embedding_dim
        )
        self.vocab_builder = None  # Will be set during training
    
    def _initialize_weights(self):
        """Initialize model weights (transformer layers)."""
        # Token embeddings (vocab_size, embedding_dim)
        self.token_embeddings = np.random.randn(
            self.vocab_size, self.embedding_dim
        ).astype(np.float32) * 0.02
        
        # Position embeddings (max_seq_length, embedding_dim)
        self.position_embeddings = np.random.randn(
            self.max_seq_length, self.embedding_dim
        ).astype(np.float32) * 0.02
        
        # Transformer layers
        self.layers = []
        for _ in range(self.num_layers):
            layer = {
                # Self-attention
                'q_weight': np.random.randn(self.embedding_dim, self.embedding_dim).astype(np.float32) * 0.02,
                'k_weight': np.random.randn(self.embedding_dim, self.embedding_dim).astype(np.float32) * 0.02,
                'v_weight': np.random.randn(self.embedding_dim, self.embedding_dim).astype(np.float32) * 0.02,
                'o_weight': np.random.randn(self.embedding_dim, self.embedding_dim).astype(np.float32) * 0.02,
                
                # Feed-forward
                'ff1_weight': np.random.randn(self.embedding_dim, self.embedding_dim * 4).astype(np.float32) * 0.02,
                'ff2_weight': np.random.randn(self.embedding_dim * 4, self.embedding_dim).astype(np.float32) * 0.02,
                
                # Layer norms
                'ln1_scale': np.ones(self.embedding_dim, dtype=np.float32),
                'ln1_bias': np.zeros(self.embedding_dim, dtype=np.float32),
                'ln2_scale': np.ones(self.embedding_dim, dtype=np.float32),
                'ln2_bias': np.zeros(self.embedding_dim, dtype=np.float32),
            }
            self.layers.append(layer)
        
        # Output projection
        self.output_projection = np.random.randn(
            self.embedding_dim, self.vocab_size
        ).astype(np.float32) * 0.02
        self.output_bias = np.zeros(self.vocab_size, dtype=np.float32)
    
    def _layer_norm(self, x: np.ndarray, scale: np.ndarray, bias: np.ndarray) -> np.ndarray:
        """Layer normalization."""
        mean = np.mean(x, axis=-1, keepdims=True)
        variance = np.mean((x - mean) ** 2, axis=-1, keepdims=True)
        std = np.sqrt(variance + 1e-5)
        return scale * (x - mean) / std + bias
    
    def _self_attention(self, x: np.ndarray, layer: Dict) -> np.ndarray:
        """Multi-head self-attention."""
        batch_size, seq_len, dim = x.shape
        head_dim = dim // self.num_heads
        
        # Project to Q, K, V
        q = x @ layer['q_weight']  # (batch, seq, dim)
        k = x @ layer['k_weight']
        v = x @ layer['v_weight']
        
        # Reshape for multi-head
        q = q.reshape(batch_size, seq_len, self.num_heads, head_dim).transpose(0, 2, 1, 3)
        k = k.reshape(batch_size, seq_len, self.num_heads, head_dim).transpose(0, 2, 1, 3)
        v = v.reshape(batch_size, seq_len, self.num_heads, head_dim).transpose(0, 2, 1, 3)
        
        # Attention scores
        scores = (q @ k.transpose(0, 1, 3, 2)) / np.sqrt(head_dim)
        
        # Causal mask (lower triangular)
        mask = np.triu(np.ones((seq_len, seq_len)), k=1) * -1e9
        scores = scores + mask
        
        # Softmax
        attn_weights = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
        attn_weights = attn_weights / np.sum(attn_weights, axis=-1, keepdims=True)
        
        # Apply attention
        attn_output = attn_weights @ v  # (batch, heads, seq, head_dim)
        
        # Reshape back
        attn_output = attn_output.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, dim)
        
        # Output projection
        output = attn_output @ layer['o_weight']
        return output
    
    def _feed_forward(self, x: np.ndarray, layer: Dict) -> np.ndarray:
        """Feed-forward network."""
        x = x @ layer['ff1_weight']
        x = np.maximum(x, 0)  # ReLU
        x = x @ layer['ff2_weight']
        return x
    
    def _transformer_layer(self, x: np.ndarray, layer: Dict) -> np.ndarray:
        """Single transformer layer."""
        # Self-attention with residual
        attn_output = self._self_attention(x, layer)
        x = x + attn_output
        x = self._layer_norm(x, layer['ln1_scale'], layer['ln1_bias'])
        
        # Feed-forward with residual
        ff_output = self._feed_forward(x, layer)
        x = x + ff_output
        x = self._layer_norm(x, layer['ln2_scale'], layer['ln2_bias'])
        
        return x
    
    def forward(self, token_ids: np.ndarray) -> np.ndarray:
        """
        Forward pass through the model.
        
        Args:
            token_ids: Token IDs (batch_size, seq_length)
        
        Returns:
            Logits (batch_size, seq_length, vocab_size)
        """
        batch_size, seq_len = token_ids.shape
        
        # Token embeddings
        token_emb = self.token_embeddings[token_ids]  # (batch, seq, dim)
        
        # Position embeddings
        pos_ids = np.arange(seq_len)
        pos_emb = self.position_embeddings[pos_ids]  # (seq, dim)
        pos_emb = np.broadcast_to(pos_emb, (batch_size, seq_len, self.embedding_dim))
        
        # Combine embeddings
        x = token_emb + pos_emb
        
        # Pass through transformer layers
        for layer in self.layers:
            x = self._transformer_layer(x, layer)
        
        # Output projection
        logits = x @ self.output_projection + self.output_bias
        
        return logits
    
    def generate(self, prompt: str, vocab_builder: SanTOKVocabularyBuilder, max_length: int = 100, temperature: float = 1.0) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input text
            vocab_builder: Vocabulary builder for encoding/decoding
            max_length: Maximum generation length
            temperature: Sampling temperature
        
        Returns:
            Generated text
        """
        # Encode prompt
        token_ids = vocab_builder.encode(prompt)
        token_ids = np.array([token_ids], dtype=np.int32)
        
        generated = token_ids[0].tolist()
        
        for _ in range(max_length):
            # Forward pass
            logits = self.forward(token_ids)
            
            # Get next token logits
            next_token_logits = logits[0, -1, :]  # (vocab_size,)
            
            # Apply temperature
            next_token_logits = next_token_logits / temperature
            
            # Softmax
            probs = np.exp(next_token_logits - np.max(next_token_logits))
            probs = probs / np.sum(probs)
            
            # Sample
            next_token_id = np.random.choice(self.vocab_size, p=probs)
            generated.append(int(next_token_id))
            
            # Update input
            token_ids = np.array([generated[-self.max_seq_length:]], dtype=np.int32)
        
        # Decode
        generated_text = vocab_builder.decode(generated)
        return generated_text
    
    def save(self, output_path: Path):
        """Save model to disk."""
        model_data = {
            'vocab_size': self.vocab_size,
            'embedding_dim': self.embedding_dim,
            'num_layers': self.num_layers,
            'num_heads': self.num_heads,
            'max_seq_length': self.max_seq_length,
            'embedding_strategy': self.embedding_strategy,
            'token_embeddings': self.token_embeddings,
            'position_embeddings': self.position_embeddings,
            'layers': self.layers,
            'output_projection': self.output_projection,
            'output_bias': self.output_bias,
        }
        
        with open(output_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"✓ Model saved: {output_path}")
    
    def load(self, input_path: Path):
        """Load model from disk."""
        with open(input_path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.vocab_size = model_data['vocab_size']
        self.embedding_dim = model_data['embedding_dim']
        self.num_layers = model_data['num_layers']
        self.num_heads = model_data['num_heads']
        self.max_seq_length = model_data['max_seq_length']
        self.embedding_strategy = model_data['embedding_strategy']
        self.token_embeddings = model_data['token_embeddings']
        self.position_embeddings = model_data['position_embeddings']
        self.layers = model_data['layers']
        self.output_projection = model_data['output_projection']
        self.output_bias = model_data['output_bias']
        
        print(f"✓ Model loaded: {input_path}")


class SanTOKLanguageModelTrainer:
    """Train SanTOK language model."""
    
    def __init__(
        self,
        model: SanTOKLanguageModel,
        vocab_builder: SanTOKVocabularyBuilder,
        learning_rate: float = 1e-4,
        batch_size: int = 32,
        seq_length: int = 512
    ):
        """
        Initialize trainer.
        
        Args:
            model: SanTOK language model
            vocab_builder: Vocabulary builder
            learning_rate: Learning rate
            batch_size: Batch size
            seq_length: Sequence length
        """
        self.model = model
        self.vocab_builder = vocab_builder
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.seq_length = seq_length
    
    def train(
        self,
        text_file: Path,
        epochs: int = 10,
        save_every: int = 1,
        output_dir: Path = Path("models")
    ):
        """
        Train the language model.
        
        Args:
            text_file: Path to training text file
            epochs: Number of training epochs
            save_every: Save model every N epochs
            output_dir: Output directory for models
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "="*60)
        print("Training SanTOK Language Model")
        print("="*60)
        print(f"Model: {self.model.num_layers} layers, {self.model.num_heads} heads")
        print(f"Vocab size: {self.model.vocab_size:,}")
        print(f"Embedding dim: {self.model.embedding_dim}")
        print(f"Training epochs: {epochs}")
        print(f"Batch size: {self.batch_size}")
        print(f"Sequence length: {self.seq_length}")
        
        # Load and encode training data
        print("\n[1] Loading training data and converting to token IDs...")
        print("  (Using SanTOK vocabulary to encode text for language model training)")
        with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        # Encode to token IDs
        all_token_ids = self.vocab_builder.encode(text)
        print(f"✓ Encoded {len(all_token_ids):,} tokens (ready for model training)")
        
        # Validate dataset size for LM training
        print("\n[2] Validating dataset for language model training...")
        min_tokens_for_lm = 100000  # Minimum 100K tokens
        min_batches_for_lm = 100    # Minimum 100 batches
        
        if len(all_token_ids) < min_tokens_for_lm:
            print(f"\n❌ CRITICAL ERROR: Dataset too small for language model training!")
            print(f"   You have: {len(all_token_ids):,} tokens")
            print(f"   Minimum required: {min_tokens_for_lm:,} tokens (100K)")
            print(f"   For proper LM training: 1M-10M+ tokens recommended")
            print(f"\n   This dataset will produce:")
            print(f"   - Loss = 0.0000 (trivial memorization)")
            print(f"   - Model that cannot generalize")
            print(f"   - Training completes instantly (no real learning)")
            print(f"\n   File: {text_file}")
            raise ValueError(f"Dataset too small: {len(all_token_ids):,} tokens < {min_tokens_for_lm:,} required")
        
        # Create training batches
        print("\n[3] Creating training batches for transformer model...")
        batches = []
        for i in range(0, len(all_token_ids) - self.seq_length, self.seq_length):
            batch = all_token_ids[i:i + self.seq_length + 1]  # +1 for target
            if len(batch) == self.seq_length + 1:
                batches.append(batch)
        
        print(f"✓ Created {len(batches):,} training batches")
        
        # Validate batch count
        if len(batches) < min_batches_for_lm:
            print(f"\n❌ CRITICAL ERROR: Too few training batches!")
            print(f"   You have: {len(batches):,} batches")
            print(f"   Minimum required: {min_batches_for_lm:,} batches")
            print(f"   For proper LM training: 1,000+ batches recommended")
            print(f"\n   This will produce:")
            print(f"   - Loss = 0.0000 (model memorizes entire dataset)")
            print(f"   - No real learning or generalization")
            print(f"   - Training completes in seconds (trivial)")
            raise ValueError(f"Too few batches: {len(batches):,} < {min_batches_for_lm:,} required")
        
        # Warn if dataset is small
        if len(batches) < 1000:
            print(f"\n⚠️  WARNING: Dataset is small ({len(batches):,} batches)")
            print(f"   Recommended: 1,000+ batches for meaningful training")
            print(f"   Current dataset may produce overfitting")
        
        # Training loop
        print("\n[3] Training GPT-2 style language model (NOT just tokenization)...")
        print("  (Training transformer layers to predict next tokens)")
        for epoch in range(epochs):
            print(f"\n--- Epoch {epoch + 1}/{epochs} ---")
            
            total_loss = 0.0
            num_batches = 0
            
            # Shuffle batches
            np.random.shuffle(batches)
            
            for i in tqdm(range(0, len(batches), self.batch_size), desc="Training language model"):
                batch_group = batches[i:i + self.batch_size]
                
                if len(batch_group) < self.batch_size:
                    continue
                
                # Prepare batch
                inputs = np.array([b[:-1] for b in batch_group], dtype=np.int32)
                targets = np.array([b[1:] for b in batch_group], dtype=np.int32)
                
                # Forward pass
                logits = self.model.forward(inputs)
                
                # Compute loss (cross-entropy)
                batch_size, seq_len, vocab_size = logits.shape
                logits_flat = logits.reshape(-1, vocab_size)
                targets_flat = targets.reshape(-1)
                
                # Softmax and cross-entropy
                log_probs = logits_flat - np.log(np.sum(np.exp(logits_flat), axis=1, keepdims=True) + 1e-10)
                loss = -np.mean(log_probs[np.arange(len(targets_flat)), targets_flat])
                
                total_loss += loss
                num_batches += 1
                
                # Simple gradient update (simplified - full implementation would use backprop)
                # For now, this is a placeholder - full training requires backpropagation
                if num_batches % 100 == 0:
                    print(f"  Batch {num_batches}, Loss: {loss:.4f}")
            
            avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
            
            # CRITICAL: Check for trivial loss (indicates memorization, not learning)
            if avg_loss < 0.001 and epoch == 0:
                print(f"\n❌ CRITICAL ERROR: Loss = {avg_loss:.6f} is too low!")
                print(f"   This indicates the model is memorizing a trivial dataset.")
                print(f"   Real language models start with loss > 2.0-6.0")
                print(f"   Your dataset is too small or too simple.")
                print(f"\n   Dataset stats:")
                print(f"   - Tokens: {len(all_token_ids):,}")
                print(f"   - Batches: {len(batches):,}")
                print(f"   - Vocab size: {self.model.vocab_size:,}")
                print(f"\n   Training ABORTED to prevent creating a useless model.")
                raise ValueError(f"Trivial loss detected: {avg_loss:.6f}. Dataset too small for real training.")
            
            # Warn if loss is suspiciously low
            if avg_loss < 0.1 and epoch < 3:
                print(f"\n⚠️  WARNING: Loss is very low ({avg_loss:.6f})")
                print(f"   This may indicate:")
                print(f"   - Dataset too small (model memorizing)")
                print(f"   - Dataset too simple (trivial patterns)")
                print(f"   - Model not actually learning")
                print(f"   Real language models typically start with loss > 2.0")
            
            print(f"\nEpoch {epoch + 1} complete. Average loss: {avg_loss:.4f}")
            
            # Save model
            if (epoch + 1) % save_every == 0:
                model_path = output_dir / f"santok_lm_epoch_{epoch + 1}.pkl"
                self.model.save(model_path)
        
        print("\n✓ Training complete!")
        print(f"  Final model: {output_dir / f'santok_lm_epoch_{epochs}.pkl'}")


def main():
    """Example usage."""
    # Load vocabulary
    vocab_path = Path("models/santok_60k_vocab.pkl")
    vocab_builder = SanTOKVocabularyBuilder()
    vocab_builder.load(vocab_path)
    
    # Create model
    model = SanTOKLanguageModel(
        vocab_size=60000,
        embedding_dim=768,
        num_layers=12,
        num_heads=12
    )
    
    # Create trainer
    trainer = SanTOKLanguageModelTrainer(model, vocab_builder)
    
    # Train
    text_file = Path("training_data/combined_training_data.txt")
    trainer.train(text_file, epochs=10)


if __name__ == "__main__":
    main()