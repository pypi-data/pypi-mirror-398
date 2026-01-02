"""
BitNeural32 Compiler: Keras-to-Bytecode Converter
Converts Keras models to optimized 1.58-bit quantized C header files.

Made to work with BitNeural32 library supporting ESP32 variants.

Workflow:
  1. Load a trained Keras model
  2. Calculate dataset statistics (mean/std for normalization)
  3. Quantize weights to {-1, 0, 1} (1.58-bit)
  4. Pack weights into 2-bit bytes
  5. Generate C header with binary blob and metadata
  6. Optionally generate metrics for inference time & memory
"""

import numpy as np
import struct
import io
from typing import Dict, Optional, Tuple
import json
import time
from bitneural32.layers import (DenseCompiler, Conv1DCompiler,
                    Conv2DCompiler, ReLuCompiler, LeakyReLuCompiler,
                    SoftmaxCompiler, FlattenCompiler, MaxPooling1DCompiler,
                    DropoutCompiler, LSTMCompiler, GRUCompiler)
from bitneural32.op_codes import (OP_INPUT_NORM, OP_LSTM, OP_GRU)
try:
    import keras
    HAS_KERAS = True
except ImportError:
    HAS_KERAS = False
    print("[WARNING] Keras not installed. Model loading disabled.")

# ============================================
# Board Type Definitions
# ============================================

BOARD_TYPES = {
    'ESP32': {
        'cores': 2,
        'freq_mhz': 240,
        'ram_kb': 520,
        'flash_kb': 4096,
        'name': 'ESP32 (Original)'
    },
    'ESP32-S3': {
        'cores': 2,
        'freq_mhz': 240,
        'ram_kb': 512,
        'flash_kb': 8192,
        'name': 'ESP32-S3 (Dual-Core, SIMD)'
    },
    'ESP32-C3': {
        'cores': 1,
        'freq_mhz': 160,
        'ram_kb': 400,
        'flash_kb': 4096,
        'name': 'ESP32-C3 (RISC-V)'
    }
}

# ============================================
# Model Compiler
# ============================================

