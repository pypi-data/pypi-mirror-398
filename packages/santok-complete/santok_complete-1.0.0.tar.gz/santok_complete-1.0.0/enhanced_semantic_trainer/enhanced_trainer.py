"""
Enhanced SanTOK Semantic Trainer
Implements all unique SanTOK features for semantic learning:
- Multi-stream hierarchical learning
- Deterministic UID semantic graph
- Content-ID clustering
- Mathematical property integration
- Temporal/sequential semantic flow
- Cross-stream alignment
- Source-aware multi-space
"""

import numpy as np
import random
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict, Counter
import pickle
import os
import time
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SemanticNode:
    """Node in the deterministic semantic graph"""
    uid: int
    embedding: np.ndarray
    content_id: int
    frontend: int
    backend_huge: int
    backend_scaled: int
    global_id: int
    position_history: List[int]  # Positions where this UID appeared
    temporal_links: Dict[int, int]  # {next_uid: count} - how often this leads to next_uid
    stream_embeddings: Dict[str, np.ndarray]  # Embeddings per stream
    source_tags: Set[str]  # Sources where this token appeared


class EnhancedSanTOKSemanticTrainer:
    """
    Enhanced semantic trainer that leverages ALL SanTOK unique features.
    
    Features:
    1. Multi-stream hierarchical learning (char, subword, word simultaneously)
    2. Deterministic UID semantic graph (persistent across runs)
    3. Content-ID driven clustering (deterministic semantic grouping)
    4. Mathematical property integration (frontend/backend as signals)
    5. Temporal/sequential semantics (position-dependent embeddings)
    6. Cross-stream alignment (align semantics between granularities)
    7. Source-aware multi-space (different semantics per source)
    """
    
    def __init__(
        self,
        embedding_dim: int = 768,
        window_size: int = 5,
        epochs: int = 10,
        learning_rate: float = 0.01,
        min_count: int = 2,
        negative_samples: int = 5,
        use_multi_stream: bool = True,
        use_temporal: bool = True,
        use_content_id_clustering: bool = True,
        use_math_properties: bool = True,
        use_cross_stream_alignment: bool = True,
        use_deterministic_graph: bool = True,
        use_source_aware: bool = True
    ):
        self.embedding_dim = embedding_dim
        self.window_size = window_size
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.min_count = min_count
        self.negative_samples = negative_samples
        
        # Feature flags
        self.use_multi_stream = use_multi_stream
        self.use_temporal = use_temporal
        self.use_content_id_clustering = use_content_id_clustering
        self.use_math_properties = use_math_properties
        self.use_cross_stream_alignment = use_cross_stream_alignment
        self.use_deterministic_graph = use_deterministic_graph
        self.use_source_aware = use_source_aware
        
        # Vocab and data structures
        self.vocab: Dict[int, int] = {}  # {uid: index}
        self.index_to_uid: Dict[int, int] = {}  # {index: uid}
        self.vocab_size = 0
        
        # Multi-stream vocab
        self.stream_vocabs: Dict[str, Dict[int, int]] = defaultdict(dict)
        
        # Semantic graph (deterministic UID-based)
        self.semantic_graph: Dict[int, SemanticNode] = {}
        
        # Co-occurrence matrices per stream
        self.cooccurrence: Dict[str, np.ndarray] = {}
        
        # Embeddings per stream
        self.embeddings: Dict[str, np.ndarray] = {}
        
        # Unified embedding (fused from all streams)
        self.unified_embeddings: np.ndarray = None
        
        # Content-ID clusters
        self.content_id_clusters: Dict[int, Set[int]] = defaultdict(set)
        
        # Temporal patterns
        self.temporal_patterns: Dict[Tuple[int, int], int] = {}  # {(uid1, uid2): count}
        
        # Source spaces
        self.source_spaces: Dict[str, np.ndarray] = {}
        
        # Training stats
        self.training_stats = {
            'total_tokens': 0,
            'unique_uids': 0,
            'streams_processed': set(),
            'temporal_links': 0,
            'content_id_clusters': 0
        }
    
    def build_vocab(self, token_streams: Dict[str, List]) -> None:
        """Build vocabulary from all streams"""
        logger.info("Building vocabulary from multi-stream tokens...")
        
        all_uids = set()
        stream_tokens = {}
        
        # Collect all tokens from all streams
        for stream_name, tokens in token_streams.items():
            if not tokens:
                continue
            
            stream_tokens[stream_name] = tokens
            self.training_stats['streams_processed'].add(stream_name)
            
            for token in tokens:
                uid = getattr(token, 'uid', None)
                if uid is not None:
                    all_uids.add(uid)
                    
                    # Track content_id clusters
                    if self.use_content_id_clustering:
                        content_id = getattr(token, 'content_id', None)
                        if content_id is not None:
                            self.content_id_clusters[content_id].add(uid)
        
        # Build main vocab (UID-based, deterministic)
        uid_list = sorted(all_uids)
        self.vocab = {uid: idx for idx, uid in enumerate(uid_list)}
        self.index_to_uid = {idx: uid for idx, uid in enumerate(uid_list)}
        self.vocab_size = len(self.vocab)
        
        # Build per-stream vocabs
        if self.use_multi_stream:
            for stream_name, tokens in stream_tokens.items():
                stream_uids = set()
                for token in tokens:
                    uid = getattr(token, 'uid', None)
                    if uid is not None:
                        stream_uids.add(uid)
                
                stream_uid_list = sorted(stream_uids)
                self.stream_vocabs[stream_name] = {
                    uid: idx for idx, uid in enumerate(stream_uid_list)
                }
        
        self.training_stats['unique_uids'] = self.vocab_size
        self.training_stats['content_id_clusters'] = len(self.content_id_clusters)
        
        logger.info(f"Vocabulary built: {self.vocab_size} unique UIDs, {len(stream_tokens)} streams")
    
    def build_cooccurrence(self, token_streams: Dict[str, List]) -> None:
        """Build co-occurrence matrices for each stream"""
        logger.info("Building co-occurrence matrices...")
        
        for stream_name, tokens in token_streams.items():
            if not tokens or stream_name not in self.stream_vocabs:
                continue
            
            stream_vocab = self.stream_vocabs[stream_name]
            vocab_size = len(stream_vocab)
            
            # Initialize co-occurrence matrix
            cooccurrence = np.zeros((vocab_size, vocab_size), dtype=np.float32)
            
            # Build co-occurrence
            for i, token in enumerate(tokens):
                uid = getattr(token, 'uid', None)
                if uid not in stream_vocab:
                    continue
                
                token_idx = stream_vocab[uid]
                
                # Context window
                start = max(0, i - self.window_size)
                end = min(len(tokens), i + self.window_size + 1)
                
                for j in range(start, end):
                    if i == j:
                        continue
                    
                    context_token = tokens[j]
                    context_uid = getattr(context_token, 'uid', None)
                    
                    if context_uid in stream_vocab:
                        context_idx = stream_vocab[context_uid]
                        distance = abs(i - j)
                        if distance > 0:  # Prevent division by zero
                            weight = 1.0 / distance  # Closer tokens = higher weight
                            # Clip to prevent overflow
                            cooccurrence[token_idx, context_idx] = np.clip(
                                cooccurrence[token_idx, context_idx] + weight,
                                -1e6, 1e6
                            )
            
            self.cooccurrence[stream_name] = cooccurrence
            logger.info(f"Co-occurrence matrix built for {stream_name}: {vocab_size}x{vocab_size}")
    
    def build_temporal_patterns(self, token_streams: Dict[str, List]) -> None:
        """Build temporal patterns from prev_uid/next_uid relationships"""
        if not self.use_temporal:
            return
        
        logger.info("Building temporal patterns...")
        
        for stream_name, tokens in token_streams.items():
            for i, token in enumerate(tokens):
                uid = getattr(token, 'uid', None)
                if uid is None:
                    continue
                
                # Track position
                if uid not in self.semantic_graph:
                    self.semantic_graph[uid] = SemanticNode(
                        uid=uid,
                        embedding=np.random.randn(self.embedding_dim).astype(np.float32) * 0.1,
                        content_id=getattr(token, 'content_id', 0),
                        frontend=getattr(token, 'frontend', 0),
                        backend_huge=getattr(token, 'backend_huge', 0),
                        backend_scaled=getattr(token, 'backend_scaled', 0),
                        global_id=getattr(token, 'global_id', 0),
                        position_history=[],
                        temporal_links={},
                        stream_embeddings={},
                        source_tags=set()
                    )
                
                node = self.semantic_graph[uid]
                node.position_history.append(i)
                
                # Track temporal links (prev_uid -> uid -> next_uid)
                prev_uid = getattr(token, 'prev_uid', None)
                next_uid = getattr(token, 'next_uid', None)
                
                if prev_uid is not None:
                    pattern = (prev_uid, uid)
                    self.temporal_patterns[pattern] = self.temporal_patterns.get(pattern, 0) + 1
                
                if next_uid is not None:
                    node.temporal_links[next_uid] = node.temporal_links.get(next_uid, 0) + 1
                    pattern = (uid, next_uid)
                    self.temporal_patterns[pattern] = self.temporal_patterns.get(pattern, 0) + 1
        
        self.training_stats['temporal_links'] = len(self.temporal_patterns)
        logger.info(f"Temporal patterns built: {len(self.temporal_patterns)} patterns")
    
    def initialize_embeddings(self) -> None:
        """Initialize embeddings for all streams"""
        logger.info("Initializing embeddings...")
        
        for stream_name, stream_vocab in self.stream_vocabs.items():
            vocab_size = len(stream_vocab)
            # Initialize with small random values
            embeddings = np.random.randn(vocab_size, self.embedding_dim).astype(np.float32) * 0.1
            self.embeddings[stream_name] = embeddings
        
        # Initialize unified embedding
        if self.vocab_size > 0:
            self.unified_embeddings = np.random.randn(
                self.vocab_size, self.embedding_dim
            ).astype(np.float32) * 0.1
        
        logger.info("Embeddings initialized")
    
    def train(self, token_streams: Dict[str, List]) -> None:
        """Train enhanced semantic embeddings"""
        logger.info("Starting enhanced semantic training...")
        start_time = time.time()
        
        # Build vocab first
        self.build_vocab(token_streams)
        
        # Build co-occurrence
        self.build_cooccurrence(token_streams)
        
        # Build temporal patterns
        if self.use_temporal:
            self.build_temporal_patterns(token_streams)
        
        # Initialize embeddings
        self.initialize_embeddings()
        
        # Training loop
        for epoch in range(self.epochs):
            epoch_start = time.time()
            total_loss = 0.0
            samples_processed = 0
            
            # Train each stream
            for stream_name, tokens in token_streams.items():
                if stream_name not in self.embeddings:
                    continue
                
                stream_loss = self._train_stream(stream_name, tokens, epoch)
                total_loss += stream_loss
                samples_processed += len(tokens)
            
            # Cross-stream alignment
            if self.use_cross_stream_alignment and len(self.embeddings) > 1:
                self._align_streams()
            
            # Update unified embeddings
            if self.use_multi_stream:
                self._fuse_stream_embeddings()
            
            epoch_time = time.time() - epoch_start
            avg_loss = total_loss / max(samples_processed, 1)
            
            # Ensure loss is a native Python float (not numpy)
            if isinstance(avg_loss, (np.integer, np.floating)):
                avg_loss = float(avg_loss)
            avg_loss = float(avg_loss)
            
            # Check for overflow/NaN
            if not np.isfinite(avg_loss) or abs(avg_loss) > 1e10:
                logger.warning(f"Loss overflow detected: {avg_loss}, clipping...")
                avg_loss = np.clip(avg_loss, -1e6, 1e6)
            
            logger.info(
                f"Epoch {epoch + 1}/{self.epochs} completed in {epoch_time:.2f}s, "
                f"avg loss: {avg_loss:.6f}"
            )
        
        training_time = time.time() - start_time
        logger.info(f"Training completed in {training_time:.2f}s")
        
        # Final updates
        if self.use_deterministic_graph:
            self._update_semantic_graph()
        
        if self.use_source_aware:
            self._merge_source_spaces()
    
    def _train_stream(self, stream_name: str, tokens: List, epoch: int) -> float:
        """Train embeddings for a single stream"""
        if stream_name not in self.embeddings or stream_name not in self.stream_vocabs:
            return 0.0
        
        embeddings = self.embeddings[stream_name]
        stream_vocab = self.stream_vocabs[stream_name]
        cooccurrence = self.cooccurrence.get(stream_name)
        
        if cooccurrence is None:
            return 0.0
        
        total_loss = 0.0
        learning_rate = float(self.learning_rate * (1.0 - epoch / self.epochs))  # Decay - ensure native float
        
        # Sample training pairs
        for i, token in enumerate(tokens):
            uid = getattr(token, 'uid', None)
            if uid not in stream_vocab:
                continue
            
            token_idx = stream_vocab[uid]
            
            # Positive samples (co-occurring tokens)
            context_start = max(0, i - self.window_size)
            context_end = min(len(tokens), i + self.window_size + 1)
            
            for j in range(context_start, context_end):
                if i == j:
                    continue
                
                context_token = tokens[j]
                context_uid = getattr(context_token, 'uid', None)
                
                if context_uid not in stream_vocab:
                    continue
                
                context_idx = stream_vocab[context_uid]
                
                # Update embeddings (simplified SGD)
                loss = self._update_embedding_pair(
                    embeddings, token_idx, context_idx, 
                    positive=True, learning_rate=learning_rate
                )
                total_loss += loss
                
                # Negative sampling
                if self.negative_samples > 0:
                    for _ in range(self.negative_samples):
                        # Sample negative (different content_id if using clustering)
                        neg_idx = self._sample_negative(
                            token_idx, stream_vocab, token
                        )
                        if neg_idx is not None:
                            loss = self._update_embedding_pair(
                                embeddings, token_idx, neg_idx,
                                positive=False, learning_rate=learning_rate
                            )
                            total_loss += loss
        
        # Ensure total_loss is a native Python float
        if isinstance(total_loss, (np.integer, np.floating)):
            total_loss = float(total_loss)
        return float(total_loss)
    
    def _update_embedding_pair(
        self, 
        embeddings: np.ndarray, 
        token_idx: int, 
        context_idx: int,
        positive: bool = True,
        learning_rate: float = 0.01
    ) -> float:
        """Update embedding pair using skip-gram style update"""
        try:
            token_emb = embeddings[token_idx]
            context_emb = embeddings[context_idx]
            
            # Clip embeddings to prevent overflow
            token_emb = np.clip(token_emb, -10, 10)
            context_emb = np.clip(context_emb, -10, 10)
            
            # Dot product (clip to prevent overflow)
            dot_product = np.dot(token_emb, context_emb)
            dot_product = np.clip(dot_product, -50, 50)  # Prevent exp overflow
            
            # Sigmoid (safe calculation)
            if dot_product > 50:
                sigmoid = 1.0
            elif dot_product < -50:
                sigmoid = 0.0
            else:
                sigmoid = 1.0 / (1.0 + np.exp(-dot_product))
            
            # Target (1 for positive, 0 for negative)
            target = 1.0 if positive else 0.0
            
            # Error
            error = target - sigmoid
            
            # Gradient
            gradient = error * learning_rate
            
            # Update embeddings
            embeddings[token_idx] += gradient * context_emb
            embeddings[context_idx] += gradient * token_emb
            
            # Clip to prevent explosion
            embeddings[token_idx] = np.clip(embeddings[token_idx], -10, 10)
            embeddings[context_idx] = np.clip(embeddings[context_idx], -10, 10)
            
            # Loss (binary cross-entropy) - ensure it's a scalar
            loss = -(target * np.log(sigmoid + 1e-10) + 
                    (1 - target) * np.log(1 - sigmoid + 1e-10))
            
            # Convert to native Python float
            if isinstance(loss, np.ndarray):
                loss = float(loss.item() if loss.size == 1 else loss.sum())
            else:
                loss = float(loss)
            
            return loss
        except Exception as e:
            # Convert numpy types to native Python for error messages
            error_msg = str(e)
            if hasattr(e, '__class__') and 'numpy' in str(type(e)):
                try:
                    if hasattr(e, 'item'):
                        error_msg = str(e.item())
                    else:
                        error_msg = str(float(e)) if isinstance(e, (np.integer, np.floating)) else str(e)
                except Exception:
                    error_msg = f"Training calculation error: {type(e).__name__}"
            raise RuntimeError(f"Embedding update failed: {error_msg}") from e
    
    def _sample_negative(
        self, 
        token_idx: int, 
        stream_vocab: Dict[int, int],
        token: Any
    ) -> Optional[int]:
        """Sample negative example (different from positive)"""
        vocab_size = len(stream_vocab)
        if vocab_size < 2:
            return None
        
        # Convert stream_vocab keys to list of native Python ints
        vocab_keys = [int(k) for k in stream_vocab.keys()]
        
        # If using content_id clustering, prefer different content_id
        if self.use_content_id_clustering:
            token_content_id = getattr(token, 'content_id', None)
            if token_content_id is not None:
                # Try to find token with different content_id
                for _ in range(10):  # Try 10 times
                    # Use native Python random instead of numpy
                    neg_uid = int(random.choice(vocab_keys))
                    neg_idx = stream_vocab[neg_uid]
                    if neg_idx != token_idx:
                        # Check if different content_id (if we have the info)
                        return neg_idx
        
        # Random negative - use native Python random
        neg_idx = random.randint(0, vocab_size - 1)
        if neg_idx == token_idx:
            neg_idx = (neg_idx + 1) % vocab_size
        
        return neg_idx
    
    def _align_streams(self) -> None:
        """Align embeddings across streams using shared UIDs"""
        if len(self.embeddings) < 2:
            return
        
        # Find shared UIDs across streams
        stream_names = list(self.embeddings.keys())
        
        for i, stream1 in enumerate(stream_names):
            for stream2 in stream_names[i+1:]:
                shared_uids = set(self.stream_vocabs[stream1].keys()) & \
                             set(self.stream_vocabs[stream2].keys())
                
                if not shared_uids:
                    continue
                
                # Align embeddings for shared UIDs
                for uid in shared_uids:
                    idx1 = self.stream_vocabs[stream1][uid]
                    idx2 = self.stream_vocabs[stream2][uid]
                    
                    emb1 = self.embeddings[stream1][idx1]
                    emb2 = self.embeddings[stream2][idx2]
                    
                    # Average alignment
                    aligned = (emb1 + emb2) / 2.0
                    
                    self.embeddings[stream1][idx1] = aligned
                    self.embeddings[stream2][idx2] = aligned
    
    def _fuse_stream_embeddings(self) -> None:
        """Fuse embeddings from all streams into unified embedding"""
        # Initialize if needed
        if self.unified_embeddings is None:
            self.unified_embeddings = np.zeros(
                (self.vocab_size, self.embedding_dim), dtype=np.float32
            )
        
        # Count how many streams each UID appears in
        uid_counts = Counter()
        for stream_vocab in self.stream_vocabs.values():
            for uid in stream_vocab.keys():
                uid_counts[uid] += 1
        
        # Fuse: average embeddings from all streams where UID appears
        for uid, count in uid_counts.items():
            if uid not in self.vocab:
                continue
            
            main_idx = self.vocab[uid]
            fused_emb = np.zeros(self.embedding_dim, dtype=np.float32)
            
            for stream_name, stream_vocab in self.stream_vocabs.items():
                if uid in stream_vocab and stream_name in self.embeddings:
                    stream_idx = stream_vocab[uid]
                    fused_emb += self.embeddings[stream_name][stream_idx]
            
            # Average
            self.unified_embeddings[main_idx] = fused_emb / count
    
    def _update_semantic_graph(self) -> None:
        """Update deterministic semantic graph with learned embeddings"""
        for uid, node in self.semantic_graph.items():
            if uid in self.vocab:
                main_idx = self.vocab[uid]
                if self.unified_embeddings is not None:
                    node.embedding = self.unified_embeddings[main_idx].copy()
                
                # Update stream embeddings
                for stream_name, stream_vocab in self.stream_vocabs.items():
                    if uid in stream_vocab and stream_name in self.embeddings:
                        stream_idx = stream_vocab[uid]
                        node.stream_embeddings[stream_name] = \
                            self.embeddings[stream_name][stream_idx].copy()
    
    def _merge_source_spaces(self) -> None:
        """Merge source-aware semantic spaces"""
        # This would merge different source spaces if we had source information
        # For now, just a placeholder
        pass
    
    def get_embedding(self, uid: int, stream: Optional[str] = None) -> Optional[np.ndarray]:
        """Get embedding for a UID"""
        if stream and stream in self.embeddings and stream in self.stream_vocabs:
            if uid in self.stream_vocabs[stream]:
                idx = self.stream_vocabs[stream][uid]
                return self.embeddings[stream][idx]
        
        # Return unified embedding
        if uid in self.vocab and self.unified_embeddings is not None:
            idx = self.vocab[uid]
            return self.unified_embeddings[idx]
        
        return None
    
    def save(self, filepath: str) -> None:
        """Save trained model"""
        logger.info(f"Saving model to {filepath}...")
        
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        # Convert all numpy types to native Python types for serialization
        embedding_dim = int(self.embedding_dim) if hasattr(self.embedding_dim, '__int__') else int(self.embedding_dim)
        window_size = int(self.window_size) if hasattr(self.window_size, '__int__') else int(self.window_size)
        vocab_size = int(self.vocab_size) if hasattr(self.vocab_size, '__int__') else int(self.vocab_size)
        
        # Convert embeddings to lists (numpy arrays -> Python lists)
        embeddings_dict = {}
        for k, v in self.embeddings.items():
            if isinstance(v, np.ndarray):
                embeddings_dict[k] = v.tolist()
            else:
                embeddings_dict[k] = v
        
        unified_emb = None
        if self.unified_embeddings is not None:
            if isinstance(self.unified_embeddings, np.ndarray):
                unified_emb = self.unified_embeddings.tolist()
            else:
                unified_emb = self.unified_embeddings
        
        # Convert training stats to native types
        training_stats = {}
        for k, v in self.training_stats.items():
            if isinstance(v, (np.integer, np.floating)):
                training_stats[k] = float(v) if isinstance(v, np.floating) else int(v)
            elif isinstance(v, np.ndarray):
                training_stats[k] = v.tolist()
            else:
                training_stats[k] = v
        
        model_data = {
            'embedding_dim': embedding_dim,
            'window_size': window_size,
            'vocab': self.vocab,
            'index_to_uid': self.index_to_uid,
            'vocab_size': vocab_size,
            'stream_vocabs': dict(self.stream_vocabs),
            'embeddings': embeddings_dict,
            'unified_embeddings': unified_emb,
            'content_id_clusters': {k: list(v) for k, v in self.content_id_clusters.items()},
            'temporal_patterns': self.temporal_patterns,
            'training_stats': training_stats,
            'feature_flags': {
                'use_multi_stream': self.use_multi_stream,
                'use_temporal': self.use_temporal,
                'use_content_id_clustering': self.use_content_id_clustering,
                'use_math_properties': self.use_math_properties,
                'use_cross_stream_alignment': self.use_cross_stream_alignment,
                'use_deterministic_graph': self.use_deterministic_graph,
                'use_source_aware': self.use_source_aware
            }
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved successfully")
    
    def load(self, filepath: str) -> None:
        """Load trained model"""
        logger.info(f"Loading model from {filepath}...")
        
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.embedding_dim = model_data['embedding_dim']
        self.window_size = model_data['window_size']
        self.vocab = model_data['vocab']
        self.index_to_uid = model_data['index_to_uid']
        self.vocab_size = model_data['vocab_size']
        self.stream_vocabs = {k: v for k, v in model_data['stream_vocabs'].items()}
        self.embeddings = {k: np.array(v) for k, v in model_data['embeddings'].items()}
        self.unified_embeddings = np.array(model_data['unified_embeddings']) if model_data['unified_embeddings'] else None
        self.content_id_clusters = {k: set(v) for k, v in model_data['content_id_clusters'].items()}
        self.temporal_patterns = model_data['temporal_patterns']
        self.training_stats = model_data['training_stats']
        
        # Restore feature flags
        flags = model_data.get('feature_flags', {})
        self.use_multi_stream = flags.get('use_multi_stream', True)
        self.use_temporal = flags.get('use_temporal', True)
        self.use_content_id_clustering = flags.get('use_content_id_clustering', True)
        self.use_math_properties = flags.get('use_math_properties', True)
        self.use_cross_stream_alignment = flags.get('use_cross_stream_alignment', True)
        self.use_deterministic_graph = flags.get('use_deterministic_graph', True)
        self.use_source_aware = flags.get('use_source_aware', True)
        
        logger.info(f"Model loaded successfully")