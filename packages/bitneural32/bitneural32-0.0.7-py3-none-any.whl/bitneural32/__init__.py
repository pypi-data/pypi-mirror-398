"""
BitNeural32: 1.58-Bit Ternary Neural Network Compiler for ESP32

A powerful library for training, quantizing, and compiling neural networks
to ultra-efficient ternary format for ESP32 deployment.

Quick Start:
    >>> from bitneural32.qat import TernaryDense
    >>> from bitneural32.compiler import BitNeuralCompiler
    >>> import keras
    >>> 
    >>> # Build and train a QAT model
    >>> model = keras.Sequential([
    ...     TernaryDense(64, activation='relu', input_shape=(10,)),
    ...     TernaryDense(10, activation='softmax')
    ... ])
    >>> model.compile(optimizer='adam', loss='categorical_crossentropy')
    >>> # model.fit(X_train, Y_train, epochs=10)
    >>> 
    >>> # Compile to ESP32
    >>> compiler = BitNeuralCompiler(board_type='ESP32-S3')
    >>> compiler.compile_model(model)
    >>> compiler.save_c_header('model_data.h')

See https://github.com/yourusername/bitneural32 for documentation.
"""

__version__ = "3.0.0"
__author__ = "Aizhee"
__email__ = "aizharjamilano@gmail.com"
__license__ = "MIT"

# Import main public API
# These use relative imports to the wrapper modules
from bitneural32.compiler import BitNeuralCompiler, load_and_compile
from bitneural32.quantize import quantize_weights_ternary, pack_weights_2bit
from bitneural32.op_codes import (
    OP_INPUT_NORM,
    OP_CONV1D_TERNARY,
    OP_DENSE_TERNARY,
    OP_CONV2D_TERNARY,
    OP_RELU,
    OP_LEAKY_RELU,
    OP_SOFTMAX,
    OP_SIGMOID,
    OP_TANH,
    OP_MAXPOOL_1D,
    OP_FLATTEN,
    OP_DROPOUT,
    OP_LSTM,
    OP_GRU,
)

# QAT Layers (optional import in case keras not installed)
try:
    from bitneural32.qat import (
        TernaryDense,
        TernaryConv1D,
        TernaryConv2D,
        TernaryLSTM,
        TernaryGRU,
        ternary_quantize,
    )
    _HAS_QAT = True
except ImportError:
    _HAS_QAT = False  # Keras not installed, QAT layers not available

__all__ = [
    "BitNeuralCompiler",
    "load_and_compile",
    "quantize_weights_ternary",
    "pack_weights_2bit",
    # OpCodes
    "OP_INPUT_NORM",
    "OP_CONV1D_TERNARY",
    "OP_DENSE_TERNARY",
    "OP_CONV2D_TERNARY",
    "OP_RELU",
    "OP_LEAKY_RELU",
    "OP_SOFTMAX",
    "OP_SIGMOID",
    "OP_TANH",
    "OP_MAXPOOL_1D",
    "OP_FLATTEN",
    "OP_DROPOUT",
    "OP_LSTM",
    "OP_GRU",
]

if _HAS_QAT:
    __all__.extend([
        "TernaryDense",
        "TernaryConv1D",
        "TernaryConv2D",
        "TernaryLSTM",
        "TernaryGRU",
        "ternary_quantize",
    ])
