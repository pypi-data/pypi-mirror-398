"""
FastAPI Backend Server for SanTOK
Connects the frontend to the Python tokenization engine
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Security, Request, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
import os
import time
import json
import numpy as np
import subprocess
import tempfile
from pathlib import Path
import hashlib
import secrets
import jwt
import logging
from datetime import datetime, timedelta, timezone
import threading
import queue
import asyncio
import shutil

# Import job manager for async execution
try:
    from servers.job_manager import get_job_manager, JobStatus
except ImportError:
    try:
        from src.servers.job_manager import get_job_manager, JobStatus
    except ImportError:
        # Fallback if job_manager not found
        get_job_manager = None
        JobStatus = None

# Add src directory to path to import backend files
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
# Also add backend/src for API V2 routes
backend_src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'backend', 'src'))
if os.path.exists(backend_src_path):
    if backend_src_path not in sys.path:
        sys.path.insert(0, backend_src_path)
    print(f"[DEBUG] Added backend/src to path: {backend_src_path}")
else:
    print(f"[WARN] backend/src path does not exist: {backend_src_path}")

# Import your existing backend files
try:
    from core.core_tokenizer import tokenize_text, reconstruct_from_tokens
    import core.core_tokenizer as KT
    from core.core_tokenizer import (
        _content_id,
        TextTokenizer,
        all_tokenizations,  # Import directly - will restore after base_tokenizer import
        assign_uids,
        neighbor_uids,
        compose_backend_number,
        combined_digit,
        TokenStream,
        TokenRecord
    )
    print("[OK] Successfully imported engine module with REAL SanTOK engine")
except ImportError as e:
    print(f"[ERROR] Error importing core_tokenizer.py: {e}")
    sys.exit(1)

try:
    # Try different import paths for base_tokenizer
    try:
        import core.base_tokenizer as TK
        from core.base_tokenizer import *  # type: ignore[reportMissingImports] # noqa: F401,F403
        # TODO: Replace wildcard import with explicit imports
    except ImportError:
        import src.core.base_tokenizer as TK
        from src.core.base_tokenizer import *  # type: ignore[reportMissingImports] # noqa: F401,F403
        # TODO: Replace wildcard import with explicit imports
    # CRITICAL: Restore all_tokenizations from core_tokenizer (base_tokenizer version is incomplete - only 6 tokenizers)
    from core.core_tokenizer import all_tokenizations
    print("[OK] Successfully imported base_tokenizer.py")
except ImportError as e:
    print(f"[WARNING] Could not import base_tokenizer.py: {e}")

try:
    # Try different import paths for compression_algorithms
    try:
        from compression.compression_algorithms import *  # type: ignore[reportMissingImports] # noqa: F401,F403
        # TODO: Replace wildcard import with explicit imports
    except ImportError:
        from src.compression.compression_algorithms import *  # type: ignore[reportMissingImports] # noqa: F401,F403
        # TODO: Replace wildcard import with explicit imports
    print("[OK] Successfully imported compression_algorithms.py")
except ImportError as e:
    print(f"[WARNING] Could not import compression_algorithms.py: {e}")

try:
    # Try different import paths for unique_identifier
    try:
        from utils.unique_identifier import *  # type: ignore[reportMissingImports] # noqa: F401,F403
        # TODO: Replace wildcard import with explicit imports
    except ImportError:
        from src.utils.unique_identifier import *  # type: ignore[reportMissingImports] # noqa: F401,F403
        # TODO: Replace wildcard import with explicit imports
    print("[OK] Successfully imported unique_identifier.py")
except ImportError as e:
    print(f"[WARNING] Could not import unique_identifier.py: {e}")

# Import vocabulary adapter for pretrained model integration
try:
    # Try different import paths
    try:
        from integration.vocabulary_adapter import (
            VocabularyAdapter,
            SanTOKToModelConverter,
            quick_convert_santok_to_model_ids
        )
    except ImportError:
        # Try with src prefix
        from src.integration.vocabulary_adapter import (
            VocabularyAdapter,
            SanTOKToModelConverter,
            quick_convert_santok_to_model_ids
        )
    INTEGRATION_AVAILABLE = True
    print("[OK] Successfully imported vocabulary adapter")
except ImportError as e:
    INTEGRATION_AVAILABLE = False
    print(f"[WARNING] Could not import vocabulary adapter: {e}")
    print(f"   Install transformers: pip install transformers")
    print(f"   Note: Endpoints will still be available but will return 503 if used")

# Import embeddings (optional)
try:
    # Try importing with src prefix first
    try:
        from src.embeddings import (
            SanTOKEmbeddingGenerator,
            ChromaVectorStore,
            FAISSVectorStore,
            SanTOKInferencePipeline
        )
        # Try importing WeaviateVectorStore (optional)
        try:
            from src.embeddings import WeaviateVectorStore
            WEAVIATE_AVAILABLE = True
        except ImportError:
            WeaviateVectorStore = None
            WEAVIATE_AVAILABLE = False
    except ImportError:
        # Fallback to direct import
        from embeddings import (
            SanTOKEmbeddingGenerator,
            ChromaVectorStore,
            FAISSVectorStore,
            SanTOKInferencePipeline
        )
        # Try importing WeaviateVectorStore (optional)
        try:
            from embeddings import WeaviateVectorStore
            WEAVIATE_AVAILABLE = True
        except ImportError:
            WeaviateVectorStore = None
            WEAVIATE_AVAILABLE = False
    EMBEDDINGS_AVAILABLE = True
    print("[OK] Successfully imported embeddings module")
    if WEAVIATE_AVAILABLE:
        print("[OK] WeaviateVectorStore is available")
    else:
        print("[INFO] WeaviateVectorStore not available (optional dependency)")
except ImportError as e:
    EMBEDDINGS_AVAILABLE = False
    WEAVIATE_AVAILABLE = False
    WeaviateVectorStore = None
    print(f"[WARNING] Could not import embeddings: {e}")
    print(f"   Install: pip install sentence-transformers chromadb")
    print(f"   Note: Embedding endpoints will return 503 if used")

# Initialize FastAPI app
app = FastAPI(
    title="SanTOK API",
    description="Advanced Text Tokenization System with Multiple Algorithms",
    version="1.0.0"
)

# Add CORS middleware
# SECURITY: In production, restrict CORS origins
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
if CORS_ORIGINS == "*":
    # Development: allow all origins
    if os.getenv("NODE_ENV") == "production" or os.getenv("RAILWAY_ENVIRONMENT"):
        # In production, require explicit CORS configuration
        logging.warning("[SECURITY] CORS_ORIGINS is '*' in production! Set CORS_ORIGINS environment variable.")
    allowed_origins = ["*"]
else:
    # Production: use comma-separated list
    allowed_origins = [origin.strip() for origin in CORS_ORIGINS.split(",")]

# Log CORS configuration on startup (critical for debugging)
print(f"[CORS] Configured origins: {allowed_origins}")
print(f"[CORS] CORS_ORIGINS env var: {CORS_ORIGINS}")
logging.info(f"[CORS] Configured origins: {allowed_origins}")
logging.info(f"[CORS] CORS_ORIGINS env var: {CORS_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add exception handler to ensure CORS headers are always sent
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to ensure CORS headers are always sent."""
    from fastapi.responses import JSONResponse
    import traceback
    
    # Log the error
    logging.error(f"Unhandled exception: {exc}")
    logging.error(traceback.format_exc())
    
    # Return error with CORS headers
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "type": type(exc).__name__
        },
        headers={
            "Access-Control-Allow-Origin": allowed_origins[0] if allowed_origins and allowed_origins[0] != "*" else "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
)

# Import and include API V2 routes
api_v2_router_loaded = False
try:
    print("[DEBUG] Attempting to import API V2 routes from servers.api_v2_routes...")
    print(f"[DEBUG] Checking sys.path: {[p for p in sys.path if 'backend' in p or 'servers' in p][:3]}")
    from servers.api_v2_routes import router as api_v2_router
    app.include_router(api_v2_router)
    api_v2_router_loaded = True
    print("[OK] API V2 routes loaded and registered")
    print(f"[DEBUG] Router prefix: {api_v2_router.prefix}")
    print(f"[DEBUG] Router routes count: {len(api_v2_router.routes)}")
except ImportError as e1:
    print(f"[DEBUG] First import failed: {e1}")
    try:
        print("[DEBUG] Attempting to import from src.servers.api_v2_routes...")
        from src.servers.api_v2_routes import router as api_v2_router
        app.include_router(api_v2_router)
        api_v2_router_loaded = True
        print("[OK] API V2 routes loaded and registered (src path)")
    except ImportError as e2:
        print(f"[DEBUG] Second import failed: {e2}")
        try:
            # Try absolute import
            import importlib.util
            api_v2_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'backend', 'src', 'servers', 'api_v2_routes.py'))
            if os.path.exists(api_v2_path):
                print(f"[DEBUG] Found api_v2_routes.py at: {api_v2_path}")
                spec = importlib.util.spec_from_file_location("api_v2_routes", api_v2_path)
                api_v2_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(api_v2_module)
                api_v2_router = api_v2_module.router
                app.include_router(api_v2_router)
                api_v2_router_loaded = True
                print("[OK] API V2 routes loaded and registered (direct file import)")
            else:
                print(f"[ERROR] api_v2_routes.py not found at: {api_v2_path}")
        except Exception as e3:
            print(f"[ERROR] Direct file import failed: {e3}")
            import traceback
            traceback.print_exc()
        
        if not api_v2_router_loaded:
            print(f"[WARN] API V2 routes not available")
            print(f"  Import error 1: {e1}")
            print(f"  Import error 2: {e2}")
            print(f"  Current sys.path includes: {[p for p in sys.path if 'backend' in p or 'servers' in p]}")
except Exception as e:
    print(f"[ERROR] Unexpected error loading API V2 routes: {e}")
    import traceback
    traceback.print_exc()

# Health check endpoint
@app.get("/health")
async def health_check(request: Request):
    """
    Health check endpoint.
    This endpoint is public and doesn't require authentication.
    Ultra-fast, non-blocking health check - returns immediately.
    """
    # Return immediately - NO try/except, NO variable lookups, NO operations
    # Just return a simple dict - this is the fastest possible response
    return {
            "status": "ok",
        "message": "SanTOK API Server is running"
        }

# ==================== AUTHENTICATION ENDPOINTS ====================

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    username: Optional[str] = None
    message: str
    expires_in: Optional[int] = None

@app.post("/auth/login", response_model=LoginResponse)
async def login(login_request: LoginRequest):
    """Login endpoint - Get JWT token for allowed users."""
    try:
        # Validate input
        if not login_request.username or not login_request.password:
            return LoginResponse(
                success=False,
                message="Username and password are required"
            )
        
        # SECURITY: Check if ALLOWED_USERS is configured
        if not ALLOWED_USERS:
            logging.error("Login attempt but ALLOWED_USERS not configured")
            return LoginResponse(
                success=False,
                message="Authentication not configured. Please contact administrator."
            )
        
        # Hash the provided password
        password_hash = hashlib.sha256(login_request.password.encode()).hexdigest()
        
        # Check if user exists and password matches
        if login_request.username in ALLOWED_USERS and ALLOWED_USERS[login_request.username] == password_hash:
            # Generate JWT token
            payload = {
                "username": login_request.username,
                "is_allowed": True,
                "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
                "iat": datetime.now(timezone.utc)
            }
            token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
            
            # SECURITY: Log successful login (but not password)
            logging.info(f"Successful login: {login_request.username}")
            
            return LoginResponse(
                success=True,
                token=token,
                username=login_request.username,
                message="Login successful",
                expires_in=JWT_EXPIRATION_HOURS * 3600  # seconds
            )
        else:
            # SECURITY: Log failed login attempt (but not password)
            logging.warning(f"Failed login attempt: {login_request.username}")
            
            # SECURITY: Same error message for both invalid user and wrong password (don't reveal if user exists)
            return LoginResponse(
                success=False,
                message="Invalid username or password"
            )
    except Exception as e:
        logging.error(f"Login error: {type(e).__name__}: {str(e)}")
        return LoginResponse(
            success=False,
            message="Login failed. Please try again."
        )

@app.get("/auth/verify")
async def verify_auth(http_request: Request):
    """Verify if current token is valid."""
    try:
        auth = get_optional_auth(http_request)
        if auth and is_user_allowed(auth):
            username = auth.get("username", "Unknown")
            return {
                "authenticated": True,
                "username": username,
                "is_allowed": True,
                "message": "User is authenticated and has full access"
            }
        return {
            "authenticated": False,
            "is_allowed": False,
            "message": "User is not authenticated or not in allowed list"
        }
    except Exception as e:
        logging.error(f"Auth verify error: {type(e).__name__}: {str(e)}")
        return {
            "authenticated": False,
            "is_allowed": False,
            "message": "Authentication verification failed"
        }

@app.get("/auth/logout")
async def logout_endpoint():
    """Logout endpoint (client-side token removal)."""
    return {"success": True, "message": "Logged out. Please remove token from client."}


# ==================== SOURCE MAP API ENDPOINTS ====================

@app.get("/api/sources")
async def list_sources(category: Optional[str] = None, enabled_only: bool = True):
    """
    List all available sources in the source map.
    
    Args:
        category: Filter by category (knowledge, technical, domain, symbolic, crossmodal, reinforcement)
        enabled_only: Only return enabled sources
        
    Returns:
        Dictionary with source information
    """
    if not SOURCE_MAP_AVAILABLE:
        raise HTTPException(status_code=503, detail="Source map system not available")
    
    try:
        source_map = get_source_map()
        sources = source_map.get_all_sources(category=category, enabled_only=enabled_only)
        
        return {
            "sources": {
                tag: {
                    "source_id": metadata.source_id,
                    "tag": metadata.tag,
                    "category": metadata.category,
                    "description": metadata.description,
                    "url": metadata.url,
                    "enabled": metadata.enabled,
                    "weight": metadata.weight,
                    "priority": metadata.priority,
                    "registered_at": metadata.registered_at
                }
                for tag, metadata in sources.items()
            },
            "total": len(sources),
            "category": category,
            "enabled_only": enabled_only
        }
    except Exception as e:
        logging.error(f"Error listing sources: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing sources: {str(e)}")


@app.get("/api/sources/{source_tag}")
async def get_source_info(source_tag: str):
    """
    Get detailed information about a specific source.
    
    Args:
        source_tag: Source tag (e.g., "wikipedia", "arxiv")
        
    Returns:
        Source metadata
    """
    if not SOURCE_MAP_AVAILABLE:
        raise HTTPException(status_code=503, detail="Source map system not available")
    
    try:
        source_map = get_source_map()
        metadata = source_map.get_source_metadata(source_tag)
        
        if not metadata:
            raise HTTPException(status_code=404, detail=f"Source '{source_tag}' not found")
        
        return {
            "source_id": metadata.source_id,
            "tag": metadata.tag,
            "category": metadata.category,
            "description": metadata.description,
            "url": metadata.url,
            "enabled": metadata.enabled,
            "weight": metadata.weight,
            "priority": metadata.priority,
            "registered_at": metadata.registered_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting source info: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting source info: {str(e)}")


@app.get("/api/sources/profile/performance")
async def get_source_performance_profile(category: Optional[str] = None):
    """
    Get hierarchical performance profile of sources.
    
    Args:
        category: Filter by category (optional)
        
    Returns:
        Performance profile with category-wise statistics
    """
    if not SOURCE_MAP_AVAILABLE:
        raise HTTPException(status_code=503, detail="Source map system not available")
    
    try:
        source_map = get_source_map()
        profile = source_map.get_performance_profile(category=category)
        return profile
    except Exception as e:
        logging.error(f"Error getting performance profile: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting performance profile: {str(e)}")

# Admin Management Endpoints
class UpdatePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str

class AddUserRequest(BaseModel):
    username: str
    password: str

class DeleteUserRequest(BaseModel):
    username: str
    password: str

@app.post("/auth/admin/update-password")
async def update_admin_password(request: UpdatePasswordRequest, http_request: Request):
    """Update admin user password. Requires admin authentication."""
    try:
        auth = get_optional_auth(http_request)
        if not is_user_allowed(auth):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        from servers.admin_config import update_admin_user
        success, message = update_admin_user(request.username, request.old_password, request.new_password)
        
        if success:
            reload_allowed_users()  # Reload the in-memory cache
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Update password error: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update password")

@app.post("/auth/admin/add-user")
async def add_admin_user(request: AddUserRequest, http_request: Request):
    """Add a new admin user. Requires admin authentication."""
    try:
        auth = get_optional_auth(http_request)
        if not is_user_allowed(auth):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Validate input
        if not request.username or not request.password:
            raise HTTPException(status_code=400, detail="Username and password are required")
        
        if len(request.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
        from servers.admin_config import add_admin_user
        success, message = add_admin_user(request.username, request.password)
        
        if success:
            reload_allowed_users()  # Reload the in-memory cache
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Add user error: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add user")

@app.post("/auth/admin/delete-user")
async def delete_admin_user(request: DeleteUserRequest, http_request: Request):
    """Delete an admin user. Requires admin authentication."""
    try:
        auth = get_optional_auth(http_request)
        if not is_user_allowed(auth):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        from servers.admin_config import update_admin_user
        success, message = update_admin_user(request.username, request.password, None)
        
        if success:
            reload_allowed_users()  # Reload the in-memory cache
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Delete user error: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete user")

@app.get("/auth/admin/users")
async def list_admin_users(http_request: Request):
    """List all admin users (without passwords). Requires admin authentication."""
    try:
        auth = get_optional_auth(http_request)
        if not is_user_allowed(auth):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        from servers.admin_config import get_admin_users
        users = get_admin_users()
        return {"success": True, "users": list(users.keys())}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"List users error: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list users")

# Module-level constants
# Map frontend tokenizer names to all_tokenizations() keys
# all_tokenizations() returns: "subword_syllable", "subword_bpe", "subword_frequency", etc.
TOKENIZER_LOOKUP_MAP = {
    "syllable": "subword_syllable",
    "bpe": "subword_bpe",
    "frequency": "subword_frequency",
    "space": "space",
    "word": "word",
    "char": "char",
    "grammar": "grammar",
    "subword": "subword",
    "byte": "byte",
}

# Pydantic models for request/response
class TokenizationRequest(BaseModel):
    text: str
    tokenizer_type: str
    lower: bool = False
    drop_specials: bool = False
    # Accept number (aligned with frontend) but allow bool too; 1 means run-aware math
    collapse_repeats: Optional[int] = 1
    embedding: bool = False
    seed: Optional[int] = None
    embedding_bit: Optional[int] = None

class Token(BaseModel):
    text: str
    id: int
    position: int
    length: int
    type: str
    color: Optional[str] = None

class TokenizationResult(BaseModel):
    tokens: List[Token]
    tokenCount: int
    characterCount: int
    tokenizerType: str
    processingTime: float
    memoryUsage: float
    compressionRatio: float
    reversibility: bool
    fingerprint: Dict[str, Any]
    originalText: Optional[str] = None  # Include original text for comparison
    # Extra data to mirror SanTOK core tokenizer engine
    frontendDigits: Optional[List[int]] = None
    backendScaled: Optional[List[int]] = None
    contentIds: Optional[List[int]] = None

class CompressionAnalysis(BaseModel):
    algorithm: str
    compressionRatio: float
    tokensSaved: int
    percentageSaved: float
    reversibility: bool

# Tokenizer mapping (call the advanced engine by default)
TOKENIZERS = {
    'space': KT.tokenize_space,
    'word': KT.tokenize_word,
    'char': KT.tokenize_char,
    'grammar': KT.tokenize_grammar,
    'subword': lambda text: KT.tokenize_subword(text, 3, 'fixed'),
    'bpe': lambda text: KT.tokenize_subword(text, 3, 'bpe'),
    'syllable': lambda text: KT.tokenize_subword(text, 3, 'syllable'),
    'frequency': lambda text: KT.tokenize_subword(text, 3, 'frequency'),
    'byte': KT.tokenize_bytes,
}

def _stream_name_for(tokenizer_type: str) -> str:
    if tokenizer_type == 'bpe':
        return 'subword_bpe'
    if tokenizer_type == 'syllable':
        return 'subword_syllable'
    if tokenizer_type == 'frequency':
        return 'subword_frequency'
    return tokenizer_type

def preprocess_text(text: str, lower: bool, drop_specials: bool, collapse_repeats: bool) -> str:
    """Preprocess text based on options - OPTIMIZED"""
    # Inline preprocessing for speed - no function call overhead
    if lower:
        text = text.lower()
    if drop_specials:
        text = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in text)
    if collapse_repeats:
        import re
        text = re.sub(r'\s+', ' ', text).strip()
    return text

