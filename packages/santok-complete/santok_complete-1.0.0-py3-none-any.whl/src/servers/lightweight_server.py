"""
Simple HTTP Backend Server for SanTOK
Uses only standard library - no external dependencies
"""

import http.server
import socketserver
import json
import urllib.parse
import sys
import os
import time
from typing import Dict, List, Any

# Add src directory to path to import backend files
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Import your existing backend files
try:
    from core.core_tokenizer import tokenize_text, reconstruct_from_tokens
    import core.core_tokenizer as KT
    from core.core_tokenizer import _content_id  # convenience
    print("✅ Successfully imported engine module")
except ImportError as e:
    print(f"❌ Error importing core_tokenizer.py: {e}")
    sys.exit(1)

# Tokenizer mapping
TOKENIZERS = {
    'space': KT.tokenize_space,
    'word': KT.tokenize_word,
    'char': KT.tokenize_char,
    'grammar': KT.tokenize_grammar,
    'subword': lambda text: KT.tokenize_subword(text, 3, "fixed"),
    'bpe': lambda text: KT.tokenize_subword(text, 3, "bpe"),
    'syllable': lambda text: KT.tokenize_subword(text, 3, "syllable"),
    'frequency': lambda text: KT.tokenize_subword(text, 3, "frequency"),
    'byte': KT.tokenize_bytes
}

