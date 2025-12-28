"""
hangeul-jamo: Korean Hangul syllable and jamo manipulation library

This is a meta-package that provides a unified interface for Korean Hangul processing.
By default, it uses the pure Python implementation (hangeul-jamo-py).
Install with [rust] extra for high-performance Rust implementation.

Installation:
    pip install hangeul-jamo          # Pure Python version
    pip install hangeul-jamo[rust]    # Rust-accelerated version

Usage:
    from hangeul_jamo import compose, decompose

    # Compose jamo into syllable
    syllable = compose('ㄱ', 'ㅏ', 'ㅁ')  # -> '감'

    # Decompose syllable into jamo
    jamos = decompose('한글')  # -> [('ㅎ', 'ㅏ', 'ㄴ'), ('ㄱ', 'ㅡ', 'ㄹ')]
"""

__version__ = "0.1.0"

# Try to import Rust implementation first (if installed)
# Fall back to pure Python implementation otherwise
_implementation = "unknown"

try:
    from hangeul_jamo_rs import *  # noqa: F401, F403

    _implementation = "rust"
except ImportError:
    try:
        from hangeul_jamo_py import *  # noqa: F401, F403

        _implementation = "python"
    except ImportError as e:
        raise ImportError(
            "Neither hangeul-jamo-rs nor hangeul-jamo-py is installed. "
            "This should not happen as hangeul-jamo-py is a required dependency. "
            "Please reinstall: pip install --force-reinstall hangeul-jamo"
        ) from e

__all__ = [
    "__version__",
    "_implementation",
]