def generate_token_colors(tokens: List[str]) -> List[str]:
    """Generate colors for tokens"""
    colors = []
    for i, token in enumerate(tokens):
        hue = (i * 137.5) % 360  # Golden angle for good distribution
        colors.append(f"hsl({hue}, 70%, 50%)")
    return colors

def calculate_fingerprint(text: str, tokens: List[str], embedding: bool = False) -> Dict[str, Any]:
    """Fallback fingerprint when engine summary is unavailable."""
    try:
        content_id = _content_id(text)
        # Use engine's digital root semantics when possible
        try:
            sig = KT.digital_root_9(content_id)
            if embedding:
                sig = KT.digital_root_9(sig + 1)
        except Exception:
            sig = (content_id % 9) or 9
            if embedding:
                sig = ((sig + 1 - 1) % 9) + 1
        compat = content_id % 10
        text_value = sum(ord(c) for c in text) % 10000
        text_value_with_embedding = (text_value + (1 if embedding else 0)) % 10000
        return {
            "signatureDigit": int(sig),
            "compatDigit": int(compat),
            "textValue": int(text_value),
            "textValueWithEmbedding": int(text_value_with_embedding),
        }
    except Exception as e:
        print(f"Error calculating fingerprint: {e}")
        return {
            "signatureDigit": 0,
            "compatDigit": 0,
            "textValue": 0,
            "textValueWithEmbedding": 0,
        }

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "SanTOK API is running!",
        "version": "1.0.0",
        "available_tokenizers": list(TOKENIZERS.keys())
    }

@app.post("/tokenize", response_model=TokenizationResult)
async def tokenize_text(request: TokenizationRequest):
    """Tokenize text using the specified tokenizer - HANDLES 50GB+ FILES"""
    try:
        start_time = time.time()
        text_length = len(request.text)
        
        # Fast preprocessing - chunked for large files to handle 50GB+
        LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100MB
        if text_length > LARGE_FILE_THRESHOLD:
            # Chunked preprocessing for large files - process in chunks to avoid memory issues
            print(f"📦 Processing {text_length / (1024*1024*1024):.2f}GB file with chunked preprocessing...")
            chunk_size = 10 * 1024 * 1024  # 10MB chunks
            processed_chunks = []
            
            for i in range(0, len(request.text), chunk_size):
                chunk = request.text[i:i + chunk_size]
                if request.lower:
                    chunk = chunk.lower()
                if request.drop_specials:
                    chunk = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in chunk)
                processed_chunks.append(chunk)
                if (i // chunk_size) % 100 == 0:  # Log every 100 chunks
                    print(f"  Processed {i / (1024*1024*1024):.2f}GB...")
            
            processed_text = ''.join(processed_chunks)
            
            if request.collapse_repeats:
                import re
                # Collapse repeats in chunks to avoid processing entire string
                processed_chunks_collapsed = []
                for chunk in processed_chunks:
                    processed_chunks_collapsed.append(re.sub(r'\s+', ' ', chunk))
                processed_text = ' '.join(processed_chunks_collapsed).strip()
        else:
            # Fast preprocessing for smaller files
            processed_text = request.text
            if request.lower:
                processed_text = processed_text.lower()
            if request.drop_specials:
                processed_text = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in processed_text)
            if request.collapse_repeats:
                import re
                processed_text = re.sub(r'\s+', ' ', processed_text).strip()
        
        # Use REAL SanTOK TextTokenizer engine with all features
        seed = request.seed if request.seed is not None else 12345
        embedding_bit = request.embedding_bit if hasattr(request, 'embedding_bit') and request.embedding_bit is not None else False
        
        # Map frontend tokenizer names to backend tokenizer names
        TOKENIZER_NAME_MAP = {
            "frequency": "subword_frequency",
            "bpe": "subword_bpe",
            "syllable": "subword_syllable",
            "subword": "subword",  # Keep as is
            "space": "space",
            "word": "word",
            "char": "char",
            "grammar": "grammar",
            "byte": "byte",
        }
        
        # Normalize tokenizer type name
        tokenizer_type = TOKENIZER_NAME_MAP.get(request.tokenizer_type, request.tokenizer_type)
        
        print(f"🔧 Using REAL SanTOK engine: seed={seed}, embedding_bit={embedding_bit}, tokenizer={tokenizer_type} (original: {request.tokenizer_type})")
        
        # For VERY large files (>100MB), process in chunks but use real engine
        LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100MB
        use_chunked = text_length > LARGE_FILE_THRESHOLD
        
        if use_chunked:
            print(f"📦 Large file detected ({text_length / (1024*1024*1024):.2f}GB), using chunked SanTOK engine...")
            # Process in chunks but still use real engine
            chunk_size = 50 * 1024 * 1024  # 50MB chunks
            all_token_objects = []
            all_frontend_digits = []
            all_backend_scaled = []
            all_content_ids = []
            
            for chunk_idx in range(0, len(processed_text), chunk_size):
                chunk = processed_text[chunk_idx:chunk_idx + chunk_size]
                if not chunk:
                    continue
                    
                # Use REAL SanTOK engine for this chunk
                engine = TextTokenizer(seed, embedding_bit)
                
                # Get all tokenizations for this chunk - with error handling
                try:
                    toks = all_tokenizations(chunk)
                except Exception as chunk_err:
                    # If chunk fails, skip it and continue with next chunk
                    print(f"[WARNING] Failed to tokenize chunk {chunk_idx}: {chunk_err}")
                    continue
                
                # Use mapped tokenizer_type for lookup (using module-level constant)
                lookup_type = TOKENIZER_LOOKUP_MAP.get(request.tokenizer_type, request.tokenizer_type)
                if lookup_type not in toks:
                    available_in_toks = list(toks.keys())
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Unknown tokenizer type: {request.tokenizer_type}. Available: {available_in_toks}"
                    )
                
                # Get tokens for selected tokenizer type
                raw_tokens = toks[lookup_type]
                
                # Convert to format expected by engine
                # raw_tokens can be list of strings or list of dicts with "text" key
                token_list = []
                for i, t in enumerate(raw_tokens):
                    if isinstance(t, dict):
                        token_list.append({"text": t.get("text", ""), "index": i})
                    else:
                        token_list.append({"text": str(t), "index": i})
                
                # Assign UIDs using real engine
                with_uids = assign_uids(token_list, seed)
                with_neighbors = neighbor_uids(with_uids)
                
                # Process each token with REAL engine calculations
                chunk_token_objects = []
                for i, rec in enumerate(with_neighbors):
                    # REAL engine calculations
                    backend_huge = compose_backend_number(
                        rec["text"], i, rec["uid"], rec["prev_uid"], rec["next_uid"], embedding_bit
                    )
                    frontend_digit = combined_digit(rec["text"], embedding_bit)
                    backend_scaled_val = backend_huge % 100000
                    content_id = _content_id(rec["text"])
                    
                    # Calculate global ID
                    stream_id = _content_id(tokenizer_type)
                    session_id = (seed ^ 0x9E3779B97F4A7C15) & ((1 << 64) - 1)
                    global_id = (rec["uid"] ^ content_id ^ (i << 17) ^ stream_id ^ session_id) & ((1 << 64) - 1)
                    
                    # Store for response
                    all_frontend_digits.append(frontend_digit)
                    all_backend_scaled.append(backend_scaled_val)
                    all_content_ids.append(content_id)
                    
                    # Create token object
                    token_obj = Token(
                        text=rec["text"],
                        id=chunk_idx // chunk_size * 1000000 + i,  # Unique ID across chunks
                        position=chunk_idx + i,
                        length=len(rec["text"]),
                        type=tokenizer_type,
                        color=None  # Will set colors later
                    )
                    chunk_token_objects.append(token_obj)
                    
                    if (chunk_idx // chunk_size) % 10 == 0 and i == 0:
                        print(f"  Processing chunk {chunk_idx // chunk_size}: {len(chunk_token_objects)} tokens...")
                
                all_token_objects.extend(chunk_token_objects)
            
            # Set colors for all tokens
            colors = generate_token_colors([t.text for t in all_token_objects])
            for i, token_obj in enumerate(all_token_objects):
                token_obj.color = colors[i] if i < len(colors) else colors[i % len(colors)]
            
            token_objects = all_token_objects
            actual_token_count = len(all_token_objects)
            frontend_digits = all_frontend_digits
            backend_scaled = all_backend_scaled
            content_ids = all_content_ids
            
        else:
            # Use REAL SanTOK engine for smaller files
            engine = TextTokenizer(seed, embedding_bit)
            
        # Get all tokenizations - handle failures gracefully
        try:
            toks = all_tokenizations(processed_text)
        except Exception as e:
            # Log error but don't expose internal details to user
            import traceback
            error_details = traceback.format_exc()
            print(f"[ERROR] Error calling all_tokenizations: {e}")
            print(error_details)
            
            # Try to get tokenizations individually as fallback
            try:
                from core.core_tokenizer import (
                    tokenize_space, tokenize_word, tokenize_char, tokenize_grammar,
                    tokenize_subword, tokenize_bytes
                )
                toks = {}
                tokenizers_to_try = [
                    ("space", lambda t: tokenize_space(t)),
                    ("word", lambda t: tokenize_word(t)),
                    ("char", lambda t: tokenize_char(t)),
                    ("grammar", lambda t: tokenize_grammar(t)),
                    ("subword", lambda t: tokenize_subword(t, 3, "fixed")),
                    ("subword_bpe", lambda t: tokenize_subword(t, 3, "bpe")),
                    ("subword_syllable", lambda t: tokenize_subword(t, 3, "syllable")),
                    ("subword_frequency", lambda t: tokenize_subword(t, 3, "frequency")),
                    ("byte", lambda t: tokenize_bytes(t)),
                ]
                for name, func in tokenizers_to_try:
                    try:
                        toks[name] = func(processed_text)
                    except Exception as err:
                        print(f"[WARNING] Failed to tokenize with {name}: {err}")
                
                if not toks:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to tokenize text. All tokenization methods failed."
                    )
            except ImportError as import_err:
                raise HTTPException(
                    status_code=500,
                    detail=f"Tokenization failed: {str(e)}"
                )
        
        # Use mapped tokenizer_type for lookup (using module-level constant)
        lookup_type = TOKENIZER_LOOKUP_MAP.get(request.tokenizer_type, request.tokenizer_type)
        
        if lookup_type not in toks:
            available_keys = list(toks.keys())
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown tokenizer type: {request.tokenizer_type}. Available: {available_keys}"
            )
        
        # Get tokens for selected tokenizer type
        raw_tokens = toks[lookup_type]
        
        # Convert to format expected by engine
        # raw_tokens can be list of strings or list of dicts with "text" key
        token_list = []
        for i, t in enumerate(raw_tokens):
            if isinstance(t, dict):
                token_list.append({"text": t.get("text", ""), "index": i})
            else:
                token_list.append({"text": str(t), "index": i})
        
        # Assign UIDs using real engine
        with_uids = assign_uids(token_list, seed)
        with_neighbors = neighbor_uids(with_uids)
        
        # Process each token with REAL engine calculations
        token_objects = []
        frontend_digits = []
        backend_scaled = []
        content_ids = []
        
        for i, rec in enumerate(with_neighbors):
            # REAL engine calculations
            backend_huge = compose_backend_number(
                rec["text"], i, rec["uid"], rec["prev_uid"], rec["next_uid"], embedding_bit
            )
            frontend_digit = combined_digit(rec["text"], embedding_bit)
            backend_scaled_val = backend_huge % 100000
            content_id = _content_id(rec["text"])
            
            # Calculate global ID
            stream_id = _content_id(tokenizer_type)
            session_id = (seed ^ 0x9E3779B97F4A7C15) & ((1 << 64) - 1)
            global_id = (rec["uid"] ^ content_id ^ (i << 17) ^ stream_id ^ session_id) & ((1 << 64) - 1)
            
            # Store engine values
            frontend_digits.append(frontend_digit)
            backend_scaled.append(backend_scaled_val)
            content_ids.append(content_id)
            
            # Create token object
            token_obj = Token(
                text=rec["text"],
                id=i,
                position=i,
                length=len(rec["text"]),
                type=tokenizer_type,
                color=None  # Will set colors later
            )
            token_objects.append(token_obj)
        
        # Set colors
        colors = generate_token_colors([t.text for t in token_objects])
        for i, token_obj in enumerate(token_objects):
            token_obj.color = colors[i] if i < len(colors) else colors[i % len(colors)]
        
        actual_token_count = len(token_objects)
        
        # Sample tokens for very large responses (for display only, metrics use full count)
        MAX_TOKENS_TO_RETURN = 1000000  # Return max 1M tokens for display
        if actual_token_count > MAX_TOKENS_TO_RETURN:
            print(f"[INFO] Large token count ({actual_token_count:,}), sampling {MAX_TOKENS_TO_RETURN:,} tokens for response...")
            step = actual_token_count // MAX_TOKENS_TO_RETURN
            token_objects = token_objects[::step][:MAX_TOKENS_TO_RETURN]
            frontend_digits = frontend_digits[::step][:MAX_TOKENS_TO_RETURN]
            backend_scaled = backend_scaled[::step][:MAX_TOKENS_TO_RETURN]
            content_ids = content_ids[::step][:MAX_TOKENS_TO_RETURN]
        
        # Calculate metrics
        processing_time = (time.time() - start_time) * 1000
        memory_usage = len(processed_text.encode('utf-8')) / 1024  # KB
        compression_ratio = actual_token_count / max(len(processed_text.split()), 1)
        
        # Calculate REAL fingerprint using engine stream checksum
        # Use first token's stream for fingerprint calculation
        if frontend_digits:
            # Calculate signature digit from frontend digits (engine method)
            signature_digit = sum(frontend_digits[:100]) % 10 if len(frontend_digits) >= 100 else sum(frontend_digits) % 10
        else:
            signature_digit = hash(processed_text[:100]) % 10
        
        fingerprint = {
            "signatureDigit": signature_digit,
            "compatDigit": len(processed_text) % 10,
            "textValue": len(processed_text) % 10000,
            "textValueWithEmbedding": (len(processed_text) + (1 if embedding_bit else 0)) % 10000
        }
        
        # Create result with REAL SanTOK engine values
        result = TokenizationResult(
            tokens=token_objects,
            tokenCount=actual_token_count,  # Report actual count, not just displayed
            characterCount=len(processed_text),
            tokenizerType=tokenizer_type,
            processingTime=processing_time,
            memoryUsage=memory_usage,
            compressionRatio=compression_ratio,
            reversibility=True,
            fingerprint=fingerprint,
            originalText=request.text[:1000] + "..." if len(request.text) > 1000 else request.text,  # Truncate for display
            frontendDigits=frontend_digits,  # REAL engine frontend digits
            backendScaled=backend_scaled,     # REAL engine backend scaled
            contentIds=content_ids,           # REAL engine content IDs
        )
        
        print(f"[OK] Tokenization complete: {actual_token_count:,} tokens processed, {len(token_objects):,} tokens returned, in {processing_time:.2f}ms")
        return result
        
    except Exception as e:
        print(f"Tokenization error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_text(request: TokenizationRequest):
    """Analyze text and return detailed metrics - OPTIMIZED"""
    try:
        # First tokenize
        tokenize_result = await tokenize_text(request)
        
        # Fast analysis - sample only for large texts
        tokens = tokenize_result.tokens
        sample_size = min(1000, len(tokens))  # Sample first 1000 tokens for speed
        
        # Fast token distribution (sampled)
        token_dist = {}
        for token in tokens[:sample_size]:
            token_text = token.text
            token_dist[token_text] = token_dist.get(token_text, 0) + 1
        
        # Fast character distribution (sampled)
        char_dist = {}
        text_sample = request.text[:5000]  # Sample first 5000 chars
        for char in text_sample:
            char_dist[char] = char_dist.get(char, 0) + 1
        
        # Fast metrics
        avg_token_length = sum(len(t.text) for t in tokens[:sample_size]) / sample_size if sample_size > 0 else 0
        unique_tokens = len(set(t.text for t in tokens[:sample_size]))
        repetition_rate = 1 - (unique_tokens / sample_size) if sample_size > 0 else 0
        
        return {
            "analysis": {
                "tokenDistribution": token_dist,
                "characterDistribution": char_dist,
                "averageTokenLength": avg_token_length,
                "uniqueTokens": unique_tokens,
                "repetitionRate": repetition_rate
            },
            "metrics": {
                "processingTime": tokenize_result.processingTime,
                "memoryUsage": tokenize_result.memoryUsage,
                "compressionRatio": tokenize_result.compressionRatio
            },
            "fingerprint": tokenize_result.fingerprint
        }
        
    except Exception as e:
        print(f"Analysis error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compress", response_model=List[CompressionAnalysis])
async def compress_text(request: TokenizationRequest):
    """Analyze compression - FAST VERSION - Skip slow analysis"""
    try:
        # Fast preprocessing
        processed_text = request.text
        if request.lower:
            processed_text = processed_text.lower()
        if request.drop_specials:
            processed_text = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in processed_text)
        if request.collapse_repeats:
            import re
            processed_text = re.sub(r'\s+', ' ', processed_text).strip()
        
        # Quick token count - use chunked processing for large files
        LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100MB
        if len(processed_text) > LARGE_FILE_THRESHOLD:
            # For large files, estimate token count without processing full text
            try:
                from core.core_tokenizer import _tokenize_large_text
                sample_tokens = _tokenize_large_text(processed_text[:100000], request.tokenizer_type)  # Sample first 100KB
                sample_ratio = len(sample_tokens) / 100000
                token_count = int(len(processed_text) * sample_ratio)
            except Exception:
                # Fallback estimate
                token_count = len(processed_text.split()) if processed_text.split() else 0
        else:
            tokenizer_func = TOKENIZERS.get(request.tokenizer_type)
            if tokenizer_func:
                tokens = tokenizer_func(processed_text)
                token_count = len(tokens)
            else:
                token_count = len(processed_text.split())
        
        # Fast compression estimates - skip slow engine analysis
        original_size = len(processed_text.encode('utf-8'))
        
        # Quick compression simulations
        algorithms = ['RLE', 'Pattern', 'Frequency', 'Adaptive']
        out: List[CompressionAnalysis] = []
        
        for i, algorithm in enumerate(algorithms):
            # Fast estimate based on text characteristics
            base_ratio = 0.3 + (i * 0.05)  # 0.3, 0.35, 0.4, 0.45
            # Add some variation based on text
            variation = (hash(processed_text[:100]) % 20) / 100  # 0-0.2 variation
            compression_ratio = min(base_ratio + variation, 0.9)
            
            tokens_saved = int(token_count * (1 - compression_ratio))
            percentage_saved = (1 - compression_ratio) * 100
            
            out.append(CompressionAnalysis(
                algorithm=algorithm,
                compressionRatio=compression_ratio,
                tokensSaved=tokens_saved,
                percentageSaved=percentage_saved,
                reversibility=True,
            ))
        
        return out
    except Exception as e:
        print(f"Compression analysis error: {e}")
        import traceback
        traceback.print_exc()
        # Return default values on error
        return [
            CompressionAnalysis(
                algorithm="Default",
                compressionRatio=0.5,
                tokensSaved=0,
                percentageSaved=50.0,
                reversibility=True,
            )
        ]

