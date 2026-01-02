"""
Tests for attention mechanisms module
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml.attention import (
    # Core attention functions
    scaled_dot_product_attention,
    multi_head_attention,
    self_attention,
    multi_head_self_attention,
    cross_attention,
    # Masks
    create_padding_mask,
    create_causal_mask,
    create_look_ahead_mask,
    # Positional encoding
    positional_encoding,
    learned_positional_encoding,
    # Utilities
    attention_score_visualization,
    softmax,
    dropout,
    # Aliases
    sdp_attention,
    mha,
    self_attn,
    cross_attn,
    pos_encoding,
    causal_mask,
    padding_mask,
)


def test_scaled_dot_product_attention():
    """Test Scaled Dot-Product Attention"""
    print("Testing scaled_dot_product_attention...")
    
    batch_size = 32
    seq_len = 10
    d_k = 64
    
    q = np.random.randn(batch_size, seq_len, d_k)
    k = np.random.randn(batch_size, seq_len, d_k)
    v = np.random.randn(batch_size, seq_len, d_k)
    
    output, weights = scaled_dot_product_attention(q, k, v)
    
    assert output.shape == (batch_size, seq_len, d_k), "Output shape incorrect"
    assert weights.shape == (batch_size, seq_len, seq_len), "Weights shape incorrect"
    
    # Check attention weights sum to 1
    weights_sum = np.sum(weights, axis=-1)
    assert np.allclose(weights_sum, 1.0), "Attention weights should sum to 1"
    
    print("✓ scaled_dot_product_attention passed")


def test_scaled_dot_product_attention_with_mask():
    """Test Scaled Dot-Product Attention with mask"""
    print("Testing scaled_dot_product_attention with mask...")
    
    batch_size = 32
    seq_len = 10
    d_k = 64
    
    q = np.random.randn(batch_size, seq_len, d_k)
    k = np.random.randn(batch_size, seq_len, d_k)
    v = np.random.randn(batch_size, seq_len, d_k)
    
    # Create mask (mask out last 3 positions)
    mask = np.zeros((batch_size, seq_len, seq_len))
    mask[:, :, -3:] = -1e9
    
    output, weights = scaled_dot_product_attention(q, k, v, mask=mask)
    
    assert output.shape == (batch_size, seq_len, d_k), "Output shape incorrect"
    
    # Check that masked positions have near-zero attention
    assert np.allclose(weights[:, :, -3:], 0.0, atol=1e-5), "Masked positions should have zero attention"
    
    print("✓ scaled_dot_product_attention with mask passed")


def test_multi_head_attention():
    """Test Multi-Head Attention"""
    print("Testing multi_head_attention...")
    
    batch_size = 32
    seq_len = 10
    d_model = 512
    num_heads = 8
    
    q = np.random.randn(batch_size, seq_len, d_model)
    k = np.random.randn(batch_size, seq_len, d_model)
    v = np.random.randn(batch_size, seq_len, d_model)
    
    output, weights = multi_head_attention(q, k, v, num_heads, d_model)
    
    assert output.shape == (batch_size, seq_len, d_model), "Output shape incorrect"
    assert weights.shape == (batch_size, num_heads, seq_len, seq_len), "Weights shape incorrect"
    
    print("✓ multi_head_attention passed")


def test_multi_head_attention_invalid_heads():
    """Test Multi-Head Attention with invalid number of heads"""
    print("Testing multi_head_attention with invalid heads...")
    
    batch_size = 32
    seq_len = 10
    d_model = 512
    num_heads = 7  # Not divisible
    
    q = np.random.randn(batch_size, seq_len, d_model)
    k = np.random.randn(batch_size, seq_len, d_model)
    v = np.random.randn(batch_size, seq_len, d_model)
    
    try:
        output, weights = multi_head_attention(q, k, v, num_heads, d_model)
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "divisible" in str(e).lower()
    
    print("✓ multi_head_attention invalid heads passed")


def test_self_attention():
    """Test Self-Attention"""
    print("Testing self_attention...")
    
    batch_size = 32
    seq_len = 10
    d_model = 512
    
    x = np.random.randn(batch_size, seq_len, d_model)
    
    output, weights = self_attention(x, d_model)
    
    assert output.shape == x.shape, "Output shape should match input"
    assert weights.shape == (batch_size, seq_len, seq_len), "Weights shape incorrect"
    
    print("✓ self_attention passed")


def test_multi_head_self_attention():
    """Test Multi-Head Self-Attention"""
    print("Testing multi_head_self_attention...")
    
    batch_size = 32
    seq_len = 10
    d_model = 512
    num_heads = 8
    
    x = np.random.randn(batch_size, seq_len, d_model)
    
    output, weights = multi_head_self_attention(x, num_heads, d_model)
    
    assert output.shape == x.shape, "Output shape should match input"
    assert weights.shape == (batch_size, num_heads, seq_len, seq_len), "Weights shape incorrect"
    
    print("✓ multi_head_self_attention passed")


def test_cross_attention():
    """Test Cross-Attention"""
    print("Testing cross_attention...")
    
    batch_size = 32
    seq_len_q = 10
    seq_len_c = 20
    d_model = 512
    
    query = np.random.randn(batch_size, seq_len_q, d_model)
    context = np.random.randn(batch_size, seq_len_c, d_model)
    
    output, weights = cross_attention(query, context, d_model)
    
    assert output.shape == (batch_size, seq_len_q, d_model), "Output shape incorrect"
    assert weights.shape == (batch_size, seq_len_q, seq_len_c), "Weights shape incorrect"
    
    print("✓ cross_attention passed")


def test_create_padding_mask():
    """Test padding mask creation"""
    print("Testing create_padding_mask...")
    
    seq = np.array([[1, 2, 3, 0, 0], [1, 2, 0, 0, 0]])
    mask = create_padding_mask(seq, pad_token=0)
    
    assert mask.shape == (2, 1, 1, 5), "Mask shape incorrect"
    
    # Check that padding positions are masked
    assert mask[0, 0, 0, 3] < 0, "Padding position should be masked"
    assert mask[0, 0, 0, 4] < 0, "Padding position should be masked"
    assert mask[0, 0, 0, 0] == 0, "Non-padding position should not be masked"
    
    print("✓ create_padding_mask passed")


def test_create_causal_mask():
    """Test causal mask creation"""
    print("Testing create_causal_mask...")
    
    seq_len = 5
    mask = create_causal_mask(seq_len)
    
    assert mask.shape == (1, 1, seq_len, seq_len), "Mask shape incorrect"
    
    # Check that upper triangle is masked
    assert mask[0, 0, 0, 1] < 0, "Future position should be masked"
    assert mask[0, 0, 0, 0] == 0, "Current position should not be masked"
    assert mask[0, 0, 2, 1] == 0, "Past position should not be masked"
    
    print("✓ create_causal_mask passed")


def test_create_look_ahead_mask():
    """Test look-ahead mask (alias for causal mask)"""
    print("Testing create_look_ahead_mask...")
    
    seq_len = 5
    mask = create_look_ahead_mask(seq_len)
    
    assert mask.shape == (1, 1, seq_len, seq_len), "Mask shape incorrect"
    
    print("✓ create_look_ahead_mask passed")


def test_positional_encoding():
    """Test sinusoidal positional encoding"""
    print("Testing positional_encoding...")
    
    seq_len = 100
    d_model = 512
    
    pos_enc = positional_encoding(seq_len, d_model)
    
    assert pos_enc.shape == (seq_len, d_model), "Shape incorrect"
    
    # Check that values are bounded
    assert np.all(np.abs(pos_enc) <= 1.0), "Values should be between -1 and 1"
    
    # Check that even indices use sine, odd use cosine
    # (This is implicit in the implementation)
    
    print("✓ positional_encoding passed")


def test_learned_positional_encoding():
    """Test learned positional encoding"""
    print("Testing learned_positional_encoding...")
    
    seq_len = 512
    d_model = 768
    
    pos_enc = learned_positional_encoding(seq_len, d_model)
    
    assert pos_enc.shape == (seq_len, d_model), "Shape incorrect"
    
    print("✓ learned_positional_encoding passed")


def test_softmax():
    """Test softmax function"""
    print("Testing softmax...")
    
    x = np.random.randn(32, 10, 10)
    
    result = softmax(x, axis=-1)
    
    assert result.shape == x.shape, "Shape should be preserved"
    
    # Check that values sum to 1 along last axis
    sums = np.sum(result, axis=-1)
    assert np.allclose(sums, 1.0), "Softmax should sum to 1"
    
    # Check that all values are positive
    assert np.all(result >= 0), "Softmax values should be non-negative"
    
    print("✓ softmax passed")


def test_dropout():
    """Test dropout function"""
    print("Testing dropout...")
    
    x = np.ones((100, 100))
    
    # Test with dropout rate 0.5
    result = dropout(x, rate=0.5)
    
    assert result.shape == x.shape, "Shape should be preserved"
    
    # Check that some values are zeroed out
    num_zeros = np.sum(result == 0)
    assert num_zeros > 0, "Some values should be dropped"
    
    # Test with dropout rate 0 (no dropout)
    result_no_dropout = dropout(x, rate=0.0)
    assert np.allclose(result_no_dropout, x), "No dropout should preserve values"
    
    print("✓ dropout passed")


def test_attention_score_visualization():
    """Test attention score visualization utility"""
    print("Testing attention_score_visualization...")
    
    # Multi-head attention weights
    weights = np.random.rand(1, 8, 10, 10)
    tokens = ['The', 'cat', 'sat', 'on', 'the', 'mat', '.']
    
    viz_data = attention_score_visualization(weights, tokens)
    
    assert 'weights' in viz_data, "Should contain weights"
    assert 'tokens' in viz_data, "Should contain tokens"
    assert 'shape' in viz_data, "Should contain shape"
    assert viz_data['weights'].shape == (10, 10), "Should average across heads"
    
    print("✓ attention_score_visualization passed")


def test_aliases():
    """Test function aliases"""
    print("Testing aliases...")
    
    batch_size = 32
    seq_len = 10
    d_k = 64
    
    q = np.random.randn(batch_size, seq_len, d_k)
    k = np.random.randn(batch_size, seq_len, d_k)
    v = np.random.randn(batch_size, seq_len, d_k)
    
    # Test sdp_attention alias
    out1, w1 = sdp_attention(q, k, v)
    out2, w2 = scaled_dot_product_attention(q, k, v)
    assert np.allclose(out1, out2), "sdp_attention alias should work"
    
    # Test pos_encoding alias
    pos1 = pos_encoding(100, 512)
    pos2 = positional_encoding(100, 512)
    assert np.allclose(pos1, pos2), "pos_encoding alias should work"
    
    # Test causal_mask alias
    mask1 = causal_mask(10)
    mask2 = create_causal_mask(10)
    assert np.allclose(mask1, mask2), "causal_mask alias should work"
    
    print("✓ aliases passed")


def test_attention_with_different_seq_lengths():
    """Test attention with different query and key sequence lengths"""
    print("Testing attention with different sequence lengths...")
    
    batch_size = 32
    seq_len_q = 10
    seq_len_k = 20
    d_k = 64
    
    q = np.random.randn(batch_size, seq_len_q, d_k)
    k = np.random.randn(batch_size, seq_len_k, d_k)
    v = np.random.randn(batch_size, seq_len_k, d_k)
    
    output, weights = scaled_dot_product_attention(q, k, v)
    
    assert output.shape == (batch_size, seq_len_q, d_k), "Output shape incorrect"
    assert weights.shape == (batch_size, seq_len_q, seq_len_k), "Weights shape incorrect"
    
    print("✓ attention with different sequence lengths passed")


def test_attention_numerical_stability():
    """Test numerical stability with extreme values"""
    print("Testing attention numerical stability...")
    
    batch_size = 32
    seq_len = 10
    d_k = 64
    
    # Test with very large values
    q = np.random.randn(batch_size, seq_len, d_k) * 1000
    k = np.random.randn(batch_size, seq_len, d_k) * 1000
    v = np.random.randn(batch_size, seq_len, d_k) * 1000
    
    output, weights = scaled_dot_product_attention(q, k, v)
    
    assert not np.any(np.isnan(output)), "Should not produce NaN"
    assert not np.any(np.isinf(output)), "Should not produce Inf"
    assert not np.any(np.isnan(weights)), "Weights should not be NaN"
    
    print("✓ attention numerical stability passed")


def test_positional_encoding_properties():
    """Test properties of positional encoding"""
    print("Testing positional encoding properties...")
    
    seq_len = 100
    d_model = 512
    
    pos_enc = positional_encoding(seq_len, d_model)
    
    # Check that different positions have different encodings
    assert not np.allclose(pos_enc[0], pos_enc[1]), "Different positions should have different encodings"
    
    # Check that encodings are smooth (nearby positions are similar)
    diff = np.abs(pos_enc[0] - pos_enc[1])
    assert np.mean(diff) < 0.5, "Nearby positions should have similar encodings"
    
    print("✓ positional encoding properties passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("ATTENTION MECHANISMS MODULE TESTS")
    print("="*60 + "\n")
    
    # Core attention
    test_scaled_dot_product_attention()
    test_scaled_dot_product_attention_with_mask()
    test_multi_head_attention()
    test_multi_head_attention_invalid_heads()
    test_self_attention()
    test_multi_head_self_attention()
    test_cross_attention()
    
    # Masks
    test_create_padding_mask()
    test_create_causal_mask()
    test_create_look_ahead_mask()
    
    # Positional encoding
    test_positional_encoding()
    test_learned_positional_encoding()
    test_positional_encoding_properties()
    
    # Utilities
    test_softmax()
    test_dropout()
    test_attention_score_visualization()
    
    # Aliases
    test_aliases()
    
    # Edge cases
    test_attention_with_different_seq_lengths()
    test_attention_numerical_stability()
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED! ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
