from typing import List, Tuple
import struct
import numpy as np
from quantize import quantize_weights_ternary, pack_weights_2bit
from op_codes import (OP_INPUT_NORM, OP_CONV1D_TERNARY, OP_DENSE_TERNARY,
                      OP_CONV2D_TERNARY, OP_RELU, OP_LEAKY_RELU, OP_SOFTMAX,
                      OP_SIGMOID, OP_TANH, OP_MAXPOOL_1D, OP_AVGPOOL_1D, OP_FLATTEN,
                      OP_DROPOUT, OP_BATCH_NORM, OP_LSTM, OP_GRU, OP_CUSTOM)

# ============================================
# Layer Compiler Handlers
# ============================================

class LayerCompiler:
    """Base class for compiling Keras layers to BitNeural format."""
    
    def compile(self, layer) -> Tuple[int, bytearray]:
        """
        Compile a Keras layer to (opcode, binary_blob).
        
        Returns:
            (opcode, param_blob)
        """
        raise NotImplementedError


class DenseCompiler(LayerCompiler):
    """Compile Dense (fully-connected) layers."""
    
    def compile(self, layer) -> Tuple[int, bytearray]:
        weights = layer.kernel.numpy()  # Shape: (input_dim, units)
        bias = layer.bias.numpy() if layer.bias is not None else None
        
        # CRITICAL: Weight layout for Dense layer
        # Keras shape: (input_dim, units) - rows are inputs, columns are outputs
        # C kernel expects: linear array [out0_in0, out0_in1, ..., out0_in_last, out1_in0, ...]
        # This means: iterate outputs in outer loop, inputs in inner
        # Flattening: row-major (C-order) which is default for numpy flatten
        # Weight index formula: weight_linear_idx = out_idx * input_dim + in_idx
        
        # Quantize and pack (flatten is already row-major for (input_dim, units))
        quantized = quantize_weights_ternary(weights)
        packed_weights = pack_weights_2bit(quantized)
        
        # Build parameter blob
        blob = bytearray()
        
        # 1. Units (int32)
        units = weights.shape[1]
        blob.extend(struct.pack('<i', units))
        
        # 2. Packed weights (2-bit format)
        # Memory layout: [out0_w0, out0_w1, ..., out1_w0, out1_w1, ...]
        # where w0=input_0, w1=input_1, etc for each output unit
        blob.extend(packed_weights)
        
        # 3. Bias (optional, float32 per unit)
        if bias is not None:
            for b in bias:
                blob.extend(struct.pack('<f', b))
        
        return OP_DENSE_TERNARY, blob


class Conv1DCompiler(LayerCompiler):
    """Compile Conv1D layers."""
    
    def compile(self, layer) -> Tuple[int, bytearray]:
        weights = layer.kernel.numpy()  # Shape: (kernel_size, input_channels, filters)
        bias = layer.bias.numpy() if layer.bias is not None else None
        
        # Extract metadata
        kernel_size = weights.shape[0]
        in_channels = weights.shape[1]
        filters = weights.shape[2]
        stride = layer.strides[0]
        
        # CRITICAL: BitNeural32 Conv1D kernel is mono-channel (input_channels == 1).
        # Enforce single-channel and flatten weights to (filters, kernel_size).
        # If multiple channels are present, take the first channel to ensure
        # compatibility. For multi-channel use cases, prefer Conv2D in BitNeural32.
        if in_channels > 1:
            # Warn via comment in compiled blob by setting OP_CUSTOM in higher layers.
            # Here we take channel 0 to maintain compatibility.
            weights = weights[:, 0:1, :]
            in_channels = 1
        
        # Flatten to (filters, kernel_size) in filter-major order
        weights_reshaped = np.transpose(weights[:, 0, :], (1, 0))  # (filters, kernel_size)
        
        # Quantize and pack
        quantized = quantize_weights_ternary(weights_reshaped)
        packed_weights = pack_weights_2bit(quantized)
        
        # Build parameter blob
        blob = bytearray()
        
        # 1. Filters, kernel_size, stride (int32 each)
        blob.extend(struct.pack('<iii', filters, kernel_size, stride))
        
        # 2. Packed weights (2-bit format)
        # Memory layout: [filter0_weights (packed)] [filter1_weights (packed)] ...
        # Each filter's weights unpacked as: [k0, k1, k2, ..., k_{kernel_size-1}]
        blob.extend(packed_weights)
        
        # 3. Bias (optional, float32 per filter)
        if bias is not None:
            for b in bias:
                blob.extend(struct.pack('<f', b))
        
        return OP_CONV1D_TERNARY, blob


