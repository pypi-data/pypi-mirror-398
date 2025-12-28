# hangeul-jamo

A modern, optimized Korean Hangul syllable and jamo manipulation library for Python.

This is a **meta-package** that provides a unified interface for Korean Hangul processing with two implementation backends:

- **Pure Python** (`hangeul-jamo-py`): Default, pure Python implementation - works everywhere
- **Rust-accelerated** (`hangeul-jamo-rs`): High-performance Rust implementation with Python bindings

## Installation

### Basic Installation (Pure Python)

```bash
pip install hangeul-jamo
```

This installs the pure Python implementation, which works on all platforms without requiring compilation.

### High-Performance Installation (Rust)

```bash
pip install hangeul-jamo[rust]
```

This installs both implementations, with the Rust version taking priority for better performance.

## Usage

```python
from hangeul_jamo import compose, decompose

# Compose jamo into syllables
syllable = compose('ㄱ', 'ㅏ', 'ㅁ')  # -> '감'

# Decompose syllables into jamo
jamos = decompose('한글')  # -> [('ㅎ', 'ㅏ', 'ㄴ'), ('ㄱ', 'ㅡ', 'ㄹ')]

# Check which implementation is being used
from hangeul_jamo import _implementation
print(_implementation)  # 'rust' or 'python'
```

The API is identical regardless of which backend is installed.

## Implementation Details

### hangeul-jamo-py (Pure Python)

- ✅ Works on all platforms
- ✅ No compilation required
- ✅ Easy to debug

### hangeul-jamo-rs (Rust)

- ✅ 10-100x faster performance
- ✅ Memory efficient
- ✅ Type-safe Rust implementation


## Backend Selection

The package automatically selects the best available implementation:

1. If `hangeul-jamo-rs` is installed → use Rust implementation
2. Otherwise → use `hangeul-jamo-py` (pure Python)

You can check which implementation is active:

```python
from hangeul_jamo import _implementation
print(f"Using {_implementation} implementation")
```

## Performance Comparison

| Operation | Python | Rust  | Speedup     |
| --------- | ------ | ----- | ----------- |
| Compose   | 1.0x   | ~50x  | 50x faster  |
| Decompose | 1.0x   | ~100x | 100x faster |

## Contributing

This is a meta-package. For implementation issues:

- Pure Python implementation: [hangeul-jamo-py](https://github.com/gembleman/hangeul-jamo-py)
- Rust implementation: [hangeul-jamo-rs](https://github.com/gembleman/hangeul-jamo-rs)