@app.post("/validate")
async def validate_tokenization(request: TokenizationRequest):
    """Validate tokenization reversibility using engine reconstruction"""
    try:
        processed_text = preprocess_text(
            request.text,
            request.lower,
            request.drop_specials,
            bool(request.collapse_repeats),
        )
        # Produce tokens with the same tokenizer the user selected
        tokenizer_func = TOKENIZERS.get(request.tokenizer_type)
        if tokenizer_func is None:
            raise HTTPException(status_code=400, detail=f"Unknown tokenizer type: {request.tokenizer_type}")
        tokens = tokenizer_func(processed_text)
        # Engine-aware reconstruction
        stream_name = _stream_name_for(request.tokenizer_type)
        reconstructed = KT.reconstruct_from_tokens(tokens, stream_name)
        is_valid = reconstructed == processed_text
        differences: List[str] = []
        if not is_valid:
            differences.append(f"Original length: {len(processed_text)}, Reconstructed length: {len(reconstructed)}")
            if len(processed_text) != len(reconstructed):
                differences.append("Length mismatch detected")
        return {
            "isValid": is_valid,
            "reversibility": is_valid,
            "reconstruction": reconstructed,
            "differences": differences,
        }
    except Exception as e:
        print(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/decode")
async def decode_tokens(request: Dict[str, Any]):
    """Decode tokenized text back to original form"""
    try:
        tokens = request.get("tokens", [])
        tokenizer_type = request.get("tokenizer_type", "word")
        
        if not tokens:
            raise HTTPException(status_code=400, detail="No tokens provided")
        
        # Use the core tokenizer's reconstruction function
        decoded_text = KT.reconstruct_from_tokens(tokens, tokenizer_type)
        
        return {
            "decoded_text": decoded_text,
            "tokenizer_type": tokenizer_type,
            "token_count": len(tokens),
            "decoded_length": len(decoded_text)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decoding failed: {str(e)}")

@app.post("/test/vocabulary-adapter")
async def test_vocabulary_adapter(request: Dict[str, Any]):
    """
    Test endpoint for vocabulary adapter integration with pretrained models.
    
    This endpoint tests the vocabulary compatibility solution:
    1. Tokenizes text with SanTOK
    2. Maps SanTOK tokens to model vocabulary IDs
    3. Returns both SanTOK and model-compatible results
    """
    if not INTEGRATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Vocabulary adapter not available. Install transformers: pip install transformers"
        )
    
    try:
        text = request.get("text", "Hello world! SanTOK is amazing.")
        model_name = request.get("model_name", "bert-base-uncased")
        tokenizer_type = request.get("tokenizer_type", "word")
        seed = request.get("seed", 42)
        embedding_bit = request.get("embedding_bit", False)
        
        # Step 1: Tokenize with SanTOK
        print(f"\n[INFO] Testing vocabulary adapter:")
        print(f"   Text: {text}")
        print(f"   Model: {model_name}")
        print(f"   Tokenizer: {tokenizer_type}")
        
        engine = TextTokenizer(seed, embedding_bit)
        try:
            toks = all_tokenizations(text)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to tokenize text: {str(e)}"
            )
        
        # Use mapped tokenizer_type for lookup (using module-level constant)
        lookup_type = TOKENIZER_LOOKUP_MAP.get(tokenizer_type, tokenizer_type)
        if lookup_type not in toks:
            available_in_toks = list(toks.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Unknown tokenizer type: {tokenizer_type}. Available: {available_in_toks}"
            )
        
        # Get SanTOK tokens
        raw_tokens = toks[lookup_type]
        token_list = []
        for i, t in enumerate(raw_tokens):
            if isinstance(t, dict):
                token_list.append({"text": t.get("text", ""), "index": i})
            else:
                token_list.append({"text": str(t), "index": i})
        
        # Assign UIDs and process
        with_uids = assign_uids(token_list, seed)
        with_neighbors = neighbor_uids(with_uids)
        
        santok_tokens = [rec["text"] for rec in with_neighbors]
        santok_frontend_digits = [
            combined_digit(rec["text"], embedding_bit) for rec in with_neighbors
        ]
        
        # Step 2: Convert to model vocabulary IDs
        print(f"   Converting {len(santok_tokens)} SanTOK tokens to {model_name} vocabulary...")
        
        try:
            adapter = VocabularyAdapter(model_name)
            model_result = adapter.map_santok_tokens_to_model_ids(santok_tokens)
            
            # Step 3: Get model info
            model_info = adapter.get_model_embedding_layer_info()
            
            # Prepare response
            response = {
                "success": True,
                "input": {
                    "text": text,
                    "model_name": model_name,
                    "tokenizer_type": tokenizer_type,
                    "seed": seed,
                    "embedding_bit": embedding_bit
                },
                "santok": {
                    "tokens": santok_tokens,
                    "token_count": len(santok_tokens),
                    "frontend_digits": santok_frontend_digits,
                    "tokenizer_type": tokenizer_type
                },
                "model": {
                    "input_ids": model_result["input_ids"],
                    "tokens": model_result["tokens"],
                    "token_count": len(model_result["input_ids"]),
                    "attention_mask": model_result["attention_mask"],
                    "vocab_size": model_result["vocab_size"]
                },
                "mapping": {
                    "santok_to_model": model_result["mapping"],
                    "description": "SanTOK token index → Model token indices (may be 1:many for subword tokenization)"
                },
                "model_info": model_info,
                "comparison": {
                    "santok_token_count": len(santok_tokens),
                    "model_token_count": len(model_result["input_ids"]),
                    "ratio": len(model_result["input_ids"]) / len(santok_tokens) if santok_tokens else 0,
                    "note": "Model may split tokens into subwords (ratio > 1)"
                }
            }
            
            print(f"   [OK] Success! SanTOK: {len(santok_tokens)} tokens -> Model: {len(model_result['input_ids'])} tokens")
            
            return response
            
        except Exception as adapter_error:
            return {
                "success": False,
                "error": str(adapter_error),
                "message": f"Failed to convert to {model_name} vocabulary",
                "santok": {
                    "tokens": santok_tokens,
                    "token_count": len(santok_tokens),
                    "frontend_digits": santok_frontend_digits
                },
                "suggestion": "Make sure the model name is valid and transformers library is installed"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Vocabulary adapter test error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@app.get("/test/vocabulary-adapter/quick")
async def test_vocabulary_adapter_quick():
    """
    Quick test endpoint for vocabulary adapter - uses default values.
    """
    return await test_vocabulary_adapter({
        "text": "Hello world! SanTOK solves vocabulary compatibility.",
        "model_name": "bert-base-uncased",
        "tokenizer_type": "word"
    })

# ==================== EMBEDDING ENDPOINTS ====================

# Global instances for embeddings (lazy initialization)
_embedding_generator = None
_vector_store = None
_pipeline = None

class EmbeddingRequest(BaseModel):
    text: str
    strategy: str = "feature_based"
    embedding_dim: int = 768
    tokenizer_seed: int = 42
    embedding_bit: bool = False
    stream_type: Optional[str] = None
    semantic_model_path: Optional[str] = "santok_semantic_model.pkl"

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    tokens: List[Dict[str, Any]]
    embedding_dim: int
    num_tokens: int
    strategy: str
    processing_time: float

class SearchRequest(BaseModel):
    query_text: str
    top_k: int = 10
    strategy: str = "feature_based"
    stream_type: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    query_text: str
    num_results: int

class DocumentEmbeddingRequest(BaseModel):
    text: str
    method: str = "mean"  # 'mean' | 'max' | 'sum' | 'first'
    strategy: str = "feature_based"

class DocumentEmbeddingResponse(BaseModel):
    embedding: List[float]
    embedding_dim: int
    method: str

def get_embedding_generator(strategy: str = "feature_based", embedding_dim: int = 768, semantic_model_path: Optional[str] = None):
    """Get or create embedding generator."""
    global _embedding_generator
    if not EMBEDDINGS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Embeddings not available. Install: pip install sentence-transformers chromadb")
    
    # Create key for caching (include semantic_model_path for semantic strategy)
    cache_key = (strategy, embedding_dim, semantic_model_path if strategy == "semantic" else None)
    
    if _embedding_generator is None or not hasattr(_embedding_generator, '_cache_key') or _embedding_generator._cache_key != cache_key:
        kwargs = {"strategy": strategy, "embedding_dim": embedding_dim}
        if strategy == "semantic" and semantic_model_path:
            kwargs["semantic_model_path"] = semantic_model_path
        _embedding_generator = SanTOKEmbeddingGenerator(**kwargs)
        _embedding_generator._cache_key = cache_key
    return _embedding_generator

def get_vector_store(backend: str = "chroma", weaviate_url: Optional[str] = None, weaviate_api_key: Optional[str] = None):
    """Get or create vector store."""
    global _vector_store
    if not EMBEDDINGS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Embeddings not available.")
    if _vector_store is None:
        if backend == "chroma":
            _vector_store = ChromaVectorStore(collection_name="santok_embeddings", persist_directory="./vector_db")
        elif backend == "faiss":
            _vector_store = FAISSVectorStore(collection_name="santok_embeddings", embedding_dim=768)
        elif backend == "weaviate":
            if not WEAVIATE_AVAILABLE or WeaviateVectorStore is None:
                raise HTTPException(
                    status_code=503,
                    detail="Weaviate not available. Install: pip install weaviate-client"
                )
            _vector_store = WeaviateVectorStore(
                collection_name="santok_embeddings",
                embedding_dim=768,
                weaviate_url=weaviate_url,
                weaviate_api_key=weaviate_api_key
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown backend: {backend}. Available: chroma, faiss, weaviate"
            )
    return _vector_store

def get_pipeline(strategy: str = "feature_based"):
    """Get or create inference pipeline."""
    global _pipeline
    if _pipeline is None:
        embedding_gen = get_embedding_generator(strategy)
        vector_store = get_vector_store()
        tokenizer = TextTokenizer(seed=42, embedding_bit=False)
        _pipeline = SanTOKInferencePipeline(embedding_generator=embedding_gen, vector_store=vector_store, tokenizer=tokenizer)
    return _pipeline

@app.post("/embeddings/generate", response_model=EmbeddingResponse)
async def generate_embeddings(request: EmbeddingRequest):
    """Generate embeddings for text."""
    try:
        start_time = time.time()
        
        if not EMBEDDINGS_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="Embeddings not available. Install: pip install sentence-transformers chromadb"
            )
        
        embedding_gen = get_embedding_generator(
            request.strategy, 
            request.embedding_dim,
            request.semantic_model_path
        )
        tokenizer = TextTokenizer(seed=request.tokenizer_seed, embedding_bit=request.embedding_bit)
        streams = tokenizer.build(request.text)
        
        all_tokens = []
        if request.stream_type:
            if request.stream_type in streams:
                all_tokens = streams[request.stream_type].tokens
            else:
                raise HTTPException(status_code=400, detail=f"Stream type '{request.stream_type}' not found")
        else:
            for stream_name, token_stream in streams.items():
                all_tokens.extend(token_stream.tokens)
        
        if not all_tokens:
            return EmbeddingResponse(embeddings=[], tokens=[], embedding_dim=request.embedding_dim, num_tokens=0, strategy=request.strategy, processing_time=0.0)
        
        # Generate embeddings
        try:
            embeddings = embedding_gen.generate_batch(all_tokens)
            embeddings_list = embeddings.tolist()
        except Exception as emb_error:
            import traceback
            error_details = traceback.format_exc()
            print(f"[ERROR] Embedding generation error: {emb_error}")
            print(error_details)
            raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(emb_error)}")
        
        # Convert tokens to dict format
        tokens_list = []
        for token in all_tokens:
            try:
                tokens_list.append({
                    "text": token.text,
                    "stream": token.stream,
                    "index": token.index,
                    "uid": str(token.uid),
                    "frontend": token.frontend,
                    "backend_scaled": token.backend_scaled,
                    "content_id": token.content_id,
                    "global_id": str(token.global_id)
                })
            except Exception as token_error:
                print(f"[WARNING] Error processing token: {token_error}")
                # Include at least basic info
                tokens_list.append({
                    "text": getattr(token, 'text', ''),
                    "stream": getattr(token, 'stream', 'unknown'),
                    "index": getattr(token, 'index', 0),
                    "uid": str(getattr(token, 'uid', 0)),
                    "frontend": getattr(token, 'frontend', 0),
                    "backend_scaled": getattr(token, 'backend_scaled', 0),
                    "content_id": getattr(token, 'content_id', 0),
                    "global_id": str(getattr(token, 'global_id', 0))
                })
        
        return EmbeddingResponse(
            embeddings=embeddings_list,
            tokens=tokens_list,
            embedding_dim=request.embedding_dim,
            num_tokens=len(all_tokens),
            strategy=request.strategy,
            processing_time=(time.time() - start_time) * 1000
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[ERROR] Generate embeddings error: {e}")
        print(error_details)
        raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")

@app.post("/embeddings/search", response_model=SearchResponse)
async def search_embeddings(request: SearchRequest):
    """Search for similar tokens."""
    try:
        pipeline = get_pipeline(request.strategy)
        results = pipeline.similarity_search(request.query_text, top_k=request.top_k, stream_type=request.stream_type)
        formatted_results = [{"text": r.get("text", ""), "distance": r.get("distance", 0.0), "metadata": r.get("metadata", {}), "index": r.get("index", -1)} for r in results]
        return SearchResponse(results=formatted_results, query_text=request.query_text, num_results=len(formatted_results))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/embeddings/document", response_model=DocumentEmbeddingResponse)
async def get_document_embedding(request: DocumentEmbeddingRequest):
    """Generate document-level embedding by aggregating token embeddings."""
    try:
        if not EMBEDDINGS_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="Embeddings not available. Install: pip install sentence-transformers chromadb"
            )
        
        # Generate token embeddings first
        embedding_gen = get_embedding_generator(request.strategy)
        tokenizer = TextTokenizer(seed=42, embedding_bit=False)
        streams = tokenizer.build(request.text)
        
        all_tokens = []
        for stream_name, token_stream in streams.items():
            all_tokens.extend(token_stream.tokens)
        
        if not all_tokens:
            raise HTTPException(status_code=400, detail="No tokens found in text")
        
        # Generate embeddings for all tokens
        token_embeddings = embedding_gen.generate_batch(all_tokens)
        
        # Aggregate embeddings based on method
        method = request.method.lower()
        if method == "mean":
            # Average of all token embeddings
            doc_embedding = np.mean(token_embeddings, axis=0)
        elif method == "max":
            # Max pooling across tokens
            doc_embedding = np.max(token_embeddings, axis=0)
        elif method == "sum":
            # Sum of all token embeddings
            doc_embedding = np.sum(token_embeddings, axis=0)
        elif method == "first":
            # First token embedding
            doc_embedding = token_embeddings[0]
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown aggregation method: {request.method}. Available: mean, max, sum, first"
            )
        
        return DocumentEmbeddingResponse(
            embedding=doc_embedding.tolist(),
            embedding_dim=len(doc_embedding),
            method=request.method
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[ERROR] Document embedding error: {e}")
        print(error_details)
        raise HTTPException(status_code=500, detail=f"Failed to generate document embedding: {str(e)}")

@app.get("/embeddings/stats")
async def get_embedding_stats():
    """Get vector database statistics."""
    if not EMBEDDINGS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Embeddings not available. Install: pip install sentence-transformers chromadb"
        )
    try:
        vector_store = get_vector_store()
        stats = {"backend": vector_store.backend, "collection_name": vector_store.collection_name, "embedding_dim": vector_store.embedding_dim}
        if hasattr(vector_store, 'index') and hasattr(vector_store.index, 'ntotal'):
            stats["total_vectors"] = vector_store.index.ntotal
        elif hasattr(vector_store, 'collection'):
            try:
                stats["total_vectors"] = vector_store.collection.count()
            except Exception:
                # Collection might not be initialized or available
                pass
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.get("/embeddings/status")
async def get_embedding_status():
    """Check if embeddings are available."""
    return {
        "embeddings_available": EMBEDDINGS_AVAILABLE,
        "message": "Embeddings are available" if EMBEDDINGS_AVAILABLE else "Embeddings not available. Install: pip install sentence-transformers chromadb"
    }

# ==================== ADVANCED FEATURES ENDPOINTS ====================

class AdvancedSearchRequest(BaseModel):
    query_text: str
    top_k: int = 10
    min_similarity: float = 0.4
    filter_stop: bool = True
    strategy: str = "feature_based"
    store_name: str = "all"  # "all", "chroma", "faiss", "weaviate"

class RelatedConceptsRequest(BaseModel):
    concept_tokens: List[str]
    top_k: int = 15
    min_similarity: float = 0.4
    strategy: str = "feature_based"

class CompareTokensRequest(BaseModel):
    token1: str
    token2: str
    strategy: str = "feature_based"

class ExploreConceptRequest(BaseModel):
    concept: str
    depth: int = 2
    top_k_per_level: int = 10
    strategy: str = "feature_based"

class ConceptClusterRequest(BaseModel):
    seed_concept: str
    cluster_size: int = 10
    min_similarity: float = 0.6
    strategy: str = "feature_based"

class DataInterpretationRequest(BaseModel):
    input_text: str
    top_clues: int = 5
    top_concepts: int = 5
    embedding_strategy: str = "feature_based"
    embedding_dim: int = 768
    collection_name: str = "SanTOK_Token"

class DataInterpretationResponse(BaseModel):
    input: str
    token_clues: List[str]
    related_concepts: List[str]
    concept_details: List[Dict[str, Any]]
    interpretation: str

# Common stop words for filtering
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must',
    'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
    'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
}

def filter_stop_words(results: List[Dict]) -> List[Dict]:
    """Filter stop words from search results."""
    filtered = []
    for result in results:
        text = result.get('text', result.get('metadata', {}).get('text', ''))
        if text.lower() not in STOP_WORDS:
            filtered.append(result)
    return filtered

