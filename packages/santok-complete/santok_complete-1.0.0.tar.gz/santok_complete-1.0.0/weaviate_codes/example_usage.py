"""
Example: Using Weaviate with SanTOK - Building Memory & Recall System

This script demonstrates how to build SanTOK's long-term memory and recall system:

1. Tokenize text with SanTOK
2. Generate embeddings
3. Retrieval - Check Weaviate for similar tokens BEFORE processing (context memory)
4. Store in Weaviate with tags (filename, date, session) - building memory
5. Search for similar tokens
6. Query tokens by ID from Weaviate
7. Search using stored vectors from Weaviate
8. Visualize embeddings with t-SNE (see SanTOK's semantic brain map)

Key Features:
- Auto-stores tokens and embeddings on every run (builds growing knowledge base)
- Tags each record with filename, date, and session for tracking
- Retrieval ability - SanTOK can recall similar embeddings from memory
- Visualization shows how SanTOK clusters words and symbols semantically

This creates a self-referential, context-aware system where SanTOK learns
from its own tokenizations and builds long-term memory!
"""

import sys
import os
from pathlib import Path
import time
import uuid as uuid_module
from datetime import datetime

# Add project root to path (for imports)
project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Try different import paths (same pattern as inference_pipeline.py)
try:
    from src.core.core_tokenizer import TextTokenizer
except ImportError:
    try:
        from core.core_tokenizer import TextTokenizer
    except ImportError:
        raise ImportError("Could not find TextTokenizer. Make sure you're running from project root.")

from src.embeddings.embedding_generator import SanTOKEmbeddingGenerator

import numpy as np


