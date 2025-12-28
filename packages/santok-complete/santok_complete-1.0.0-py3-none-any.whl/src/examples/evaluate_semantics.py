"""
evaluate_semantics.py - SanTOK Evaluation Utility
--------------------------------------------------
Compares Feature-Based vs Hybrid embeddings
to verify if semantic relationships have improved.
"""

import os
import numpy as np
import sys
import pickle
import json
from pathlib import Path

# Add project root to sys.path if needed for src.* imports.
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.embeddings.vector_store import FAISSVectorStore
from src.embeddings.embedding_generator import SanTOKEmbeddingGenerator
from src.embeddings.semantic_trainer import SanTOKSemanticTrainer
from src.core.core_tokenizer import tokenize_text


# --------------------------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------------------------
output_dir = "workflow_output"
tokens_path = os.path.join(output_dir, "tokens.pkl")
metadata_path = os.path.join(output_dir, "embedding_batches_metadata.json")
semantic_model_path = os.path.join(output_dir, "semantic_model.pkl")
# Save vector store to avoid reloading from scratch
vector_store_cache_dir = os.path.join(output_dir, "vector_store_cache")
vector_store_cache_file = os.path.join(vector_store_cache_dir, "evaluation_vector_store.faiss")
vector_store_cache_meta = os.path.join(vector_store_cache_dir, "evaluation_vector_store_meta.pkl")
# Semantic vector store cache
semantic_vector_store_cache_file = os.path.join(vector_store_cache_dir, "semantic_evaluation_vector_store.faiss")
semantic_vector_store_cache_meta = os.path.join(vector_store_cache_dir, "semantic_evaluation_vector_store_meta.pkl")

TEST_TERMS = [
    "artificial", "intelligence",
    "machine", "learning",
    "neural", "network",
    "data", "science",
    "model", "training",
]

TOP_N = 5
# Use VERY small batch count to avoid memory issues (5 batches = 250k tokens max)
MAX_BATCHES_FOR_EVAL = 5


# --------------------------------------------------------------------------
# HELPERS
# --------------------------------------------------------------------------

def load_tokens(tokens_file):
    """Load tokens from disk with proper import handling."""
    print(f"\n[INFO] Loading tokens from {tokens_file}...")
    try:
        import types
        from pathlib import Path
        
        project_root = Path(__file__).parent.parent.parent
        src_path = project_root / 'src'
        
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        # Create mock modules for pickle compatibility
        if 'core' not in sys.modules:
            core_module = types.ModuleType('core')
            sys.modules['core'] = core_module
        if 'core.core_tokenizer' not in sys.modules:
            core_tokenizer_module = types.ModuleType('core.core_tokenizer')
            sys.modules['core.core_tokenizer'] = core_tokenizer_module
            try:
                from src.core.core_tokenizer import TokenRecord, TokenStream
                core_tokenizer_module.TokenRecord = TokenRecord
                core_tokenizer_module.TokenStream = TokenStream
            except ImportError:
                pass
        
        # Custom unpickler
        class CustomUnpickler(pickle.Unpickler):
            def find_class(self, module, name):
                if module == 'core.core_tokenizer' or module == 'core':
                    try:
                        from src.core.core_tokenizer import TokenRecord, TokenStream
                        if name == 'TokenRecord':
                            return TokenRecord
                        elif name == 'TokenStream':
                            return TokenStream
                    except ImportError:
                        pass
                return super().find_class(module, name)
        
        with open(tokens_file, 'rb') as f:
            try:
                unpickler = CustomUnpickler(f)
                tokens = unpickler.load()
            except Exception:
                f.seek(0)
                tokens = pickle.load(f)
        
        print(f"[OK] Loaded {len(tokens):,} tokens")
        return tokens
    except Exception as e:
        print(f"[ERROR] Failed to load tokens: {e}")
        import traceback
        traceback.print_exc()
        return None