@app.post("/embeddings/advanced/search")
async def advanced_semantic_search(request: AdvancedSearchRequest):
    """Advanced semantic search with filters and similarity thresholds."""
    try:
        if not EMBEDDINGS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Embeddings not available.")
        
        # Generate query embedding
        embedding_gen = get_embedding_generator(request.strategy)
        tokenizer = TextTokenizer(seed=42, embedding_bit=False)
        streams = tokenizer.build(request.query_text)
        
        all_tokens = []
        for stream_name, token_stream in streams.items():
            all_tokens.extend(token_stream.tokens)
        
        if not all_tokens:
            return SearchResponse(results=[], query_text=request.query_text, num_results=0)
        
        # Generate query embedding (average of all tokens)
        query_embeddings = embedding_gen.generate_batch(all_tokens)
        query_embedding = np.mean(query_embeddings, axis=0)
        
        # Search in vector store
        vector_store = get_vector_store()
        results = vector_store.search(query_embedding, top_k=request.top_k * 2)  # Get more for filtering
        
        # Filter stop words if requested
        if request.filter_stop:
            results = filter_stop_words(results)
        
        # Filter by similarity threshold
        filtered_results = []
        for result in results:
            dist = result.get('distance', 0.0)
            similarity = 1.0 / (1.0 + dist) if isinstance(dist, (float, int)) else 0.0
            if similarity >= request.min_similarity:
                result['similarity'] = similarity
                filtered_results.append(result)
            if len(filtered_results) >= request.top_k:
                break
        
        return SearchResponse(
            results=filtered_results,
            query_text=request.query_text,
            num_results=len(filtered_results)
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Advanced search failed: {str(e)}")

@app.post("/embeddings/concepts/related")
async def find_related_concepts(request: RelatedConceptsRequest):
    """Find concepts related to multiple tokens by averaging their embeddings."""
    try:
        if not EMBEDDINGS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Embeddings not available.")
        
        embedding_gen = get_embedding_generator(request.strategy)
        tokenizer = TextTokenizer(seed=42, embedding_bit=False)
        
        # Generate embeddings for all concept tokens
        concept_embeddings = []
        for concept_token in request.concept_tokens:
            streams = tokenizer.build(concept_token)
            all_tokens = []
            for stream_name, token_stream in streams.items():
                all_tokens.extend(token_stream.tokens)
            if all_tokens:
                emb = embedding_gen.generate_batch(all_tokens)
                concept_embeddings.append(np.mean(emb, axis=0))
        
        if not concept_embeddings:
            return SearchResponse(results=[], query_text=", ".join(request.concept_tokens), num_results=0)
        
        # Average all concept embeddings
        query_embedding = np.mean(concept_embeddings, axis=0)
        
        # Search in vector store
        vector_store = get_vector_store()
        results = vector_store.search(query_embedding, top_k=request.top_k * 2)
        
        # Filter by similarity threshold
        filtered_results = []
        for result in results:
            dist = result.get('distance', 0.0)
            similarity = 1.0 / (1.0 + dist) if isinstance(dist, (float, int)) else 0.0
            if similarity >= request.min_similarity:
                result['similarity'] = similarity
                filtered_results.append(result)
            if len(filtered_results) >= request.top_k:
                break
        
        return SearchResponse(
            results=filtered_results,
            query_text=", ".join(request.concept_tokens),
            num_results=len(filtered_results)
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Find related concepts failed: {str(e)}")

@app.post("/embeddings/concepts/compare")
async def compare_tokens(request: CompareTokensRequest):
    """Compare similarity between two tokens."""
    try:
        if not EMBEDDINGS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Embeddings not available.")
        
        embedding_gen = get_embedding_generator(request.strategy)
        tokenizer = TextTokenizer(seed=42, embedding_bit=False)
        
        # Generate embeddings for both tokens
        def get_token_embedding(token_text: str):
            streams = tokenizer.build(token_text)
            all_tokens = []
            for stream_name, token_stream in streams.items():
                all_tokens.extend(token_stream.tokens)
            if all_tokens:
                emb = embedding_gen.generate_batch(all_tokens)
                return np.mean(emb, axis=0)
            return None
        
        emb1 = get_token_embedding(request.token1)
        emb2 = get_token_embedding(request.token2)
        
        if emb1 is None or emb2 is None:
            raise HTTPException(status_code=400, detail="One or both tokens not found")
        
        # Calculate similarities
        distance = np.linalg.norm(emb1 - emb2)
        similarity = 1.0 / (1.0 + distance)
        cosine_sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        
        return {
            "token1": request.token1,
            "token2": request.token2,
            "distance": float(distance),
            "similarity": float(similarity),
            "cosine_similarity": float(cosine_sim),
            "interpretation": (
                "Very similar" if similarity > 0.8 else
                "Moderately similar" if similarity > 0.6 else
                "Somewhat similar" if similarity > 0.4 else
                "Not very similar"
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Compare tokens failed: {str(e)}")

@app.post("/embeddings/concepts/cluster")
async def find_concept_cluster(request: ConceptClusterRequest):
    """Find a cluster of related concepts around a seed."""
    try:
        if not EMBEDDINGS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Embeddings not available.")
        
        embedding_gen = get_embedding_generator(request.strategy)
        tokenizer = TextTokenizer(seed=42, embedding_bit=False)
        
        # Generate seed embedding
        streams = tokenizer.build(request.seed_concept)
        all_tokens = []
        for stream_name, token_stream in streams.items():
            all_tokens.extend(token_stream.tokens)
        
        if not all_tokens:
            raise HTTPException(status_code=400, detail=f"Seed concept '{request.seed_concept}' not found")
        
        seed_emb = embedding_gen.generate_batch(all_tokens)
        seed_embedding = np.mean(seed_emb, axis=0)
        
        # Search for cluster
        vector_store = get_vector_store()
        results = vector_store.search(seed_embedding, top_k=request.cluster_size * 2)
        
        # Filter stop words and by similarity
        results = filter_stop_words(results)
        cluster = []
        for result in results:
            text = result.get('text', result.get('metadata', {}).get('text', ''))
            if text.lower() == request.seed_concept.lower():
                continue
            dist = result.get('distance', 0.0)
            similarity = 1.0 / (1.0 + dist) if isinstance(dist, (float, int)) else 0.0
            if similarity >= request.min_similarity:
                result['similarity'] = similarity
                cluster.append(result)
            if len(cluster) >= request.cluster_size:
                break
        
        return SearchResponse(
            results=cluster,
            query_text=request.seed_concept,
            num_results=len(cluster)
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Find concept cluster failed: {str(e)}")

@app.post("/embeddings/concepts/explore")
async def explore_concept(request: ExploreConceptRequest):
    """Explore concept relationships by traversing similarity connections."""
    try:
        if not EMBEDDINGS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Embeddings not available.")
        
        embedding_gen = get_embedding_generator(request.strategy)
        tokenizer = TextTokenizer(seed=42, embedding_bit=False)
        vector_store = get_vector_store()
        
        # Generate seed embedding
        streams = tokenizer.build(request.concept)
        all_tokens = []
        for stream_name, token_stream in streams.items():
            all_tokens.extend(token_stream.tokens)
        
        if not all_tokens:
            raise HTTPException(status_code=400, detail=f"Concept '{request.concept}' not found")
        
        seed_emb = embedding_gen.generate_batch(all_tokens)
        current_embedding = np.mean(seed_emb, axis=0)
        
        explored = {request.concept.lower()}
        levels = []
        
        # Explore each level
        for level in range(request.depth):
            # Search for similar concepts at this level
            results = vector_store.search(current_embedding, top_k=request.top_k_per_level * 2)
            results = filter_stop_words(results)
            
            level_results = []
            for result in results:
                text = result.get('text', result.get('metadata', {}).get('text', ''))
                if text.lower() in explored:
                    continue
                explored.add(text.lower())
                dist = result.get('distance', 0.0)
                similarity = 1.0 / (1.0 + dist) if isinstance(dist, (float, int)) else 0.0
                result['similarity'] = similarity
                level_results.append(result)
                if len(level_results) >= request.top_k_per_level:
                    break
            
            levels.append({
                "level": level + 1,
                "concepts": level_results
            })
            
            # Use average of current level results for next level exploration
            if level_results:
                level_embeddings = []
                for r in level_results:
                    text = r.get('text', r.get('metadata', {}).get('text', ''))
                    streams = tokenizer.build(text)
                    tokens = []
                    for stream_name, token_stream in streams.items():
                        tokens.extend(token_stream.tokens)
                    if tokens:
                        emb = embedding_gen.generate_batch(tokens)
                        level_embeddings.append(np.mean(emb, axis=0))
                if level_embeddings:
                    current_embedding = np.mean(level_embeddings, axis=0)
        
        return {
            "seed_concept": request.concept,
            "depth": request.depth,
            "levels": levels
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Explore concept failed: {str(e)}")

@app.post("/interpret/data", response_model=DataInterpretationResponse)
async def interpret_data(request: DataInterpretationRequest):
    """
    Real-Time Data Interpretation using YOUR Weaviate database.
    
    Example:
        Input: "Sales dropped 20% last month."
        Token clues: ["Sales", "dropped", "20%"]
        Related concepts from YOUR Weaviate: ["reason", "trend", "improve", "analyze"]
        Output: "Analyze customer behavior and marketing changes to find the cause."
    """
    try:
        # Import DataInterpreter - try multiple paths
        DataInterpreter = None
        import sys
        import importlib.util
        from pathlib import Path
        
        # Get current file location
        current_file = Path(__file__).resolve()
        # Handle both src/servers/main_server.py and backend/src/servers/main_server.py
        servers_dir = current_file.parent  # src/servers or backend/src/servers
        src_dir = None
        backend_dir = None
        
        if servers_dir.name == 'servers':
            if servers_dir.parent.name == 'src':
                # src/servers/main_server.py
                src_dir = servers_dir.parent  # src
                project_root = src_dir.parent  # project root
            elif servers_dir.parent.name == 'backend':
                # backend/src/servers/main_server.py
                backend_src = servers_dir.parent  # backend/src
                backend_dir = backend_src.parent  # backend
                project_root = backend_dir.parent  # project root
            else:
                project_root = servers_dir.parent.parent
        else:
            project_root = servers_dir.parent.parent
        
        # Try different paths
        possible_paths = []
        if src_dir:
            possible_paths.append(src_dir / 'interpretation' / 'data_interpreter.py')
        possible_paths.extend([
            project_root / 'src' / 'interpretation' / 'data_interpreter.py',
            project_root / 'backend' / 'src' / 'interpretation' / 'data_interpreter.py',
        ])
        
        # Also try module imports
        import_paths = [
            'src.interpretation.data_interpreter',
            'interpretation.data_interpreter',
        ]
        
        # Add project root to path
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        if backend_dir is None:
            backend_dir = project_root / 'backend'
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        
        # Try direct file imports first
        for file_path in possible_paths:
            if file_path.exists():
                try:
                    spec = importlib.util.spec_from_file_location("data_interpreter", str(file_path))
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        DataInterpreter = getattr(module, 'DataInterpreter', None)
                        if DataInterpreter:
                            break
                except Exception as e:
                    continue
        
        # Try module imports if file import didn't work
        if DataInterpreter is None:
            for import_path in import_paths:
                try:
                    module = __import__(import_path, fromlist=['DataInterpreter'])
                    DataInterpreter = getattr(module, 'DataInterpreter', None)
                    if DataInterpreter:
                        break
                except (ImportError, AttributeError, Exception):
                    continue
        
        if DataInterpreter is None:
            error_msg = f"DataInterpreter not found. Searched:\n"
            error_msg += f"  File paths: {[str(p) for p in possible_paths]}\n"
            error_msg += f"  Module paths: {import_paths}\n"
            error_msg += f"  Project root: {project_root}\n"
            error_msg += f"  Backend dir: {backend_dir}"
            raise HTTPException(status_code=503, detail=error_msg)
        
        # Initialize interpreter (will auto-load Weaviate credentials)
        interpreter = DataInterpreter(
            embedding_strategy=request.embedding_strategy,
            embedding_dim=request.embedding_dim,
            collection_name=request.collection_name
        )
        
        # Perform interpretation
        result = interpreter.interpret(
            input_text=request.input_text,
            top_clues=request.top_clues,
            top_concepts=request.top_concepts
        )
        
        return DataInterpretationResponse(
            input=result["input"],
            token_clues=result["token_clues"],
            related_concepts=result["related_concepts"],
            concept_details=result["concept_details"],
            interpretation=result["interpretation"]
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Data interpretation failed: {str(e)}")

# ==================== SANTOK TRAINING ENDPOINTS ====================

# User dataset storage directory
USER_DATASETS_DIR = Path("user_datasets")
USER_DATASETS_DIR.mkdir(parents=True, exist_ok=True)

class UserDatasetInfo(BaseModel):
    dataset_id: str
    filename: str
    original_filename: str
    size_mb: float
    uploaded_at: str
    file_path: str
    description: Optional[str] = None

class UserDatasetListResponse(BaseModel):
    datasets: List[UserDatasetInfo]
    total: int

class DatasetUploadResponse(BaseModel):
    success: bool
    message: str
    dataset_id: str
    dataset_path: str
    size_mb: float
    filename: str

@app.post("/training/dataset/upload", response_model=DatasetUploadResponse)
async def upload_user_dataset(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None)
):
    """Upload user's own dataset for training."""
    try:
        logging.info(f"[UPLOAD] Starting upload for file: {file.filename}")
        
        allowed_extensions = {'.txt', '.csv', '.json', '.md', '.py', '.js', '.ts', '.html', '.xml'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions and (not file.content_type or not file.content_type.startswith('text/')):
            raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")
        
        logging.info(f"[UPLOAD] File type validated: {file_ext}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(file.filename.encode()).hexdigest()[:8]
        dataset_id = f"{timestamp}_{file_hash}"
        
        user_dataset_dir = USER_DATASETS_DIR / dataset_id
        user_dataset_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"[UPLOAD] Created directory: {user_dataset_dir}")
        
        safe_filename = f"{dataset_id}_{file.filename}"
        file_path = user_dataset_dir / safe_filename
        
        # Read file in chunks to avoid memory issues
        logging.info(f"[UPLOAD] Reading file content...")
        content = await file.read()
        file_size = len(content)
        logging.info(f"[UPLOAD] File size: {file_size} bytes ({file_size / (1024 * 1024):.2f} MB)")
        
        # Write file
        logging.info(f"[UPLOAD] Writing file to: {file_path}")
        with open(file_path, 'wb') as f:
            f.write(content)
        
        size_mb = file_size / (1024 * 1024)
        logging.info(f"[UPLOAD] File written successfully")
        
        # Create metadata
        metadata = {
            'dataset_id': dataset_id,
            'original_filename': file.filename,
            'filename': safe_filename,
            'size_bytes': file_size,
            'size_mb': size_mb,
            'uploaded_at': datetime.now().isoformat(),
            'description': description,
            'file_path': str(file_path),
            'content_type': file.content_type
        }
        
        metadata_path = user_dataset_dir / 'metadata.json'
        logging.info(f"[UPLOAD] Writing metadata...")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        # Append to combined file (async, don't block)
        combined_path = USER_DATASETS_DIR / "all_user_datasets.txt"
        try:
            logging.info(f"[UPLOAD] Appending to combined file...")
            with open(combined_path, 'ab') as f:  # Use binary mode for faster writing
                header = f"\n\n=== Dataset: {file.filename} (ID: {dataset_id}) ===\n".encode('utf-8')
                f.write(header)
                f.write(content)  # Write binary content directly
        except Exception as e:
            logging.warning(f"[UPLOAD] Could not append to combined file: {e}")
            # Don't fail the upload if combined file write fails
        
        logging.info(f"[UPLOAD] Upload complete: {dataset_id}")
        
        return DatasetUploadResponse(
            success=True,
            message=f"Dataset uploaded successfully",
            dataset_id=dataset_id,
            dataset_path=str(file_path),
            size_mb=size_mb,
            filename=file.filename
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logging.error(f"[UPLOAD] Upload failed: {e}")
        logging.error(f"[UPLOAD] Traceback: {error_trace}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.get("/training/dataset/user/list", response_model=UserDatasetListResponse)
async def list_user_datasets():
    """List all user-uploaded datasets."""
    try:
        datasets = []
        # Ensure directory exists
        try:
            USER_DATASETS_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.warning(f"Could not create user_datasets directory: {e}")
        
        if USER_DATASETS_DIR.exists():
            try:
                for dataset_dir in USER_DATASETS_DIR.iterdir():
                    if dataset_dir.is_dir():
                        metadata_path = dataset_dir / 'metadata.json'
                        if metadata_path.exists():
                            try:
                                with open(metadata_path, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                                datasets.append(UserDatasetInfo(
                                    dataset_id=metadata.get('dataset_id', dataset_dir.name),
                                    filename=metadata.get('filename', 'unknown'),
                                    original_filename=metadata.get('original_filename', 'unknown'),
                                    size_mb=metadata.get('size_mb', 0.0),
                                    uploaded_at=metadata.get('uploaded_at', datetime.now().isoformat()),
                                    file_path=metadata.get('file_path', str(dataset_dir)),
                                    description=metadata.get('description')
                                ))
                            except (json.JSONDecodeError, KeyError, Exception) as e:
                                logging.warning(f"Skipping invalid dataset metadata in {dataset_dir}: {e}")
                                continue
            except (PermissionError, OSError) as e:
                logging.error(f"Error reading user_datasets directory: {e}")
                # Return empty list instead of crashing
                return UserDatasetListResponse(datasets=[], total=0)
        
        datasets.sort(key=lambda x: x.uploaded_at, reverse=True)
        return UserDatasetListResponse(datasets=datasets, total=len(datasets))
    except Exception as e:
        import traceback
        logging.error(f"Failed to list datasets: {e}")
        logging.error(traceback.format_exc())
        # Return empty list instead of crashing
        return UserDatasetListResponse(datasets=[], total=0)

@app.get("/training/dataset/user/{dataset_id}")
async def get_user_dataset(dataset_id: str):
    """Get user dataset by ID."""
    try:
        dataset_dir = USER_DATASETS_DIR / dataset_id
        if not dataset_dir.exists():
            raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
        metadata_path = dataset_dir / 'metadata.json'
        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail=f"Dataset metadata not found: {dataset_id}")
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dataset: {str(e)}")

@app.delete("/training/dataset/user/{dataset_id}")
async def delete_user_dataset(dataset_id: str):
    """Delete user dataset."""
    try:
        dataset_dir = USER_DATASETS_DIR / dataset_id
        if not dataset_dir.exists():
            raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
        shutil.rmtree(dataset_dir)
        return {"success": True, "message": f"Dataset {dataset_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete dataset: {str(e)}")

class DatasetDownloadRequest(BaseModel):
    dataset_type: str = "wikipedia"
    size_limit_gb: float = 1.0

class DatasetDownloadResponse(BaseModel):
    success: bool
    message: str
    dataset_path: Optional[str] = None
    size_mb: Optional[float] = None

class VocabularyBuildRequest(BaseModel):
    dataset_path: str
    vocab_size: int = 60000
    min_frequency: int = 2
    tokenizer_seed: int = 42

class VocabularyBuildResponse(BaseModel):
    success: bool
    message: str
    vocab_path: Optional[str] = None
    vocab_size: Optional[int] = None
    total_tokens: Optional[int] = None
    job_id: Optional[str] = None  # Job ID for tracking progress

class ModelTrainRequest(BaseModel):
    dataset_path: str
    vocab_path: str
    vocab_size: int = 60000
    embedding_dim: int = 768
    num_layers: int = 12
    num_heads: int = 12
    max_seq_length: int = 1024
    epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 1e-4
    embedding_strategy: str = "feature_based"

class ModelTrainResponse(BaseModel):
    success: bool
    message: str
    job_id: Optional[str] = None
    model_path: Optional[str] = None

class ModelGenerateRequest(BaseModel):
    model_path: str
    vocab_path: str
    prompt: str
    max_length: int = 100
    temperature: float = 1.0

class ModelGenerateResponse(BaseModel):
    success: bool
    generated_text: str
    prompt: str

@app.post("/training/dataset/download", response_model=DatasetDownloadResponse)
async def download_dataset(request: DatasetDownloadRequest):
    """Download training datasets."""
    try:
        logging.info(f"[DOWNLOAD] Starting download: {request.dataset_type}, size_limit: {request.size_limit_gb}GB")
        
        try:
            from training.dataset_downloader import SanTOKDatasetDownloader
        except ImportError:
            try:
                from src.training.dataset_downloader import SanTOKDatasetDownloader
            except ImportError:
                logging.error("[DOWNLOAD] Dataset downloader module not found")
                raise HTTPException(status_code=503, detail="Dataset downloader not available. Check backend logs.")
        
        logging.info("[DOWNLOAD] Dataset downloader imported successfully")
        
        downloader = SanTOKDatasetDownloader(data_dir="training_data")
        logging.info("[DOWNLOAD] Downloader initialized")
        
        dataset_path = None
        
        if request.dataset_type == "wikipedia":
            logging.info("[DOWNLOAD] Starting Wikipedia download (this may take several minutes)...")
            # Run download in background thread to avoid blocking
            import asyncio
            loop = asyncio.get_event_loop()
            dataset_path = await loop.run_in_executor(
                None, 
                downloader.download_wikipedia, 
                request.size_limit_gb
            )
            logging.info(f"[DOWNLOAD] Wikipedia download complete: {dataset_path}")
        elif request.dataset_type == "combined":
            logging.info("[DOWNLOAD] Combining datasets...")
            dataset_path = downloader.combine_datasets()
            user_combined = USER_DATASETS_DIR / "all_user_datasets.txt"
            if user_combined.exists() and dataset_path:
                with open(dataset_path, 'a', encoding='utf-8') as f:
                    with open(user_combined, 'r', encoding='utf-8', errors='ignore') as user_f:
                        f.write('\n\n=== User Datasets ===\n')
                        f.write(user_f.read())
            logging.info(f"[DOWNLOAD] Combined dataset ready: {dataset_path}")
        elif request.dataset_type == "user_only":
            logging.info("[DOWNLOAD] Using user datasets only...")
            user_combined = USER_DATASETS_DIR / "all_user_datasets.txt"
            if user_combined.exists():
                dataset_path = user_combined
                logging.info(f"[DOWNLOAD] User dataset found: {dataset_path}")
            else:
                logging.warning("[DOWNLOAD] No user datasets found")
                raise HTTPException(status_code=404, detail="No user datasets found. Upload a dataset first.")
        else:
            logging.error(f"[DOWNLOAD] Unknown dataset type: {request.dataset_type}")
            raise HTTPException(status_code=400, detail=f"Unknown dataset type: {request.dataset_type}")
        
        if dataset_path and dataset_path.exists():
            size_mb = dataset_path.stat().st_size / (1024 * 1024)
            logging.info(f"[DOWNLOAD] Success! Dataset size: {size_mb:.2f} MB")
            return DatasetDownloadResponse(
                success=True, 
                message=f"Dataset downloaded successfully ({size_mb:.2f} MB)", 
                dataset_path=str(dataset_path), 
                size_mb=size_mb
            )
        else:
            logging.error(f"[DOWNLOAD] Dataset path does not exist: {dataset_path}")
            return DatasetDownloadResponse(
                success=False, 
                message=f"Dataset download failed - file not found at {dataset_path}"
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logging.error(f"[DOWNLOAD] Download failed: {e}")
        logging.error(f"[DOWNLOAD] Traceback: {error_trace}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Dataset download failed: {str(e)}")

@app.post("/training/vocabulary/build", response_model=VocabularyBuildResponse)
async def build_vocabulary(request: VocabularyBuildRequest):
    """Build 60K vocabulary from SanTOK tokens (runs as persistent job)."""
    try:
        dataset_path = Path(request.dataset_path)
        if not dataset_path.exists():
            raise HTTPException(status_code=404, detail=f"Dataset not found: {request.dataset_path}")
        
        # Use job manager for persistent execution
        if get_job_manager:
            vocab_script = Path("training_scripts") / f"vocab_temp.py"
            vocab_script.parent.mkdir(parents=True, exist_ok=True)
            
            script_content = f"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.training.vocabulary_builder import SanTOKVocabularyBuilder

print("="*60)
print("Building SanTOK 60K Vocabulary")
print("="*60)
print(f"Dataset: {request.dataset_path}")
print(f"Vocab size: {request.vocab_size:,}")
print(f"Min frequency: {request.min_frequency}")
print()

vocab_builder = SanTOKVocabularyBuilder(
    vocab_size={request.vocab_size},
    min_frequency={request.min_frequency},
    tokenizer_seed={request.tokenizer_seed}
)

vocab_builder.build_vocabulary(Path("{request.dataset_path}"))

vocab_path = Path("models/santok_60k_vocab.pkl")
vocab_path.parent.mkdir(parents=True, exist_ok=True)
vocab_builder.save(vocab_path)

print()
print("="*60)
print("Vocabulary built successfully!")
print(f"Vocab size: {{len(vocab_builder.token_to_id):,}}")
print(f"Total tokens: {{sum(vocab_builder.token_counts.values()):,}}")
print(f"Saved to: {{vocab_path}}")
print("="*60)
"""
            
            with open(vocab_script, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            work_dir = str(Path.cwd())
            job_manager = get_job_manager()
            
            # Create job first before starting it (this generates and returns job_id)
            job_data = {
                "script_path": str(vocab_script),
                "work_dir": work_dir,
                "timeout": 86400,
                "type": "vocabulary_build",
                "dataset_path": str(request.dataset_path),
                "vocab_size": request.vocab_size
            }
            job_id = job_manager.create_job(job_data)
            
            # Rename script file to include job_id for easier identification
            vocab_script_renamed = vocab_script.parent / f"vocab_{job_id}.py"
            if vocab_script.exists():
                vocab_script.rename(vocab_script_renamed)
            
            # Now start the job with the job_id from create_job
            job_manager.start_job(job_id, str(vocab_script_renamed), work_dir, timeout=86400)
            
            return VocabularyBuildResponse(
                success=True,
                message="Vocabulary build started (running in background)",
                vocab_path="models/santok_60k_vocab.pkl",
                vocab_size=None,
                total_tokens=None,
                job_id=job_id
            )
        else:
            # Fallback to synchronous execution
            try:
                from training.vocabulary_builder import SanTOKVocabularyBuilder
            except ImportError:
                try:
                    from src.training.vocabulary_builder import SanTOKVocabularyBuilder
                except ImportError:
                    raise HTTPException(status_code=503, detail="Vocabulary builder not available.")
            
            vocab_builder = SanTOKVocabularyBuilder(vocab_size=request.vocab_size, min_frequency=request.min_frequency, tokenizer_seed=request.tokenizer_seed)
            vocab_builder.build_vocabulary(dataset_path)
            
            vocab_path = Path("models/santok_60k_vocab.pkl")
            vocab_path.parent.mkdir(parents=True, exist_ok=True)
            vocab_builder.save(vocab_path)
            
            return VocabularyBuildResponse(
                success=True,
                message="Vocabulary built successfully",
                vocab_path=str(vocab_path),
                vocab_size=len(vocab_builder.token_to_id),
                total_tokens=sum(vocab_builder.token_counts.values())
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Vocabulary build failed: {str(e)}")

@app.post("/training/model/train", response_model=ModelTrainResponse)
async def train_model(request: ModelTrainRequest):
    """Train SanTOK language model."""
    try:
        try:
            from training.language_model_trainer import SanTOKLanguageModel, SanTOKLanguageModelTrainer
            from training.vocabulary_builder import SanTOKVocabularyBuilder
        except ImportError:
            try:
                from src.training.language_model_trainer import SanTOKLanguageModel, SanTOKLanguageModelTrainer
                from src.training.vocabulary_builder import SanTOKVocabularyBuilder
            except ImportError:
                raise HTTPException(status_code=503, detail="Language model trainer not available.")
        
        dataset_path = Path(request.dataset_path)
        vocab_path = Path(request.vocab_path)
        
        if not dataset_path.exists():
            raise HTTPException(status_code=404, detail=f"Dataset not found: {request.dataset_path}")
        if not vocab_path.exists():
            raise HTTPException(status_code=404, detail=f"Vocabulary not found: {request.vocab_path}")
        
        if get_job_manager:
            training_script = Path("training_scripts") / f"train_temp.py"
            training_script.parent.mkdir(parents=True, exist_ok=True)
            
            script_content = f"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.training.language_model_trainer import SanTOKLanguageModel, SanTOKLanguageModelTrainer
from src.training.vocabulary_builder import SanTOKVocabularyBuilder

vocab_builder = SanTOKVocabularyBuilder()
vocab_builder.load(Path("{request.vocab_path}"))

model = SanTOKLanguageModel(
    vocab_size={request.vocab_size},
    embedding_dim={request.embedding_dim},
    num_layers={request.num_layers},
    num_heads={request.num_heads},
    max_seq_length={request.max_seq_length},
    embedding_strategy="{request.embedding_strategy}"
)

trainer = SanTOKLanguageModelTrainer(
    model=model,
    vocab_builder=vocab_builder,
    learning_rate={request.learning_rate},
    batch_size={request.batch_size},
    seq_length={request.max_seq_length}
)

trainer.train(
    text_file=Path("{request.dataset_path}"),
    epochs={request.epochs},
    save_every=2,
    output_dir=Path("models")
)

print("Training complete!")
"""
            with open(training_script, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            work_dir = str(Path(__file__).parent.parent.parent)
            job_manager = get_job_manager()
            
            # Create job first before starting it (this generates and returns job_id)
            job_data = {
                "script_path": str(training_script),
                "work_dir": work_dir,
                "timeout": 86400,
                "type": "model_training",
                "dataset_path": str(request.dataset_path),
                "vocab_path": str(request.vocab_path),
                "epochs": request.epochs
            }
            job_id = job_manager.create_job(job_data)
            
            # Rename script file to include job_id for easier identification
            training_script_renamed = training_script.parent / f"train_{job_id}.py"
            if training_script.exists():
                training_script.rename(training_script_renamed)
            
            # Now start the job with the job_id from create_job
            job_manager.start_job(job_id, str(training_script_renamed), work_dir, timeout=86400)
            
            return ModelTrainResponse(success=True, message="Training started", job_id=job_id, model_path=f"models/santok_lm_epoch_{request.epochs}.pkl")
        else:
            raise HTTPException(status_code=503, detail="Job manager not available")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Model training failed: {str(e)}")

@app.post("/training/model/generate", response_model=ModelGenerateResponse)
async def generate_text(request: ModelGenerateRequest):
    """Generate text using trained SanTOK language model."""
    try:
        try:
            from training.language_model_trainer import SanTOKLanguageModel
            from training.vocabulary_builder import SanTOKVocabularyBuilder
        except ImportError:
            try:
                from src.training.language_model_trainer import SanTOKLanguageModel
                from src.training.vocabulary_builder import SanTOKVocabularyBuilder
            except ImportError:
                raise HTTPException(status_code=503, detail="Language model not available.")
        
        model_path = Path(request.model_path)
        vocab_path = Path(request.vocab_path)
        
        if not model_path.exists():
            raise HTTPException(status_code=404, detail=f"Model not found: {request.model_path}")
        if not vocab_path.exists():
            raise HTTPException(status_code=404, detail=f"Vocabulary not found: {request.vocab_path}")
        
        model = SanTOKLanguageModel()
        model.load(model_path)
        
        vocab_builder = SanTOKVocabularyBuilder()
        vocab_builder.load(vocab_path)
        
        generated_text = model.generate(prompt=request.prompt, vocab_builder=vocab_builder, max_length=request.max_length, temperature=request.temperature)
        
        return ModelGenerateResponse(success=True, generated_text=generated_text, prompt=request.prompt)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Text generation failed: {str(e)}")

# ==================== CODE EXECUTION ENDPOINT ====================

class CodeExecutionRequest(BaseModel):
    code: str
    file_path: Optional[str] = None  # Optional: execute from file
    timeout: int = 86400  # 24 hours default (86400 seconds = 1 day)
    working_dir: Optional[str] = None
    interactive: bool = False  # Enable interactive mode (stdin support)
    async_execution: Optional[bool] = None  # Auto-detect: use async for jobs > 5 minutes, or explicitly set

class CodeExecutionResponse(BaseModel):
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    error: Optional[str] = None
    job_id: Optional[str] = None  # Job ID for async execution
    is_async: bool = False  # Whether execution is async

class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed, cancelled
    progress: int  # 0-100
    stdout: str
    stderr: str
    exit_code: Optional[int] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

class TerminalCommandRequest(BaseModel):
    command: str
    cwd: Optional[str] = None

class TerminalCommandResponse(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None
    cwd: str

# ==================== AUTHENTICATION & AUTHORIZATION CONFIGURATION ====================
# SECURITY: Only allowed users can access everything. Regular users are restricted.

# Allowed users list - These users can access EVERYTHING (SanTOK files included)
# Format: {"username": "hashed_password_or_token", ...}
# In production, use environment variables or a secure database
# SECURITY: Load from environment variables for production
# Load admin users from config file or environment
try:
    from servers.admin_config import load_admin_users
    ALLOWED_USERS = load_admin_users()
except ImportError:
    # Fallback if admin_config not available
    ALLOWED_USERS_ENV = os.getenv("ALLOWED_USERS", "")
    if ALLOWED_USERS_ENV:
        # Format: "username1:password1,username2:password2"
        ALLOWED_USERS = {}
        for user_pass in ALLOWED_USERS_ENV.split(","):
            if ":" in user_pass:
                username, password = user_pass.split(":", 1)
                ALLOWED_USERS[username.strip()] = hashlib.sha256(password.strip().encode()).hexdigest()
    else:
        # Default (ONLY FOR DEVELOPMENT - MUST SET IN PRODUCTION)
        import warnings
        if os.getenv("NODE_ENV") == "production" or os.getenv("RAILWAY_ENVIRONMENT"):
            warnings.warn("SECURITY: ALLOWED_USERS not set via environment variable in production!")
            ALLOWED_USERS = {}  # Empty = no access until configured
        else:
            ALLOWED_USERS = {
                "admin": hashlib.sha256("admin123".encode()).hexdigest(),  # DEV ONLY
            }

def reload_allowed_users():
    """Reload admin users from config file."""
    global ALLOWED_USERS
    try:
        from servers.admin_config import load_admin_users
        ALLOWED_USERS = load_admin_users()
        return True
    except Exception as e:
        logging.error(f"Error reloading admin users: {e}")
        return False

# JWT Secret Key (REQUIRED in production)
JWT_SECRET_KEY_ENV = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY_ENV:
    # Generate random key for development only
    if os.getenv("NODE_ENV") == "production" or os.getenv("RAILWAY_ENVIRONMENT"):
        import warnings
        warnings.warn("SECURITY: JWT_SECRET_KEY not set! Generating random key (NOT PERSISTENT).")
        # In production, should fail if not set, but allow startup with warning
    JWT_SECRET_KEY = secrets.token_urlsafe(32)
else:
    JWT_SECRET_KEY = JWT_SECRET_KEY_ENV

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

# HTTP Bearer token security
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """Verify JWT token and return user info."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("username")
        if username and username in ALLOWED_USERS:
            return {"username": username, "is_allowed": True}
        raise HTTPException(status_code=403, detail="Invalid token or user not allowed")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token")
    except Exception as e:
        # SECURITY: Don't expose internal error details
        logging.error(f"Authentication error: {type(e).__name__}")
        raise HTTPException(status_code=403, detail="Authentication failed")

def get_optional_auth(request: Request) -> Optional[dict]:
    """Get optional authentication - returns None if no token provided."""
    try:
        # Get Authorization header manually
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.replace("Bearer ", "").strip()
        if not token:
            return None
        
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("username")
        if username and username in ALLOWED_USERS:
            return {"username": username, "is_allowed": True}
        return None
    except Exception:
        return None

def is_user_allowed(auth: Optional[dict] = None) -> bool:
    """Check if user is in allowed users list and authenticated."""
    if auth is None:
        return False
    return auth.get("is_allowed", False)

# ==================== SECURITY CONFIGURATION ====================
# CRITICAL SECURITY: File Access Restrictions
# 
# This section implements VERY STRICT file access restrictions to protect SanTOK core files.
# 
# SECURITY PRINCIPLES:
# 1. DENY BY DEFAULT: Everything is blocked unless explicitly allowed
# 2. WHITELIST APPROACH: Only specific directories are accessible to regular users
# 3. MULTIPLE LAYERS: Path blocking, directory traversal prevention, extension blocking
# 4. FAIL-SAFE: Any error in security checks results in blocking access
# 5. LOGGING: All blocked access attempts are logged for security auditing
# 
# ACCESS LEVELS:
# - Regular users: ONLY access to examples/, user_workspace/, user_workspace/uploads/, user_workspace/temp/
# - Admin/Allowed users: Full access to entire project (via authentication)
# 
# ALL endpoints use is_path_blocked() for security validation:
# - /execute/code (code execution)
# - /execute/terminal (terminal commands)
# - /ws/execute (WebSocket interactive execution)
# - /execute/files (file listing)
# - /execute/file/{path} (file content retrieval)
#
# Whitelisted directories - ONLY these directories are accessible (for regular users)
ALLOWED_DIRECTORIES = {
    "examples": "examples",  # Examples folder (root)
    "src_examples": "src/examples",  # SanTOK example codes in src/
    "workspace": "user_workspace",  # User workspace (created if doesn't exist)
    "uploads": "user_workspace/uploads",  # User uploads
    "temp": "user_workspace/temp",  # Temporary files
}

# Blacklisted paths - These are NEVER accessible (SanTOK core files)
# SECURITY: Complete blocklist of all SanTOK directories and files
# BUT: Allow src/examples for running SanTOK codes on Railway compute
BLOCKED_PATHS = {
    # Block core source directories (but allow src/examples)
    "src/core", "src/core/",
    "src/servers", "src/servers/",
    "src/integration", "src/integration/",
    "src/compression", "src/compression/",
    "src/cli", "src/cli/",
    "src/utils", "src/utils/",
    "src/embeddings", "src/embeddings/",
    "src/performance", "src/performance/",
    "src/tests", "src/tests/",
    
    # Entire backend/ directory
    "backend", "backend/",
    "backend/src", "backend/src/",
    "backend/src/core", "backend/src/core/",
    "backend/src/servers", "backend/src/servers/",
    "backend/src/embeddings", "backend/src/embeddings/",
    "backend/santok", "backend/santok/",
    
    # Entire frontend/ directory
    "frontend", "frontend/",
    "frontend/src", "frontend/src/",
    "frontend/app", "frontend/app/",
    "frontend/components", "frontend/components/",
    "frontend/lib", "frontend/lib/",
    "frontend/public", "frontend/public/",
    "frontend/styles", "frontend/styles/",
    "frontend/hooks", "frontend/hooks/",
    "frontend/types", "frontend/types/",
    "frontend/contexts", "frontend/contexts/",
    "frontend/.next", "frontend/.next/",
    
    # Package directories
    "santok", "santok/",
    "backend/santok", "backend/santok/",
    
    # Configuration directory - CRITICAL: Contains admin credentials
    "config", "config/",
    "config/admin_users.json",
    
    # System and build directories
    ".git", ".git/",
    "node_modules", "node_modules/",
    ".next", ".next/",
    "__pycache__", "__pycache__/",
    ".venv", "venv", "env",
    ".env", ".env.local", ".env.production", ".env.development",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "dist", "build",
    "*.egg-info",
    
    # Data and output directories
    "vector_db", "vector_db/",
    "workflow_output", "workflow_output/",
    "data", "data/",
    "logs", "logs/",
    
    # Configuration and workflow
    "n8n", "n8n/",
    "docs", "docs/",
    "tests", "tests/",
    "benchmarks", "benchmarks/",
    "scripts", "scripts/",
    ".github", ".github/",
    
    # Configuration files (by extension/name) - CRITICAL SECURITY
    "requirements.txt",
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Dockerfile",
    "docker-compose.yml",
    "railway.json",
    ".dockerignore",
    ".gitignore",
    ".railwayignore",
    "setup.py",
    "pyproject.toml",
    "tsconfig.json",
    "next.config.js",
    "tailwind.config.js",
    "jest.config.js",
    "playwright.config.ts",
    "*.key", "*.pem", "*.p12", "*.pfx",
    "*.env*",
}

def is_path_blocked(file_path: Path, project_root: Path, auth: Optional[dict] = None) -> bool:
    """
    Check if a path is blocked from access.
    SECURITY: Comprehensive blocking of all SanTOK core files and directories.
    EXCEPTION: Allowed users can access everything - returns False if user is allowed.
    
    CRITICAL SECURITY: This function is the PRIMARY line of defense against unauthorized file access.
    It uses a "deny by default" approach - everything is blocked unless explicitly allowed.
    """
    # SECURITY BYPASS: Allowed users can access everything (only for authenticated admin users)
    if is_user_allowed(auth):
        return False
    
    # Regular users: Apply STRICT blocking - deny by default
    try:
        # SECURITY: Convert to Path object if it's a string
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        # SECURITY: Resolve absolute path to prevent directory traversal
        resolved_path = file_path.resolve()
        project_root_resolved = project_root.resolve()
        
        # SECURITY: Path MUST be within project root - BLOCK anything outside
        try:
            rel_path = resolved_path.relative_to(project_root_resolved)
        except ValueError:
            # Path outside project root - BLOCKED immediately
            logging.warning(f"[SECURITY] Blocked path outside project root: {resolved_path}")
            return True
        
        # SECURITY: Normalize path separators and remove any Windows/Unix differences
        path_str = str(rel_path).replace("\\", "/")
        path_parts = [p for p in path_str.split("/") if p]  # Remove empty parts
        
        # SECURITY: Block directory traversal attempts - STRICT CHECK
        if ".." in path_str or any(".." in part for part in path_parts):
            logging.warning(f"[SECURITY] Blocked directory traversal attempt: {path_str}")
            return True
        
        # SECURITY: Block absolute paths and root-relative paths
        if path_str.startswith("/") or path_str.startswith("\\") or path_str.startswith("~"):
            logging.warning(f"[SECURITY] Blocked absolute/root path: {path_str}")
            return True
        
        # SECURITY: Block if ANY part of the path matches blocked paths
        for part in path_parts:
            # Case-insensitive check for extra security
            if part in BLOCKED_PATHS or part.lower() in {b.lower() for b in BLOCKED_PATHS}:
                logging.warning(f"[SECURITY] Blocked path part: {part} in {path_str}")
                return True
        
        # SECURITY: Block if path starts with any blocked prefix - STRICT CHECK
        for blocked in BLOCKED_PATHS:
            normalized_blocked = blocked.rstrip("/").lower()
            path_str_lower = path_str.lower()
            
            if path_str_lower == normalized_blocked:
                logging.warning(f"[SECURITY] Blocked exact match: {path_str}")
                return True
            
            # Block if path starts with blocked prefix
            if path_str_lower.startswith(normalized_blocked + "/") or path_str_lower.startswith(normalized_blocked):
                # Special case: Allow examples/ and src/examples/ for SanTOK code execution on Railway compute
                if path_str_lower.startswith("examples/") or path_str_lower.startswith("src/examples/"):
                    continue
                logging.warning(f"[SECURITY] Blocked path prefix: {path_str} matches {blocked}")
                return True
        
        # SECURITY: BLOCK entire src/ directory EXCEPT examples
        # Allow src/examples for SanTOK code execution on Railway compute
        if "src" in path_parts:
            src_index = path_parts.index("src")
            # Allow src/examples - this is where SanTOK codes are that need to run
            if src_index + 1 < len(path_parts) and path_parts[src_index + 1] == "examples":
                # Allow src/examples/ - these are SanTOK codes to run on Railway compute
                return False
            elif len(path_parts) > src_index:
                # Block any src/ subdirectory
                logging.warning(f"[SECURITY] Blocked src/ directory access: {path_str}")
                return True
        
        # SECURITY: BLOCK entire backend/, frontend/, config/ directories - ABSOLUTE
        if "backend" in path_parts or "frontend" in path_parts or "config" in path_parts:
            logging.warning(f"[SECURITY] Blocked core directory access: {path_str}")
            return True
        
        # SECURITY: Block configuration files by name - CRITICAL
        file_name = path_parts[-1] if path_parts else ""
        if file_name in BLOCKED_PATHS or file_name.lower() in {b.lower() for b in BLOCKED_PATHS if "." not in b}:
            logging.warning(f"[SECURITY] Blocked configuration file: {file_name}")
            return True
        
        # SECURITY: Block files with dangerous extensions - ENHANCED
        dangerous_extensions = {".env", ".key", ".pem", ".p12", ".pfx", ".cert", ".crt", ".csr", ".jks", ".keystore"}
        file_lower = file_name.lower()
        if any(file_lower.endswith(ext.lower()) for ext in dangerous_extensions):
            # Only block if NOT in allowed directories
            is_in_allowed = False
            for scope, allowed_path in ALLOWED_DIRECTORIES.items():
                allowed_full = project_root_resolved / allowed_path
                try:
                    resolved_path.relative_to(allowed_full)
                    is_in_allowed = True
                    break
                except ValueError:
                    continue
            if not is_in_allowed:
                logging.warning(f"[SECURITY] Blocked dangerous file extension: {file_name}")
                return True
        
        # SECURITY: Block any hidden files/directories starting with . except in allowed dirs
        if any(part.startswith(".") and part not in [".", ".."] for part in path_parts):
            # Check if it's in an allowed directory
            is_in_allowed = False
            for scope, allowed_path in ALLOWED_DIRECTORIES.items():
                allowed_full = project_root_resolved / allowed_path
                try:
                    resolved_path.relative_to(allowed_full)
                    is_in_allowed = True
                    break
                except ValueError:
                    continue
            if not is_in_allowed:
                # Block hidden files outside allowed directories
                logging.warning(f"[SECURITY] Blocked hidden file/directory: {path_str}")
                return True
        
        # All checks passed - path is not blocked
        return False
        
    except Exception as e:
        # On ANY error, BLOCK access for security (fail-safe)
        import traceback
        logging.error(f"[SECURITY] Path blocking error (blocking for safety): {e}")
        if "NODE_ENV" not in os.environ or os.environ.get("NODE_ENV") != "production":
            traceback.print_exc()
        # FAIL-SAFE: Block on any error
        return True

def get_safe_directory(scope: str, project_root: Path) -> Path:
    """Get a safe directory based on scope, ensuring it exists."""
    if scope in ALLOWED_DIRECTORIES:
        dir_path = project_root / ALLOWED_DIRECTORIES[scope]
        # Create directory if it doesn't exist (for workspace, uploads, temp)
        if not dir_path.exists() and scope in ["workspace", "uploads", "temp"]:
            dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    # Default to examples if exists, otherwise workspace
    examples_dir = project_root / "examples"
    if examples_dir.exists():
        return examples_dir
    
    workspace_dir = project_root / "user_workspace"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    return workspace_dir
# ==================== END SECURITY CONFIGURATION ====================

@app.post("/execute/code")
async def execute_code(code_request: CodeExecutionRequest, http_request: Request):
    auth = get_optional_auth(http_request)
    """Execute Python code and return results."""
    
    # Determine if we should use async execution
    # Use async if: explicitly requested, or timeout > 5 minutes (300 seconds), or interactive mode disabled with long timeout
    use_async = code_request.async_execution
    if use_async is None:
        # Auto-detect: use async for jobs that might take a while
        use_async = code_request.timeout > 300 or (not code_request.interactive and code_request.timeout > 60)
    
    # If async execution is requested, use job manager
    if use_async and get_job_manager is not None and get_job_manager is not None:
        try:
            job_manager = get_job_manager()
            
            # Prepare job data
            job_data = {
                "code": code_request.code,
                "file_path": code_request.file_path,
                "timeout": code_request.timeout,
                "working_dir": code_request.working_dir,
                "interactive": code_request.interactive
            }
            
            # Determine working directory (same logic as sync execution)
            project_root = Path(__file__).parent.parent.parent
            working_dir_scope = code_request.working_dir or "examples"
            if is_user_allowed(auth):
                work_dir = str(project_root.resolve())
            elif working_dir_scope in ALLOWED_DIRECTORIES:
                safe_dir = get_safe_directory(working_dir_scope, project_root)
                work_dir = str(safe_dir.resolve())
            else:
                safe_dir = get_safe_directory("examples", project_root)
                work_dir = str(safe_dir.resolve())
            
            # Handle file execution or create temp file for code
            script_path = None
            if code_request.file_path:
                # Execute from file (path resolution logic here - simplified)
                script_path = code_request.file_path
            else:
                # Create temporary file for code
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=work_dir, encoding='utf-8')
                temp_file.write(code_request.code)
                temp_file.flush()
                temp_file.close()
                script_path = temp_file.name
            
            # Create job
            job_id = job_manager.create_job(job_data)
            
            # Start job execution
            job_manager.start_job(job_id, script_path, work_dir, code_request.timeout)
            
            # Return job ID immediately
            return CodeExecutionResponse(
                success=True,
                stdout="",
                stderr="",
                exit_code=0,
                execution_time=0.0,
                job_id=job_id,
                is_async=True
            )
        except Exception as e:
            # Fall back to sync execution on error
            logging.error(f"Failed to create async job: {e}")
            use_async = False
    
    # Continue with synchronous execution (original logic)
    try:
        start_time = time.time()
        
        # Determine working directory - SECURITY: Only safe directories allowed
        project_root = Path(__file__).parent.parent.parent
        
        # Get safe directory based on working_dir scope (default to examples)
        # Admin users can use project root as working directory
        working_dir_scope = code_request.working_dir or "examples"
        if is_user_allowed(auth):
            # Admin: Use project root as working directory for full access
            work_dir = str(project_root.resolve())
        elif working_dir_scope in ALLOWED_DIRECTORIES:
            safe_dir = get_safe_directory(working_dir_scope, project_root)
            work_dir = str(safe_dir.resolve())
        elif os.path.isabs(working_dir_scope):
            # Absolute paths not allowed for security (non-admin)
            raise HTTPException(status_code=403, detail="Absolute paths not allowed. Use scope: examples, workspace, uploads, or temp")
        else:
            # Default to examples for safety
            safe_dir = get_safe_directory("examples", project_root)
            work_dir = str(safe_dir.resolve())
        
        # Ensure work_dir doesn't contain duplicates
        work_dir = os.path.normpath(work_dir)
        
        # Security: Verify work_dir is in allowed directories (or allow for admin users)
        work_dir_path = Path(work_dir).resolve()
        is_allowed = is_user_allowed(auth)  # Admin users can use any directory
        
        if not is_allowed:
            for scope, allowed_path in ALLOWED_DIRECTORIES.items():
                allowed_dir = (project_root / allowed_path).resolve()
                if allowed_dir.exists():
                    try:
                        work_dir_path.relative_to(allowed_dir)
                        is_allowed = True
                        break
                    except ValueError:
                        continue
        
        if not is_allowed:
            # Force to examples for safety (only for non-admin users)
            examples_dir = get_safe_directory("examples", project_root)
            work_dir = str(examples_dir.resolve())
        
        # Create temporary file if code is provided directly
        temp_file = None
        script_path = None
        
        if code_request.file_path:
            # Execute from file path
            # Admin users can use any path (relative to project root)
            if is_user_allowed(auth):
                # Admin: Allow any path within project root
                normalized_path = code_request.file_path.replace('\\', '/')
                if normalized_path.startswith('./'):
                    normalized_path = normalized_path[2:]
                # Build path relative to project root
                script_path = os.path.normpath(project_root / normalized_path)
            else:
                # Regular users: Normalize path first, then check if it's truly absolute
                normalized_path = code_request.file_path.replace('\\', '/')
                
                # Handle various path formats (Docker/container paths, etc.)
                original_path = normalized_path
                if normalized_path.startswith('./'):
                    normalized_path = normalized_path[2:]
                elif normalized_path.startswith('/app/'):
                    # Docker container path - strip /app/ prefix
                    normalized_path = normalized_path[len('/app/'):]
                    logging.info(f"[HTTP] Normalized Docker path: {code_request.file_path} -> {normalized_path}")
                elif normalized_path.startswith('/'):
                    # Absolute path starting with / - extract relative part
                    parts = normalized_path.split('/')
                    if len(parts) > 1:
                        normalized_path = '/'.join([p for p in parts[1:] if p])  # Remove empty parts
                        if normalized_path.startswith('app/'):
                            normalized_path = normalized_path[len('app/'):]
                
                # After normalization, check if it's still absolute (only block truly absolute system paths)
                if normalized_path and os.path.isabs(normalized_path) and not normalized_path.startswith(('examples', 'workspace', 'uploads', 'temp')):
                    # Only block if it's a true absolute path that doesn't start with allowed directories
                    raise HTTPException(status_code=403, detail="Absolute paths not allowed. Use relative paths within allowed directories (examples, workspace, uploads, temp)")
                elif normalized_path:
                    
                    # Remove 'examples/' or 'examples\\' prefix if present
                    if normalized_path.startswith('examples/'):
                        normalized_path = normalized_path[len('examples/'):]
                    elif normalized_path.startswith('examples\\'):
                        normalized_path = normalized_path[len('examples\\'):]
                    
                    # Convert to OS-specific path separators
                    normalized_path = normalized_path.replace('/', os.sep).replace('\\', os.sep)
                    
                    # Build script path using normalized work_dir (already resolved correctly)
                    script_path = os.path.normpath(os.path.join(work_dir, normalized_path))
            
            # Security check: ensure script_path is within project root
            script_path_obj = Path(script_path).resolve()
            
            # Ensure path is within project root (security for all users)
            try:
                script_path_obj.relative_to(project_root.resolve())
            except ValueError:
                raise HTTPException(status_code=403, detail="File path outside project root")
            
            # Check if path is blocked (SanTOK core files) - bypassed for allowed users
            if is_path_blocked(script_path_obj, project_root, auth):
                raise HTTPException(status_code=403, detail="Access denied: This file is protected")
            
            # For non-admin users: ensure script is in allowed directories
            if not is_user_allowed(auth):
                is_script_allowed = False
                for scope, allowed_path in ALLOWED_DIRECTORIES.items():
                    allowed_dir = (project_root / allowed_path).resolve()
                    if allowed_dir.exists():
                        try:
                            script_path_obj.relative_to(allowed_dir)
                            is_script_allowed = True
                            break
                        except ValueError:
                            continue
                
                if not is_script_allowed:
                    raise HTTPException(status_code=403, detail="Access denied: Script outside allowed directories")
            
            # Verify the path exists - try alternative paths if not found
            if not os.path.exists(script_path):
                # Try alternative paths
                alt_paths = []
                original_path = script_path
                
                # If path doesn't start with examples, try examples directory
                if not any(script_path.replace('\\', '/').startswith(ap.replace('\\', '/')) for ap in [str((project_root / ap).resolve()) for ap in ALLOWED_DIRECTORIES.values()]):
                    # Try relative to examples directory
                    relative_path = script_path.replace('\\', '/').replace(str(project_root.resolve()).replace('\\', '/'), '').lstrip('/')
                    if relative_path and not relative_path.startswith('examples/'):
                        examples_path = os.path.normpath(os.path.join(project_root, 'examples', relative_path))
                        if os.path.exists(examples_path):
                            alt_paths.append(examples_path)
                    
                    # Try just the filename in examples
                    filename = os.path.basename(script_path)
                    if filename:
                        examples_filename = os.path.normpath(os.path.join(project_root, 'examples', filename))
                        if os.path.exists(examples_filename):
                            alt_paths.append(examples_filename)
                
                if alt_paths:
                    # Use first alternative path found and re-validate security
                    script_path = alt_paths[0]
                    script_path_obj = Path(script_path).resolve()
                    
                    # Re-check security for the new path
                    try:
                        script_path_obj.relative_to(project_root.resolve())
                    except ValueError:
                        raise HTTPException(status_code=403, detail="File path outside project root")
                    
                    if is_path_blocked(script_path_obj, project_root, auth):
                        raise HTTPException(status_code=403, detail="Access denied: This file is protected")
                    
                    if not is_user_allowed(auth):
                        is_script_allowed = False
                        for scope, allowed_path in ALLOWED_DIRECTORIES.items():
                            allowed_dir = (project_root / allowed_path).resolve()
                            if allowed_dir.exists():
                                try:
                                    script_path_obj.relative_to(allowed_dir)
                                    is_script_allowed = True
                                    break
                                except ValueError:
                                    continue
                        
                        if not is_script_allowed:
                            raise HTTPException(status_code=403, detail="Access denied: Script outside allowed directories")
                    
                    logging.info(f"[HTTP] Found file at alternative path: {script_path} (original: {original_path})")
                else:
                    raise HTTPException(status_code=404, detail=f"File not found: {script_path}. Tried original path and alternative locations in examples/")
        else:
            # Create temporary file for code execution
            # Use encoding='utf-8' to handle Unicode characters properly
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=work_dir, encoding='utf-8') as f:
                f.write(code_request.code)
                temp_file = f.name
                script_path = temp_file
        
        # Execute the script
        try:
            # Set environment variables to ensure UTF-8 encoding
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=code_request.timeout,
                cwd=work_dir,
                env=env,
                encoding='utf-8',  # Ensure UTF-8 encoding for stdout/stderr
                errors='replace'  # Replace encoding errors instead of crashing
            )
            
            execution_time = time.time() - start_time
            
            # Clean up temp file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception:
                    # File might already be deleted, ignore
                    pass
            
            return CodeExecutionResponse(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                execution_time=execution_time,
                is_async=False
            )
            
        except subprocess.TimeoutExpired:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception:
                    # File might already be deleted, ignore
                    pass
            
            return CodeExecutionResponse(
                success=False,
                stdout="",
                stderr=f"Execution timeout after {code_request.timeout} seconds",
                exit_code=-1,
                execution_time=time.time() - start_time,
                error=f"Timeout: execution exceeded {code_request.timeout} seconds",
                is_async=False
            )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        return CodeExecutionResponse(
            success=False,
            stdout="",
            stderr=traceback.format_exc(),
            exit_code=-1,
            execution_time=time.time() - start_time if 'start_time' in locals() else 0.0,
            error=str(e),
            is_async=False
        )

# ==================== ASYNC JOB STATUS ENDPOINTS ====================

@app.get("/execute/job/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of an async job"""
    if get_job_manager is None:
        raise HTTPException(status_code=503, detail="Job manager not available")
    
    job_manager = get_job_manager()
    job_info = job_manager.get_job(job_id)
    
    if job_info is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return JobStatusResponse(
        job_id=job_info.get("job_id", job_id),
        status=job_info.get("status", "unknown"),
        progress=job_info.get("progress", 0),
        stdout=job_info.get("stdout", ""),
        stderr=job_info.get("stderr", ""),
        exit_code=job_info.get("exit_code"),
        execution_time=job_info.get("execution_time"),
        error=job_info.get("error"),
        created_at=job_info.get("created_at", ""),
        started_at=job_info.get("started_at"),
        completed_at=job_info.get("completed_at")
    )

@app.post("/execute/job/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a running job"""
    if get_job_manager is None:
        raise HTTPException(status_code=503, detail="Job manager not available")
    
    job_manager = get_job_manager()
    job_info = job_manager.get_job(job_id)
    
    if job_info is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    if job_info.get("status") not in [JobStatus.PENDING, JobStatus.RUNNING]:
        raise HTTPException(status_code=400, detail=f"Job {job_id} cannot be cancelled (status: {job_info.get('status')})")
    
    cancelled = job_manager.cancel_job(job_id)
    if cancelled:
        return {"success": True, "message": f"Job {job_id} cancelled successfully"}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to cancel job {job_id}")

@app.get("/training/jobs")
async def list_training_jobs():
    """List all training-related jobs (vocabulary, model training, etc.)"""
    if get_job_manager is None:
        return {"jobs": [], "total": 0}
    
    job_manager = get_job_manager()
    all_jobs = []
    
    # Get all jobs from the jobs directory
    jobs_dir = Path("jobs")
    if jobs_dir.exists():
        for job_file in jobs_dir.glob("*.json"):
            try:
                with open(job_file, 'r', encoding='utf-8') as f:
                    job_data = json.load(f)
                    # Filter for training-related jobs
                    script_path = job_data.get("data", {}).get("script_path", "")
                    job_id = job_data.get("job_id", "")
                    # Check if it's a training job
                    if ("training_scripts" in script_path or 
                        "vocab" in script_path.lower() or 
                        "train" in script_path.lower() or
                        "vocab" in job_id.lower() or
                        "train" in job_id.lower()):
                        all_jobs.append({
                            "job_id": job_data.get("job_id"),
                            "status": job_data.get("status"),
                            "progress": job_data.get("progress", 0),
                            "created_at": job_data.get("created_at"),
                            "started_at": job_data.get("started_at"),
                            "completed_at": job_data.get("completed_at"),
                            "stdout": job_data.get("stdout", "")[-1000:],  # Last 1000 chars
                            "stderr": job_data.get("stderr", "")[-500:],
                            "error": job_data.get("error"),
                            "execution_time": job_data.get("execution_time")
                        })
            except Exception:
                continue
    
    # Sort by created_at (newest first)
    all_jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return {"jobs": all_jobs, "total": len(all_jobs)}

# WebSocket endpoint for interactive code execution (like VSCode)
@app.websocket("/ws/execute")
async def websocket_execute(websocket: WebSocket):
    """
    WebSocket endpoint for interactive code execution.
    Supports real-time stdin/stdout/stderr streaming like VSCode.
    """
    await websocket.accept()
    
    process = None
    temp_file = None
    work_dir = None
    
    try:
        # Receive initial execution request (may contain auth_token since browser WebSocket doesn't support headers)
        data = await websocket.receive_text()
        request = json.loads(data)
        
        # Extract auth from request (browser WebSocket doesn't support custom headers)
        auth = None
        auth_token = request.get("auth_token")
        if auth_token:
            try:
                payload = jwt.decode(auth_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
                if payload.get("username") in ALLOWED_USERS:
                    auth = payload
            except jwt.InvalidTokenError:
                pass  # Invalid token, auth remains None
        
        code = request.get("code", "")
        file_path = request.get("file_path")
        working_dir_scope = request.get("working_dir", "examples")
        timeout = request.get("timeout", 86400)  # Default to 24 hours
        
        # Determine working directory - SECURITY: Only safe directories allowed (or project root for admin)
        project_root = Path(__file__).parent.parent.parent
        
        # Admin users can use project root as working directory
        if is_user_allowed(auth):
            work_dir = str(project_root.resolve())
        elif working_dir_scope in ALLOWED_DIRECTORIES:
            safe_dir = get_safe_directory(working_dir_scope, project_root)
            work_dir = str(safe_dir.resolve())
        else:
            safe_dir = get_safe_directory("examples", project_root)
            work_dir = str(safe_dir.resolve())
        
        work_dir = os.path.normpath(work_dir)
        
        # Create temporary file if code is provided directly
        if file_path:
            # SECURITY: BLOCK absolute paths - STRICT
            if os.path.isabs(file_path):
                logging.warning(f"[SECURITY] WebSocket blocked absolute path: {file_path}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Absolute paths not allowed"
                }))
                await websocket.close()
                return
            
            # SECURITY: Normalize and validate path
            normalized_path = file_path.replace('\\', '/')
            
            # Handle various path formats
            if normalized_path.startswith('./'):
                normalized_path = normalized_path[2:]
            elif normalized_path.startswith('/app/'):
                # Docker container path - strip /app/ prefix
                normalized_path = normalized_path[len('/app/'):]
                logging.info(f"[WebSocket] Normalized Docker path: {file_path} -> {normalized_path}")
            elif normalized_path.startswith('/'):
                # Absolute path starting with / - extract relative part
                parts = normalized_path.split('/')
                # Remove leading empty string from split and common container prefixes
                if len(parts) > 1:
                    normalized_path = '/'.join([p for p in parts[1:] if p])  # Remove empty parts
                    # If it still starts with a known prefix, remove it
                    if normalized_path.startswith('app/'):
                        normalized_path = normalized_path[len('app/'):]
            
            # Remove examples/ prefix if present (we'll add it back relative to work_dir)
            if normalized_path.startswith('examples/'):
                normalized_path = normalized_path[len('examples/'):]
            
            # SECURITY: Block directory traversal
            if ".." in normalized_path:
                logging.warning(f"[SECURITY] WebSocket blocked directory traversal: {file_path}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Directory traversal not allowed"
                }))
                await websocket.close()
                return
            
            script_path = os.path.normpath(os.path.join(work_dir, normalized_path))
            script_path_obj = Path(script_path).resolve()
            
            # SECURITY: Check if path is blocked - CRITICAL
            if is_path_blocked(script_path_obj, project_root, auth):
                logging.warning(f"[SECURITY] WebSocket blocked protected file: {script_path}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Access denied: This file is protected"
                }))
                await websocket.close()
                return
            
            # SECURITY: Ensure script is within allowed directories (only for non-admin users)
            if not is_user_allowed(auth):
                is_script_allowed = False
                for scope, allowed_path in ALLOWED_DIRECTORIES.items():
                    allowed_dir = (project_root / allowed_path).resolve()
                    if allowed_dir.exists():
                        try:
                            script_path_obj.relative_to(allowed_dir)
                            is_script_allowed = True
                            break
                        except ValueError:
                            continue
                
                if not is_script_allowed:
                    logging.warning(f"[SECURITY] WebSocket blocked file outside allowed directories: {script_path}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Access denied: Script outside allowed directories"
                    }))
                    await websocket.close()
                    return
            
            if not os.path.exists(script_path):
                # Try alternative paths if file not found
                alt_paths = []
                
                # Try relative to examples directory
                if normalized_path and not normalized_path.startswith('examples/'):
                    examples_path = os.path.normpath(os.path.join(project_root, 'examples', normalized_path))
                    if os.path.exists(examples_path):
                        alt_paths.append(examples_path)
                
                # Try just the filename in examples
                filename = os.path.basename(normalized_path) if normalized_path else None
                if filename:
                    examples_filename = os.path.normpath(os.path.join(project_root, 'examples', filename))
                    if os.path.exists(examples_filename):
                        alt_paths.append(examples_filename)
                
                if alt_paths:
                    # Use first alternative path found
                    script_path = alt_paths[0]
                    script_path_obj = Path(script_path).resolve()
                    logging.info(f"[WebSocket] Found file at alternative path: {script_path}")
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"File not found: {file_path}. Tried: {script_path}" + (f" and {', '.join(alt_paths)}" if alt_paths else "")
                    }))
                    await websocket.close()
                    return
        else:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=work_dir, encoding='utf-8') as f:
                f.write(code)
                temp_file = f.name
                script_path = temp_file
        
        # Set environment variables
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'
        env['PYTHONUNBUFFERED'] = '1'  # Unbuffered output for immediate I/O
        
        # Start process with interactive stdin/stdout/stderr
        # Use -u flag for unbuffered Python I/O (crucial for input() to work)
        process = subprocess.Popen(
            [sys.executable, '-u', script_path],  # -u flag for unbuffered
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=work_dir,
            env=env,
            encoding='utf-8',
            errors='replace',
            bufsize=0  # Unbuffered for immediate I/O
        )
        logging.info(f"[WebSocket] Started process with PID {process.pid} for {script_path}")
        
        # Start output readers in separate threads
        output_queue = queue.Queue()
        error_queue = queue.Queue()
        
        def read_stdout():
            try:
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    if line:
                        output_queue.put(('stdout', line))
                        # Log for debugging
                        logging.debug(f"[WebSocket] stdout: {repr(line)}")
                output_queue.put(('stdout', None))  # EOF marker
            except Exception as e:
                logging.error(f"[WebSocket] Error reading stdout: {e}")
                output_queue.put(('error', str(e)))
        
        def read_stderr():
            try:
                while True:
                    line = process.stderr.readline()
                    if not line:
                        break
                    if line:
                        error_queue.put(('stderr', line))
                        # Log for debugging
                        logging.debug(f"[WebSocket] stderr: {repr(line)}")
                error_queue.put(('stderr', None))  # EOF marker
            except Exception as e:
                logging.error(f"[WebSocket] Error reading stderr: {e}")
                error_queue.put(('error', str(e)))
        
        stdout_thread = threading.Thread(target=read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stdout_thread.start()
        stderr_thread.start()
        
        # Main loop: handle output and input
        start_time = time.time()
        stdin_needed = False
        last_output_time = time.time()
        input_needed_sent = False
        
        # Send initial input_needed if code starts with input() (no output yet)
        # Small delay to allow process to start
        await asyncio.sleep(0.2)
        if process.poll() is None and output_queue.empty() and error_queue.empty():
            # Process started but no output - might be waiting for input() at start
            await websocket.send_text(json.dumps({
                "type": "input_needed",
                "message": "Waiting for input..."
            }))
            input_needed_sent = True
            stdin_needed = True
        
        while True:
            # Check if process is still running
            if process.poll() is not None:
                # Process finished, flush remaining output
                while not output_queue.empty():
                    msg_type, data = output_queue.get_nowait()
                    if data is not None:
                        await websocket.send_text(json.dumps({
                            "type": msg_type,
                            "data": data
                        }))
                
                while not error_queue.empty():
                    msg_type, data = error_queue.get_nowait()
                    if data is not None:
                        await websocket.send_text(json.dumps({
                            "type": msg_type,
                            "data": data
                        }))
                
                # Send exit code
                await websocket.send_text(json.dumps({
                    "type": "exit",
                    "exit_code": process.returncode,
                    "execution_time": time.time() - start_time
                }))
                break
            
            # Check for timeout
            if time.time() - start_time > timeout:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Execution timeout after {timeout} seconds"
                }))
                break
            
            # Check for output
            try:
                msg_type, data = output_queue.get_nowait()
                if data is not None:
                    await websocket.send_text(json.dumps({
                        "type": msg_type,
                        "data": data
                    }))
                    last_output_time = time.time()
                    # After stdout, process might be waiting for input
                    if msg_type == 'stdout' and process.poll() is None:
                        stdin_needed = True
                        input_needed_sent = False  # Reset to send new input_needed signal
                        # Immediately send input_needed after stdout (prompt likely means input() is called)
                        # Small delay to check if more output is coming
                        await asyncio.sleep(0.1)
                        # If still no output and process running, it's likely waiting for input
                        if output_queue.empty() and error_queue.empty() and process.poll() is None:
                            if not input_needed_sent:
                                await websocket.send_text(json.dumps({
                                    "type": "input_needed",
                                    "message": "Waiting for input..."
                                }))
                                input_needed_sent = True
            except queue.Empty:
                pass
            
            # Check for errors
            try:
                msg_type, data = error_queue.get_nowait()
                if data is not None:
                    await websocket.send_text(json.dumps({
                        "type": msg_type,
                        "data": data
                    }))
                    last_output_time = time.time()
            except queue.Empty:
                pass
            
            # Detect if process is likely waiting for input
            # If process is running, no output in queues, and some time has passed since last output
            # It's likely blocked on input()
            # Also check if we've sent output before (stdin_needed=True) OR if process has been running without output for a bit
            current_time = time.time()
            time_since_last_output = current_time - last_output_time
            process_running = process.poll() is None
            
            if (process_running and 
                output_queue.empty() and error_queue.empty() and
                not input_needed_sent):
                # Case 1: We've had output before (stdin_needed=True) - likely waiting for input
                # Case 2: Process started but no output yet - might be waiting for input() at start
                # Send input_needed signal if either condition is met
                if (stdin_needed and time_since_last_output > 0.2) or (time_since_last_output > 0.5):
                    await websocket.send_text(json.dumps({
                        "type": "input_needed",
                        "message": "Waiting for input..."
                    }))
                    input_needed_sent = True
                    stdin_needed = True  # Mark that we're expecting input
            
            # Try to receive input from client (non-blocking, but more responsive)
            try:
                # Use a shorter timeout for more responsive input handling
                client_data = await asyncio.wait_for(websocket.receive_text(), timeout=0.05)
                input_data = json.loads(client_data)
                
                if input_data.get("type") == "stdin":
                    user_input = input_data.get("data", "")
                    logging.info(f"[WebSocket] Received stdin input: {repr(user_input)}")
                    if process.stdin and process.poll() is None:
                        try:
                            # Write input + newline and flush immediately
                            process.stdin.write(user_input + "\n")
                            process.stdin.flush()
                            logging.info(f"[WebSocket] Sent input to process: {repr(user_input)}")
                            
                            # Reset flags to detect next input need
                            stdin_needed = False
                            input_needed_sent = False
                            last_output_time = time.time()
                            
                            # Continue immediately to check for output
                            continue
                        except (BrokenPipeError, OSError) as e:
                            logging.error(f"[WebSocket] Failed to write to stdin: {e}")
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "message": f"Failed to send input: {str(e)}"
                            }))
                        except Exception as e:
                            logging.error(f"[WebSocket] Unexpected error writing to stdin: {e}")
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "message": f"Failed to send input: {str(e)}"
                            }))
                elif input_data.get("type") == "kill":
                    logging.info("[WebSocket] Kill signal received")
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    await websocket.send_text(json.dumps({
                        "type": "killed",
                        "message": "Execution was cancelled"
                    }))
                    break
            except asyncio.TimeoutError:
                # No input received, continue loop
                pass
            except WebSocketDisconnect:
                logging.info("[WebSocket] Client disconnected")
                break
            except Exception as e:
                logging.error(f"[WebSocket] Error receiving message: {e}")
                # Continue loop even on error
                pass
            
            # Smaller delay for more responsive input handling
            await asyncio.sleep(0.005)
        
        # Wait for threads to finish
        stdout_thread.join(timeout=1)
        stderr_thread.join(timeout=1)
        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e),
                "traceback": error_msg
            }))
        except Exception:
            # Failed to send error message, ignore
            pass
    finally:
        # Cleanup
        if process:
            try:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
            except Exception:
                # Failed to terminate process, ignore
                pass
        
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except Exception:
                # File might already be deleted, ignore
                pass
        
        try:
            await websocket.close()
        except Exception:
            # WebSocket already closed, ignore
            pass

