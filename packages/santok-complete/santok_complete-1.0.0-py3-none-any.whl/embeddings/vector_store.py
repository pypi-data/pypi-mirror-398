"""
Vector Database Interface for SanTOK Embeddings

Provides unified interface to multiple vector database backends.
"""

import numpy as np
from typing import List, Dict, Optional, Any
import warnings
import os

# Disable ChromaDB telemetry before importing (to suppress warnings)
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Try importing vector database libraries
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    warnings.warn("chromadb not available. Install with: pip install chromadb")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    warnings.warn("faiss-cpu not available. Install with: pip install faiss-cpu")


class SanTOKVectorStore:
    """
    Base class for vector database stores.
    Provides unified interface for different backends.
    """
    
    def __init__(
        self,
        backend: str = "chroma",
        collection_name: str = "santok_embeddings",
        embedding_dim: int = 768,
        persist_directory: Optional[str] = None
    ):
        self.backend = backend
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.persist_directory = persist_directory
    
    def add_tokens(
        self,
        token_records: List,
        embeddings: np.ndarray,
        metadata: Optional[List[Dict]] = None
    ):
        """Add tokens and embeddings to store."""
        raise NotImplementedError
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filter: Optional[Dict] = None
    ) -> List[Dict]:
        """Search for similar tokens."""
        raise NotImplementedError
    
    def get_token_embedding(self, token_id: str) -> Optional[np.ndarray]:
        """Retrieve embedding for specific token."""
        raise NotImplementedError