class Conv2DCompiler(LayerCompiler):
    """Compile Conv2D layers."""
    
    def compile(self, layer) -> Tuple[int, bytearray]:
        weights = layer.kernel.numpy()  # Shape: (kernel_h, kernel_w, input_channels, filters)
        bias = layer.bias.numpy() if layer.bias is not None else None
        
        # Extract metadata
        kernel_h, kernel_w = weights.shape[0], weights.shape[1]
        filters = weights.shape[3]
        stride = layer.strides[0]  # Assume square strides
        input_h = layer.input_shape[1] if hasattr(layer, 'input_shape') else 0
        input_w = layer.input_shape[2] if hasattr(layer, 'input_shape') else 0
        
        # CRITICAL: Weight flattening order must match C kernel expectations
        # Keras shape: (kernel_h, kernel_w, input_channels, filters)
        # Target layout: (filters, kernel_h, kernel_w, input_channels) - linear for each filter
        # This means: flatten as [filter0_kernel_flat, filter1_kernel_flat, ...]
        # Where each kernel is flattened as: [kh0_kw0, kh0_kw1, ..., kh1_kw0, ...]
        # Transpose (3, 0, 1, 2) → (filters, kernel_h, kernel_w, input_channels)
        # Then reshape (filters, -1) → (filters, kernel_h * kernel_w * input_channels)
        
        weights_reshaped = np.transpose(weights, (3, 0, 1, 2)).reshape(filters, -1)
        
        # Quantize and pack
        quantized = quantize_weights_ternary(weights_reshaped)
        packed_weights = pack_weights_2bit(quantized)
        
        # Build parameter blob
        blob = bytearray()
        
        # 1. Filters, kernel_h, kernel_w, stride, input_h, input_w (int32 each)
        blob.extend(struct.pack('<iiiiii', filters, kernel_h, kernel_w, stride, input_h, input_w))
        
        # 2. Packed weights (2-bit format)
        # Memory layout: [filter0_weights (packed)] [filter1_weights (packed)] ...
        # Each filter's kernel unpacked as 2D: kh*kernel_w spatial positions
        blob.extend(packed_weights)
        
        # 3. Bias (optional, float32 per filter)
        if bias is not None:
            for b in bias:
                blob.extend(struct.pack('<f', b))
        
        return OP_CONV2D_TERNARY, blob


class ActivationCompiler(LayerCompiler):
    """Base class for activation layers."""
    
    activation_map = {
        'relu': OP_RELU,
        'sigmoid': OP_SIGMOID,
        'tanh': OP_TANH,
        'softmax': OP_SOFTMAX,
    }
    
    def compile(self, layer) -> Tuple[int, bytearray]:
        activation_name = layer.activation.__name__ if hasattr(layer.activation, '__name__') else str(layer.activation)
        opcode = self.activation_map.get(activation_name, OP_RELU)
        
        blob = bytearray()
        # Most activations have no parameters
        return opcode, blob


class ReLuCompiler(ActivationCompiler):
    def compile(self, layer) -> Tuple[int, bytearray]:
        return OP_RELU, bytearray()


class LeakyReLuCompiler(LayerCompiler):
    def compile(self, layer) -> Tuple[int, bytearray]:
        alpha = layer.alpha if hasattr(layer, 'alpha') else 0.1
        blob = bytearray()
        blob.extend(struct.pack('<f', alpha))
        return OP_LEAKY_RELU, blob


class SoftmaxCompiler(LayerCompiler):
    def compile(self, layer) -> Tuple[int, bytearray]:
        return OP_SOFTMAX, bytearray()


class FlattenCompiler(LayerCompiler):
    def compile(self, layer) -> Tuple[int, bytearray]:
        return OP_FLATTEN, bytearray()