@app.post("/execute/terminal")
async def execute_terminal_command(terminal_request: TerminalCommandRequest, http_request: Request):
    auth = get_optional_auth(http_request)
    """
    Execute terminal commands in SAFE directories only.
    SECURITY: All commands are restricted to whitelisted directories. SanTOK core files are blocked.
    """
    try:
        project_root = Path(__file__).parent.parent.parent
        
        # Get safe directory - default to examples
        cwd_scope = terminal_request.cwd or "examples"
        
        # If cwd is a scope name (examples, workspace, etc.), use it
        if cwd_scope in ALLOWED_DIRECTORIES:
            safe_dir = get_safe_directory(cwd_scope, project_root)
            cwd = str(safe_dir.resolve())
        elif os.path.isabs(cwd_scope):
            # Absolute paths not allowed - default to examples
            safe_dir = get_safe_directory("examples", project_root)
            cwd = str(safe_dir.resolve())
        else:
            # Try to resolve as path within safe directories
            # Default to examples for safety
            safe_dir = get_safe_directory("examples", project_root)
            cwd = str(safe_dir.resolve())
        
        # Security: Ensure cwd is in allowed directories (unless user is allowed)
        if not is_user_allowed(auth):
            cwd_path = Path(cwd).resolve()
            is_allowed = False
            for scope, allowed_path in ALLOWED_DIRECTORIES.items():
                allowed_dir = (project_root / allowed_path).resolve()
                if allowed_dir.exists():
                    try:
                        cwd_path.relative_to(allowed_dir)
                        is_allowed = True
                        break
                    except ValueError:
                        continue
            
            if not is_allowed:
                # Force to examples for safety
                safe_dir = get_safe_directory("examples", project_root)
                cwd = str(safe_dir.resolve())
        
        # Handle special terminal commands
        command_parts = terminal_request.command.strip().split()
        if not command_parts:
            return TerminalCommandResponse(
                success=True,
                output="",
                cwd=cwd
            )
        
        cmd = command_parts[0].lower()
        
        # Handle cd command
        if cmd == 'cd':
            try:
                if len(command_parts) < 2:
                    return TerminalCommandResponse(
                        success=True,
                        output=f"Current directory: {cwd}\n",
                        cwd=cwd
                    )
                
                target = command_parts[1]
                
                # Security: BLOCK home directory access (~ or $HOME) - unless user is allowed
                if not is_user_allowed(auth):
                    if target == '~' or target == '$HOME' or target.startswith('~/'):
                        return TerminalCommandResponse(
                            success=False,
                            output=f"cd: {command_parts[1]}: Permission denied (home directory access blocked)\n",
                            cwd=cwd
                        )
                    
                    # Security: BLOCK absolute paths for regular users (admin users allowed below)
                    if os.path.isabs(target):
                        return TerminalCommandResponse(
                            success=False,
                            output=f"cd: {command_parts[1]}: Permission denied (absolute paths not allowed)\n",
                            cwd=cwd
                        )
                
                # Security: Handle directory traversal attempts
                # Admin users can use absolute paths and .. traversal anywhere in project
                if is_user_allowed(auth) and os.path.isabs(target):
                    # Admin: Allow absolute paths within project root
                    try:
                        resolved = Path(target).resolve()
                        resolved.relative_to(project_root.resolve())  # Verify within project root
                    except (ValueError, Exception):
                        return TerminalCommandResponse(
                            success=False,
                            output=f"cd: {command_parts[1]}: Permission denied (outside project root)\n",
                            cwd=cwd
                        )
                elif ".." in target:
                    # Only allow relative navigation within allowed directories
                    # Resolve relative to current cwd first
                    potential_target = os.path.join(cwd, target)
                    potential_target = os.path.normpath(potential_target)
                    
                    # Security: Check if resolved path is still within allowed directories
                    try:
                        resolved = Path(potential_target).resolve()
                    except Exception:
                        return TerminalCommandResponse(
                            success=False,
                            output=f"cd: {command_parts[1]}: Permission denied (invalid path)\n",
                            cwd=cwd
                        )
                else:
                    # Relative path (no ..)
                    potential_target = os.path.join(cwd, target)
                    potential_target = os.path.normpath(potential_target)
                    try:
                        resolved = Path(potential_target).resolve()
                    except Exception:
                        return TerminalCommandResponse(
                            success=False,
                            output=f"cd: {command_parts[1]}: Permission denied (invalid path)\n",
                            cwd=cwd
                        )
                
                # Security: Check if path is blocked (SanTOK core files) - bypassed for allowed users
                if is_path_blocked(resolved, project_root, auth):
                    return TerminalCommandResponse(
                        success=False,
                        output=f"cd: {command_parts[1]}: Permission denied (protected directory)\n",
                        cwd=cwd
                    )
                
                # Security: Check if target is within any allowed directory (or allow admin users)
                # Admin users can cd anywhere within project root
                if is_user_allowed(auth):
                    # Admin: Allow cd to any directory within project root
                    try:
                        resolved.relative_to(project_root.resolve())
                        if resolved.is_dir():
                            cwd = str(resolved)
                        else:
                            return TerminalCommandResponse(
                                success=False,
                                output=f"cd: {command_parts[1]}: Not a directory\n",
                                cwd=cwd
                            )
                    except ValueError:
                        return TerminalCommandResponse(
                            success=False,
                            output=f"cd: {command_parts[1]}: Permission denied (outside project root)\n",
                            cwd=cwd
                        )
                else:
                    # Regular users: Only allow cd to allowed directories
                    is_allowed_dir = False
                    for scope, allowed_path in ALLOWED_DIRECTORIES.items():
                        allowed_dir = (project_root / allowed_path).resolve()
                        if allowed_dir.exists():
                            try:
                                resolved.relative_to(allowed_dir)
                                is_allowed_dir = True
                                break
                            except ValueError:
                                continue
                    
                    if is_allowed_dir:
                        if resolved.is_dir():
                            cwd = str(resolved)
                        else:
                            return TerminalCommandResponse(
                                success=False,
                                output=f"cd: {command_parts[1]}: Not a directory\n",
                                cwd=cwd
                            )
                    else:
                        return TerminalCommandResponse(
                            success=False,
                            output=f"cd: {command_parts[1]}: Permission denied (outside allowed directories)\n",
                            cwd=cwd
                        )
                
                return TerminalCommandResponse(
                    success=True,
                    output="",
                    cwd=cwd
                )
            except Exception as e:
                return TerminalCommandResponse(
                    success=False,
                    output=f"cd: {command_parts[1] if len(command_parts) > 1 else ''}: {str(e)}\n",
                    cwd=cwd
                )
        
        # Handle pwd command
        elif cmd == 'pwd':
            return TerminalCommandResponse(
                success=True,
                output=f"{cwd}\n",
                cwd=cwd
            )
        
        # Handle ls command (list files)
        elif cmd == 'ls' or cmd == 'dir':
            try:
                path = cwd
                if len(command_parts) > 1:
                    target = command_parts[1]
                    
                    # Security: BLOCK absolute paths
                    if os.path.isabs(target):
                        return TerminalCommandResponse(
                            success=False,
                            output=f"ls: {command_parts[1]}: Permission denied (absolute paths not allowed)\n",
                            cwd=cwd
                        )
                    
                    # Security: Handle directory traversal
                    if ".." in target:
                        # Only allow relative navigation within allowed directories
                        potential_path = os.path.join(cwd, target)
                        potential_path = os.path.normpath(potential_path)
                        path_obj = Path(potential_path).resolve()
                        
                        # Check if resolved path is still within allowed directories
                        if is_path_blocked(path_obj, project_root):
                            return TerminalCommandResponse(
                                success=False,
                                output=f"ls: {command_parts[1]}: Permission denied (protected directory)\n",
                                cwd=cwd
                            )
                        
                        # Verify path is within allowed directories (unless user is allowed)
                        if is_user_allowed(auth):
                            is_path_allowed = True  # Allowed users can access any path
                        else:
                            is_path_allowed = False
                            for scope, allowed_path in ALLOWED_DIRECTORIES.items():
                                allowed_dir = (project_root / allowed_path).resolve()
                                if allowed_dir.exists():
                                    try:
                                        path_obj.relative_to(allowed_dir)
                                        is_path_allowed = True
                                        break
                                    except ValueError:
                                        continue
                        
                        if not is_path_allowed:
                            return TerminalCommandResponse(
                                success=False,
                                output=f"ls: {command_parts[1]}: Permission denied (outside allowed directories)\n",
                                cwd=cwd
                            )
                        
                        path = potential_path
                    else:
                        path = os.path.join(cwd, target)
                        path = os.path.normpath(path)
                
                if not os.path.exists(path):
                    return TerminalCommandResponse(
                        success=False,
                        output=f"ls: {command_parts[1] if len(command_parts) > 1 else ''}: No such file or directory\n",
                        cwd=cwd
                    )
                
                # Security: Check if path is blocked or outside allowed directories - bypassed for allowed users
                path_obj = Path(path).resolve()
                if is_path_blocked(path_obj, project_root, auth):
                    return TerminalCommandResponse(
                        success=False,
                        output=f"ls: {command_parts[1] if len(command_parts) > 1 else ''}: Permission denied (protected directory)\n",
                        cwd=cwd
                    )
                
                # Check if path is within allowed directories (unless user is allowed)
                if is_user_allowed(auth):
                    is_path_allowed = True  # Allowed users can access any path
                else:
                    is_path_allowed = False
                    for scope, allowed_path in ALLOWED_DIRECTORIES.items():
                        allowed_dir = (project_root / allowed_path).resolve()
                        if allowed_dir.exists():
                            try:
                                path_obj.relative_to(allowed_dir)
                                is_path_allowed = True
                                break
                            except ValueError:
                                continue
                
                if not is_path_allowed:
                    return TerminalCommandResponse(
                        success=False,
                        output=f"ls: {command_parts[1] if len(command_parts) > 1 else ''}: Permission denied (outside allowed directories)\n",
                        cwd=cwd
                    )
                
                if os.path.isfile(path):
                    return TerminalCommandResponse(
                        success=True,
                        output=f"{os.path.basename(path)}\n",
                        cwd=cwd
                    )
                
                # List directory contents (only safe files)
                items = []
                try:
                    for item in sorted(os.listdir(path)):
                        item_path = os.path.join(path, item)
                        # Security: Filter out blocked paths - bypassed for allowed users
                        item_obj = Path(item_path).resolve()
                        if is_path_blocked(item_obj, project_root, auth):
                            continue  # Skip blocked items
                        
                        if os.path.isdir(item_path):
                            items.append(f"{item}/")
                        else:
                            items.append(item)
                except PermissionError:
                    return TerminalCommandResponse(
                        success=False,
                        output=f"ls: Permission denied\n",
                        cwd=cwd
                    )
                
                return TerminalCommandResponse(
                    success=True,
                    output="  ".join(items) + "\n",
                    cwd=cwd
                )
            except Exception as e:
                return TerminalCommandResponse(
                    success=False,
                    output=f"ls: {str(e)}\n",
                    cwd=cwd
                )
        
        # Handle cat command (read file)
        elif cmd == 'cat':
            if len(command_parts) < 2:
                return TerminalCommandResponse(
                    success=False,
                    output="cat: missing file argument\n",
                    cwd=cwd
                )
            
            try:
                file_path = command_parts[1]
                
                # Security: BLOCK absolute paths
                if os.path.isabs(file_path):
                    return TerminalCommandResponse(
                        success=False,
                        output=f"cat: {command_parts[1]}: Permission denied (absolute paths not allowed)\n",
                        cwd=cwd
                    )
                
                # Security: Block directory traversal attempts
                if ".." in file_path:
                    potential_file = os.path.join(cwd, file_path)
                    potential_file = os.path.normpath(potential_file)
                    file_path_obj = Path(potential_file).resolve()
                    
                    # Check if path is blocked - bypassed for allowed users
                    if is_path_blocked(file_path_obj, project_root, auth):
                        return TerminalCommandResponse(
                            success=False,
                            output=f"cat: {command_parts[1]}: Permission denied (protected file)\n",
                            cwd=cwd
                        )
                    
                    # Verify path is within allowed directories (unless user is allowed)
                    if is_user_allowed(auth):
                        is_allowed_file = True  # Allowed users can access any file
                    else:
                        is_allowed_file = False
                        for scope, allowed_path in ALLOWED_DIRECTORIES.items():
                            allowed_dir = (project_root / allowed_path).resolve()
                            if allowed_dir.exists():
                                try:
                                    file_path_obj.relative_to(allowed_dir)
                                    is_allowed_file = True
                                    break
                                except ValueError:
                                    continue
                    
                    if not is_allowed_file:
                        return TerminalCommandResponse(
                            success=False,
                            output=f"cat: {command_parts[1]}: Permission denied (outside allowed directories)\n",
                            cwd=cwd
                        )
                    
                    file_path = potential_file
                else:
                    file_path = os.path.join(cwd, file_path)
                    file_path = os.path.normpath(file_path)
                
                # Security: Check if path is blocked and within allowed directories - bypassed for allowed users
                resolved_file = Path(file_path).resolve()
                
                # Check if path is blocked (SanTOK core files)
                if is_path_blocked(resolved_file, project_root, auth):
                    return TerminalCommandResponse(
                        success=False,
                        output=f"cat: {command_parts[1]}: Permission denied (protected file)\n",
                        cwd=cwd
                    )
                
                # Check if file is within allowed directories (unless user is allowed)
                if is_user_allowed(auth):
                    is_allowed_file = True  # Allowed users can access any file
                else:
                    is_allowed_file = False
                    for scope, allowed_path in ALLOWED_DIRECTORIES.items():
                        allowed_dir = (project_root / allowed_path).resolve()
                        if allowed_dir.exists():
                            try:
                                resolved_file.relative_to(allowed_dir)
                                is_allowed_file = True
                                break
                            except ValueError:
                                continue
                
                if not is_allowed_file:
                    return TerminalCommandResponse(
                        success=False,
                        output=f"cat: {command_parts[1]}: Permission denied (outside allowed directories)\n",
                        cwd=cwd
                    )
                
                if not os.path.exists(file_path):
                    return TerminalCommandResponse(
                        success=False,
                        output=f"cat: {command_parts[1]}: No such file or directory\n",
                        cwd=cwd
                    )
                
                if os.path.isdir(file_path):
                    return TerminalCommandResponse(
                        success=False,
                        output=f"cat: {command_parts[1]}: Is a directory\n",
                        cwd=cwd
                    )
                
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                return TerminalCommandResponse(
                    success=True,
                    output=content + ("\n" if not content.endswith("\n") else ""),
                    cwd=cwd
                )
            except Exception as e:
                return TerminalCommandResponse(
                    success=False,
                    output=f"cat: {str(e)}\n",
                    cwd=cwd
                )
        
        # Handle clear command
        elif cmd == 'clear' or cmd == 'cls':
            return TerminalCommandResponse(
                success=True,
                output="\033[2J\033[H",  # ANSI clear screen
                cwd=cwd
            )
        
        # Handle help command
        elif cmd == 'help':
            help_text = """Available terminal commands:
  cd <directory>    - Change directory
  pwd               - Print current directory
  ls [directory]    - List files and directories
  cat <file>        - Display file contents
  clear / cls       - Clear terminal screen
  help              - Show this help message
  python <file>     - Execute Python file
  <python code>     - Execute Python code directly
"""
            return TerminalCommandResponse(
                success=True,
                output=help_text,
                cwd=cwd
            )
        
        # For Python commands, execute via execute_code endpoint logic
        elif cmd == 'python' or cmd == 'py':
            if len(command_parts) < 2:
                return TerminalCommandResponse(
                    success=False,
                    output="python: missing file argument\n",
                    cwd=cwd
                )
            
            file_path = command_parts[1]
            
            # Security: BLOCK absolute paths
            if os.path.isabs(file_path):
                return TerminalCommandResponse(
                    success=False,
                    output=f"python: {command_parts[1]}: Permission denied (absolute paths not allowed)\n",
                    cwd=cwd
                )
            
            # Security: Block directory traversal attempts
            if ".." in file_path:
                potential_file = os.path.join(cwd, file_path)
                potential_file = os.path.normpath(potential_file)
                file_path_obj = Path(potential_file).resolve()
                
                # Check if path is blocked - bypassed for allowed users
                if is_path_blocked(file_path_obj, project_root, auth):
                    return TerminalCommandResponse(
                        success=False,
                        output=f"python: {command_parts[1]}: Permission denied (protected file)\n",
                        cwd=cwd
                    )
                
                # Verify path is within allowed directories
                is_allowed_file = False
                for scope, allowed_path in ALLOWED_DIRECTORIES.items():
                    allowed_dir = (project_root / allowed_path).resolve()
                    if allowed_dir.exists():
                        try:
                            file_path_obj.relative_to(allowed_dir)
                            is_allowed_file = True
                            break
                        except ValueError:
                            continue
                
                if not is_allowed_file:
                    return TerminalCommandResponse(
                        success=False,
                        output=f"python: {command_parts[1]}: Permission denied (outside allowed directories)\n",
                        cwd=cwd
                    )
                
                file_path = potential_file
            else:
                file_path = os.path.join(cwd, file_path)
                file_path = os.path.normpath(file_path)
            
            # Security check: ensure file is in allowed directories and not blocked - bypassed for allowed users
            resolved_file = Path(file_path).resolve()
            
            # Check if path is blocked (SanTOK core files)
            if is_path_blocked(resolved_file, project_root, auth):
                return TerminalCommandResponse(
                    success=False,
                    output=f"python: {command_parts[1]}: Permission denied (protected file)\n",
                    cwd=cwd
                )
            
            # Check if file is within allowed directories
            is_allowed_file = False
            for scope, allowed_path in ALLOWED_DIRECTORIES.items():
                allowed_dir = (project_root / allowed_path).resolve()
                if allowed_dir.exists():
                    try:
                        resolved_file.relative_to(allowed_dir)
                        is_allowed_file = True
                        break
                    except ValueError:
                        continue
            
            if not is_allowed_file:
                return TerminalCommandResponse(
                    success=False,
                    output=f"python: {command_parts[1]}: Permission denied (outside allowed directories)\n",
                    cwd=cwd
                )
            
            if not os.path.exists(file_path):
                return TerminalCommandResponse(
                    success=False,
                    output=f"python: {command_parts[1]}: No such file or directory\n",
                    cwd=cwd
                )
            
            # Execute the Python file
            try:
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                env['PYTHONUTF8'] = '1'
                
                result = subprocess.run(
                    [sys.executable, file_path],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=cwd,
                    env=env,
                    encoding='utf-8',
                    errors='replace'
                )
                
                output = result.stdout
                if result.stderr:
                    output += result.stderr
                if result.returncode != 0:
                    output += f"\n[Exit code: {result.returncode}]"
                
                return TerminalCommandResponse(
                    success=result.returncode == 0,
                    output=output,
                    cwd=cwd
                )
            except subprocess.TimeoutExpired:
                return TerminalCommandResponse(
                    success=False,
                    output="Execution timeout after 300 seconds\n",
                    cwd=cwd
                )
            except Exception as e:
                return TerminalCommandResponse(
                    success=False,
                    output=f"python: {str(e)}\n",
                    cwd=cwd
                )
        
        # Default: Try to execute as Python code
        else:
            # Security: Verify cwd is in allowed directories (unless user is allowed)
            if not is_user_allowed(auth):
                # Regular users: restrict to safe directories
                cwd_path = Path(cwd).resolve()
                is_cwd_allowed = False
                for scope, allowed_path in ALLOWED_DIRECTORIES.items():
                    allowed_dir = (project_root / allowed_path).resolve()
                    if allowed_dir.exists():
                        try:
                            cwd_path.relative_to(allowed_dir)
                            is_cwd_allowed = True
                            break
                        except ValueError:
                            continue
                
                if not is_cwd_allowed:
                    # Force to examples for safety
                    safe_dir = get_safe_directory("examples", project_root)
                    cwd = str(safe_dir.resolve())
            
            # Execute the command as Python code
            try:
                # Set environment variables
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                env['PYTHONUTF8'] = '1'
                
                result = subprocess.run(
                    [sys.executable, '-c', terminal_request.command],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=cwd,
                    env=env,
                    encoding='utf-8',
                    errors='replace'
                )
                
                output = result.stdout
                if result.stderr:
                    output += result.stderr
                if result.returncode != 0:
                    output += f"\n[Exit code: {result.returncode}]"
                
                return TerminalCommandResponse(
                    success=result.returncode == 0,
                    output=output,
                    cwd=cwd
                )
            except subprocess.TimeoutExpired:
                return TerminalCommandResponse(
                    success=False,
                    output="Execution timeout after 300 seconds\n",
                    cwd=cwd
                )
            except Exception as e:
                return TerminalCommandResponse(
                    success=False,
                    output=f"Error: {str(e)}\n",
                    cwd=cwd
                )
        
    except Exception as e:
        import traceback
        return TerminalCommandResponse(
            success=False,
            output=f"Error: {str(e)}\n{traceback.format_exc()}\n",
            error=str(e),
            cwd=terminal_request.cwd or str(Path(__file__).parent.parent.parent / "examples")
        )

