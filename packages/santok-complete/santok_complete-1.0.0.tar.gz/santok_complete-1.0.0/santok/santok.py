#!/usr/bin/env python3
"""
SanTOK Tokenization Engine - A Complete Text Tokenization Module
Convert your tokenizer into a reusable Python module
"""

from typing import Dict, List, Optional, Any, Union

class TextTokenizationEngine:
    """
    A complete text tokenization system with mathematical analysis
    """
    
    def __init__(
        self, 
        random_seed: int = 12345, 
        embedding_bit: bool = False, 
        normalize_case: bool = True, 
        remove_punctuation: bool = False, 
        collapse_repetitions: int = 0
    ) -> None:
        """
        Initialize the tokenization engine with configuration parameters
        
        Args:
            random_seed: Deterministic seed for reproducible tokenization
            embedding_bit: Enable embedding bit for additional variation in calculations
            normalize_case: Convert input text to lowercase for case-insensitive processing
            remove_punctuation: Strip punctuation and special characters from input
            collapse_repetitions: Collapse repeated character sequences (0=disabled, 1=run-aware, N=collapse to N)
        
        Raises:
            TypeError: If parameter types are incorrect
            ValueError: If parameter values are invalid
        """
        if not isinstance(random_seed, int):
            raise TypeError(f"random_seed must be int, got {type(random_seed).__name__}")
        if not isinstance(embedding_bit, bool):
            raise TypeError(f"embedding_bit must be bool, got {type(embedding_bit).__name__}")
        if not isinstance(normalize_case, bool):
            raise TypeError(f"normalize_case must be bool, got {type(normalize_case).__name__}")
        if not isinstance(remove_punctuation, bool):
            raise TypeError(f"remove_punctuation must be bool, got {type(remove_punctuation).__name__}")
        if not isinstance(collapse_repetitions, int) or collapse_repetitions < 0:
            raise ValueError(f"collapse_repetitions must be non-negative int, got {collapse_repetitions}")
        
        self.random_seed: int = random_seed
        self.embedding_bit: bool = embedding_bit
        self.normalize_case: bool = normalize_case
        self.remove_punctuation: bool = remove_punctuation
        self.collapse_repetitions: int = collapse_repetitions
        
        # Initialize alphabet table for fast lookup
        self._init_alphabetic_table()
    
    def _init_alphabetic_table(self) -> None:
        """Initialize alphabet table for fast alphabetic value lookup"""
        self._alphabet_table: List[int] = []
        for i in range(26):
            self._alphabet_table.append((i % 9) + 1)
    
    def _normalize_case(self, text: str) -> str:
        """Convert text to lowercase for case-insensitive processing"""
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        result = ""
        for char in text:
            if 65 <= ord(char) <= 90:  # A-Z
                result += chr(ord(char) + 32)  # Convert to lowercase
            else:
                result += char
        return result
    
    def _remove_punctuation(self, text: str) -> str:
        """Remove punctuation and special characters, preserve alphanumeric characters and whitespace"""
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        result = ""
        for char in text:
            if (65 <= ord(char) <= 90) or (97 <= ord(char) <= 122) or (48 <= ord(char) <= 57) or char == ' ':
                result += char
        return result
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace by collapsing multiple consecutive spaces into single space"""
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        result = ""
        prev_was_space = False
        for char in text:
            if char == ' ':
                if not prev_was_space:
                    result += char
                    prev_was_space = True
            else:
                result += char
                prev_was_space = False
        return result
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess input text according to configuration parameters
        
        Args:
            text: Raw input text to preprocess
            
        Returns:
            Preprocessed text ready for tokenization
        
        Raises:
            TypeError: If text is not a string
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        
        processed_text = text
        
        if self.normalize_case:
            processed_text = self._normalize_case(processed_text)
        
        if self.remove_punctuation:
            processed_text = self._remove_punctuation(processed_text)
        
        processed_text = self._normalize_whitespace(processed_text)
        
        return processed_text
    
    def _calculate_weighted_sum(self, text: str) -> int:
        """
        Calculate weighted character sum using position-based multiplication
        
        Args:
            text: Input text for weighted sum calculation
            
        Returns:
            Weighted sum value
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        total = 0
        i = 1
        for char in text:
            total += ord(char) * i
            i += 1
        return total
    
    def _compute_digital_root(self, n: int) -> int:
        """
        Compute digital root using 9-centric reduction algorithm
        
        Args:
            n: Integer value to reduce to digital root
            
        Returns:
            Digital root value (1-9)
        """
        if not isinstance(n, int):
            raise TypeError(f"n must be int, got {type(n).__name__}")
        if n <= 0:
            return 9
        return ((n - 1) % 9) + 1
    
    def _compute_hash(self, text: str) -> int:
        """
        Compute hash value using polynomial rolling hash algorithm
        
        Args:
            text: Input text for hash computation
            
        Returns:
            Computed hash value
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        h = 0
        for char in text:
            h = h * 31 + ord(char)
        return h
    
    def _generate_frontend_digit(self, text: str) -> int:
        """
        Generate frontend digit using weighted sum and hash-based methods
        
        Args:
            text: Input text for frontend digit generation
            
        Returns:
            Frontend digit value (1-9)
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        # Method 1: Weighted sum + digital root
        weighted_sum = self._calculate_weighted_sum(text)
        weighted_digit = self._compute_digital_root(weighted_sum)
        
        # Method 2: Hash + modulo 10
        hash_value = self._compute_hash(text)
        hash_digit = hash_value % 10
        
        # Combination: (Weighted_Digit × 9 + Hash_Digit) % 9 + 1
        combined_digit = (weighted_digit * 9 + hash_digit) % 9 + 1
        return combined_digit
    
    def _tokenize_by_whitespace(self, text: str) -> List[str]:
        """
        Tokenize input text by whitespace delimiters
        
        Args:
            text: Input text for whitespace-based tokenization
            
        Returns:
            List of token strings
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        tokens: List[str] = []
        current_token = ""
        
        for char in text:
            if char == ' ':
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            else:
                current_token += char
        
        if current_token:
            tokens.append(current_token)
        
        return tokens
    
    def _tokenize_by_character(self, text: str) -> List[str]:
        """
        Tokenize input text into individual character units
        
        Args:
            text: Input text for character-level tokenization
            
        Returns:
            List of character token strings
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        return list(text)
    
    def _tokenize_by_word_boundary(self, text: str) -> List[str]:
        """
        Tokenize input text by word boundaries (alphabetic characters only)
        
        Args:
            text: Input text for word-based tokenization
            
        Returns:
            List of word token strings
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        tokens: List[str] = []
        current_word = ""
        
        for char in text:
            if (65 <= ord(char) <= 90) or (97 <= ord(char) <= 122):  # A-Z or a-z
                current_word += char
            else:
                if current_word:
                    tokens.append(current_word)
                    current_word = ""
        
        if current_word:
            tokens.append(current_word)
        
        return tokens
    
    def _tokenize_by_subword(self, text: str, chunk_size: int = 3) -> List[str]:
        """
        Tokenize input text into subword units of specified size
        
        Args:
            text: Input text for subword tokenization
            chunk_size: Maximum size of each subword unit
            
        Returns:
            List of subword token strings
        
        Raises:
            ValueError: If chunk_size is less than 1
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        if not isinstance(chunk_size, int) or chunk_size < 1:
            raise ValueError(f"chunk_size must be positive int, got {chunk_size}")
        
        tokens: List[str] = []
        words = self._tokenize_by_word_boundary(text)
        
        for word in words:
            for i in range(0, len(word), chunk_size):
                chunk = word[i:i+chunk_size]
                if chunk:
                    tokens.append(chunk)
        
        return tokens
    
    def _compute_statistical_features(
        self, 
        tokens: List[str], 
        frontend_digits: List[int]
    ) -> Dict[str, Union[int, float]]:
        """
        Compute statistical features from tokenized data and frontend digit values
        
        Args:
            tokens: List of tokenized text units
            frontend_digits: List of corresponding frontend digit values
            
        Returns:
            Dictionary containing computed statistical features
        """
        if not isinstance(tokens, list):
            raise TypeError(f"tokens must be list, got {type(tokens).__name__}")
        if not isinstance(frontend_digits, list):
            raise TypeError(f"frontend_digits must be list, got {type(frontend_digits).__name__}")
        
        if not frontend_digits:
            return {
                'length_factor': 0,
                'balance_index': 0,
                'entropy_index': 0
            }
        
        # Length Factor: Number of tokens modulo 10
        length_factor = len(tokens) % 10
        
        # Balance Index: Mean of frontend digits modulo 10
        mean_value = sum(frontend_digits) / len(frontend_digits)
        balance_index = int(mean_value) % 10
        
        # Entropy Index: Variance of frontend digits modulo 10
        variance = sum((x - mean_value) ** 2 for x in frontend_digits) / len(frontend_digits)
        entropy_index = int(variance) % 10
        
        return {
            'length_factor': length_factor,
            'balance_index': balance_index,
            'entropy_index': entropy_index,
            'mean': mean_value,
            'variance': variance
        }
    
    def tokenize(
        self, 
        text: str, 
        tokenization_method: str = "whitespace", 
        compute_features: bool = True
    ) -> Dict[str, Any]:
        """
        Main tokenization method for text processing
        
        Args:
            text: Input text to tokenize
            tokenization_method: Tokenization strategy ("whitespace", "word", "character", "subword")
            compute_features: Whether to compute and return statistical features
            
        Returns:
            Dictionary containing tokens, frontend digits, and features
        
        Raises:
            TypeError: If text is not a string
            ValueError: If tokenization_method is unsupported
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        if not isinstance(tokenization_method, str):
            raise TypeError(f"tokenization_method must be str, got {type(tokenization_method).__name__}")
        if not isinstance(compute_features, bool):
            raise TypeError(f"compute_features must be bool, got {type(compute_features).__name__}")
        
        # Preprocess input text
        preprocessed_text = self._preprocess_text(text)
        
        # Apply tokenization based on method
        if tokenization_method == "whitespace":
            tokens = self._tokenize_by_whitespace(preprocessed_text)
        elif tokenization_method == "word":
            tokens = self._tokenize_by_word_boundary(preprocessed_text)
        elif tokenization_method == "character":
            tokens = self._tokenize_by_character(preprocessed_text)
        elif tokenization_method == "subword":
            tokens = self._tokenize_by_subword(preprocessed_text)
        else:
            valid_methods = ["whitespace", "word", "character", "subword"]
            raise ValueError(
                f"Unsupported tokenization method: {tokenization_method}. "
                f"Valid methods are: {', '.join(valid_methods)}"
            )
        
        # Generate frontend digits for each token
        frontend_digits: List[int] = [self._generate_frontend_digit(token) for token in tokens]
        
        # Compute statistical features if requested
        features: Optional[Dict[str, Union[int, float]]] = None
        if compute_features:
            features = self._compute_statistical_features(tokens, frontend_digits)
        
        return {
            'original_text': text,
            'preprocessed_text': preprocessed_text,
            'tokens': tokens,
            'frontend_digits': frontend_digits,
            'features': features,
            'tokenization_method': tokenization_method,
            'configuration': {
                'random_seed': self.random_seed,
                'embedding_bit': self.embedding_bit,
                'normalize_case': self.normalize_case,
                'remove_punctuation': self.remove_punctuation,
                'collapse_repetitions': self.collapse_repetitions
            }
        }
    
    def analyze_text(
        self, 
        text: str, 
        tokenization_methods: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze text using multiple tokenization strategies
        
        Args:
            text: Input text for analysis
            tokenization_methods: List of tokenization methods to apply. 
                If None, uses all available methods.
            
        Returns:
            Dictionary containing analysis results for each tokenization method
        
        Raises:
            TypeError: If text is not a string or tokenization_methods is not a list
            ValueError: If any method in tokenization_methods is invalid
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        
        if tokenization_methods is None:
            tokenization_methods = ["whitespace", "word", "character", "subword"]
        elif not isinstance(tokenization_methods, list):
            raise TypeError(f"tokenization_methods must be list or None, got {type(tokenization_methods).__name__}")
        
        analysis_results: Dict[str, Dict[str, Any]] = {}
        for method in tokenization_methods:
            if not isinstance(method, str):
                raise TypeError(f"Each method must be str, got {type(method).__name__}")
            analysis_results[method] = self.tokenize(text, method)
        
        return analysis_results
    
    def generate_summary(self, text: str) -> Dict[str, Any]:
        """
        Generate comprehensive summary statistics for text analysis
        
        Args:
            text: Input text for summary generation
            
        Returns:
            Dictionary containing summary statistics
        
        Raises:
            TypeError: If text is not a string
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        
        tokenization_result = self.tokenize(text, "whitespace")
        
        return {
            'text_length': len(text),
            'token_count': len(tokenization_result['tokens']),
            'unique_tokens': len(set(tokenization_result['tokens'])),
            'frontend_digits': tokenization_result['frontend_digits'],
            'statistical_features': tokenization_result['features']
        }


