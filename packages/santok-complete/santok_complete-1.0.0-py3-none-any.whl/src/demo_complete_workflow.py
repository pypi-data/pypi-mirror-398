#!/usr/bin/env python3
"""
Complete SanTOK Demo - Tokenization to Semantic Embeddings

This demo shows:
1. Tokenization (with outputs)
2. Embeddings (with outputs)
3. Semantic Embeddings (with outputs)
4. Vector Store (with outputs)
5. Similarity Search (with outputs)
6. All results saved to files
"""

import os
import json
import numpy as np
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent  # Go up one level from src/ to project root
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(current_dir))

from src.core.core_tokenizer import tokenize_text, reconstruct_from_tokens
from src.embeddings.embedding_generator import SanTOKEmbeddingGenerator
from src.embeddings.vector_store import FAISSVectorStore
from src.embeddings.semantic_trainer import SanTOKSemanticTrainer

# Demo output directory
DEMO_DIR = Path("demo_output")
DEMO_DIR.mkdir(exist_ok=True)

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")

def save_json(data, filename):
    """Save data to JSON file."""
    filepath = DEMO_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  [SAVED] {filepath}")
    return filepath

def save_text(text, filename):
    """Save text to file."""
    filepath = DEMO_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"  [SAVED] {filepath}")
    return filepath

def demo_tokenization():
    """Demo 1: Tokenization with outputs."""
    print_section("DEMO 1: TOKENIZATION")
    
    # Sample text
    sample_texts = [
        "Hello world! This is a test.",
        "Artificial intelligence is transforming technology.",
        "Machine learning and deep learning are powerful tools.",
        "Natural language processing enables computers to understand text.",
    ]
    
    tokenizer_types = ["space", "word", "char"]
    
    all_results = {}
    
    for text in sample_texts:
        print(f"\nText: {text}")
        print("-" * 60)
        
        text_results = {}
        
        for tokenizer_type in tokenizer_types:
            print(f"\n  Tokenizer: {tokenizer_type}")
            
            # Tokenize
            tokens = tokenize_text(text, tokenizer_type)
            
            # Reconstruct
            reconstructed = reconstruct_from_tokens(tokens, tokenizer_type)
            
            # Token info
            token_info = []
            for i, token in enumerate(tokens[:10]):  # First 10 tokens
                token_info.append({
                    "index": i,
                    "text": getattr(token, 'text', ''),
                    "uid": str(getattr(token, 'uid', 0)),
                    "stream": getattr(token, 'stream', ''),
                    "frontend": getattr(token, 'frontend', 0),
                })
            
            result = {
                "original_text": text,
                "tokenizer_type": tokenizer_type,
                "total_tokens": len(tokens),
                "tokens": token_info,
                "reconstructed_text": reconstructed,
                "perfect_reconstruction": reconstructed == text,
            }
            
            text_results[tokenizer_type] = result
            
            print(f"    Tokens: {len(tokens)}")
            print(f"    Reconstructed: {reconstructed}")
            print(f"    Perfect: {'Yes' if reconstructed == text else 'No'}")
            print(f"    Sample tokens: {[t.get('text', '') for t in token_info[:5]]}")
        
        all_results[text] = text_results
    
    # Save tokenization results
    save_json(all_results, "1_tokenization_results.json")
    
    # Save summary
    summary = {
        "total_texts": len(sample_texts),
        "tokenizer_types": tokenizer_types,
        "timestamp": datetime.now().isoformat(),
    }
    save_json(summary, "1_tokenization_summary.json")
    
    print("\n✅ Tokenization demo complete!")
    return all_results

