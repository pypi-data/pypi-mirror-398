"""
Genesis Tokenizer Module

Supports multiple tokenization strategies:
- tiktoken (GPT-4 style BPE)
- sentencepiece (LLaMA style)
- character-level (fallback)
"""

import os
from abc import ABC, abstractmethod
from typing import List, Optional, Union
import json


class BaseTokenizer(ABC):
    """Abstract base class for tokenizers."""
    
    @abstractmethod
    def encode(self, text: str) -> List[int]:
        """Encode text to token ids."""
        pass
    
    @abstractmethod
    def decode(self, ids: List[int]) -> str:
        """Decode token ids to text."""
        pass
    
    @property
    @abstractmethod
    def vocab_size(self) -> int:
        """Return vocabulary size."""
        pass
    
    @property
    @abstractmethod
    def bos_token_id(self) -> Optional[int]:
        """Beginning of sequence token."""
        pass
    
    @property
    @abstractmethod
    def eos_token_id(self) -> Optional[int]:
        """End of sequence token."""
        pass
    
    @property
    @abstractmethod
    def pad_token_id(self) -> Optional[int]:
        """Padding token."""
        pass


class TiktokenWrapper(BaseTokenizer):
    """
    Wrapper for tiktoken (OpenAI's BPE tokenizer).
    
    Recommended for Genesis as it's fast, well-tested, and has
    reasonable vocabulary sizes for small models.
    """
    
    def __init__(
        self,
        encoding_name: str = "cl100k_base",  # GPT-4 encoding
        special_tokens: Optional[dict] = None,
    ):
        try:
            import tiktoken
        except ImportError:
            raise ImportError("tiktoken not installed. Run: pip install tiktoken")
        
        self.encoding = tiktoken.get_encoding(encoding_name)
        self.encoding_name = encoding_name
        
        # Special tokens
        self._special_tokens = special_tokens or {
            "<|bos|>": 100257,
            "<|eos|>": 100258,
            "<|pad|>": 100259,
            "<|im_start|>": 100260,
            "<|im_end|>": 100261,
        }
        
        # Create extended encoding with special tokens
        self.extended_encoding = tiktoken.Encoding(
            name=f"{encoding_name}_extended",
            pat_str=self.encoding._pat_str,
            mergeable_ranks=self.encoding._mergeable_ranks,
            special_tokens={**self.encoding._special_tokens, **self._special_tokens},
        )
    
    def encode(self, text: str, add_special_tokens: bool = False) -> List[int]:
        """Encode text to token ids."""
        ids = self.extended_encoding.encode(text, allowed_special="all")
        if add_special_tokens:
            ids = [self.bos_token_id] + ids + [self.eos_token_id]
        return ids
    
    def decode(self, ids: List[int]) -> str:
        """Decode token ids to text."""
        return self.extended_encoding.decode(ids)
    
    @property
    def vocab_size(self) -> int:
        return self.extended_encoding.n_vocab
    
    @property
    def bos_token_id(self) -> int:
        return self._special_tokens["<|bos|>"]
    
    @property
    def eos_token_id(self) -> int:
        return self._special_tokens["<|eos|>"]
    
    @property
    def pad_token_id(self) -> int:
        return self._special_tokens["<|pad|>"]
    
    @property
    def im_start_id(self) -> int:
        return self._special_tokens["<|im_start|>"]
    
    @property
    def im_end_id(self) -> int:
        return self._special_tokens["<|im_end|>"]