def load_vector_store_cache(output_dir, cache_file=None, cache_meta=None):
    """Load vector store from cache if it exists."""
    if cache_file is None:
        cache_file = vector_store_cache_file
    if cache_meta is None:
        cache_meta = vector_store_cache_meta
    
    if not os.path.exists(cache_file) or not os.path.exists(cache_meta):
        return None
    
    try:
        print("[INFO] Loading vector store from cache...")
        import faiss
        
        # Load FAISS index
        index = faiss.read_index(cache_file)
        
        # Load metadata
        with open(cache_meta, 'rb') as f:
            cache_meta_data = pickle.load(f)
        
        # Recreate vector store
        vector_store = FAISSVectorStore(embedding_dim=cache_meta_data['embedding_dim'])
        vector_store.index = index
        vector_store.token_map = cache_meta_data['token_map']
        
        print(f"[OK] Loaded vector store from cache ({cache_meta_data['total_tokens']:,} tokens)")
        return vector_store
    except Exception as e:
        print(f"[WARNING] Failed to load vector store cache: {e}")
        return None


def save_vector_store_cache(vector_store, output_dir, cache_file=None, cache_meta=None):
    """Save vector store to disk for fast reloading."""
    if cache_file is None:
        cache_file = vector_store_cache_file
    if cache_meta is None:
        cache_meta = vector_store_cache_meta
    
    try:
        os.makedirs(vector_store_cache_dir, exist_ok=True)
        
        # Save FAISS index
        import faiss
        faiss.write_index(vector_store.index, cache_file)
        
        # Save token map metadata
        cache_meta_data = {
            'token_map': vector_store.token_map,
            'embedding_dim': vector_store.embedding_dim,
            'total_tokens': vector_store.index.ntotal
        }
        with open(cache_meta, 'wb') as f:
            pickle.dump(cache_meta_data, f)
        
        print(f"[OK] Saved vector store cache ({vector_store.index.ntotal:,} tokens)")
        return True
    except Exception as e:
        print(f"[WARNING] Failed to save vector store cache: {e}")
        return False


def load_vector_store(output_dir, strategy="feature_based", max_batches=5, force_reload=False):
    """Load vector store with RESUME functionality - checks cache first."""
    print(f"\n[INFO] Loading vector store ({strategy})...")
    
    # Check cache first (unless force_reload)
    if not force_reload:
        cached_store = load_vector_store_cache(output_dir)
        if cached_store is not None:
            return cached_store
        print("[INFO] No cache found, loading from batches...")
    
    print(f"[INFO] Maximum batches to load: {max_batches} (to avoid memory issues)")
    
    # Load metadata
    metadata_file = os.path.join(output_dir, "embedding_batches_metadata.json")
    if not os.path.exists(metadata_file):
        print(f"[ERROR] Metadata file not found: {metadata_file}")
        return None
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    # Use VERY small batch count to avoid memory issues
    batch_files = metadata.get("batch_files", [])[:max_batches]
    embedding_dim = metadata.get("embedding_dim", 768)
    batch_size = metadata.get("batch_size", 50000)
    
    if len(batch_files) == 0:
        print("[ERROR] No batch files found")
        return None
    
    # Load tokens (only sample needed)
    tokens_file = os.path.join(output_dir, "tokens.pkl")
    print("[INFO] Loading token sample...")
    all_tokens = load_tokens(tokens_file)
    if all_tokens is None:
        return None
    
    # Create vector store
    try:
        vector_store = FAISSVectorStore(embedding_dim=embedding_dim)
    except Exception as e:
        print(f"[ERROR] Failed to create vector store: {e}")
        return None
    
    # Load batches with memory safety - VERY small chunks
    max_tokens = max_batches * batch_size
    sample_tokens = all_tokens[:min(max_tokens, len(all_tokens))]
    
    total_added = 0
    chunk_size = 3000  # VERY small chunks for memory safety
    
    try:
        for batch_idx, batch_file in enumerate(batch_files):
            if not os.path.exists(batch_file):
                print(f"[WARNING] Batch file not found: {batch_file}")
                continue
            
            try:
                print(f"[INFO] Loading batch {batch_idx + 1}/{len(batch_files)}...")
                batch_emb = np.load(batch_file)
                batch_start = batch_idx * batch_size
                batch_end = min(batch_start + len(batch_emb), len(sample_tokens))
                batch_tokens = sample_tokens[batch_start:batch_end]
                
                # Add in VERY small chunks to avoid memory issues
                for chunk_start in range(0, len(batch_tokens), chunk_size):
                    chunk_end = min(chunk_start + chunk_size, len(batch_tokens))
                    try:
                        vector_store.add_tokens(
                            batch_tokens[chunk_start:chunk_end],
                            batch_emb[chunk_start:chunk_end]
                        )
                    except MemoryError:
                        print(f"[ERROR] Memory error at batch {batch_idx + 1}, chunk {chunk_start}")
                        print(f"[INFO] Stopping at {total_added:,} tokens - saving cache...")
                        # Save what we have before failing
                        if total_added > 0:
                            save_vector_store_cache(vector_store, output_dir, vector_store_cache_file, vector_store_cache_meta)
                        return vector_store
                
                total_added += len(batch_tokens)
                print(f"  [OK] Batch {batch_idx + 1}/{len(batch_files)} loaded ({total_added:,} tokens)")
                
            except MemoryError as e:
                print(f"[ERROR] Memory error loading batch {batch_idx + 1}: {e}")
                print(f"[INFO] Stopped loading at {total_added:,} tokens - saving cache...")
                # Save what we have before failing
                if total_added > 0:
                    save_vector_store_cache(vector_store, output_dir, vector_store_cache_file, vector_store_cache_meta)
                return vector_store
            except Exception as e:
                print(f"[WARNING] Error loading batch {batch_idx + 1}: {e}")
                continue
        
        if total_added == 0:
            print("[ERROR] No tokens were added to vector store")
            return None
        
        print(f"[OK] Loaded {total_added:,} tokens into vector store")
        
        # Save cache for next time
        save_vector_store_cache(vector_store, output_dir, vector_store_cache_file, vector_store_cache_meta)
        
        return vector_store
        
    except MemoryError as e:
        print(f"[ERROR] Memory error: {e}")
        print(f"[INFO] Loaded {total_added:,} tokens before memory error - saving cache...")
        if total_added > 0:
            save_vector_store_cache(vector_store, output_dir, vector_store_cache_file, vector_store_cache_meta)
            return vector_store
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        if total_added > 0:
            save_vector_store_cache(vector_store, output_dir, vector_store_cache_file, vector_store_cache_meta)
        return None


