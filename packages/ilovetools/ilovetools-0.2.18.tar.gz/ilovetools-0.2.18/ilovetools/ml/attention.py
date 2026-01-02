"""
Attention Mechanisms for Neural Networks

This module provides various attention mechanisms used in deep learning:
- Scaled Dot-Product Attention
- Multi-Head Attention
- Self-Attention
- Cross-Attention
- Causal/Masked Attention
- Positional Encoding
- Attention Masks

All attention functions support batched operations and are optimized for Transformers.
"""

import numpy as np
from typing import Tuple, Optional, Union


# ============================================================================
# SCALED DOT-PRODUCT ATTENTION
# ============================================================================

def scaled_dot_product_attention(
    query: np.ndarray,
    key: np.ndarray,
    value: np.ndarray,
    mask: Optional[np.ndarray] = None,
    dropout_rate: float = 0.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Scaled Dot-Product Attention
    
    The fundamental attention mechanism used in Transformers.
    
    Formula: Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) * V
    
    Args:
        query: Query tensor of shape (..., seq_len_q, d_k)
        key: Key tensor of shape (..., seq_len_k, d_k)
        value: Value tensor of shape (..., seq_len_v, d_v)
        mask: Optional mask tensor of shape (..., seq_len_q, seq_len_k)
              Values should be 0 (keep) or -inf (mask out)
        dropout_rate: Dropout rate for attention weights (default: 0.0)
        
    Returns:
        Tuple of (attention_output, attention_weights)
        - attention_output: shape (..., seq_len_q, d_v)
        - attention_weights: shape (..., seq_len_q, seq_len_k)
        
    Example:
        >>> # Single head attention
        >>> q = np.random.randn(32, 10, 64)  # (batch, seq_len, d_k)
        >>> k = np.random.randn(32, 10, 64)
        >>> v = np.random.randn(32, 10, 64)
        >>> output, weights = scaled_dot_product_attention(q, k, v)
        >>> print(output.shape)  # (32, 10, 64)
        >>> print(weights.shape)  # (32, 10, 10)
    """
    # Get dimension for scaling
    d_k = query.shape[-1]
    
    # Compute attention scores: Q * K^T / sqrt(d_k)
    scores = np.matmul(query, key.swapaxes(-2, -1)) / np.sqrt(d_k)
    
    # Apply mask if provided
    if mask is not None:
        scores = scores + mask
    
    # Apply softmax to get attention weights
    attention_weights = softmax(scores, axis=-1)
    
    # Apply dropout if specified
    if dropout_rate > 0.0:
        attention_weights = dropout(attention_weights, dropout_rate)
    
    # Compute weighted sum of values
    output = np.matmul(attention_weights, value)
    
    return output, attention_weights


def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    """
    Numerically stable softmax
    
    Args:
        x: Input array
        axis: Axis along which to compute softmax
        
    Returns:
        Softmax probabilities
    """
    # Subtract max for numerical stability
    x_shifted = x - np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x_shifted)
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


def dropout(x: np.ndarray, rate: float) -> np.ndarray:
    """
    Apply dropout (for training)
    
    Args:
        x: Input array
        rate: Dropout rate (probability of dropping)
        
    Returns:
        Array with dropout applied
    """
    if rate <= 0.0 or rate >= 1.0:
        return x
    
    mask = np.random.binomial(1, 1 - rate, size=x.shape)
    return x * mask / (1 - rate)


# ============================================================================
# MULTI-HEAD ATTENTION
# ============================================================================

def multi_head_attention(
    query: np.ndarray,
    key: np.ndarray,
    value: np.ndarray,
    num_heads: int,
    d_model: int,
    mask: Optional[np.ndarray] = None,
    dropout_rate: float = 0.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Multi-Head Attention
    
    Applies multiple attention heads in parallel, allowing the model to attend
    to information from different representation subspaces.
    
    Formula: MultiHead(Q,K,V) = Concat(head_1,...,head_h)W^O
             where head_i = Attention(QW_i^Q, KW_i^K, VW_i^V)
    
    Args:
        query: Query tensor of shape (batch, seq_len_q, d_model)
        key: Key tensor of shape (batch, seq_len_k, d_model)
        value: Value tensor of shape (batch, seq_len_v, d_model)
        num_heads: Number of attention heads
        d_model: Model dimension (must be divisible by num_heads)
        mask: Optional mask tensor
        dropout_rate: Dropout rate for attention weights
        
    Returns:
        Tuple of (output, attention_weights)
        - output: shape (batch, seq_len_q, d_model)
        - attention_weights: shape (batch, num_heads, seq_len_q, seq_len_k)
        
    Example:
        >>> q = np.random.randn(32, 10, 512)  # (batch, seq_len, d_model)
        >>> k = np.random.randn(32, 10, 512)
        >>> v = np.random.randn(32, 10, 512)
        >>> output, weights = multi_head_attention(q, k, v, num_heads=8, d_model=512)
        >>> print(output.shape)  # (32, 10, 512)
        >>> print(weights.shape)  # (32, 8, 10, 10)
    """
    if d_model % num_heads != 0:
        raise ValueError(f"d_model ({d_model}) must be divisible by num_heads ({num_heads})")
    
    batch_size = query.shape[0]
    seq_len_q = query.shape[1]
    seq_len_k = key.shape[1]
    
    # Dimension per head
    d_k = d_model // num_heads
    
    # Initialize projection weights (in practice, these would be learned)
    W_q = np.random.randn(d_model, d_model) * 0.01
    W_k = np.random.randn(d_model, d_model) * 0.01
    W_v = np.random.randn(d_model, d_model) * 0.01
    W_o = np.random.randn(d_model, d_model) * 0.01
    
    # Linear projections
    Q = np.matmul(query, W_q)  # (batch, seq_len_q, d_model)
    K = np.matmul(key, W_k)    # (batch, seq_len_k, d_model)
    V = np.matmul(value, W_v)  # (batch, seq_len_v, d_model)
    
    # Split into multiple heads
    # Reshape: (batch, seq_len, d_model) -> (batch, seq_len, num_heads, d_k)
    Q = Q.reshape(batch_size, seq_len_q, num_heads, d_k)
    K = K.reshape(batch_size, seq_len_k, num_heads, d_k)
    V = V.reshape(batch_size, seq_len_k, num_heads, d_k)
    
    # Transpose: (batch, seq_len, num_heads, d_k) -> (batch, num_heads, seq_len, d_k)
    Q = Q.transpose(0, 2, 1, 3)
    K = K.transpose(0, 2, 1, 3)
    V = V.transpose(0, 2, 1, 3)
    
    # Apply scaled dot-product attention for each head
    attention_output, attention_weights = scaled_dot_product_attention(
        Q, K, V, mask=mask, dropout_rate=dropout_rate
    )
    
    # Concatenate heads
    # Transpose back: (batch, num_heads, seq_len_q, d_k) -> (batch, seq_len_q, num_heads, d_k)
    attention_output = attention_output.transpose(0, 2, 1, 3)
    
    # Reshape: (batch, seq_len_q, num_heads, d_k) -> (batch, seq_len_q, d_model)
    attention_output = attention_output.reshape(batch_size, seq_len_q, d_model)
    
    # Final linear projection
    output = np.matmul(attention_output, W_o)
    
    return output, attention_weights


