from typing import Optional
import numpy as np

# ============================================
# Weight Quantization
# ============================================

def quantize_weights_ternary(weights: np.ndarray, threshold: Optional[float] = None) -> np.ndarray:
    """
    Quantize floating-point weights to {-1, 0, 1}.
    
    Strategy:
      - If threshold not specified, use the median absolute value
      - Values with |w| > threshold map to sign(w)
      - Otherwise map to 0
    
    Args:
        weights: Float32 array of weights
        threshold: Quantization threshold (if None, auto-compute)
    
    Returns:
        Quantized int8 array
    """
    if threshold is None:
        # Auto-compute threshold as median absolute value
        threshold = np.median(np.abs(weights.flatten()))
    
    quantized = np.zeros_like(weights, dtype=np.int8)
    mask_pos = weights > threshold
    mask_neg = weights < -threshold
    
    quantized[mask_pos] = 1
    quantized[mask_neg] = -1
    
    return quantized


def pack_weights_2bit(weights: np.ndarray) -> np.ndarray:
    """
    Pack quaternary weights {-1, 0, 1} into 2-bit bytes.
    
    Packing scheme:
      - 4 weights per byte: (w1<<6) | (w2<<4) | (w3<<2) | w4
      - Mapping: 0->00, 1->01, -1->10, reserved->11
    
    Args:
        weights: Flat int8 array
    
    Returns:
        Packed uint8 array (1/4 the size of input)
    """
    weights_flat = weights.flatten()
    num_weights = len(weights_flat)
    num_bytes = (num_weights + 3) // 4
    
    packed = np.zeros(num_bytes, dtype=np.uint8)
    
    for i, w in enumerate(weights_flat):
        byte_idx = i // 4
        bit_offset = (3 - (i % 4)) * 2
        
        # Map: -1->10, 0->00, 1->01
        if w == 1:
            encoded = 0b01
        elif w == -1:
            encoded = 0b10
        else:
            encoded = 0b00
        
        packed[byte_idx] |= (encoded << bit_offset)
    
    return packed