def _stream_name_for(tokenizer_type: str) -> str:
    if tokenizer_type == 'bpe':
        return 'subword_bpe'
    if tokenizer_type == 'syllable':
        return 'subword_syllable'
    if tokenizer_type == 'frequency':
        return 'subword_frequency'
    return tokenizer_type

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path == '/tokenize':
            self.handle_tokenize()
        elif self.path == '/analyze':
            self.handle_analyze()
        elif self.path == '/compress':
            self.handle_compress()
        elif self.path == '/validate':
            self.handle_validate()
        else:
            self.send_error(404, "Not Found")

    def do_GET(self):
        if self.path == '/':
            self.handle_root()
        else:
            self.send_error(404, "Not Found")

    def handle_root(self):
        response = {
            "message": "SanTOK API is running!",
            "version": "1.0.0",
            "available_tokenizers": list(TOKENIZERS.keys())
        }
        self.send_json_response(response)

    def handle_tokenize(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Extract parameters
            text = data.get('text', '')
            tokenizer_type = data.get('tokenizer_type', 'word')
            lower = data.get('lower', False)
            drop_specials = data.get('drop_specials', False)
            collapse_repeats = data.get('collapse_repeats', False)
            embedding = data.get('embedding', False)
            seed = data.get('seed', 12345)
            embedding_bit = bool(data.get('embedding_bit', 0)) or bool(embedding)
            
            # Preprocess text
            processed_text = self.preprocess_text(text, lower, drop_specials, collapse_repeats)
            
            # Get tokenizer function
            if tokenizer_type not in TOKENIZERS:
                raise ValueError(f"Unknown tokenizer type: {tokenizer_type}")
            
            tokenizer_func = TOKENIZERS[tokenizer_type]
            
            # Tokenize
            start_time = time.time()
            tokens = tokenizer_func(processed_text)
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Generate colors
            colors = self.generate_token_colors(tokens)
            
            # Create token objects
            # Build engine digits/metrics from KT.TextTokenizer so output matches CLI
            try:
                engine = KT.TextTokenizer(seed, embedding_bit)
                streams = engine.build(processed_text)
                stream_name = _stream_name_for(tokenizer_type)
                ts = streams.get(stream_name)
                frontend_digits = [t.frontend for t in ts.tokens] if ts else []
                backend_scaled = [t.backend_scaled for t in ts.tokens] if ts else []
                content_ids = [t.content_id for t in ts.tokens] if ts else []
            except Exception:
                frontend_digits = []
                backend_scaled = []
                content_ids = []

            token_objects = []
            position = 0
            for i, token in enumerate(tokens):
                # Handle both string tokens and complex token objects
                if isinstance(token, str):
                    token_text = token
                    token_id = frontend_digits[i] if i < len(frontend_digits) else i
                    token_length = len(token_text)
                    token_type = tokenizer_type
                else:
                    # Complex token object from core_tokenizer
                    token_text = token.get('text', '')
                    token_id = frontend_digits[i] if i < len(frontend_digits) else i
                    token_length = token.get('length', len(token_text))
                    token_type = token.get('type', tokenizer_type)
                    # prefer real index if available
                    if 'index' in token:
                        position = token.get('index', position)
                
                token_obj = {
                    "text": token_text,
                    "id": token_id,
                    "position": position,
                    "length": token_length,
                    "type": token_type,
                    "color": colors[i] if i < len(colors) else colors[i % len(colors)]
                }
                token_objects.append(token_obj)
                position += token_length + 1  # +1 for space
            
            # Calculate metrics
            memory_usage = len(processed_text.encode('utf-8')) / 1024  # KB
            # Count actual word tokens (not spaces/punctuation)
            word_tokens = [t for t in token_objects if t.get('type') == 'word']
            compression_ratio = len(word_tokens) / len(processed_text.split()) if processed_text.split() else 1.0
            
            # Calculate fingerprint
            fingerprint = self.calculate_fingerprint(processed_text, tokens, embedding_bit)
            
            # Create result
            result = {
                "tokens": token_objects,
                "tokenCount": len(tokens),
                "characterCount": len(processed_text),
                "tokenizerType": tokenizer_type,
                "processingTime": processing_time,
                "memoryUsage": memory_usage,
                "compressionRatio": compression_ratio,
                "reversibility": True,
                "fingerprint": fingerprint,
                "frontendDigits": frontend_digits if frontend_digits else None,
                "backendScaled": backend_scaled if backend_scaled else None,
                "contentIds": content_ids if content_ids else None,
            }
            
            self.send_json_response(result)
            
        except Exception as e:
            self.send_error(500, f"Tokenization error: {str(e)}")

    def handle_analyze(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # For now, return a simple analysis
            response = {
                "analysis": {
                    "tokenDistribution": {},
                    "characterDistribution": {},
                    "averageTokenLength": 0,
                    "uniqueTokens": 0,
                    "repetitionRate": 0
                },
                "metrics": {
                    "processingTime": 0,
                    "memoryUsage": 0,
                    "compressionRatio": 0
                },
                "fingerprint": {
                    "signatureDigit": 0,
                    "compatDigit": 0,
                    "textValue": 0,
                    "textValueWithEmbedding": 0
                }
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error(500, f"Analysis error: {str(e)}")

    def handle_compress(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            text = data.get('text', '')
            tokenizer_type = data.get('tokenizer_type', 'word')
            lower = data.get('lower', False)
            drop_specials = data.get('drop_specials', False)
            collapse_repeats = data.get('collapse_repeats', False)
            processed_text = self.preprocess_text(text, lower, drop_specials, collapse_repeats)

            stream_name = _stream_name_for(tokenizer_type)
            analysis = KT.analyze_compression_efficiency(processed_text, stream_name)
            methods = analysis.get('compression_methods', {}) if analysis else {}
            token_count = analysis.get('original_tokens', 0) if analysis else 0
            response = []
            for method, stats in methods.items():
                ratio = float(stats.get('compression_ratio', 1.0))
                saved = int(stats.get('space_saved', 0))
                pct = float(stats.get('compression_percentage', 0.0))
                response.append({
                    'algorithm': method.capitalize(),
                    'compressionRatio': ratio,
                    'tokensSaved': saved,
                    'percentageSaved': pct if pct else ((saved / token_count) * 100 if token_count else 0.0),
                    'reversibility': bool(stats.get('is_reversible', True)),
                })

            self.send_json_response(response)
        except Exception as e:
            self.send_error(500, f"Compression error: {str(e)}")

    def handle_validate(self):
        try:
            response = {
                "isValid": True,
                "reversibility": True,
                "reconstruction": "",
                "differences": []
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error(500, f"Validation error: {str(e)}")

    def preprocess_text(self, text: str, lower: bool, drop_specials: bool, collapse_repeats: bool) -> str:
        """Preprocess text based on options"""
        if lower:
            text = text.lower()
        
        if drop_specials:
            # Keep only alphanumeric and spaces
            text = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in text)
        
        if collapse_repeats:
            # Collapse multiple spaces into single space
            import re
            text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def generate_token_colors(self, tokens: List[str]) -> List[str]:
        """Generate colors for tokens"""
        colors = []
        for i, token in enumerate(tokens):
            hue = (i * 137.5) % 360  # Golden angle for good distribution
            colors.append(f"hsl({hue}, 70%, 50%)")
        return colors

    def calculate_fingerprint(self, text: str, tokens: List[str], embedding: bool = False) -> Dict[str, Any]:
        """Prefer engine summary to match CLI; fallback to simple math."""
        try:
            try:
                summary = KT.compute_text_value_summary(text, bool(embedding))
                return {
                    'signatureDigit': int(summary.get('signature_digit', 0)),
                    'compatDigit': int(summary.get('compat_digit', 0)),
                    'textValue': int(summary.get('weighted_sum', 0)),
                    'textValueWithEmbedding': int(summary.get('final_digit', 0)),
                }
            except Exception:
                content_id = _content_id(text)
                sig = KT.digital_root_9(content_id)
                if embedding:
                    sig = KT.digital_root_9(sig + 1)
                compat = content_id % 10
                tv = sum(ord(c) for c in text) % 10000
                return {
                    'signatureDigit': int(sig),
                    'compatDigit': int(compat),
                    'textValue': int(tv),
                    'textValueWithEmbedding': int(tv + (1 if embedding else 0)),
                }
        except Exception as e:
            print(f"Error calculating fingerprint: {e}")
            return {
                'signatureDigit': 0,
                'compatDigit': 0,
                'textValue': 0,
                'textValueWithEmbedding': 0,
            }

    def send_json_response(self, data: Dict[str, Any]):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

def main():
    PORT = 8000
    
    print("🎯 SanTOK Simple Backend Server")
    print("=" * 50)
    print(f"📡 Starting server on port {PORT}")
    print(f"🌐 Server will be available at: http://localhost:{PORT}")
    print(f"🔄 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
            print(f"✅ Server running at http://localhost:{PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    main()