# Convenience functions for simplified usage
def tokenize_text(text: str, tokenization_method: str = "whitespace") -> Dict[str, Any]:
    """
    Convenience function for text tokenization
    
    Args:
        text: Input text to tokenize
        tokenization_method: Tokenization strategy to apply
        
    Returns:
        Tokenization results
    """
    tokenization_engine = TextTokenizationEngine()
    return tokenization_engine.tokenize(text, tokenization_method)

def analyze_text_comprehensive(text: str) -> Dict[str, Dict[str, Any]]:
    """
    Convenience function for comprehensive text analysis
    
    Args:
        text: Input text for analysis
        
    Returns:
        Comprehensive analysis results
    """
    tokenization_engine = TextTokenizationEngine()
    return tokenization_engine.analyze_text(text)

def generate_text_summary(text: str) -> Dict[str, Any]:
    """
    Convenience function for text summary generation
    
    Args:
        text: Input text for summary generation
        
    Returns:
        Summary statistics
    """
    tokenization_engine = TextTokenizationEngine()
    return tokenization_engine.generate_summary(text)


# Example usage
if __name__ == "__main__":
    # Example usage
    print("SanTOK Tokenization Engine Module Example")
    print("=" * 50)
    
    # Create tokenization engine instance
    tokenization_engine = TextTokenizationEngine(random_seed=12345, embedding_bit=False)
    
    # Test text
    text = "Hello World! This is a test."
    
    # Basic tokenization
    result = tokenization_engine.tokenize(text, "whitespace")
    print(f"Original: {result['original_text']}")
    print(f"Preprocessed: {result['preprocessed_text']}")
    print(f"Tokens: {result['tokens']}")
    print(f"Frontend Digits: {result['frontend_digits']}")
    print(f"Features: {result['features']}")
    
    print("\n" + "=" * 50)
    
    # Multiple tokenization methods
    analysis = tokenization_engine.analyze_text(text)
    for method, result in analysis.items():
        print(f"{method}: {len(result['tokens'])} tokens")
    
    print("\n" + "=" * 50)
    
    # Generate summary
    summary = tokenization_engine.generate_summary(text)
    print(f"Summary: {summary}")