def get_embedding_for_text(text, generator, all_tokens=None):
    """Get embedding for a text string by tokenizing first or finding in existing tokens."""
    # Try to find token in existing tokens first (more efficient)
    if all_tokens:
        for token in all_tokens:
            if hasattr(token, 'text') and token.text.lower() == text.lower():
                try:
                    embedding = generator.generate(token)
                    return embedding
                except Exception as e:
                    break
    
    # Fallback: tokenize the text
    try:
        tokens = tokenize_text(text, tokenizer_type="word")
        if not tokens or len(tokens) == 0:
            return None
        
        # Use first token's embedding
        first_token = tokens[0]
        embedding = generator.generate(first_token)
        return embedding
    except Exception as e:
        return None


def filter_results(results, min_similarity=0.7, filter_stop_words=True, filter_whitespace=True):
    """Filter search results to remove low-quality matches."""
    filtered = []
    seen = set()
    stop_words = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
        'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'it', 'its',
        'they', 'them', 'their', 'there', 'here', 'where', 'when', 'what', 'who',
        'which', 'how', 'why', 'if', 'then', 'else', 'so', 'than', 'more', 'most',
        'very', 'just', 'only', 'also', 'too', 'up', 'down', 'out', 'off', 'over',
        'under', 'again', 'further', 'then', 'once', 'often', 'will', 'know'
    }
    
    for item in results:
        text = item.get('text', '').strip()
        distance = item.get('distance', float('inf'))
        similarity = 1.0 / (1.0 + distance) if distance > 0 else 1.0
        
        # Skip if similarity too low
        if similarity < min_similarity:
            continue
        
        # Skip if duplicate
        text_lower = text.lower()
        if text_lower in seen:
            continue
        seen.add(text_lower)
        
        # Skip stop words if filtering enabled
        if filter_stop_words and text_lower in stop_words:
            continue
        
        # Skip whitespace/newline tokens if filtering enabled
        if filter_whitespace:
            if not text or text.isspace() or text in ['\n', '\r', '\t', '\n\n', '\r\n']:
                continue
            # Skip tokens that are mostly whitespace
            if len(text.strip()) == 0:
                continue
        
        # Skip very short tokens (likely noise)
        if len(text.strip()) < 2:
            continue
        
        filtered.append({
            'text': text,
            'distance': distance,
            'similarity': similarity
        })
    
    return filtered