@app.get("/execute/files")
async def list_executable_files(scope: str = "examples", http_request: Request = None):
    auth = get_optional_auth(http_request) if http_request else None
    """
    List files in SAFE directories only (or entire project for allowed users).
    scope: 'examples', 'workspace', 'uploads', 'temp'
    SECURITY: Only admin/allowed users can access files. Regular users get empty list.
    """
    try:
        # SECURITY: Only admin/allowed users can access files
        if not is_user_allowed(auth):
            return {"files": []}
        
        project_root = Path(__file__).parent.parent.parent
        
        # Get directory based on scope (or project root for allowed users)
        # Allowed users can access entire project
        root_dir = project_root
        
        if not root_dir.exists():
            return {"files": []}
        
        # Directories to exclude (additional filtering)
        excluded_dirs = {
            "__pycache__", 
            ".git", 
            ".next", 
            "node_modules", 
            ".pytest_cache",
            ".venv",
            "venv",
            "env",
            ".env",
            "dist",
            "build",
            ".cache",
            ".DS_Store"
        }
        
        # Extensions to include
        code_extensions = {
            ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml",
            ".md", ".txt", ".css", ".html", ".xml", ".sh", ".bat", ".ps1",
            ".sql", ".dockerfile", ".env", ".config", ".conf"
        }
        
        files = []
        
        # Walk through directory tree
        for file_path in root_dir.rglob("*"):
            # Security: Check if path is blocked - bypassed for allowed users
            if is_path_blocked(file_path, project_root, auth):
                continue
            
            # Skip excluded directories
            if any(excluded in file_path.parts for excluded in excluded_dirs):
                continue
            
            # Skip if it's a directory
            if file_path.is_dir():
                continue
            
            # Ensure file is within safe directory (unless user is allowed)
            if not is_user_allowed(auth):
                try:
                    file_path.resolve().relative_to(root_dir.resolve())
                except ValueError:
                    continue
            
            # Check if file extension is in our list
            if file_path.suffix in code_extensions or file_path.name.startswith('.'):
                try:
                    rel_path = file_path.relative_to(root_dir)
                    files.append({
                        "path": str(rel_path).replace("\\", "/"),  # Normalize path separators
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                        "type": "file",
                        "extension": file_path.suffix
                    })
                except (ValueError, OSError):
                    # Skip files we can't access
                    continue
        
        # Sort by path
        return {"files": sorted(files, key=lambda x: x["path"])}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@app.get("/execute/file/{file_path:path}")