def main():
    # Import weaviate only when main() is called (not during multiprocessing worker imports)
    # CRITICAL: Import weaviate-client package, avoiding conflict with local weaviate folder

    # Folder containing this example (expected to also contain weaviate_vector_store.py)
    example_folder = Path(__file__).parent.resolve()
    # The project root (we added earlier)
    proj_root = project_root

    # Save current sys.path to restore later
    original_sys_path = sys.path.copy()

    # If project_root is in sys.path, temporarily remove it to avoid local package shadowing
    try:
        if str(proj_root) in sys.path:
            sys.path.remove(str(proj_root))

        # Also remove any exact path equal to example_folder (if present) to avoid local 'weaviate' folder shadowing site-packages
        if str(example_folder) in sys.path:
            sys.path.remove(str(example_folder))

        # If a 'weaviate' module is already loaded and points to a local file in example_folder, unload it
        if 'weaviate' in sys.modules:
            wm = sys.modules['weaviate']
            weav_mod_file = getattr(wm, '__file__', None)
            if weav_mod_file:
                weav_mod_path = Path(weav_mod_file).resolve()
                # if the module file is inside the example folder, remove all 'weaviate' keys
                if str(weav_mod_path).startswith(str(example_folder)):
                    keys_to_remove = [k for k in list(sys.modules.keys()) if k.startswith('weaviate')]
                    for k in keys_to_remove:
                        del sys.modules[k]

        # Now import installed weaviate-client from site-packages
        try:
            import weaviate as _weaviate_pkg

            # Try the modern import (Weaviate ≥ 4.0)
            try:
                from weaviate.classes.init import Auth as _AuthClass
            except ModuleNotFoundError:
                # Fallback for older client versions (Weaviate < 4.0)
                if hasattr(_weaviate_pkg, "AuthApiKey"):
                    class _AuthClass:
                        @staticmethod
                        def api_key(api_key):
                            return _weaviate_pkg.AuthApiKey(api_key=api_key)
                else:
                    raise ImportError(
                        "Could not find Auth class in weaviate-client. "
                        "Run: pip install -U weaviate-client"
                    )

            # Double-check that imported package is not shadowed by a local folder
            pkg_file = getattr(_weaviate_pkg, "__file__", None)
            if pkg_file:
                pkg_path = Path(pkg_file).resolve()
                if str(pkg_path).startswith(str(example_folder)):
                    raise ImportError(
                        "Imported weaviate package appears to come from the local folder. "
                        "Rename the local 'weaviate' folder to avoid shadowing the installed package."
                    )

        except ImportError as e:
            # Restore sys.path before re-raising so environment is not left broken
            sys.path[:] = original_sys_path
            raise ImportError(
                "weaviate-client not installed or could not be imported. "
                "Run: pip install weaviate-client"
            ) from e


        # Keep references to the imported package and Auth class
        _weaviate_package = _weaviate_pkg
        _Auth_class = _AuthClass

    finally:
        # Restore sys.path (put project root back at front) so subsequent local imports work
        sys.path[:] = original_sys_path
        if str(proj_root) not in sys.path:
            sys.path.insert(0, str(proj_root))

    # Load the local weaviate vector store helper module (we expect it next to this example)
    weaviate_store_file = example_folder / "weaviate_vector_store.py"
    if not weaviate_store_file.exists():
        raise FileNotFoundError(f"Expected weaviate_vector_store.py next to this example ({weaviate_store_file})")

    import importlib.util
    spec = importlib.util.spec_from_file_location("weaviate_store_local", str(weaviate_store_file))
    if spec is None or spec.loader is None:
        raise ImportError("Could not load spec for weaviate_vector_store.py")
    weaviate_store_module = importlib.util.module_from_spec(spec)
    # Inject the imported (site-packages) weaviate package and Auth class into the module globals
    weaviate_store_module.__dict__['weaviate'] = _weaviate_package
    weaviate_store_module.__dict__['Auth'] = _Auth_class
    # Make sure 'weaviate' key in sys.modules refers to the site-packages package while loading the local module
    sys.modules['weaviate'] = _weaviate_package
    spec.loader.exec_module(weaviate_store_module)
    WeaviateVectorStore = getattr(weaviate_store_module, "WeaviateVectorStore", None)
    if WeaviateVectorStore is None:
        raise ImportError("weaviate_vector_store.py does not define WeaviateVectorStore")

    print("SanTOK + Weaviate Example\n")

    # Step 1: Initialize SanTOK tokenizer
    print("1. Initializing SanTOK tokenizer...")
    tokenizer = TextTokenizer(seed=42, embedding_bit=False)

    # Step 2: Initialize embedding generator
    print("2. Initializing embedding generator...")
    embedding_generator = SanTOKEmbeddingGenerator(strategy="feature_based")

    # Step 3: Initialize Weaviate vector store
    print("3. Connecting to Weaviate...")
    try:
        vector_store = WeaviateVectorStore(
            collection_name="SanTOK_Token",
            embedding_dim=768
        )
        print("[OK] Connected to Weaviate!\n")
    except Exception as e:
        print(f"[ERROR] Failed to connect: {e}")
        print("\nMake sure you have:")
        print("   - WEAVIATE_URL in your .env file")
        print("   - WEAVIATE_API_KEY in your .env file")
        return

    try:
        # Step 3.5: Retrieval - Check Weaviate for similar tokens BEFORE processing
        # This makes SanTOK recall similar embeddings it saw before (context memory)
        print("3.5. Retrieval - Checking Weaviate for similar tokens...")
        sample_query_text = "Hello world! This is SanTOK tokenization with Weaviate."
        
        # Generate embedding for the query text to check for similar tokens
        try:
            # Create a temporary token to generate embedding
            temp_streams = tokenizer.build(sample_query_text)
            if "word" in temp_streams and hasattr(temp_streams["word"], "tokens"):
                temp_tokens = temp_streams["word"].tokens[:1]  # Just first token for query
            else:
                first_stream = next(iter(temp_streams.values()))
                temp_tokens = [getattr(first_stream, "tokens", [])[0]] if getattr(first_stream, "tokens", []) else []
            
            if temp_tokens:
                query_emb = embedding_generator.generate_batch(temp_tokens)
                query_emb = np.asarray(query_emb)
                if query_emb.ndim == 2 and query_emb.shape[0] > 0:
                    query_emb = query_emb[0]  # Get first embedding
                    
                    # Search Weaviate for similar tokens (SanTOK's memory recall)
                    recall_results = vector_store.search(query_emb, top_k=5)
                    
                    if recall_results:
                        print(f"   [OK] Found {len(recall_results)} similar tokens in memory:")
                        for i, r in enumerate(recall_results[:3], 1):  # Show top 3
                            text_val = r.get("text", "N/A")
                            distance = r.get("distance", None)
                            distance_str = f"{distance:.4f}" if isinstance(distance, (float, int)) else "N/A"
                            metadata = r.get("metadata", {})
                            content_id = metadata.get("content_id", "N/A")
                            print(f"   {i}. '{text_val}' (distance: {distance_str})")
                            if "run_" in str(content_id):
                                print(f"      Source: {content_id.split('_')[-1] if '_' in content_id else 'N/A'}")
                        print("   → SanTOK can recall similar embeddings from its memory!\n")
                    else:
                        print("   → No similar tokens found in memory (this is a new context)\n")
                else:
                    print("   → Could not generate query embedding for retrieval\n")
            else:
                print("   → Could not tokenize query text for retrieval\n")
        except Exception as e:
            print(f"   [WARNING] Retrieval check failed: {e}\n")
        
        # Step 4: Tokenize some text
        print("4. Tokenizing text...")
        text = "Hello world! This is SanTOK tokenization with Weaviate."
        streams = tokenizer.build(text)

        # Get tokens from word stream or first available stream
        if "word" in streams and hasattr(streams["word"], "tokens"):
            tokens = streams["word"].tokens
            print(f"   Found {len(tokens)} tokens")
            print(f"   Tokens: {[t.text for t in tokens[:5]]}...\n")
        else:
            first_stream = next(iter(streams.values()))
            tokens = getattr(first_stream, "tokens", [])
            print(f"   Found {len(tokens)} tokens\n")

        # Step 5: Generate embeddings
        print("5. Generating embeddings...")
        embeddings = embedding_generator.generate_batch(tokens)
        # Make sure embeddings is a numpy array
        embeddings = np.asarray(embeddings)
        if embeddings.ndim != 2:
            raise ValueError("Embeddings must be a 2D array: (n_tokens, dim)")
        print(f"   Generated {embeddings.shape[0]} embeddings of dimension {embeddings.shape[1]}\n")

        # Step 6: Store in Weaviate with tags (building SanTOK's long-term memory)
        print("6. Storing tokens and embeddings in Weaviate (building memory)...")
        
        # Generate tags for this run (filename, date, session)
        # These tags help SanTOK remember where tokens came from
        session_id = f"session_{uuid_module.uuid4().hex[:8]}"
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename_tag = "example_usage_2.py"  # In real usage, this would be the actual file being processed
        run_id = f"run_{int(time.time() * 1000000)}_{uuid_module.uuid4().hex[:8]}"
        
        # Create metadata with tags to build SanTOK's memory base
        # Each record gets tagged with filename, date, and session for tracking
        metadata_list = []
        for token in tokens:
            token_metadata = {
                "text": getattr(token, 'text', ''),
                "stream": getattr(token, 'stream', ''),
                "uid": str(getattr(token, 'uid', '')),
                "frontend": str(getattr(token, 'frontend', '')),
                "index": int(getattr(token, 'index', 0)),
                # Store tags in content_id and global_id for tracking
                "content_id": f"{getattr(token, 'content_id', '')}_{run_id}",
                "global_id": f"{getattr(token, 'global_id', '')}_{run_id}|filename:{filename_tag}|date:{current_date}|session:{session_id}"
            }
            metadata_list.append(token_metadata)
        
        # Auto-store tokens and embeddings into Weaviate
        # This builds SanTOK's growing knowledge vector space - it learns from its own history
        vector_store.add_tokens(tokens, embeddings, metadata=metadata_list)
        print(f"   [OK] Stored {len(tokens)} tokens with tags:")
        print(f"        - Filename: {filename_tag}")
        print(f"        - Date: {current_date}")
        print(f"        - Session: {session_id}")
        print(f"        - Run ID: {run_id}")
        print("   → SanTOK's memory base is growing!\n")
        
        # Store the first token's UUID for later querying (we'll get it from search results)
        stored_token_uuids = []

        # Step 7: Search for similar tokens
        print("7. Searching for similar tokens...")
        # Use first token's embedding as query
        query_embedding = embeddings[0]
        results = vector_store.search(query_embedding, top_k=5)

        print(f"   Found {len(results)} similar tokens:")
        for i, result in enumerate(results, 1):
            text_val = result.get('text', result.get('metadata', {}).get('text', 'N/A'))
            distance = result.get('distance', None)
            distance_str = f"{distance:.4f}" if isinstance(distance, (float, int)) else "N/A"
            uid = result.get('metadata', {}).get('uid', 'N/A')
            token_id = result.get('id', None)
            if token_id:
                stored_token_uuids.append(token_id)
            print(f"   {i}. '{text_val}' (distance: {distance_str})")
            print(f"      UID: {uid}")
            if token_id:
                print(f"      UUID: {token_id}")

        # Step 8: Query token by ID from Weaviate
        print("\n8. Querying token by ID from Weaviate...")
        if stored_token_uuids:
            # Get the first token's UUID
            token_uuid = stored_token_uuids[0]
            try:
                # Access the Weaviate collection directly to query by ID
                collection = vector_store.collection
                obj = collection.data.fetch_by_id(token_uuid)
                
                if obj:
                    print(f"   [OK] Retrieved token by UUID: {token_uuid}")
                    print(f"   Text: {obj.properties.get('text', 'N/A')}")
                    print(f"   Stream: {obj.properties.get('stream', 'N/A')}")
                    print(f"   UID: {obj.properties.get('uid', 'N/A')}")
                    print(f"   Global ID: {obj.properties.get('global_id', 'N/A')}")
                    if hasattr(obj, 'vector') and obj.vector:
                        print(f"   Vector dimension: {len(obj.vector)}")
                else:
                    print(f"   [WARNING] Token with UUID {token_uuid} not found")
            except Exception as e:
                print(f"   [WARNING] Could not query by ID: {e}")
        else:
            print("   [SKIP] No token UUIDs available for querying")

        # Step 9: Search similar tokens using stored vector
        print("\n9. Searching similar tokens using stored vector from Weaviate...")
        if stored_token_uuids:
            try:
                collection = vector_store.collection
                obj = collection.data.fetch_by_id(stored_token_uuids[0])
                
                if obj and hasattr(obj, 'vector') and obj.vector:
                    query_vector = np.array(obj.vector)
                    print(f"   Using stored vector from token: {obj.properties.get('text', 'N/A')}")
                    similar_results = vector_store.search(query_vector, top_k=5)
                    
                    print(f"   Found {len(similar_results)} similar tokens:")
                    for i, r in enumerate(similar_results, 1):
                        text_val = r.get("text", "N/A")
                        distance = r.get("distance", None)
                        distance_str = f"{distance:.4f}" if isinstance(distance, (float, int)) else "N/A"
                        print(f"   {i}. '{text_val}' (distance: {distance_str})")
                else:
                    print("   [WARNING] Could not retrieve vector from stored token")
            except Exception as e:
                print(f"   [WARNING] Could not search with stored vector: {e}")
        else:
            print("   [SKIP] No stored token available for vector search")

        # Step 10: Visualize embeddings (see SanTOK's brain)
        # This shows how SanTOK clusters words and symbols semantically
        print("\n10. Visualizing embeddings (SanTOK's semantic brain map)...")
        try:
            from sklearn.manifold import TSNE
            import matplotlib.pyplot as plt
            
            # Fetch tokens from Weaviate for visualization
            print("   Fetching tokens from Weaviate memory...")
            collection = vector_store.collection
            
            # Get a batch of objects (limit to reasonable number for visualization)
            sample_results = collection.query.fetch_objects(limit=100)  # Get more tokens for better visualization
            
            if sample_results.objects:
                vectors = []
                texts = []
                for obj in sample_results.objects:
                    if hasattr(obj, 'vector') and obj.vector:
                        vectors.append(obj.vector)
                        texts.append(obj.properties.get('text', 'N/A'))
                
                if len(vectors) >= 3:  # Need at least 3 points for t-SNE
                    vectors_array = np.array(vectors)
                    print(f"   Reducing {len(vectors)} token embeddings to 2D with t-SNE...")
                    print("   This shows which tokens SanTOK thinks are 'close in meaning'...")
                    
                    # Use t-SNE to reduce dimensionality
                    reduced = TSNE(n_components=2, random_state=42, perplexity=min(30, len(vectors)-1)).fit_transform(vectors_array)
                    
                    # Create visualization - see SanTOK's embedding space
                    plt.figure(figsize=(14, 10))
                    scatter = plt.scatter(reduced[:, 0], reduced[:, 1], alpha=0.6, s=50, c=range(len(vectors)), cmap='viridis')
                    
                    # Annotate points with token text (show semantic clusters)
                    for i, (x, y) in enumerate(reduced[:20]):  # Label first 20 tokens
                        token_text = texts[i][:15] if len(texts[i]) > 15 else texts[i]
                        plt.annotate(token_text, (x, y), fontsize=7, alpha=0.8, 
                                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.6))
                    
                    plt.title("SanTOK Embedding Space - Semantic Map of Token Relationships", fontsize=14, fontweight='bold')
                    plt.xlabel("t-SNE Dimension 1", fontsize=12)
                    plt.ylabel("t-SNE Dimension 2", fontsize=12)
                    plt.grid(True, alpha=0.3)
                    plt.colorbar(scatter, label='Token Index')
                    
                    # Add informative text
                    plt.figtext(0.5, 0.02, 
                              "Clusters show tokens that SanTOK perceives as semantically similar", 
                              ha='center', fontsize=10, style='italic')
                    
                    # Save the plot
                    output_file = example_folder / "santok_embeddings_visualization.png"
                    plt.savefig(output_file, dpi=200, bbox_inches='tight')
                    print(f"   [OK] Visualization saved to: {output_file}")
                    print("   → This semantic map shows how SanTOK clusters words and symbols!")
                    print("   (To display interactively, uncomment plt.show() in the code)")
                    # plt.show()  # Uncomment to display interactively
                    plt.close()
                else:
                    print(f"   [SKIP] Need at least 3 tokens for visualization, found {len(vectors)}")
            else:
                print("   [SKIP] No tokens found in Weaviate for visualization")
        except ImportError:
            print("   [SKIP] sklearn or matplotlib not available.")
            print("   Install with: pip install scikit-learn matplotlib")
        except Exception as e:
            print(f"   [WARNING] Visualization failed: {e}")

        print("\n[OK] Example completed successfully!")
        
        # ====================================================================
        # Integration Workflow: Building SanTOK's Memory System
        # ====================================================================
        # 
        # 1. KEEP BUILDING SANTOK'S MEMORY (Long-term Data)
        #    Every SanTOK run auto-stores its tokens and embeddings into Weaviate.
        #    Every analysis, file, or user text adds to its memory base.
        # 
        #    How: Integrate this call in your main SanTOK loop:
        #         vector_store.add_tokens(tokens, embeddings)
        # 
        #    Give each record a tag (filename, date, session):
        #         - filename: Track which file/document the tokens came from
        #         - date: When the tokens were processed
        #         - session: Group related processing runs
        # 
        #    This builds a growing knowledge vector space - SanTOK learns from its own history!
        # 
        # 2. ADD RETRIEVAL ABILITY (Make it Recall)
        #    Before processing new input, let SanTOK check Weaviate for similar tokens.
        #    This makes it "remember" similar embeddings it saw before - context memory.
        # 
        #    Example:
        #         query_emb = embedding_generator.generate_single("payment error on stripe api")
        #         results = vector_store.search(query_emb, top_k=5)
        # 
        #    Now SanTOK can recall similar embeddings from its memory!
        #    This turns it into an intelligent recall system (foundation for SanTOK AI).
        # 
        # 3. VISUALIZE EMBEDDINGS (See SanTOK's Brain)
        #    Visualize stored vectors to see how SanTOK clusters words and symbols semantically.
        #    This helps you see which tokens SanTOK thinks are "close in meaning."
        # 
        #    The visualization shows SanTOK's semantic understanding of token relationships.
        # 
        # This creates a self-referential, context-aware system where SanTOK learns
        # from its own tokenizations and builds long-term memory!
        # ====================================================================

    except Exception as e:
        print(f"\n[ERROR] Error during execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always close connection if available
        print("\nClosing Weaviate connection...")
        try:
            if hasattr(vector_store, "close"):
                vector_store.close()
        except Exception:
            pass
        print("[OK] Done!")


if __name__ == "__main__":
    main()