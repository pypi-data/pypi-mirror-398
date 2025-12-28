"""
Test that hyperspec works correctly in Python 3.14+ subinterpreters.

hyperspec supports Python 3.14+ subinterpreters through:
- Multi-phase module initialization (PEP 489/630)
- Per-interpreter module state
- Per-interpreter heap-allocated StructMixinType (to avoid tp_subclasses corruption)
- Thread-local state caching for fast access
"""

import sys

import pytest

# Import hyperspec in the main interpreter first
import hyperspec  # noqa: F401

pytestmark = [
    pytest.mark.skipif(
        sys.version_info < (3, 14), reason="subinterpreters require Python 3.14+"
    ),
]


def test_import_in_subinterpreter():
    """Test that hyperspec can be imported in a subinterpreter."""
    import concurrent.interpreters as interpreters

    interp = interpreters.create()
    try:
        interp.exec("""
import hyperspec
assert hyperspec is not None
""")
    finally:
        interp.close()


def test_json_encode_decode_in_subinterpreter():
    """Test basic JSON encoding/decoding in a subinterpreter."""
    import concurrent.interpreters as interpreters

    interp = interpreters.create()
    try:
        interp.exec("""
import hyperspec

# Test encoding
data = {"hello": "world", "number": 42, "list": [1, 2, 3]}
encoded = hyperspec.json.encode(data)
assert encoded == b'{"hello":"world","number":42,"list":[1,2,3]}'

# Test decoding
decoded = hyperspec.json.decode(encoded)
assert decoded == data
""")
    finally:
        interp.close()


def test_struct_in_subinterpreter():
    """Test Struct definition and usage in a subinterpreter."""
    import concurrent.interpreters as interpreters

    interp = interpreters.create()
    try:
        interp.exec("""
import hyperspec

class Point(hyperspec.Struct):
    x: int
    y: int

p = Point(x=1, y=2)
assert p.x == 1
assert p.y == 2

# Test encoding/decoding structs
encoded = hyperspec.json.encode(p)
assert encoded == b'{"x":1,"y":2}'

decoded = hyperspec.json.decode(encoded, type=Point)
assert decoded.x == 1
assert decoded.y == 2
""")
    finally:
        interp.close()


def test_msgpack_in_subinterpreter():
    """Test msgpack encoding/decoding in a subinterpreter."""
    import concurrent.interpreters as interpreters

    interp = interpreters.create()
    try:
        interp.exec("""
import hyperspec

data = {"key": "value", "numbers": [1, 2, 3]}
encoded = hyperspec.msgpack.encode(data)
decoded = hyperspec.msgpack.decode(encoded)
assert decoded == data
""")
    finally:
        interp.close()


def test_validation_error_in_subinterpreter():
    """Test that ValidationError works correctly in a subinterpreter."""
    import concurrent.interpreters as interpreters

    interp = interpreters.create()
    try:
        interp.exec("""
import hyperspec

try:
    hyperspec.json.decode(b'"not an int"', type=int)
    assert False, "Should have raised ValidationError"
except hyperspec.ValidationError as e:
    assert "Expected `int`" in str(e)
""")
    finally:
        interp.close()


def test_encoder_decoder_classes_in_subinterpreter():
    """Test Encoder and Decoder classes in a subinterpreter."""
    import concurrent.interpreters as interpreters

    interp = interpreters.create()
    try:
        interp.exec("""
import hyperspec

# JSON Encoder/Decoder
json_enc = hyperspec.json.Encoder()
json_dec = hyperspec.json.Decoder()

data = {"test": 123}
encoded = json_enc.encode(data)
decoded = json_dec.decode(encoded)
assert decoded == data

# Msgpack Encoder/Decoder
mp_enc = hyperspec.msgpack.Encoder()
mp_dec = hyperspec.msgpack.Decoder()

encoded = mp_enc.encode(data)
decoded = mp_dec.decode(encoded)
assert decoded == data
""")
    finally:
        interp.close()


def test_multiple_subinterpreters_sequential():
    """Test that hyperspec works in multiple subinterpreters sequentially.

    Note: Creating multiple subinterpreters and closing them works correctly
    when the main interpreter has imported hyperspec first.
    """
    import concurrent.interpreters as interpreters

    interp1 = interpreters.create()
    interp2 = interpreters.create()

    try:
        # Use hyperspec in first interpreter
        interp1.exec("""
import hyperspec
data1 = hyperspec.json.encode({"from": "interp1"})
assert b"interp1" in data1
""")

        # Use hyperspec in second interpreter
        interp2.exec("""
import hyperspec
data2 = hyperspec.json.encode({"from": "interp2"})
assert b"interp2" in data2
""")

        # Use again in first interpreter
        interp1.exec("""
decoded = hyperspec.json.decode(b'{"test": true}')
assert decoded == {"test": True}
""")
    finally:
        # Close in reverse order (LIFO) for better cleanup
        interp2.close()
        interp1.close()


if __name__ == "__main__":
    print(f"Python version: {sys.version}")

    if sys.version_info < (3, 14):
        print("Skipping tests: Python 3.14+ required for subinterpreters")
        sys.exit(0)

    print("Running subinterpreter tests...")
    print("(hyperspec already imported in main interpreter)")
    print()

    test_import_in_subinterpreter()
    print("✓ test_import_in_subinterpreter passed")

    test_json_encode_decode_in_subinterpreter()
    print("✓ test_json_encode_decode_in_subinterpreter passed")

    test_struct_in_subinterpreter()
    print("✓ test_struct_in_subinterpreter passed")

    test_msgpack_in_subinterpreter()
    print("✓ test_msgpack_in_subinterpreter passed")

    test_validation_error_in_subinterpreter()
    print("✓ test_validation_error_in_subinterpreter passed")

    test_encoder_decoder_classes_in_subinterpreter()
    print("✓ test_encoder_decoder_classes_in_subinterpreter passed")

    test_multiple_subinterpreters_sequential()
    print("✓ test_multiple_subinterpreters_sequential passed")

    # Test many sequential subinterpreters
    print()
    print("Testing many sequential subinterpreters...")
    for i in range(10):
        test_import_in_subinterpreter()
        print(f"  ✓ Iteration {i + 1}/10 passed")

    print()
    print("All subinterpreter tests passed!")
    print()
    print(
        "hyperspec now supports Python 3.14+ subinterpreters with per-interpreter caching."
    )