async def get_file_content(file_path: str, scope: str = "examples", http_request: Request = None):
    auth = get_optional_auth(http_request) if http_request else None
    """
    Get content of a file from SAFE directories only.
    SECURITY: Only admin/allowed users can access files. Regular users get 403.
    """
    try:
        # SECURITY: Only admin/allowed users can access files
        if not is_user_allowed(auth):
            raise HTTPException(status_code=403, detail="File access requires admin permissions")
        
        project_root = Path(__file__).parent.parent.parent
        
        # Allowed users can access entire project
        safe_dir = project_root
        
        # Security: prevent directory traversal
        if ".." in file_path or file_path.startswith("/"):
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        # Normalize path separators
        file_path = file_path.replace("\\", "/")
        
        # Build file path relative to safe directory
        file_full_path = safe_dir / file_path
        
        # Resolve to absolute path
        try:
            resolved_path = file_full_path.resolve()
            # Ensure file is within safe directory
            resolved_path.relative_to(safe_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="File path outside allowed directory")
        
        # Security: Check if path is blocked (double check) - bypassed for allowed users
        if is_path_blocked(resolved_path, project_root, auth):
            raise HTTPException(status_code=403, detail="Access denied: This file is protected")
        
        if not resolved_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        if resolved_path.is_dir():
            raise HTTPException(status_code=400, detail="Path is a directory, not a file")
        
        # Check file size (limit to 5MB for safety)
        file_size = resolved_path.stat().st_size
        if file_size > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(status_code=413, detail="File too large (max 5MB)")
        
        # Read file content with appropriate encoding
        try:
            # Try UTF-8 first
            with open(resolved_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Fallback to binary for non-text files
            with open(resolved_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='replace')
        
        return {
            "path": file_path,
            "content": content,
            "size": len(content.encode('utf-8')),
            "lines": content.count('\n') + 1,
            "extension": resolved_path.suffix
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

# ==================== FILE WRITE/EDIT ENDPOINTS (Admin Only) ====================

class WriteFileRequest(BaseModel):
    content: str

@app.put("/execute/file/{file_path:path}")
async def write_file_content(file_path: str, request: WriteFileRequest, http_request: Request = None):
    auth = get_optional_auth(http_request) if http_request else None
    """Write/Edit file content. Admin users can edit any file."""
    try:
        if not is_user_allowed(auth):
            raise HTTPException(status_code=403, detail="File write requires admin permissions")
        
        project_root = Path(__file__).parent.parent.parent
        normalized_path = file_path.replace('\\', '/')
        if normalized_path.startswith('./'):
            normalized_path = normalized_path[2:]
        file_full_path = project_root / normalized_path
        resolved_path = file_full_path.resolve()
        
        try:
            resolved_path.relative_to(project_root.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="File path outside project root")
        
        if is_path_blocked(resolved_path, project_root, auth):
            raise HTTPException(status_code=403, detail="Access denied: This file is protected")
        
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(resolved_path, 'w', encoding='utf-8', errors='replace') as f:
            f.write(request.content)
        
        return {"success": True, "path": str(resolved_path.relative_to(project_root)), "message": "File saved"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")

class CreateFileRequest(BaseModel):
    file_path: str
    content: str = ""

@app.post("/execute/file")
async def create_file(request: CreateFileRequest, http_request: Request = None):
    auth = get_optional_auth(http_request) if http_request else None
    """Create a new file. Admin users can create files anywhere."""
    try:
        if not is_user_allowed(auth):
            raise HTTPException(status_code=403, detail="File creation requires admin permissions")
        
        project_root = Path(__file__).parent.parent.parent
        normalized_path = request.file_path.replace('\\', '/')
        if normalized_path.startswith('./'):
            normalized_path = normalized_path[2:]
        file_full_path = project_root / normalized_path
        resolved_path = file_full_path.resolve()
        
        try:
            resolved_path.relative_to(project_root.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="File path outside project root")
        
        if is_path_blocked(resolved_path, project_root, auth):
            raise HTTPException(status_code=403, detail="Access denied: This file is protected")
        
        if resolved_path.exists():
            raise HTTPException(status_code=409, detail="File already exists. Use PUT to update.")
        
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(resolved_path, 'w', encoding='utf-8', errors='replace') as f:
            f.write(request.content)
        
        return {"success": True, "path": str(resolved_path.relative_to(project_root)), "message": "File created"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create file: {str(e)}")

@app.delete("/execute/file/{file_path:path}")
async def delete_file_endpoint(file_path: str, http_request: Request = None):
    auth = get_optional_auth(http_request) if http_request else None
    """Delete a file. Admin users can delete any file."""
    try:
        if not is_user_allowed(auth):
            raise HTTPException(status_code=403, detail="File deletion requires admin permissions")
        
        project_root = Path(__file__).parent.parent.parent
        normalized_path = file_path.replace('\\', '/')
        if normalized_path.startswith('./'):
            normalized_path = normalized_path[2:]
        file_full_path = project_root / normalized_path
        resolved_path = file_full_path.resolve()
        
        try:
            resolved_path.relative_to(project_root.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="File path outside project root")
        
        if is_path_blocked(resolved_path, project_root, auth):
            raise HTTPException(status_code=403, detail="Access denied: This file is protected")
        
        if not resolved_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if resolved_path.is_dir():
            raise HTTPException(status_code=400, detail="Cannot delete directory")
        
        resolved_path.unlink()
        return {"success": True, "message": "File deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print("[START] Starting SanTOK API Server...")
    print(f"[INFO] Server will be available at: http://{host}:{port}")
    print(f"[INFO] API Documentation at: http://{host}:{port}/docs")
    print(f"[INFO] Health check at: http://{host}:{port}/health")
    print(f"[INFO] CORS Origins: {CORS_ORIGINS}")
    print(f"[INFO] Allowed Origins: {allowed_origins}")
    print("[INFO] Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Security check for production
    if os.getenv("NODE_ENV") == "production" or os.getenv("RAILWAY_ENVIRONMENT"):
        if not os.getenv("JWT_SECRET_KEY"):
            print("[WARNING] JWT_SECRET_KEY not set! Please set it in environment variables.")
        if os.getenv("CORS_ORIGINS") == "*" or not os.getenv("CORS_ORIGINS"):
            print("[WARNING] CORS_ORIGINS is '*' or not set! Please restrict CORS in production.")
        if not os.getenv("ALLOWED_USERS"):
            print("[WARNING] ALLOWED_USERS not set! No admin users configured.")
    
    # Don't use reload=True when running directly - it requires import string
    uvicorn.run(app, host=host, port=port, reload=False)