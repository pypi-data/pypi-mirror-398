"""
SanTOK Source Map Integration
==============================

Integration layer for connecting SanTOK Source Map with tokenization
and embedding generation workflows.

Designed for Railway compute.
"""

from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.santok_sources import get_source_map, SourceMetadata
    SOURCE_MAP_AVAILABLE = True
except ImportError:
    SOURCE_MAP_AVAILABLE = False
    print("Warning: Source map module not available")


class SourceMapTokenizer:
    """
    Wrapper for tokenizer that adds source tagging capabilities.
    """
    
    def __init__(self, source_tag: str = "wikipedia", enable_source_tagging: bool = True):
        """
        Initialize source-aware tokenizer.
        
        Args:
            source_tag: Source tag to use for tokenization (e.g., "wikipedia", "arxiv")
            enable_source_tagging: Whether to enable source tagging
        """
        self.source_tag = source_tag
        self.enable_source_tagging = enable_source_tagging and SOURCE_MAP_AVAILABLE
        
        if self.enable_source_tagging:
            self.source_map = get_source_map()
            self.source_metadata = self.source_map.get_source_metadata(source_tag)
            if not self.source_metadata:
                print(f"Warning: Source tag '{source_tag}' not found, disabling source tagging")
                self.enable_source_tagging = False
        else:
            self.source_map = None
            self.source_metadata = None
    
    def tokenize_with_source(
        self,
        text: str,
        method: str = "word",
        algorithm_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tokenize text with source tagging.
        
        Args:
            text: Text to tokenize
            method: Tokenization method
            algorithm_id: Algorithm ID (defaults to method name)
            
        Returns:
            Dictionary with tokens and source metadata
        """
        from src.core.core_tokenizer import TextTokenizer
        
        # Tokenize
        tokenizer = TextTokenizer()
        tokens = tokenizer.tokenize(text, method=method)
        
        result = {
            "tokens": tokens,
            "method": method,
            "token_count": len(tokens)
        }
        
        # Add source metadata if enabled
        if self.enable_source_tagging and self.source_metadata:
            algorithm_id = algorithm_id or f"{method}_tokenization"
            source_tags = self.source_map.get_source_tags_for_token(
                source_tag=self.source_tag,
                algorithm_id=algorithm_id
            )
            result["source_metadata"] = source_tags
            result["source_id"] = source_tags["source_id"]
            result["source_tag"] = self.source_tag
            result["algorithm_id"] = algorithm_id
            result["timestamp"] = source_tags["timestamp"]
        
        return result


class SourceMapEmbeddingGenerator:
    """
    Wrapper for embedding generator that adds source-aware embedding merging.
    """
    
    def __init__(self, enable_source_merging: bool = True):
        """
        Initialize source-aware embedding generator.
        
        Args:
            enable_source_merging: Whether to enable source-based embedding merging
        """
        self.enable_source_merging = enable_source_merging and SOURCE_MAP_AVAILABLE
        
        if self.enable_source_merging:
            self.source_map = get_source_map()
        else:
            self.source_map = None
    
    def generate_with_source(
        self,
        tokens: List[Any],
        source_tag: str = "wikipedia",
        strategy: str = "feature_based",
        algorithm_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate embeddings with source metadata.
        
        Args:
            tokens: List of token objects
            source_tag: Source tag for the tokens
            strategy: Embedding strategy
            algorithm_id: Algorithm ID used
            
        Returns:
            Dictionary with embeddings and source metadata
        """
        from src.embeddings.embedding_generator import SanTOKEmbeddingGenerator
        
        # Generate embeddings
        generator = SanTOKEmbeddingGenerator(strategy=strategy)
        embeddings = generator.generate_embeddings(tokens, strategy=strategy)
        
        result = {
            "embeddings": embeddings,
            "strategy": strategy,
            "embedding_count": len(embeddings) if isinstance(embeddings, list) else 1
        }
        
        # Add source metadata if enabled
        if self.enable_source_merging and self.source_map:
            source_metadata = self.source_map.get_source_metadata(source_tag)
            if source_metadata:
                algorithm_id = algorithm_id or f"{strategy}_embedding"
                source_tags = self.source_map.get_source_tags_for_token(
                    source_tag=source_tag,
                    algorithm_id=algorithm_id
                )
                result["source_metadata"] = source_tags
                result["source_id"] = source_tags["source_id"]
                result["source_tag"] = source_tag
                result["weight"] = source_tags["weight"]
                result["priority"] = source_tags["priority"]
        
        return result
    
    def merge_embeddings_from_sources(
        self,
        embeddings_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Merge embeddings from multiple sources.
        
        Args:
            embeddings_list: List of embedding dictionaries, each with:
                - embeddings: List of embedding vectors
                - source_metadata: Source metadata dict
                
        Returns:
            Dictionary with merged embeddings and combined metadata
        """
        if not self.enable_source_merging or not self.source_map:
            raise ValueError("Source merging not enabled or source map not available")
        
        # Prepare embeddings for merging
        embedding_tuples = []
        for emb_dict in embeddings_list:
            embeddings = emb_dict.get("embeddings", [])
            source_metadata = emb_dict.get("source_metadata", {})
            
            if isinstance(embeddings, list) and len(embeddings) > 0:
                # Use first embedding as representative (or average if multiple)
                if isinstance(embeddings[0], (list, tuple)):
                    # Average multiple embeddings
                    avg_embedding = [
                        sum(vals) / len(vals) 
                        for vals in zip(*embeddings)
                    ]
                else:
                    avg_embedding = embeddings[0]
                
                embedding_tuples.append((avg_embedding, source_metadata))
        
        if not embedding_tuples:
            raise ValueError("No valid embeddings to merge")
        
        # Merge using source map
        merged_embedding, combined_metadata = self.source_map.merge_embeddings(embedding_tuples)
        
        return {
            "merged_embedding": merged_embedding,
            "combined_metadata": combined_metadata,
            "source_count": len(embedding_tuples)
        }


def create_source_aware_workflow(
    text: str,
    source_tag: str = "wikipedia",
    tokenization_method: str = "word",
    embedding_strategy: str = "feature_based"
) -> Dict[str, Any]:
    """
    Complete workflow: tokenization + embedding generation with source tagging.
    
    Args:
        text: Text to process
        source_tag: Source tag
        tokenization_method: Tokenization method
        embedding_strategy: Embedding strategy
        
    Returns:
        Complete workflow result with source metadata
    """
    # Tokenize with source
    tokenizer = SourceMapTokenizer(source_tag=source_tag)
    token_result = tokenizer.tokenize_with_source(
        text=text,
        method=tokenization_method
    )
    
    # Generate embeddings with source
    embedding_gen = SourceMapEmbeddingGenerator()
    embedding_result = embedding_gen.generate_with_source(
        tokens=token_result["tokens"],
        source_tag=source_tag,
        strategy=embedding_strategy,
        algorithm_id=f"{tokenization_method}_tokenization"
    )
    
    return {
        "tokenization": token_result,
        "embedding": embedding_result,
        "source_tag": source_tag,
        "workflow_timestamp": datetime.now(timezone.utc).isoformat()
    }


__all__ = [
    "SourceMapTokenizer",
    "SourceMapEmbeddingGenerator",
    "create_source_aware_workflow",
    "SOURCE_MAP_AVAILABLE"
]