def demo_embeddings(tokenization_results):
    """Demo 2: Embeddings with outputs."""
    print_section("DEMO 2: EMBEDDINGS")
    
    # Initialize embedding generator
    print("Initializing embedding generator...")
    embedding_gen = SanTOKEmbeddingGenerator(
        strategy="feature_based",
        embedding_dim=768
    )
    print("✅ Embedding generator ready")
    
    # Get tokens from tokenization results
    all_tokens = []
    token_texts = []
    
    for text, results in tokenization_results.items():
        for tokenizer_type, result in results.items():
            # Re-tokenize to get token objects
            tokens = tokenize_text(text, tokenizer_type)
            all_tokens.extend(tokens)
            token_texts.append({
                "text": text,
                "tokenizer_type": tokenizer_type,
                "token_count": len(tokens),
            })
    
    print(f"\nTotal tokens to embed: {len(all_tokens)}")
    
    # Generate embeddings (sample - first 100 tokens)
    sample_tokens = all_tokens[:100]
    print(f"Generating embeddings for {len(sample_tokens)} sample tokens...")
    
    embeddings = []
    embedding_info = []
    
    for i, token in enumerate(sample_tokens):
        try:
            embedding = embedding_gen.generate(token)
            embeddings.append(embedding.tolist())
            embedding_info.append({
                "index": i,
                "text": getattr(token, 'text', ''),
                "uid": str(getattr(token, 'uid', 0)),
                "embedding_dim": len(embedding),
                "embedding_sample": embedding[:5].tolist(),  # First 5 values
            })
            
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(sample_tokens)} tokens...")
        except Exception as e:
            print(f"  Error processing token {i}: {e}")
    
    # Save embeddings
    embeddings_array = np.array(embeddings, dtype=np.float32)
    embeddings_file = DEMO_DIR / "2_embeddings.npy"
    np.save(embeddings_file, embeddings_array)
    print(f"  [SAVED] {embeddings_file} ({embeddings_array.shape})")
    
    # Save embedding info
    embedding_results = {
        "total_tokens": len(sample_tokens),
        "embedding_dim": 768,
        "embeddings_generated": len(embeddings),
        "embeddings_info": embedding_info[:20],  # First 20
        "embedding_stats": {
            "mean": float(np.mean(embeddings_array)),
            "std": float(np.std(embeddings_array)),
            "min": float(np.min(embeddings_array)),
            "max": float(np.max(embeddings_array)),
        },
        "timestamp": datetime.now().isoformat(),
    }
    save_json(embedding_results, "2_embeddings_results.json")
    
    print("\n✅ Embeddings demo complete!")
    return embeddings_array, embedding_info, sample_tokens

def demo_semantic_embeddings(tokens, embeddings):
    """Demo 3: Semantic Embeddings with outputs."""
    print_section("DEMO 3: SEMANTIC EMBEDDINGS")
    
    print("Initializing semantic trainer...")
    
    try:
        # Create semantic trainer
        trainer = SanTOKSemanticTrainer(
            embedding_dim=768,
            window_size=5,
            min_count=1,
        )
        
        print("Training semantic embeddings...")
        print(f"  Tokens: {len(tokens)}")
        
        # Train on tokens (sample for demo)
        sample_size = min(100, len(tokens))
        sample_tokens = tokens[:sample_size]
        
        print(f"  Training on {sample_size} tokens...")
        
        # Prepare token data for training
        token_data = []
        for token in sample_tokens:
            uid = getattr(token, 'uid', 0)
            text = getattr(token, 'text', '')
            if uid and text:
                token_data.append({
                    "uid": uid,
                    "text": text,
                })
        
        if len(token_data) < 10:
            print("  ⚠️  Not enough tokens for semantic training. Skipping...")
            return None, None
        
        # Train (simplified for demo)
        print("  Training semantic model...")
        trainer.train(token_data, epochs=1, batch_size=32)
        
        print("  ✅ Semantic model trained!")
        
        # Generate semantic embeddings
        print("Generating semantic embeddings...")
        semantic_embeddings = []
        semantic_info = []
        
        for i, token in enumerate(sample_tokens[:50]):  # First 50
            try:
                uid = getattr(token, 'uid', 0)
                if uid:
                    emb = trainer.get_embedding(uid)
                    if emb is not None:
                        semantic_embeddings.append(emb.tolist())
                        semantic_info.append({
                            "index": i,
                            "text": getattr(token, 'text', ''),
                            "uid": str(uid),
                            "embedding_dim": len(emb),
                            "embedding_sample": emb[:5].tolist(),
                        })
            except Exception as e:
                print(f"  Error generating semantic embedding {i}: {e}")
        
        if semantic_embeddings:
            # Save semantic embeddings
            semantic_array = np.array(semantic_embeddings, dtype=np.float32)
            semantic_file = DEMO_DIR / "3_semantic_embeddings.npy"
            np.save(semantic_file, semantic_array)
            print(f"  [SAVED] {semantic_file} ({semantic_array.shape})")
            
            # Save semantic results
            semantic_results = {
                "total_tokens": len(sample_tokens),
                "semantic_embeddings_generated": len(semantic_embeddings),
                "embedding_dim": 768,
                "semantic_info": semantic_info[:20],
                "semantic_stats": {
                    "mean": float(np.mean(semantic_array)),
                    "std": float(np.std(semantic_array)),
                    "min": float(np.min(semantic_array)),
                    "max": float(np.max(semantic_array)),
                },
                "timestamp": datetime.now().isoformat(),
            }
            save_json(semantic_results, "3_semantic_embeddings_results.json")
            
            # Save model
            model_file = DEMO_DIR / "3_semantic_model.pkl"
            trainer.save(str(model_file))
            print(f"  [SAVED] {model_file}")
            
            print("\n✅ Semantic embeddings demo complete!")
            return semantic_array, semantic_info
        
    except Exception as e:
        print(f"  ⚠️  Semantic training error: {e}")
        print("  Continuing without semantic embeddings...")
        return None, None
    
    return None, None