class BitNeuralCompiler:
    """
    Main compiler: Converts Keras models to BitNeural C headers.
    Supports metrics generation for inference time & memory estimation.
    """
    
    LAYER_COMPILER_MAP = {
        'Dense': DenseCompiler,
        'TernaryDense': DenseCompiler,
        'Conv1D': Conv1DCompiler,
        'TernaryConv1D': Conv1DCompiler,
        'Conv2D': Conv2DCompiler,
        'TernaryConv2D': Conv2DCompiler,
        'ReLU': ReLuCompiler,
        'LeakyReLU': LeakyReLuCompiler,
        'Softmax': SoftmaxCompiler,
        'Flatten': FlattenCompiler,
        'MaxPooling1D': MaxPooling1DCompiler,
        'Dropout': DropoutCompiler,
        'LSTM': LSTMCompiler,
        'TernaryLSTM': LSTMCompiler,
        'GRU': GRUCompiler,
        'TernaryGRU': GRUCompiler,
    }
    
    def __init__(self, model: Optional['keras.Model'] = None, board_type: str = 'ESP32'):
        """
        Initialize compiler.
        
        Args:
            model: Optional Keras model to compile
            board_type: Target board ('ESP32', 'ESP32-S3', 'ESP32-C3')
        """
        self.model = model
        self.layers_compiled = []
        self.model_data = bytearray()
        self.board_type = board_type if board_type in BOARD_TYPES else 'ESP32'
        self.metrics = {}
        self.input_shape = None
        self.output_shape = None
    
    def compile_model(self, model: 'keras.Model', input_data: Optional[np.ndarray] = None,
                     allow_metrics: bool = False) -> str:
        """
        Compile a Keras model to C header with optional metrics.
        
        Args:
            model: Keras model to compile
            input_data: Optional training data for normalization statistics
            allow_metrics: If True, generate inference metrics
        
        Returns:
            C header string (const uint8_t model_data[] = {...};)
        """
        self.model = model
        self.layers_compiled = []
        self.input_shape = model.input_shape if hasattr(model, 'input_shape') else None
        self.output_shape = model.output_shape if hasattr(model, 'output_shape') else None
        
        # Initialize model binary blob
        blob = bytearray()
        
        # 1. Write magic number
        blob.extend(b'BITN')
        
        # 2. Collect layer descriptors
        layer_data = bytearray()
        
        # 3. Add INPUT_NORM layer for preprocessing
        if input_data is not None:
            norm_mean = np.mean(input_data)
            norm_std = np.std(input_data)
        else:
            norm_mean = 0.0
            norm_std = 1.0
        
        norm_blob = bytearray()
        norm_blob.extend(struct.pack('<ff', norm_mean, norm_std))
        layer_data.append(OP_INPUT_NORM)
        layer_data.extend(struct.pack('<i', len(norm_blob)))
        layer_data.extend(norm_blob)
        
        # 4. Compile each Keras layer
        num_compiled_layers = 1
        
        for keras_layer in model.layers:
            layer_type = type(keras_layer).__name__
            
            if layer_type not in self.LAYER_COMPILER_MAP:
                print(f"[WARNING] Unsupported layer type: {layer_type}. Skipping.")
                continue
            
            compiler_class = self.LAYER_COMPILER_MAP[layer_type]
            compiler = compiler_class()
            
            try:
                opcode, param_blob = compiler.compile(keras_layer)
                
                layer_data.append(opcode)
                layer_data.extend(struct.pack('<i', len(param_blob)))
                layer_data.extend(param_blob)
                
                self.layers_compiled.append((layer_type, opcode, len(param_blob)))
                num_compiled_layers += 1
                
            except Exception as e:
                print(f"[ERROR] Failed to compile {layer_type}: {e}")
                continue
        
        # 5. Write num_layers
        blob.extend(struct.pack('<i', num_compiled_layers))
        blob.extend(layer_data)
        
        self.model_data = blob
        
        # 6. Generate metrics if requested
        if allow_metrics:
            self._generate_metrics()
        
        return self._generate_c_header()
    
    def _generate_metrics(self):
        """Generate inference metrics and performance estimates."""
        board_info = BOARD_TYPES[self.board_type]
        
        # Estimate parameters and computations
        total_params = 0
        total_macs = 0  # Multiply-accumulate operations
        layer_metrics = []
        
        # Simple estimation based on layer types
        for layer_type, opcode, param_size in self.layers_compiled:
            if 'Dense' in layer_type or 'LSTM' in layer_type or 'GRU' in layer_type:
                # Dense-like layers
                estimated_macs = param_size * 4  # Very rough estimate
            elif 'Conv' in layer_type:
                estimated_macs = param_size * 8
            else:
                estimated_macs = 0
            
            total_params += param_size
            total_macs += estimated_macs
            
            layer_metrics.append({
                'type': layer_type,
                'param_bytes': param_size,
                'est_macs': estimated_macs
            })
        
        # Estimate inference time (at 1 operation per cycle, simplified)
        cycles_per_inference = total_macs
        freq_hz = board_info['freq_mhz'] * 1e6
        est_time_ms = (cycles_per_inference / freq_hz) * 1000 * 2  # Add 2x safety margin
        
        # Estimate RAM usage (input + output + intermediate buffers)
        if self.input_shape:
            input_elements = np.prod(self.input_shape[1:]) if len(self.input_shape) > 1 else 10
        else:
            input_elements = 100
        
        if self.output_shape:
            output_elements = np.prod(self.output_shape[1:]) if len(self.output_shape) > 1 else 10
        else:
            output_elements = 100
        
        # Buffers: input, output, 2 intermediate (ping-pong)
        bytes_per_float = 4
        est_ram_bytes = (input_elements + output_elements * 3) * bytes_per_float
        
        self.metrics = {
            'board_type': self.board_type,
            'board_info': board_info,
            'model_size_bytes': len(self.model_data),
            'total_parameters': sum(p[2] for p in self.layers_compiled),
            'total_macs': int(total_macs),
            'estimated_inference_time_ms': float(est_time_ms),
            'estimated_ram_bytes': int(est_ram_bytes),
            'available_ram_kb': board_info['ram_kb'],
            'available_flash_kb': board_info['flash_kb'],
            'num_cores': board_info['cores'],
            'layers': layer_metrics
        }
    
    def _generate_c_header(self, var_name: str = "model_data") -> str:
        """Generate C header from compiled model."""
        hex_data = ', '.join(f'0x{b:02x}' for b in self.model_data)
        
        c_code = f"""
/* BitNeural32 Model - Auto-generated by BitNeural32 built in compiler */
#include <stdint.h>

const uint8_t {var_name}[] = {{
    {hex_data}
}};

const int {var_name}_len = {len(self.model_data)};
"""
        return c_code
    
    def save_c_header(self, filepath: str, include_metrics: bool = False):
        """
        Save C header to file.
        
        Args:
            filepath: Output file path
            include_metrics: If True, append metrics as comments
        """
        c_code = self._generate_c_header()
        
        # Append metrics if available
        if include_metrics and self.metrics:
            metrics_comment = self._generate_metrics_comment()
            c_code += metrics_comment
        
        with open(filepath, 'w') as f:
            f.write(c_code)
        print(f"[OK] Model exported to {filepath}")
        print(f"     Size: {len(self.model_data)} bytes")
        print(f"     Layers compiled: {len(self.layers_compiled)}")
    
    def _generate_metrics_comment(self) -> str:
        """Generate metrics as C comment block."""
        if not self.metrics:
            return ""
        
        m = self.metrics
        comment = f"""
/*
 * ============================================
 * INFERENCE METRICS & PERFORMANCE DATA
 * ============================================
 * Target Board:    {m['board_type']} ({m['board_info']['name']})
 * Cores:           {m['num_cores']} @ {m['board_info']['freq_mhz']} MHz
 * Available RAM:   {m['board_info']['ram_kb']} KB
 * Available Flash: {m['board_info']['flash_kb']} KB
 *
 * Model Statistics:
 *   Model Size:       {m['model_size_bytes']} bytes
 *   Total Parameters: {m['total_parameters']} bytes (quantized)
 *   Total MACs:       {m['total_macs']} (estimated)
 *
 * Inference Estimates:
 *   Inference Time:   ~{m['estimated_inference_time_ms']:.2f} ms
 *   RAM Usage:        ~{m['estimated_ram_bytes']} bytes
 *   Num Layers:       {len(m['layers'])}
 *
 * Layer Breakdown:
"""
        for i, layer in enumerate(m['layers']):
            comment += f" *   [{i}] {layer['type']}: {layer['param_bytes']} bytes params, ~{layer['est_macs']} MACs\n"
        
        comment += " */"
        return comment
    
    def export_model(self, filepath: str, allow_metrics: bool = False) -> str:
        """
        Export model to C header with optional metrics.
        
        Args:
            filepath: Output .h file path
            allow_metrics: If True, include inference metrics
        
        Returns:
            Path to exported file
        """
        self.save_c_header(filepath, include_metrics=allow_metrics)
        return filepath
    
    def get_compilation_report(self) -> Dict:
        """Get human-readable compilation report including metrics."""
        report = {
            "board_type": self.board_type,
            "total_size_bytes": len(self.model_data),
            "num_layers": len(self.layers_compiled),
            "layers": [
                {
                    "index": i,
                    "type": layer_type,
                    "opcode": opcode,
                    "param_size": param_size
                }
                for i, (layer_type, opcode, param_size) in enumerate(self.layers_compiled)
            ]
        }
        
        if self.metrics:
            report.update({
                "inference_time_ms": self.metrics['estimated_inference_time_ms'],
                "ram_usage_bytes": self.metrics['estimated_ram_bytes'],
                "total_macs": self.metrics['total_macs']
            })
        
        return report