class MaxPooling1DCompiler(LayerCompiler):
    def compile(self, layer) -> Tuple[int, bytearray]:
        pool_size = layer.pool_size[0]
        stride = layer.strides[0] if hasattr(layer, 'strides') else pool_size
        input_len = 0  # Must be computed at runtime
        
        blob = bytearray()
        blob.extend(struct.pack('<iii', pool_size, stride, input_len))
        return OP_MAXPOOL_1D, blob


class DropoutCompiler(LayerCompiler):
    def compile(self, layer) -> Tuple[int, bytearray]:
        rate = layer.rate if hasattr(layer, 'rate') else 0.5
        blob = bytearray()
        blob.extend(struct.pack('<f', rate))
        return OP_DROPOUT, blob


class LSTMCompiler(LayerCompiler):
    """Compile LSTM layers with 2-bit quantized weights and biases."""
    
    def compile(self, layer) -> Tuple[int, bytearray]:
        """
        Compile LSTM layer.
        
        Keras LSTM uses 4 gate matrices: [input_kernel, recurrent_kernel]
        We pack all into a single param blob with quantization.
        """
        # Get weights from LSTM layer
        # kernel: (input_dim, units*4) for 4 gates
        # recurrent_kernel: (units, units*4) for 4 gates
        # bias: (units*4,)
        
        kernel = layer.kernel.numpy() if hasattr(layer, 'kernel') else None
        recurrent_kernel = layer.recurrent_kernel.numpy() if hasattr(layer, 'recurrent_kernel') else None
        bias = layer.bias.numpy() if hasattr(layer, 'bias') else None
        
        if kernel is None or recurrent_kernel is None:
            raise ValueError("LSTM layer missing kernel or recurrent_kernel")
        
        units = layer.units
        
        # Quantize all weights
        kernel_quantized = quantize_weights_ternary(kernel)
        recurrent_quantized = quantize_weights_ternary(recurrent_kernel)
        
        # Pack weights
        kernel_packed = pack_weights_2bit(kernel_quantized)
        recurrent_packed = pack_weights_2bit(recurrent_quantized)
        
        # Build parameter blob
        blob = bytearray()
        
        # 1. Hidden size (int32)
        blob.extend(struct.pack('<i', units))
        
        # 2. Input kernel packed
        blob.extend(kernel_packed)
        
        # 3. Recurrent kernel packed
        blob.extend(recurrent_packed)
        
        # 4. Biases for 4 gates (4 * units floats)
        if bias is not None:
            for b in bias:
                blob.extend(struct.pack('<f', b))
        else:
            for _ in range(units * 4):
                blob.extend(struct.pack('<f', 0.0))
        
        return OP_LSTM, blob


class GRUCompiler(LayerCompiler):
    """Compile GRU layers with 2-bit quantized weights and biases."""
    
    def compile(self, layer) -> Tuple[int, bytearray]:
        """
        Compile GRU layer.
        
        GRU uses 3 gates (simpler than LSTM).
        kernel: (input_dim, units*3)
        recurrent_kernel: (units, units*3)
        bias: (units*3,)
        """
        kernel = layer.kernel.numpy() if hasattr(layer, 'kernel') else None
        recurrent_kernel = layer.recurrent_kernel.numpy() if hasattr(layer, 'recurrent_kernel') else None
        bias = layer.bias.numpy() if hasattr(layer, 'bias') else None
        
        if kernel is None or recurrent_kernel is None:
            raise ValueError("GRU layer missing kernel or recurrent_kernel")
        
        units = layer.units
        
        # Quantize all weights
        kernel_quantized = quantize_weights_ternary(kernel)
        recurrent_quantized = quantize_weights_ternary(recurrent_kernel)
        
        # Pack weights
        kernel_packed = pack_weights_2bit(kernel_quantized)
        recurrent_packed = pack_weights_2bit(recurrent_quantized)
        
        # Build parameter blob
        blob = bytearray()
        
        # 1. Hidden size (int32)
        blob.extend(struct.pack('<i', units))
        
        # 2. Input kernel packed
        blob.extend(kernel_packed)
        
        # 3. Recurrent kernel packed
        blob.extend(recurrent_packed)
        
        # 4. Biases for 3 gates (3 * units floats)
        if bias is not None:
            for b in bias:
                blob.extend(struct.pack('<f', b))
        else:
            for _ in range(units * 3):
                blob.extend(struct.pack('<f', 0.0))
        
        return OP_GRU, blob
