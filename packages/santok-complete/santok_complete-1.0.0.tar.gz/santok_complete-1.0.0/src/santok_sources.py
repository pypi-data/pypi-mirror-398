"""
SanTOK Source Map - Universal Knowledge Source Registration System
===================================================================

This module provides a comprehensive source map for SanTOK that can integrate
various knowledge sources for token evolution and semantic embedding calibration.

Designed for Railway compute and cloud-based execution.
"""

import hashlib
import json
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import os


@dataclass
class SourceMetadata:
    """Metadata for a knowledge source."""
    source_id: str  # 64-bit hash-based UID
    tag: str  # Source tag (e.g., "wikipedia")
    category: str  # Category (knowledge, technical, domain, symbolic, crossmodal, reinforcement)
    description: str  # Human-readable description
    url: str  # Source URL or identifier
    registered_at: str  # ISO format timestamp
    enabled: bool = True  # Whether source is currently enabled
    weight: float = 1.0  # Weight for embedding merging (default: 1.0)
    priority: int = 5  # Priority level (1-10, higher = more important)


class SanTOKSourceMap:
    """
    Universal source map for SanTOK that manages knowledge sources,
    source UID generation, and source tagging for tokens.
    """
    
    # Core Knowledge Bases (Textual Canon)
    KNOWLEDGE_SOURCES = {
        "wikipedia": {
            "description": "General human knowledge",
            "url": "https://en.wikipedia.org/",
            "notes": "Use Wikipedia API or full dump (monthly updated). Excellent for core linguistic embedding.",
            "weight": 1.0,
            "priority": 9
        },
        "wikidata": {
            "description": "Structured knowledge graph",
            "url": "https://www.wikidata.org/",
            "notes": "Use for entity embedding (UID ↔ text linking). Pairs perfectly with SanTOK's UID system.",
            "weight": 1.0,
            "priority": 9
        },
        "arxiv": {
            "description": "Scientific papers",
            "url": "https://arxiv.org/",
            "notes": "Best for technical corpus training. Focus on CS, math, NLP.",
            "weight": 1.0,
            "priority": 8
        },
        "pubmed": {
            "description": "Biomedical literature",
            "url": "https://pubmed.ncbi.nlm.nih.gov/",
            "notes": "Medical/numerical text domain coverage. Useful for numeric-rich embeddings.",
            "weight": 1.0,
            "priority": 7
        },
        "project_gutenberg": {
            "description": "Classic literature",
            "url": "https://www.gutenberg.org/",
            "notes": "Old linguistic structures and diverse syntax patterns. Boosts long-sequence embedding diversity.",
            "weight": 1.0,
            "priority": 6
        },
        "stackexchange": {
            "description": "QA-style corpora",
            "url": "https://stackexchange.com/",
            "notes": "Captures human reasoning, grammar variance, logic patterns.",
            "weight": 1.0,
            "priority": 7
        },
        "reddit": {
            "description": "Conversational embeddings",
            "url": "https://www.reddit.com/",
            "notes": "For natural, informal, context-switching data. Filter via Pushshift dataset.",
            "weight": 0.8,
            "priority": 5
        },
        "commoncrawl": {
            "description": "General web data",
            "url": "https://commoncrawl.org/",
            "notes": "Trillions of sentences; tokenize into 'frequency patterns.' Use frequency tokenization here.",
            "weight": 1.0,
            "priority": 8
        }
    }
    
    # Technical Corpora
    TECHNICAL_SOURCES = {
        "huggingface_datasets": {
            "description": "Prebuilt NLP datasets",
            "url": "https://huggingface.co/datasets",
            "notes": "Ready-made cleaned datasets (e.g., SQuAD, BooksCorpus, etc.)",
            "weight": 1.0,
            "priority": 8
        },
        "github_corpus": {
            "description": "Public source code",
            "url": "https://github.com",
            "notes": "Excellent for structural tokenization — especially 'grammar' and 'byte' modes.",
            "weight": 1.0,
            "priority": 7
        },
        "paperswithcode": {
            "description": "ML and AI papers + metadata",
            "url": "https://paperswithcode.com",
            "notes": "Use for technical embedding validation and domain alignment.",
            "weight": 1.0,
            "priority": 7
        },
        "openai_cookbook": {
            "description": "Real engineering workflows",
            "url": "https://cookbook.openai.com/",
            "notes": "Useful for understanding code + natural language patterns.",
            "weight": 0.9,
            "priority": 6
        },
        "pytorch_docs": {
            "description": "Framework doc embeddings",
            "url": "https://pytorch.org/docs/",
            "notes": "For programming language semantics, method and API token linking.",
            "weight": 1.0,
            "priority": 6
        },
        "tensorflow_docs": {
            "description": "Tensor-based logic & symbolic graph",
            "url": "https://www.tensorflow.org/api_docs",
            "notes": "Adds symbolic-graph syntax diversity.",
            "weight": 1.0,
            "priority": 6
        }
    }
    
    # Domain-Specific Knowledge
    DOMAIN_SOURCES = {
        "financial_reports": {
            "description": "Finance domain",
            "url": "https://www.sec.gov/edgar.shtml",
            "notes": "Text numerology patterns, excellent for numeric backend embeddings.",
            "weight": 1.0,
            "priority": 6
        },
        "legal_cases": {
            "description": "Law domain",
            "url": "https://www.courtlistener.com/",
            "notes": "Logical reasoning text corpus. Excellent for long token dependencies.",
            "weight": 1.0,
            "priority": 6
        },
        "medical_guidelines": {
            "description": "Medicine domain",
            "url": "https://www.who.int/publications",
            "notes": "Tokenizes technical terms with non-English root stability.",
            "weight": 1.0,
            "priority": 7
        },
        "news_articles": {
            "description": "Journalism domain",
            "url": "https://newsapi.org/",
            "notes": "Temporal linguistic evolution (time-aware embeddings).",
            "weight": 0.9,
            "priority": 5
        },
        "academic_theses": {
            "description": "Research domain",
            "url": "https://ethos.bl.uk/",
            "notes": "Deep-structured reasoning paragraphs. Boosts long-range token coherence.",
            "weight": 1.0,
            "priority": 6
        }
    }
    
    # Structural + Symbolic Data
    SYMBOLIC_SOURCES = {
        "unicode_tables": {
            "description": "Unicode + byte data",
            "url": "https://unicode.org/Public/",
            "notes": "Ensures multilingual + emoji tokenization stability.",
            "weight": 1.0,
            "priority": 8
        },
        "ascii_map": {
            "description": "Base reference map",
            "url": "https://www.asciitable.com/",
            "notes": "Core of your digit + hash algorithms.",
            "weight": 1.0,
            "priority": 9
        },
        "latex_corpus": {
            "description": "Math and equations",
            "url": "https://arxiv.org/archive/cs",
            "notes": "Core dataset for Grammar/Byte algorithms.",
            "weight": 1.0,
            "priority": 7
        },
        "json_schema": {
            "description": "Structural token boundaries",
            "url": "https://json-schema.org/",
            "notes": "Excellent for structural text parsing & embedding segmentation.",
            "weight": 1.0,
            "priority": 7
        },
        "yaml_configs": {
            "description": "Hierarchical structure language",
            "url": "https://yaml.org/spec/",
            "notes": "Adds indentation-based grammar features.",
            "weight": 1.0,
            "priority": 6
        },
        "regex_dataset": {
            "description": "Pattern data",
            "url": "https://regex101.com/",
            "notes": "Directly train frequency & grammar tokenizers.",
            "weight": 1.0,
            "priority": 6
        }
    }
    
    # Semantic + Visual Crosslink
    CROSSMODAL_SOURCES = {
        "wikimedia_images": {
            "description": "Images paired with text",
            "url": "https://commons.wikimedia.org/",
            "notes": "To generate multimodal embeddings later.",
            "weight": 0.9,
            "priority": 5
        },
        "laion_5b": {
            "description": "Large text-image corpus",
            "url": "https://laion.ai/blog/laion-5b/",
            "notes": "For cross-modal linking, aligns visual symbols with SanTOK's numerical backend.",
            "weight": 1.0,
            "priority": 6
        },
        "ocr_corpus": {
            "description": "Text from scanned docs",
            "url": "https://www.robots.ox.ac.uk/~vgg/data/text/",
            "notes": "Real-world noisy text; stress test reconstruction.",
            "weight": 0.8,
            "priority": 5
        }
    }
    
    # Reinforcement Feedback
    REINFORCEMENT_SOURCES = {
        "user_feedback": {
            "description": "Human-in-the-loop ratings",
            "url": "internal_feedback_stream",
            "notes": "For reinforcement calibration of reconstruction quality.",
            "weight": 1.0,
            "priority": 7
        },
        "model_logs": {
            "description": "Token/embedding traces",
            "url": "internal_trace_buffer",
            "notes": "For debugging token-level drift.",
            "weight": 1.0,
            "priority": 8
        },
        "synthetic_corpus": {
            "description": "Generated training text",
            "url": "santok_synthetic_v1",
            "notes": "To expand algorithmic coverage during internal testing.",
            "weight": 0.9,
            "priority": 5
        }
    }
    
    def __init__(self, registry_file: Optional[str] = None):
        """
        Initialize the source map.
        
        Args:
            registry_file: Path to JSON file for persistent source registry.
                          If None, uses in-memory registry only.
        """
        self.registry_file = registry_file or os.path.join(
            os.path.dirname(__file__), '..', 'data', 'santok_sources_registry.json'
        )
        self.sources: Dict[str, SourceMetadata] = {}
        self._initialize_sources()
        
        # Load existing registry if available
        if os.path.exists(self.registry_file):
            self._load_registry()
    
    def _initialize_sources(self):
        """Initialize all built-in sources."""
        categories = {
            "knowledge": self.KNOWLEDGE_SOURCES,
            "technical": self.TECHNICAL_SOURCES,
            "domain": self.DOMAIN_SOURCES,
            "symbolic": self.SYMBOLIC_SOURCES,
            "crossmodal": self.CROSSMODAL_SOURCES,
            "reinforcement": self.REINFORCEMENT_SOURCES
        }
        
        for category, sources in categories.items():
            for tag, info in sources.items():
                if tag not in self.sources:
                    source_id = self._generate_source_uid(tag, info["url"])
                    self.sources[tag] = SourceMetadata(
                        source_id=source_id,
                        tag=tag,
                        category=category,
                        description=info["description"],
                        url=info["url"],
                        registered_at=datetime.now(timezone.utc).isoformat(),
                        enabled=True,
                        weight=info.get("weight", 1.0),
                        priority=info.get("priority", 5)
                    )
    
    @staticmethod
    def _generate_source_uid(tag: str, url: str) -> str:
        """
        Generate a deterministic 64-bit hash-based UID for a source.
        
        Args:
            tag: Source tag
            url: Source URL or identifier
            
        Returns:
            64-bit hexadecimal string (16 characters)
        """
        # Create deterministic identifier
        identifier = f"{tag}:{url}"
        
        # Generate SHA-256 hash
        hash_obj = hashlib.sha256(identifier.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        
        # Use first 16 characters (64 bits) as UID
        return hash_hex[:16]
    
    def get_source_id(self, tag: str) -> Optional[str]:
        """
        Get the source UID for a given tag.
        
        Args:
            tag: Source tag
            
        Returns:
            Source UID if found, None otherwise
        """
        if tag in self.sources:
            return self.sources[tag].source_id
        return None
    
    def get_source_metadata(self, tag: str) -> Optional[SourceMetadata]:
        """
        Get full metadata for a source.
        
        Args:
            tag: Source tag
            
        Returns:
            SourceMetadata if found, None otherwise
        """
        return self.sources.get(tag)
    
    def register_source(
        self,
        tag: str,
        category: str,
        description: str,
        url: str,
        weight: float = 1.0,
        priority: int = 5,
        enabled: bool = True
    ) -> str:
        """
        Register a new source or update an existing one.
        
        Args:
            tag: Unique source tag
            category: Source category
            description: Human-readable description
            url: Source URL or identifier
            weight: Weight for embedding merging
            priority: Priority level (1-10)
            enabled: Whether source is enabled
            
        Returns:
            Source UID
        """
        source_id = self._generate_source_uid(tag, url)
        
        self.sources[tag] = SourceMetadata(
            source_id=source_id,
            tag=tag,
            category=category,
            description=description,
            url=url,
            registered_at=datetime.now(timezone.utc).isoformat(),
            enabled=enabled,
            weight=weight,
            priority=priority
        )
        
        # Save to registry
        self._save_registry()
        
        return source_id
    
    def get_all_sources(self, category: Optional[str] = None, enabled_only: bool = True) -> Dict[str, SourceMetadata]:
        """
        Get all sources, optionally filtered by category and enabled status.
        
        Args:
            category: Filter by category (None for all)
            enabled_only: Only return enabled sources
            
        Returns:
            Dictionary of source tags to SourceMetadata
        """
        filtered = {}
        for tag, metadata in self.sources.items():
            if category and metadata.category != category:
                continue
            if enabled_only and not metadata.enabled:
                continue
            filtered[tag] = metadata
        return filtered
    
    def get_source_tags_for_token(
        self,
        source_tag: str,
        algorithm_id: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate source tagging metadata for a token.
        
        Args:
            source_tag: Source tag
            algorithm_id: Algorithm ID used for tokenization
            timestamp: Timestamp (ISO format), defaults to current time
            
        Returns:
            Dictionary with source_id, algorithm_id, and timestamp
        """
        source_metadata = self.get_source_metadata(source_tag)
        if not source_metadata:
            raise ValueError(f"Unknown source tag: {source_tag}")
        
        return {
            "source_id": source_metadata.source_id,
            "source_tag": source_tag,
            "algorithm_id": algorithm_id or "unknown",
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            "weight": source_metadata.weight,
            "priority": source_metadata.priority
        }
    
    def merge_embeddings(
        self,
        embeddings: List[Tuple[List[float], Dict[str, str]]]
    ) -> Tuple[List[float], Dict[str, any]]:
        """
        Merge embeddings from different sources using weighted averaging.
        
        Args:
            embeddings: List of (embedding_vector, source_metadata) tuples
            
        Returns:
            Tuple of (merged_embedding, combined_metadata)
        """
        if not embeddings:
            raise ValueError("Cannot merge empty embedding list")
        
        if len(embeddings) == 1:
            return embeddings[0]
        
        # Calculate weighted average
        weighted_sum = None
        total_weight = 0.0
        combined_metadata = {
            "source_ids": [],
            "source_tags": [],
            "algorithm_ids": [],
            "weights": [],
            "merged_at": datetime.now(timezone.utc).isoformat()
        }
        
        for embedding, metadata in embeddings:
            weight = metadata.get("weight", 1.0)
            
            if weighted_sum is None:
                weighted_sum = [x * weight for x in embedding]
            else:
                if len(weighted_sum) != len(embedding):
                    raise ValueError("All embeddings must have the same dimension")
                weighted_sum = [s + x * weight for s, x in zip(weighted_sum, embedding)]
            
            total_weight += weight
            
            # Combine metadata
            combined_metadata["source_ids"].append(metadata.get("source_id"))
            combined_metadata["source_tags"].append(metadata.get("source_tag"))
            combined_metadata["algorithm_ids"].append(metadata.get("algorithm_id"))
            combined_metadata["weights"].append(weight)
        
        # Normalize by total weight
        merged_embedding = [x / total_weight for x in weighted_sum]
        
        return merged_embedding, combined_metadata
    
    def get_performance_profile(self, category: Optional[str] = None) -> Dict[str, any]:
        """
        Get hierarchical performance profile of sources.
        
        Args:
            category: Filter by category (None for all)
            
        Returns:
            Dictionary with category-wise source statistics
        """
        profile = {
            "categories": {},
            "total_sources": 0,
            "enabled_sources": 0,
            "total_weight": 0.0,
            "average_priority": 0.0
        }
        
        sources = self.get_all_sources(category=category, enabled_only=False)
        profile["total_sources"] = len(sources)
        profile["enabled_sources"] = sum(1 for s in sources.values() if s.enabled)
        
        total_priority = 0
        for metadata in sources.values():
            category_name = metadata.category
            if category_name not in profile["categories"]:
                profile["categories"][category_name] = {
                    "sources": [],
                    "count": 0,
                    "enabled_count": 0,
                    "total_weight": 0.0,
                    "average_priority": 0.0
                }
            
            cat_profile = profile["categories"][category_name]
            cat_profile["sources"].append({
                "tag": metadata.tag,
                "source_id": metadata.source_id,
                "enabled": metadata.enabled,
                "weight": metadata.weight,
                "priority": metadata.priority
            })
            cat_profile["count"] += 1
            if metadata.enabled:
                cat_profile["enabled_count"] += 1
            cat_profile["total_weight"] += metadata.weight
            cat_profile["average_priority"] += metadata.priority
            profile["total_weight"] += metadata.weight
            total_priority += metadata.priority
        
        # Calculate averages
        if profile["total_sources"] > 0:
            profile["average_priority"] = total_priority / profile["total_sources"]
        
        for cat_profile in profile["categories"].values():
            if cat_profile["count"] > 0:
                cat_profile["average_priority"] = cat_profile["average_priority"] / cat_profile["count"]
        
        return profile
    
    def _save_registry(self):
        """Save source registry to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
            registry_data = {
                tag: asdict(metadata) for tag, metadata in self.sources.items()
            }
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save source registry: {e}")
    
    def _load_registry(self):
        """Load source registry from JSON file."""
        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                registry_data = json.load(f)
            
            for tag, data in registry_data.items():
                if tag not in self.sources:
                    self.sources[tag] = SourceMetadata(**data)
                else:
                    # Update existing source with registry data (preserve weights/priority if custom)
                    existing = self.sources[tag]
                    self.sources[tag] = SourceMetadata(
                        source_id=data.get("source_id", existing.source_id),
                        tag=tag,
                        category=data.get("category", existing.category),
                        description=data.get("description", existing.description),
                        url=data.get("url", existing.url),
                        registered_at=data.get("registered_at", existing.registered_at),
                        enabled=data.get("enabled", existing.enabled),
                        weight=data.get("weight", existing.weight),
                        priority=data.get("priority", existing.priority)
                    )
        except Exception as e:
            print(f"Warning: Could not load source registry: {e}")
    
    def to_dict(self) -> Dict:
        """Convert source map to dictionary."""
        return {
            "sources": {tag: asdict(metadata) for tag, metadata in self.sources.items()},
            "registry_file": self.registry_file,
            "total_sources": len(self.sources)
        }
    
    def __repr__(self) -> str:
        return f"SanTOKSourceMap(total_sources={len(self.sources)}, registry_file='{self.registry_file}')"


# Global instance
_source_map_instance: Optional[SanTOKSourceMap] = None


def get_source_map(registry_file: Optional[str] = None) -> SanTOKSourceMap:
    """
    Get or create the global source map instance.
    
    Args:
        registry_file: Optional registry file path
        
    Returns:
        SanTOKSourceMap instance
    """
    global _source_map_instance
    if _source_map_instance is None:
        _source_map_instance = SanTOKSourceMap(registry_file=registry_file)
    return _source_map_instance


# Export for easy access
__all__ = [
    "SanTOKSourceMap",
    "SourceMetadata",
    "get_source_map",
    "SANTOK_SOURCES"  # For backward compatibility if needed
]

# Create a structured dict export (for compatibility with user's format)
SANTOK_SOURCES = {
    "knowledge": {tag: info["url"] for tag, info in SanTOKSourceMap.KNOWLEDGE_SOURCES.items()},
    "technical": {tag: info["url"] for tag, info in SanTOKSourceMap.TECHNICAL_SOURCES.items()},
    "domain": {tag: info["url"] for tag, info in SanTOKSourceMap.DOMAIN_SOURCES.items()},
    "symbolic": {tag: info["url"] for tag, info in SanTOKSourceMap.SYMBOLIC_SOURCES.items()},
    "crossmodal": {tag: info["url"] for tag, info in SanTOKSourceMap.CROSSMODAL_SOURCES.items()},
    "reinforcement": {tag: info["url"] for tag, info in SanTOKSourceMap.REINFORCEMENT_SOURCES.items()}
}