class GPTNeoXTokenizer(BaseTokenizer):
    """
    GPT-NeoX/Pythia tokenizer from EleutherAI.
    
    Advantages over GPT-2:
    - Better whitespace tokenization (good for code)
    - Trained on The Pile (more diverse than WebText)
    - Apache 2.0 license
    - Vocab size: 50,304 (fits in uint16)
    
    Chat tokens registered:
    - <|im_start|>, <|im_end|> for ChatML format
    """
    
    def __init__(self, add_chat_tokens: bool = True):
        try:
            from transformers import AutoTokenizer
        except ImportError:
            raise ImportError("transformers not installed. Run: pip install transformers")
        
        # Load GPT-NeoX tokenizer (same as Pythia)
        self.tokenizer = AutoTokenizer.from_pretrained(
            "EleutherAI/pythia-70m",  # Smallest model, same tokenizer
            trust_remote_code=True,
        )
        
        # IMPORTANTE: pad_token = eos_token (GPT-NeoX não tem pad nativo)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Registrar tokens especiais para ChatML (instruction tuning)
        if add_chat_tokens:
            self._chat_tokens_added = False
            self._special_tokens_map = {
                "<|im_start|>": None,
                "<|im_end|>": None,
            }
    
    def add_chat_tokens(self):
        """
        Adiciona tokens especiais para ChatML.
        DEVE ser chamado ANTES do instruction tuning.
        Retorna: número de tokens adicionados (para resize_embeddings)
        """
        if hasattr(self, '_chat_tokens_added') and self._chat_tokens_added:
            return 0
        
        special_tokens = {
            "additional_special_tokens": [
                "<|im_start|>", "<|im_end|>"
            ]
        }
        num_added = self.tokenizer.add_special_tokens(special_tokens)
        
        # Atualizar mapa de IDs
        self._special_tokens_map["<|im_start|>"] = self.tokenizer.convert_tokens_to_ids("<|im_start|>")
        self._special_tokens_map["<|im_end|>"] = self.tokenizer.convert_tokens_to_ids("<|im_end|>")
        
        self._chat_tokens_added = True
        return num_added
    
    @property
    def vocab_size(self) -> int:
        return len(self.tokenizer)
    
    @property
    def bos_token_id(self) -> int:
        return self.tokenizer.bos_token_id
    
    @property
    def eos_token_id(self) -> int:
        return self.tokenizer.eos_token_id
    
    @property
    def pad_token_id(self) -> int:
        return self.tokenizer.pad_token_id
    
    @property
    def im_start_id(self) -> Optional[int]:
        return self._special_tokens_map.get("<|im_start|>", None)
    
    @property
    def im_end_id(self) -> Optional[int]:
        return self._special_tokens_map.get("<|im_end|>", None)
    
    def encode(self, text: str, add_special_tokens: bool = False) -> List[int]:
        return self.tokenizer.encode(text, add_special_tokens=add_special_tokens)
    
    def encode_batch(self, texts: List[str], add_special_tokens: bool = False) -> List[List[int]]:
        """
        Batch encode multiple texts in parallel.
        
        Uses HuggingFace's native batch encoding which parallelizes via Rust.
        This is ~3-5x faster than sequential encode() calls.
        
        Args:
            texts: List of strings to tokenize
            add_special_tokens: Whether to add BOS/EOS tokens
            
        Returns:
            List of token id lists
        """
        # HuggingFace tokenizer supports batch encoding natively
        # This parallelizes internally via the Rust tokenizers library
        encoded = self.tokenizer(
            texts, 
            add_special_tokens=add_special_tokens,
            padding=False,  # No padding needed for pre-training
            truncation=False,  # No truncation - we handle this ourselves
        )
        return encoded['input_ids']
    
    def decode(self, ids: List[int]) -> str:
        return self.tokenizer.decode(ids, skip_special_tokens=True)
    
    @property
    def vocab_size(self) -> int:
        return len(self.tokenizer)  # Inclui tokens adicionados
    
    @property
    def base_vocab_size(self) -> int:
        return 50304  # Vocab original GPT-NeoX
    
    @property
    def bos_token_id(self) -> int:
        return self.tokenizer.bos_token_id or 0
    
    @property
    def eos_token_id(self) -> int:
        return self.tokenizer.eos_token_id or 0
    
    @property
    def pad_token_id(self) -> int:
        return self.tokenizer.pad_token_id or self.eos_token_id
    
    @property
    def im_start_id(self) -> Optional[int]:
        if hasattr(self, '_special_tokens_map'):
            return self._special_tokens_map.get("<|im_start|>")
        return None
    
    @property
    def im_end_id(self) -> Optional[int]:
        if hasattr(self, '_special_tokens_map'):
            return self._special_tokens_map.get("<|im_end|>")
        return None


class SmallBPETokenizer(BaseTokenizer):
    """
    GPT-2 BPE tokenizer (fallback if GPT-NeoX unavailable).
    
    Uses tiktoken GPT-2 encoding (50,257 vocab).
    """
    
    def __init__(self):
        try:
            import tiktoken
        except ImportError:
            raise ImportError("tiktoken not installed. Run: pip install tiktoken")
        
        # GPT-2 encoding has 50257 tokens
        self.encoding = tiktoken.get_encoding("gpt2")
        
        # Add special tokens
        self._bos_id = 50257
        self._eos_id = 50258
        self._pad_id = 50259
    
    def encode(self, text: str, add_special_tokens: bool = False) -> List[int]:
        # disallowed_special=() permite tokens especiais no texto do FineWeb
        ids = self.encoding.encode(text, disallowed_special=())
        if add_special_tokens:
            ids = [self._bos_id] + ids + [self._eos_id]
        return ids
    
    def decode(self, ids: List[int]) -> str:
        # Filter out special tokens for decoding
        ids = [i for i in ids if i < 50257]
        return self.encoding.decode(ids)
    
    @property
    def vocab_size(self) -> int:
        return 50260  # Base + 3 special tokens
    
    @property
    def bos_token_id(self) -> int:
        return self._bos_id
    
    @property
    def eos_token_id(self) -> int:
        return self._eos_id
    
    @property
    def pad_token_id(self) -> int:
        return self._pad_id