def demo_vector_store(tokens, embeddings):
    """Demo 4: Vector Store with outputs."""
    print_section("DEMO 4: VECTOR STORE")
    
    print("Creating vector store...")
    
    try:
        # Create FAISS vector store
        vector_store = FAISSVectorStore(embedding_dim=768)
        
        print(f"Adding {len(tokens)} tokens to vector store...")
        
        # Add tokens to vector store (sample)
        sample_size = min(100, len(tokens))
        sample_tokens = tokens[:sample_size]
        sample_embeddings = embeddings[:sample_size]
        
        vector_store.add_batch(sample_tokens, sample_embeddings)
        
        print(f"  ✅ Added {sample_size} tokens to vector store")
        
        # Save vector store
        store_file = DEMO_DIR / "4_vector_store.index"
        vector_store.save(str(store_file))
        print(f"  [SAVED] {store_file}")
        
        # Vector store info
        store_info = {
            "total_tokens": sample_size,
            "embedding_dim": 768,
            "index_type": "FAISS",
            "timestamp": datetime.now().isoformat(),
        }
        save_json(store_info, "4_vector_store_info.json")
        
        print("\n✅ Vector store demo complete!")
        return vector_store, sample_tokens, sample_embeddings
    
    except Exception as e:
        print(f"  ⚠️  Vector store error: {e}")
        return None, None, None

def demo_similarity_search(vector_store, tokens, embeddings):
    """Demo 5: Similarity Search with outputs."""
    print_section("DEMO 5: SIMILARITY SEARCH")
    
    if vector_store is None:
        print("  ⚠️  Vector store not available. Skipping...")
        return
    
    print("Performing similarity search...")
    
    # Search queries
    search_queries = [
        "artificial",
        "machine",
        "learning",
        "intelligence",
    ]
    
    search_results = {}
    
    for query in search_queries:
        print(f"\n  Searching for: '{query}'")
        
        # Find query token
        query_token = None
        query_embedding = None
        
        for i, token in enumerate(tokens):
            if getattr(token, 'text', '').lower() == query.lower():
                query_token = token
                query_embedding = embeddings[i]
                break
        
        if query_embedding is None:
            print(f"    ⚠️  Token '{query}' not found. Skipping...")
            continue
        
        # Search
        results = vector_store.search(query_embedding, top_k=10)
        
        # Format results
        formatted_results = []
        for j, result in enumerate(results):
            formatted_results.append({
                "rank": j + 1,
                "text": result.get('text', ''),
                "distance": float(result.get('distance', 0.0)),
                "similarity": float(1.0 / (1.0 + result.get('distance', 1.0))),
                "uid": str(result.get('token_id', '')),
            })
        
        search_results[query] = {
            "query": query,
            "results": formatted_results,
        }
        
        print(f"    Found {len(formatted_results)} results:")
        for result in formatted_results[:5]:
            print(f"      {result['rank']}. {result['text']} (similarity: {result['similarity']:.3f})")
    
    # Save search results
    save_json(search_results, "5_similarity_search_results.json")
    
    print("\n✅ Similarity search demo complete!")
    return search_results