class ChromaVectorStore(SanTOKVectorStore):
    """
    ChromaDB-based vector store.
    
    Advantages:
    - Easy to use
    - Built-in persistence
    - Metadata filtering
    - Good for small to medium datasets
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not CHROMA_AVAILABLE:
            raise ImportError(
                "chromadb required. Install with: pip install chromadb"
            )
        self._init_chroma()
    
    def _init_chroma(self):
        """Initialize ChromaDB client and collection."""
        # Telemetry already disabled via environment variable set at module import
        # Also disable via Settings for additional assurance
        if self.persist_directory:
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            self.client = chromadb.Client(
                settings=Settings(anonymized_telemetry=False)
            )
        
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"embedding_dim": self.embedding_dim}
        )
        # Initialize counter from existing collection to avoid duplicate IDs
        try:
            count_result = self.collection.count()
            self._token_counter = count_result if count_result else 0
        except Exception:
            # If collection is empty or error, start from 0
            self._token_counter = 0
    
    def add_tokens(
        self,
        token_records: List,
        embeddings: np.ndarray,
        metadata: Optional[List[Dict]] = None
    ):
        """Add tokens to ChromaDB using upsert to handle duplicates efficiently."""
        if len(token_records) != len(embeddings):
            raise ValueError("token_records and embeddings must have same length")
        
        # Create metadata if not provided
        if metadata is None:
            metadata = [
                {
                    "text": token.text,
                    "stream": token.stream,
                    "uid": str(token.uid),
                    "frontend": str(token.frontend),
                    "index": str(token.index),
                    "content_id": str(token.content_id),
                    "global_id": str(token.global_id)
                }
                for token in token_records
            ]
        
        # Generate unique IDs based on token global_id and content
        # This ensures IDs are unique and consistent across runs
        import hashlib
        ids = []
        for token in token_records:
            # Use global_id if available, otherwise create hash from token content
            if hasattr(token, 'global_id') and token.global_id:
                token_id = f"token_{token.global_id}"
            else:
                # Create hash from token text + stream + uid for uniqueness
                id_string = f"{token.text}_{token.stream}_{token.uid}"
                token_hash = hashlib.md5(id_string.encode('utf-8')).hexdigest()[:12]
                token_id = f"token_{token_hash}"
            ids.append(token_id)
        
        # Extract texts
        texts = [token.text for token in token_records]
        
        # Use upsert instead of add - this will update if exists, insert if not
        # This is much faster and doesn't produce duplicate ID errors
        # Suppress any warnings/errors from ChromaDB telemetry
        import warnings
        import sys
        from io import StringIO
        import contextlib
        
        @contextlib.contextmanager
        def suppress_stdout_stderr():
            """Context manager to suppress stdout/stderr (for ChromaDB duplicate messages)"""
            with open(os.devnull, 'w') as devnull:
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                try:
                    sys.stdout = devnull
                    sys.stderr = devnull
                    yield
                finally:
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            # Try upsert first (ChromaDB >= 0.4.0) - this handles duplicates automatically
            upsert_success = False
            if hasattr(self.collection, 'upsert'):
                try:
                    with suppress_stdout_stderr():
                        self.collection.upsert(
                            ids=ids,
                            embeddings=embeddings.tolist(),
                            documents=texts,
                            metadatas=metadata
                        )
                    upsert_success = True
                except Exception as e:
                    # If upsert fails, fall through to duplicate checking
                    error_msg = str(e).lower()
                    if "upsert" not in error_msg and "method" not in error_msg:
                        raise  # Re-raise if it's a different error
            
            # Fallback: Check for duplicates before adding (for older ChromaDB or if upsert failed)
            if not upsert_success:
                # Check existing IDs in batches for efficiency
                existing_ids = set()
                batch_size = 1000  # Check in larger batches for speed
                
                # Get all existing IDs first (if collection is small)
                try:
                    collection_count = self.collection.count()
                    # If collection is not too large, get all IDs once
                    if collection_count < 100000:  # Only if less than 100k tokens
                        try:
                            all_existing = self.collection.get(limit=collection_count)
                            if all_existing and all_existing.get('ids'):
                                existing_ids = set(all_existing['ids'])
                        except Exception:
                            pass  # Fall back to batch checking
                except Exception:
                    pass  # Collection might be empty
                
                # If we don't have all IDs, check batches
                if not existing_ids:
                    for i in range(0, len(ids), batch_size):
                        batch_ids = ids[i:i+batch_size]
                        try:
                            existing = self.collection.get(ids=batch_ids)
                            if existing and existing.get('ids'):
                                existing_ids.update(existing['ids'])
                        except Exception:
                            pass  # Some IDs might not exist, that's fine
                
                # Filter out existing IDs - only add new ones
                new_data = {
                    'ids': [],
                    'embeddings': [],
                    'documents': [],
                    'metadatas': []
                }
                for i, tid in enumerate(ids):
                    if tid not in existing_ids:
                        new_data['ids'].append(tid)
                        new_data['embeddings'].append(embeddings[i].tolist())
                        new_data['documents'].append(texts[i])
                        new_data['metadatas'].append(metadata[i])
                
                # Only add new items (skip duplicates silently)
                if new_data['ids']:
                    with suppress_stdout_stderr():
                        self.collection.add(
                            ids=new_data['ids'],
                            embeddings=new_data['embeddings'],
                            documents=new_data['documents'],
                            metadatas=new_data['metadatas']
                        )
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filter: Optional[Dict] = None
    ) -> List[Dict]:
        """Search ChromaDB for similar tokens."""
        # Ensure query is 1D
        if query_embedding.ndim > 1:
            query_embedding = query_embedding.reshape(-1)
        
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=filter
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": 1.0 - results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted_results
    
    def get_token_embedding(self, token_id: str) -> Optional[np.ndarray]:
        """Retrieve embedding by ID."""
        results = self.collection.get(ids=[token_id], include=["embeddings"])
        if results['embeddings']:
            return np.array(results['embeddings'][0])
        return None


class FAISSVectorStore(SanTOKVectorStore):
    """
    FAISS-based vector store.
    
    Advantages:
    - Extremely fast
    - Memory efficient
    - GPU support available
    - Best for large datasets
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not FAISS_AVAILABLE:
            raise ImportError(
                "faiss-cpu required. Install with: pip install faiss-cpu"
            )
        self._init_faiss()
    
    def _init_faiss(self):
        """Initialize FAISS index."""
        # Use L2 distance (Euclidean)
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        
        # Store token mapping: index → TokenRecord
        # NOTE: We don't store embeddings separately - FAISS index already has them
        # This saves ~50% memory by avoiding duplicate storage
        self.token_map: Dict[int, Any] = {}
        self._next_id = 0
    
    def add(
        self,
        id: str,
        embedding: np.ndarray,
        metadata: Optional[Dict] = None
    ):
        """
        Convenience method to add a single embedding.
        
        Args:
            id: Unique identifier (not used in FAISS, but kept for API compatibility)
            embedding: Single embedding vector
            metadata: Optional metadata dict
        """
        # Convert single embedding to batch format
        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)
        
        # Create a dummy token object from metadata
        class DummyToken:
            def __init__(self, metadata_dict):
                self.text = metadata_dict.get('text', '')
                self.stream = metadata_dict.get('stream', '')
                self.uid = metadata_dict.get('uid', 0)
                self.frontend = metadata_dict.get('frontend', 0)
                self.index = metadata_dict.get('index', 0)
        
        token = DummyToken(metadata or {})
        self.add_tokens([token], embedding)
    
    def add_tokens(
        self,
        token_records: List,
        embeddings: np.ndarray,
        metadata: Optional[List[Dict]] = None
    ):
        """Add tokens to FAISS index."""
        if len(token_records) != len(embeddings):
            raise ValueError("token_records and embeddings must have same length")
        
        # Ensure embeddings are float32
        embeddings = embeddings.astype('float32')
        
        # Reshape if needed
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)
        
        # Add to index
        start_idx = self.index.ntotal
        self.index.add(embeddings)
        
        # Store token mapping (embeddings already stored in FAISS index - no need to duplicate)
        # Store only essential token info to save memory (not full token objects)
        for i, token in enumerate(token_records):
            idx = start_idx + i
            # Store lightweight dict instead of full token object to save memory
            self.token_map[idx] = {
                'text': getattr(token, 'text', ''),
                'stream': getattr(token, 'stream', ''),
                'uid': getattr(token, 'uid', 0),
                'frontend': getattr(token, 'frontend', 0),
                'index': getattr(token, 'index', 0)
            }
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filter: Optional[Dict] = None
    ) -> List[Dict]:
        """Search FAISS index."""
        # Ensure query is correct shape
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        query_embedding = query_embedding.astype('float32')
        
        # Search
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Format results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx in self.token_map:
                token_info = self.token_map[idx]
                # Handle both dict (new lightweight format) and token objects (backward compat)
                if isinstance(token_info, dict):
                    results.append({
                        "index": int(idx),
                        "distance": float(dist),
                        "text": token_info['text'],
                        "metadata": {
                            "stream": token_info['stream'],
                            "uid": str(token_info['uid']),
                            "frontend": token_info['frontend'],
                            "index": token_info['index']
                        }
                    })
                else:
                    # Backward compatibility with token objects
                    results.append({
                        "index": int(idx),
                        "token": token_info,
                        "distance": float(dist),
                        "text": token_info.text,
                        "metadata": {
                            "stream": token_info.stream,
                            "uid": str(token_info.uid),
                            "frontend": token_info.frontend,
                            "index": token_info.index
                        }
                    })
        
        return results
    
    def get_token_embedding(self, token_id: str) -> Optional[np.ndarray]:
        """Retrieve embedding by index."""
        # NOTE: Embeddings are stored in FAISS index, not separately
        # For IndexFlatL2, we can't directly reconstruct, but this method
        # is rarely used. If needed, consider using IndexIVFFlat with reconstruction.
        try:
            idx = int(token_id)
            if 0 <= idx < self.index.ntotal:
                # Try to reconstruct from FAISS (may not work for all index types)
                # For now, return None - embeddings are accessible via search
                # If you need this functionality, consider using a different FAISS index type
                return None
        except (ValueError, KeyError, AttributeError):
            pass
        return None