def pretty_print(title, items):
    """Print search results."""
    # Filter results first
    filtered = filter_results(items, min_similarity=0.65, filter_stop_words=True, filter_whitespace=True)
    
    print(f"\n[SEARCH] {title}")
    print("-" * 60)
    if not filtered:
        print("  No meaningful results found (all filtered)")
    else:
        for i, item in enumerate(filtered[:TOP_N], start=1):
            text = item.get('text', 'N/A')
            distance = item.get('distance', 0.0)
            similarity = item.get('similarity', 0.0)
            # Truncate long text for display
            display_text = text[:30] if len(text) > 30 else text
            print(f" {i:2d}. {display_text:30s}  (distance: {distance:.3f}, similarity: {similarity:.3f})")
    print("-" * 60)


# --------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------

def main():
    print("=" * 80)
    print("SanTOK Semantic Evaluation Utility")
    print("=" * 80)

    if not os.path.exists(tokens_path):
        print(f"[ERROR] Missing tokens file: {tokens_path}")
        print("   Please run test_full_workflow_500k.py first.")
        return

    # Load tokens
    all_tokens = load_tokens(tokens_path)
    if all_tokens is None:
        return

    print(f"[OK] Loaded {len(all_tokens):,} tokens for evaluation")

    # Load vector stores (both use same batches, but we can compare feature vs semantic)
    # Use VERY small batch count to avoid memory issues - checks cache first!
    print("\n[INFO] Loading feature-based vector store...")
    print("[INFO] Will check cache first - if exists, will load instantly!")
    feature_store = load_vector_store(output_dir, strategy="feature_based", max_batches=MAX_BATCHES_FOR_EVAL, force_reload=False)
    
    if feature_store is None:
        print("[ERROR] Failed to load vector store.")
        return

    # Create embedding generators
    feature_generator = SanTOKEmbeddingGenerator(strategy="feature_based")

    # Evaluate across test terms
    results = []
    for term in TEST_TERMS:
        print(f"\n\n=== Evaluating term: '{term}' ===")

        # Generate query vector by tokenizing the term or finding in existing tokens
        query_emb = get_embedding_for_text(term, feature_generator, all_tokens)
        if query_emb is None:
            print(f"[WARNING] No embedding found for '{term}' - skipping")
            continue

        try:
            # Search feature-based (get more results to filter)
            feature_results = feature_store.search(query_emb, top_k=TOP_N * 3)  # Get more for filtering
            if not feature_results:
                print(f"[WARNING] No results found for '{term}'")
                continue
            
            # Filter results to remove stop words and whitespace
            filtered_results = filter_results(feature_results, min_similarity=0.65, filter_stop_words=True, filter_whitespace=True)
            
            if not filtered_results:
                print(f"[WARNING] No meaningful results found for '{term}' after filtering")
                # Show original results without filtering for debugging
                print(f"[INFO] Original results (unfiltered):")
                for item in feature_results[:TOP_N]:
                    print(f"  - {item.get('text', 'N/A')}")
                continue
            
            pretty_print("Feature-Based Results", filtered_results[:TOP_N])

            # Extract token texts for comparison (from filtered results)
            feature_tokens = [item.get('text', '') for item in filtered_results[:TOP_N]]

            results.append({
                "term": term,
                "feature_top": feature_tokens,
                "results": feature_results,
            })
        except Exception as e:
            print(f"[ERROR] Error searching for '{term}': {e}")
            continue

    print("\n\n[SUMMARY] COMPARISON")
    print("=" * 80)
    for r in results:
        print(f"Term: {r['term']}")
        print(f"  Top Results: {r['feature_top']}")
        print("-" * 80)


if __name__ == "__main__":
    main()