class CharTokenizer(BaseTokenizer):
    """
    Simple character-level tokenizer.
    
    Good for testing and small datasets, but inefficient
    for real training (5-10x more tokens needed).
    """
    
    def __init__(self, vocab: Optional[str] = None):
        if vocab is None:
            # Standard ASCII printable + common Unicode
            self.chars = list(" !\"#$%&'()*+,-./0123456789:;<=>?@"
                            "ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`"
                            "abcdefghijklmnopqrstuvwxyz{|}~\n\t")
        else:
            self.chars = sorted(list(set(vocab)))
        
        self.stoi = {ch: i + 3 for i, ch in enumerate(self.chars)}  # Reserve 0,1,2
        self.itos = {i + 3: ch for i, ch in enumerate(self.chars)}
        
        # Special tokens
        self._pad_id = 0
        self._bos_id = 1
        self._eos_id = 2
    
    def encode(self, text: str, add_special_tokens: bool = False) -> List[int]:
        ids = [self.stoi.get(c, self._pad_id) for c in text]
        if add_special_tokens:
            ids = [self._bos_id] + ids + [self._eos_id]
        return ids
    
    def decode(self, ids: List[int]) -> str:
        return ''.join([self.itos.get(i, '') for i in ids if i > 2])
    
    @property
    def vocab_size(self) -> int:
        return len(self.chars) + 3  # chars + pad/bos/eos
    
    @property
    def bos_token_id(self) -> int:
        return self._bos_id
    
    @property
    def eos_token_id(self) -> int:
        return self._eos_id
    
    @property
    def pad_token_id(self) -> int:
        return self._pad_id
    
    @classmethod
    def from_text(cls, text: str) -> "CharTokenizer":
        """Create tokenizer from text corpus."""
        return cls(vocab=text)
    
    def save(self, path: str):
        """Save tokenizer to file."""
        with open(path, 'w') as f:
            json.dump({'chars': self.chars}, f)
    
    @classmethod
    def load(cls, path: str) -> "CharTokenizer":
        """Load tokenizer from file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(vocab=''.join(data['chars']))


def get_tokenizer(name: str = "neox") -> BaseTokenizer:
    """
    Get a tokenizer by name.
    
    Args:
        name: One of 'neox', 'gpt2', 'gpt4', 'char', or path to saved tokenizer
        
    Returns:
        Tokenizer instance
        
    Default: 'neox' (GPT-NeoX/Pythia tokenizer - recommended)
    """
    if name == "neox" or name == "pythia" or name == "gpt-neox":
        return GPTNeoXTokenizer()
    elif name == "gpt2":
        return SmallBPETokenizer()
    elif name == "gpt4" or name == "cl100k_base":
        return TiktokenWrapper("cl100k_base")
    elif name == "char":
        return CharTokenizer()
    elif os.path.exists(name):
        return CharTokenizer.load(name)
    else:
        raise ValueError(f"Unknown tokenizer: {name}. Options: neox, gpt2, gpt4, char")


# Chat template for instruction tuning
CHAT_TEMPLATE = """<|im_start|>system
{system}<|im_end|>
<|im_start|>user
{user}<|im_end|>
<|im_start|>assistant
{assistant}<|im_end|>"""

CHAT_TEMPLATE_NO_SYSTEM = """<|im_start|>user
{user}<|im_end|>
<|im_start|>assistant
{assistant}<|im_end|>"""


def format_chat(
    user: str,
    assistant: str = "",
    system: str = "You are a helpful assistant.",
    include_system: bool = True,
) -> str:
    """Format a conversation for instruction tuning."""
    if include_system and system:
        return CHAT_TEMPLATE.format(system=system, user=user, assistant=assistant)
    return CHAT_TEMPLATE_NO_SYSTEM.format(user=user, assistant=assistant)
