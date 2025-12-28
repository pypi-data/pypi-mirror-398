"""
Vocabulary Adapter for SanTOK → Pretrained Model Integration

CRITICAL ISSUE ADDRESSED:
SanTOK generates its own token IDs (UIDs, frontend digits, backend numbers) that are
NOT compatible with pretrained transformer model vocabularies. Pretrained models have
embedding layers that map their own vocabulary IDs to embeddings.

This module provides:
1. Vocabulary mapping from SanTOK tokens (text strings) to standard model vocabularies
2. Adapter functions to convert SanTOK tokenization results to model-compatible IDs
3. Integration utilities for HuggingFace transformers
"""

from typing import List, Dict, Optional, Union, Tuple
import warnings

try:
    from transformers import AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    warnings.warn("transformers library not available. Install with: pip install transformers")


class VocabularyAdapter:
    """
    Adapter to map SanTOK tokens to pretrained model vocabulary IDs.
    
    This solves the critical issue where SanTOK's internal IDs don't match
    pretrained model vocabularies.
    """
    
    def __init__(self, model_name: str = "bert-base-uncased", use_fast: bool = True):
        """
        Initialize vocabulary adapter for a specific pretrained model.
        
        Args:
            model_name: HuggingFace model identifier (e.g., "bert-base-uncased", "gpt2", "t5-base")
            use_fast: Whether to use fast tokenizer if available
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "transformers library required. Install with: pip install transformers"
            )
        
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=use_fast)
        self.vocab_size = len(self.tokenizer.vocab) if hasattr(self.tokenizer, 'vocab') else len(self.tokenizer.get_vocab())
        
    def map_santok_tokens_to_model_ids(
        self, 
        santok_tokens: List[Union[str, Dict]]
    ) -> Dict[str, Union[List[int], List[str], Dict]]:
        """
        Map SanTOK token strings to model vocabulary IDs.
        
        Args:
            santok_tokens: List of SanTOK tokens. Can be:
                - List of strings: ["hello", "world"]
                - List of dicts with "text" key: [{"text": "hello"}, {"text": "world"}]
        
        Returns:
            Dictionary with:
                - "input_ids": List of model vocabulary IDs
                - "tokens": List of token strings (may differ from input due to subword tokenization)
                - "attention_mask": Attention mask (all 1s for standard tokens)
                - "mapping": Mapping from SanTOK token indices to model token indices
        """
        # Extract token texts from various formats
        token_texts = []
        for token in santok_tokens:
            if isinstance(token, dict):
                token_texts.append(token.get("text", str(token)))
            else:
                token_texts.append(str(token))
        
        # Join tokens back into text (models expect text input)
        # Note: This may lose some information, but it's necessary for model compatibility
        text = " ".join(token_texts)
        
        # Tokenize using the model's tokenizer
        encoded = self.tokenizer(
            text,
            return_tensors=None,  # Return Python lists
            add_special_tokens=True,
            padding=False,
            truncation=False
        )
        
        # Create mapping: SanTOK token index -> Model token indices (for subword tokens)
        # This is approximate since model tokenizer may split tokens differently
        mapping = self._create_token_mapping(token_texts, encoded["input_ids"])
        
        return {
            "input_ids": encoded["input_ids"],
            "tokens": encoded.tokens() if hasattr(encoded, 'tokens') else self.tokenizer.convert_ids_to_tokens(encoded["input_ids"]),
            "attention_mask": encoded.get("attention_mask", [1] * len(encoded["input_ids"])),
            "mapping": mapping,
            "model_name": self.model_name,
            "vocab_size": self.vocab_size
        }
    
    def _create_token_mapping(
        self, 
        santok_tokens: List[str], 
        model_ids: List[int]
    ) -> Dict[int, List[int]]:
        """
        Create approximate mapping from SanTOK token indices to model token indices.
        
        This handles cases where model tokenizer splits tokens into subwords.
        """
        # Reconstruct text from SanTOK tokens
        santok_text = " ".join(santok_tokens)
        
        # Tokenize again to get alignment
        model_tokens = self.tokenizer.convert_ids_to_tokens(model_ids)
        model_text = self.tokenizer.convert_tokens_to_string(model_tokens)
        
        # Simple alignment: map based on character positions
        # This is approximate and may not be perfect for all cases
        mapping = {}
        santok_pos = 0
        
        for santok_idx, santok_token in enumerate(santok_tokens):
            token_start = santok_pos
            token_end = santok_pos + len(santok_token)
            
            # Find which model tokens correspond to this SanTOK token
            model_indices = []
            char_pos = 0
            
            for model_idx, model_token in enumerate(model_tokens):
                # Skip special tokens for alignment
                if model_token in self.tokenizer.all_special_tokens:
                    continue
                
                # Approximate alignment
                if char_pos >= token_start and char_pos < token_end:
                    model_indices.append(model_idx)
                
                # Advance character position (approximate)
                clean_token = model_token.replace("##", "").replace("▁", "")
                char_pos += len(clean_token) + 1  # +1 for space
            
            mapping[santok_idx] = model_indices if model_indices else [0]  # Default to first token
        
        return mapping
    
    def get_model_embedding_layer_info(self) -> Dict:
        """
        Get information about the model's embedding layer.
        
        Returns:
            Dictionary with embedding layer metadata
        """
        return {
            "model_name": self.model_name,
            "vocab_size": self.vocab_size,
            "special_tokens": self.tokenizer.special_tokens_map,
            "pad_token_id": self.tokenizer.pad_token_id,
            "unk_token_id": self.tokenizer.unk_token_id,
            "mask_token_id": getattr(self.tokenizer, 'mask_token_id', None),
            "cls_token_id": getattr(self.tokenizer, 'cls_token_id', None),
            "sep_token_id": getattr(self.tokenizer, 'sep_token_id', None),
        }


class SanTOKToModelConverter:
    """
    High-level converter that takes SanTOK tokenization results and converts them
    for use with pretrained models.
    """
    
    def __init__(self, model_name: str = "bert-base-uncased"):
        """
        Initialize converter.
        
        Args:
            model_name: HuggingFace model identifier
        """
        self.adapter = VocabularyAdapter(model_name)
        self.model_name = model_name
    
    def convert_santok_result(
        self, 
        santok_result: Dict,
        tokenizer_type: str = "word"
    ) -> Dict:
        """
        Convert SanTOK tokenization result to model-compatible format.
        
        Args:
            santok_result: Result from SanTOK tokenization (from run_once or TextTokenizer.build)
            tokenizer_type: Which tokenization strategy to use (e.g., "word", "char", "subword_bpe")
        
        Returns:
            Dictionary with model-compatible token IDs and metadata
        """
        if tokenizer_type not in santok_result:
            raise ValueError(
                f"Tokenization type '{tokenizer_type}' not found in SanTOK result. "
                f"Available: {list(santok_result.keys())}"
            )
        
        # Extract tokens from SanTOK result
        tokens_data = santok_result[tokenizer_type]
        
        # Get token texts
        if "records" in tokens_data:
            tokens = [rec["text"] for rec in tokens_data["records"]]
        else:
            raise ValueError("SanTOK result must contain 'records' with token texts")
        
        # Map to model vocabulary
        model_encoded = self.adapter.map_santok_tokens_to_model_ids(tokens)
        
        # Preserve SanTOK metadata
        return {
            "model_input_ids": model_encoded["input_ids"],
            "model_tokens": model_encoded["tokens"],
            "model_attention_mask": model_encoded["attention_mask"],
            "santok_tokens": tokens,
            "santok_frontend_digits": tokens_data.get("digits", []),
            "santok_backend_scaled": tokens_data.get("scaled", []),
            "santok_tokenizer_type": tokenizer_type,
            "token_mapping": model_encoded["mapping"],
            "model_info": self.adapter.get_model_embedding_layer_info(),
            "vocab_size": model_encoded["vocab_size"]
        }
    
    def prepare_for_inference(
        self, 
        santok_result: Dict,
        tokenizer_type: str = "word",
        return_tensors: str = "pt"
    ) -> Dict:
        """
        Prepare SanTOK result for model inference (returns tensors if transformers available).
        
        Args:
            santok_result: SanTOK tokenization result
            tokenizer_type: Tokenization strategy to use
            return_tensors: "pt" for PyTorch, "tf" for TensorFlow, None for lists
        
        Returns:
            Dictionary ready for model(**inputs)
        """
        converted = self.convert_santok_result(santok_result, tokenizer_type)
        
        if return_tensors and return_tensors != "np":
            try:
                import torch
                if return_tensors == "pt":
                    return {
                        "input_ids": torch.tensor([converted["model_input_ids"]]),
                        "attention_mask": torch.tensor([converted["model_attention_mask"]])
                    }
            except ImportError:
                warnings.warn("PyTorch not available, returning lists instead of tensors")
        
        return {
            "input_ids": converted["model_input_ids"],
            "attention_mask": converted["model_attention_mask"]
        }


def create_vocabulary_adapter(model_name: str = "bert-base-uncased") -> VocabularyAdapter:
    """
    Factory function to create a vocabulary adapter.
    
    Args:
        model_name: HuggingFace model identifier
    
    Returns:
        VocabularyAdapter instance
    """
    return VocabularyAdapter(model_name)


def quick_convert_santok_to_model_ids(
    santok_tokens: List[Union[str, Dict]],
    model_name: str = "bert-base-uncased"
) -> List[int]:
    """
    Quick conversion function: SanTOK tokens -> Model vocabulary IDs.
    
    Args:
        santok_tokens: List of SanTOK token strings or dicts with "text" key
        model_name: HuggingFace model identifier
    
    Returns:
        List of model vocabulary IDs
    """
    adapter = VocabularyAdapter(model_name)
    result = adapter.map_santok_tokens_to_model_ids(santok_tokens)
    return result["input_ids"]