# ============================================================================
# SELF-ATTENTION
# ============================================================================

def self_attention(
    x: np.ndarray,
    d_model: int,
    mask: Optional[np.ndarray] = None,
    dropout_rate: float = 0.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Self-Attention
    
    Special case where query, key, and value all come from the same input.
    Used in BERT and GPT.
    
    Args:
        x: Input tensor of shape (batch, seq_len, d_model)
        d_model: Model dimension
        mask: Optional mask tensor
        dropout_rate: Dropout rate
        
    Returns:
        Tuple of (output, attention_weights)
        
    Example:
        >>> x = np.random.randn(32, 10, 512)
        >>> output, weights = self_attention(x, d_model=512)
        >>> print(output.shape)  # (32, 10, 512)
    """
    # Use same input for Q, K, V
    return scaled_dot_product_attention(x, x, x, mask=mask, dropout_rate=dropout_rate)


def multi_head_self_attention(
    x: np.ndarray,
    num_heads: int,
    d_model: int,
    mask: Optional[np.ndarray] = None,
    dropout_rate: float = 0.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Multi-Head Self-Attention
    
    Combines multi-head attention with self-attention.
    Standard building block in Transformers.
    
    Args:
        x: Input tensor of shape (batch, seq_len, d_model)
        num_heads: Number of attention heads
        d_model: Model dimension
        mask: Optional mask tensor
        dropout_rate: Dropout rate
        
    Returns:
        Tuple of (output, attention_weights)
        
    Example:
        >>> x = np.random.randn(32, 10, 512)
        >>> output, weights = multi_head_self_attention(x, num_heads=8, d_model=512)
        >>> print(output.shape)  # (32, 10, 512)
    """
    return multi_head_attention(x, x, x, num_heads, d_model, mask, dropout_rate)


# ============================================================================
# CROSS-ATTENTION
# ============================================================================

def cross_attention(
    query: np.ndarray,
    context: np.ndarray,
    d_model: int,
    mask: Optional[np.ndarray] = None,
    dropout_rate: float = 0.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Cross-Attention
    
    Attention between two different sequences. Query comes from one sequence,
    while key and value come from another (context).
    
    Used in encoder-decoder architectures and multimodal models.
    
    Args:
        query: Query tensor of shape (batch, seq_len_q, d_model)
        context: Context tensor of shape (batch, seq_len_c, d_model)
        d_model: Model dimension
        mask: Optional mask tensor
        dropout_rate: Dropout rate
        
    Returns:
        Tuple of (output, attention_weights)
        
    Example:
        >>> # Decoder attending to encoder
        >>> decoder_out = np.random.randn(32, 10, 512)
        >>> encoder_out = np.random.randn(32, 20, 512)
        >>> output, weights = cross_attention(decoder_out, encoder_out, d_model=512)
        >>> print(output.shape)  # (32, 10, 512)
        >>> print(weights.shape)  # (32, 10, 20)
    """
    # Query from first sequence, Key and Value from context
    return scaled_dot_product_attention(
        query, context, context, mask=mask, dropout_rate=dropout_rate
    )


# ============================================================================
# ATTENTION MASKS
# ============================================================================

def create_padding_mask(seq: np.ndarray, pad_token: int = 0) -> np.ndarray:
    """
    Create padding mask for sequences with padding tokens
    
    Args:
        seq: Sequence tensor of shape (batch, seq_len)
        pad_token: Token ID used for padding (default: 0)
        
    Returns:
        Mask tensor of shape (batch, 1, 1, seq_len)
        Values are 0 (keep) or -inf (mask out)
        
    Example:
        >>> seq = np.array([[1, 2, 3, 0, 0], [1, 2, 0, 0, 0]])
        >>> mask = create_padding_mask(seq, pad_token=0)
        >>> print(mask.shape)  # (2, 1, 1, 5)
    """
    # Create mask: 1 for padding tokens, 0 for real tokens
    mask = (seq == pad_token).astype(np.float32)
    
    # Add dimensions for broadcasting
    # (batch, seq_len) -> (batch, 1, 1, seq_len)
    mask = mask[:, np.newaxis, np.newaxis, :]
    
    # Convert to -inf for masked positions
    mask = mask * -1e9
    
    return mask


def create_causal_mask(seq_len: int) -> np.ndarray:
    """
    Create causal (look-ahead) mask for autoregressive models
    
    Prevents positions from attending to subsequent positions.
    Used in GPT and other autoregressive models.
    
    Args:
        seq_len: Sequence length
        
    Returns:
        Mask tensor of shape (1, 1, seq_len, seq_len)
        Upper triangle is -inf (masked), lower triangle is 0 (keep)
        
    Example:
        >>> mask = create_causal_mask(5)
        >>> print(mask.shape)  # (1, 1, 5, 5)
        >>> # Position i can only attend to positions <= i
    """
    # Create upper triangular matrix of 1s
    mask = np.triu(np.ones((seq_len, seq_len)), k=1)
    
    # Add batch and head dimensions
    mask = mask[np.newaxis, np.newaxis, :, :]
    
    # Convert to -inf for masked positions
    mask = mask * -1e9
    
    return mask


def create_look_ahead_mask(seq_len: int) -> np.ndarray:
    """
    Alias for create_causal_mask
    
    Args:
        seq_len: Sequence length
        
    Returns:
        Causal mask tensor
    """
    return create_causal_mask(seq_len)


# ============================================================================
# POSITIONAL ENCODING
# ============================================================================

def positional_encoding(
    seq_len: int,
    d_model: int,
    n: int = 10000
) -> np.ndarray:
    """
    Sinusoidal Positional Encoding
    
    Adds position information to embeddings using sine and cosine functions.
    Used in original Transformer paper.
    
    Formula:
        PE(pos, 2i) = sin(pos / n^(2i/d_model))
        PE(pos, 2i+1) = cos(pos / n^(2i/d_model))
    
    Args:
        seq_len: Maximum sequence length
        d_model: Model dimension (embedding size)
        n: Base for positional encoding (default: 10000)
        
    Returns:
        Positional encoding tensor of shape (seq_len, d_model)
        
    Example:
        >>> pos_enc = positional_encoding(seq_len=100, d_model=512)
        >>> print(pos_enc.shape)  # (100, 512)
        >>> 
        >>> # Add to embeddings
        >>> embeddings = np.random.randn(32, 100, 512)
        >>> embeddings_with_pos = embeddings + pos_enc
    """
    # Create position indices
    position = np.arange(seq_len)[:, np.newaxis]  # (seq_len, 1)
    
    # Create dimension indices
    div_term = np.exp(np.arange(0, d_model, 2) * -(np.log(n) / d_model))
    
    # Initialize positional encoding matrix
    pos_encoding = np.zeros((seq_len, d_model))
    
    # Apply sine to even indices
    pos_encoding[:, 0::2] = np.sin(position * div_term)
    
    # Apply cosine to odd indices
    pos_encoding[:, 1::2] = np.cos(position * div_term)
    
    return pos_encoding


def learned_positional_encoding(
    seq_len: int,
    d_model: int
) -> np.ndarray:
    """
    Learned Positional Encoding
    
    Alternative to sinusoidal encoding where positions are learned parameters.
    Used in BERT and GPT.
    
    Args:
        seq_len: Maximum sequence length
        d_model: Model dimension
        
    Returns:
        Initialized positional encoding tensor of shape (seq_len, d_model)
        
    Example:
        >>> pos_enc = learned_positional_encoding(seq_len=512, d_model=768)
        >>> print(pos_enc.shape)  # (512, 768)
    """
    # Initialize with small random values (would be learned during training)
    return np.random.randn(seq_len, d_model) * 0.01


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def attention_score_visualization(
    attention_weights: np.ndarray,
    tokens: Optional[list] = None
) -> dict:
    """
    Prepare attention weights for visualization
    
    Args:
        attention_weights: Attention weights of shape (batch, num_heads, seq_len, seq_len)
                          or (batch, seq_len, seq_len)
        tokens: Optional list of token strings for labeling
        
    Returns:
        Dictionary with visualization data
        
    Example:
        >>> weights = np.random.rand(1, 8, 10, 10)
        >>> tokens = ['The', 'cat', 'sat', 'on', 'the', 'mat', '.']
        >>> viz_data = attention_score_visualization(weights, tokens)
    """
    # Average across heads if multi-head
    if attention_weights.ndim == 4:
        avg_weights = np.mean(attention_weights, axis=1)  # (batch, seq_len, seq_len)
    else:
        avg_weights = attention_weights
    
    # Take first batch
    weights_2d = avg_weights[0]
    
    return {
        'weights': weights_2d,
        'tokens': tokens,
        'shape': weights_2d.shape,
        'max_attention': np.max(weights_2d),
        'min_attention': np.min(weights_2d)
    }


# Aliases for convenience
sdp_attention = scaled_dot_product_attention
mha = multi_head_attention
self_attn = self_attention
cross_attn = cross_attention
pos_encoding = positional_encoding
causal_mask = create_causal_mask
padding_mask = create_padding_mask