# ============================================
# Utility Functions
# ============================================

def load_and_compile(model_path: str, output_path: str, input_data: Optional[np.ndarray] = None,
                    board_type: str = 'ESP32', allow_metrics: bool = False):
    """
    Convenience function: Load Keras model and compile to C header.
    
    Args:
        model_path: Path to .h5 or SavedModel
        output_path: Output C header file path
        input_data: Optional training data for normalization
        board_type: Target board type ('ESP32', 'ESP32-S3', 'ESP32-C3')
        allow_metrics: If True, generate and include metrics
    """
    if not HAS_KERAS:
        raise RuntimeError("Keras not installed.")
    
    print(f"[*] Loading model from {model_path}...")
    model = keras.models.load_model(model_path)
    
    print(f"[*] Compiling model for {board_type}...")
    compiler = BitNeuralCompiler(board_type=board_type)
    compiler.compile_model(model, input_data, allow_metrics=allow_metrics)
    
    print(f"[*] Saving to {output_path}...")
    compiler.save_c_header(output_path, include_metrics=allow_metrics)
    
    print("\n" + "="*60)
    print("Compilation Report:")
    print("="*60)
    report = compiler.get_compilation_report()
    print(json.dumps(report, indent=2))
    
    if allow_metrics:
        print("\n" + "="*60)
        print("Performance Metrics:")
        print("="*60)
        print(f"Board: {compiler.board_type}")
        print(f"Est. Inference Time: {compiler.metrics['estimated_inference_time_ms']:.2f} ms")
        print(f"Est. RAM Usage: {compiler.metrics['estimated_ram_bytes']} bytes")
        print(f"Flash Usage: {len(compiler.model_data)} bytes")


# ============================================
# Example Usage
# ============================================

if __name__ == "__main__":
    print("BitNeural32 Compiler (with metrics & multi-board support)")
    print("="*60)
    
    print("\nUsage Examples:")
    print("  # Basic compilation")
    print("  compiler = BitNeuralCompiler(board_type='ESP32-S3')")
    print("  compiler.compile_model(keras_model, input_data, allow_metrics=True)")
    print("  compiler.save_c_header('model.h', include_metrics=True)")
    print()
    print("  # Or use convenience function")
    print("  load_and_compile('model.h5', 'model_data.h', board_type='ESP32', allow_metrics=True)")