def create_demo_summary():
    """Create a summary of all demos."""
    print_section("DEMO SUMMARY")
    
    summary = {
        "demo_date": datetime.now().isoformat(),
        "output_directory": str(DEMO_DIR),
        "demos_completed": [],
        "files_created": [],
    }
    
    # Check which files were created
    if (DEMO_DIR / "1_tokenization_results.json").exists():
        summary["demos_completed"].append("Tokenization")
        summary["files_created"].append("1_tokenization_results.json")
    
    if (DEMO_DIR / "2_embeddings.npy").exists():
        summary["demos_completed"].append("Embeddings")
        summary["files_created"].append("2_embeddings.npy")
        summary["files_created"].append("2_embeddings_results.json")
    
    if (DEMO_DIR / "3_semantic_embeddings.npy").exists():
        summary["demos_completed"].append("Semantic Embeddings")
        summary["files_created"].append("3_semantic_embeddings.npy")
        summary["files_created"].append("3_semantic_embeddings_results.json")
        summary["files_created"].append("3_semantic_model.pkl")
    
    if (DEMO_DIR / "4_vector_store.index").exists():
        summary["demos_completed"].append("Vector Store")
        summary["files_created"].append("4_vector_store.index")
        summary["files_created"].append("4_vector_store_info.json")
    
    if (DEMO_DIR / "5_similarity_search_results.json").exists():
        summary["demos_completed"].append("Similarity Search")
        summary["files_created"].append("5_similarity_search_results.json")
    
    # Save summary
    save_json(summary, "demo_summary.json")
    
    # Create README
    readme = f"""# SanTOK Complete Demo Results

## Demo Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Demos Completed:
{chr(10).join(f'- {demo}' for demo in summary['demos_completed'])}

## Files Created:
{chr(10).join(f'- {f}' for f in summary['files_created'])}

## How to View Results:

### 1. Tokenization Results
- File: `1_tokenization_results.json`
- Contains: Tokenization results for all sample texts

### 2. Embeddings
- File: `2_embeddings.npy` (NumPy array)
- File: `2_embeddings_results.json` (Stats and info)
- Contains: Feature-based embeddings

### 3. Semantic Embeddings
- File: `3_semantic_embeddings.npy` (NumPy array)
- File: `3_semantic_embeddings_results.json` (Stats and info)
- File: `3_semantic_model.pkl` (Trained model)
- Contains: Semantic embeddings

### 4. Vector Store
- File: `4_vector_store.index` (FAISS index)
- File: `4_vector_store_info.json` (Info)
- Contains: Vector store for similarity search

### 5. Similarity Search
- File: `5_similarity_search_results.json`
- Contains: Similarity search results

## Next Steps:

1. View JSON files for results
2. Load NumPy arrays for embeddings
3. Load vector store for similarity search
4. Use semantic model for inference

## Notes:

- All outputs are in the `demo_output/` directory
- JSON files can be opened in any text editor
- NumPy arrays can be loaded with: `np.load('filename.npy')`
- Vector store can be loaded with: `FAISSVectorStore.load('filename.index')`
"""
    
    save_text(readme, "README.md")
    
    print("✅ Demo summary created!")
    print(f"\n📁 All demo outputs saved to: {DEMO_DIR}")
    print(f"📄 Summary: {DEMO_DIR / 'demo_summary.json'}")
    print(f"📖 README: {DEMO_DIR / 'README.md'}")

def main():
    """Run complete demo."""
    print("=" * 80)
    print(" SANTOK COMPLETE DEMO - Tokenization to Semantic Embeddings")
    print("=" * 80)
    print(f"\nOutput directory: {DEMO_DIR}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")
    
    try:
        # Demo 1: Tokenization
        tokenization_results = demo_tokenization()
        
        # Demo 2: Embeddings
        embeddings, embedding_info, tokens = demo_embeddings(tokenization_results)
        
        # Demo 3: Semantic Embeddings
        semantic_embeddings, semantic_info = demo_semantic_embeddings(tokens, embeddings)
        
        # Demo 4: Vector Store
        vector_store, store_tokens, store_embeddings = demo_vector_store(tokens, embeddings)
        
        # Demo 5: Similarity Search
        if vector_store is not None:
            search_results = demo_similarity_search(vector_store, store_tokens, store_embeddings)
        
        # Create summary
        create_demo_summary()
        
        print("\n" + "=" * 80)
        print(" ✅ COMPLETE DEMO FINISHED!")
        print("=" * 80)
        print(f"\n📁 All outputs saved to: {DEMO_DIR}")
        print(f"📄 View results in: {DEMO_DIR}")
        print(f"📖 Read README: {DEMO_DIR / 'README.md'}")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()