"""Test that all public imports work correctly."""

import pytest


def test_main_imports():
    """Test that main package imports work."""
    from titans_miras import (
        MACTransformer,
        TransformerConfig,
        NeuralMemoryConfig,
        MIRASConfig,
        MIRASArchitecture,
        MemoraNormalizeMode,
    )

    assert MACTransformer is not None
    assert TransformerConfig is not None
    assert NeuralMemoryConfig is not None
    assert MIRASConfig is not None
    assert MIRASArchitecture is not None
    assert MemoraNormalizeMode is not None


def test_miras_imports():
    """Test that MIRAS framework imports work."""
    from titans_miras import (
        MIRAS,
        AttentionalBias,
        RetentionGate,
        MSEBias,
        HuberBias,
        GeneralizedNormBias,
        MSERetentionGate,
        GeneralizedNormRetentionGate,
        ProbabilityMapRetentionGate,
    )

    assert MIRAS is not None
    assert AttentionalBias is not None
    assert RetentionGate is not None
    assert MSEBias is not None
    assert HuberBias is not None
    assert GeneralizedNormBias is not None
    assert MSERetentionGate is not None
    assert GeneralizedNormRetentionGate is not None
    assert ProbabilityMapRetentionGate is not None


def test_memory_imports():
    """Test that memory model imports work."""
    from titans_miras import (
        NeuralMemory,
        MemoryMLP,
        MemoryAttention,
    )

    assert NeuralMemory is not None
    assert MemoryMLP is not None
    assert MemoryAttention is not None


def test_version():
    """Test that version is defined."""
    from titans_miras import __version__

    assert __version__ is not None
    assert isinstance(__version__, str)


def test_miras_architecture_enum():
    """Test MIRASArchitecture enum values."""
    from titans_miras import MIRASArchitecture

    assert MIRASArchitecture.DEFAULT == "default"
    assert MIRASArchitecture.YAAD == "yaad"
    assert MIRASArchitecture.MONETA == "moneta"
    assert MIRASArchitecture.MEMORA == "memora"


def test_memora_normalize_mode_enum():
    """Test MemoraNormalizeMode enum values."""
    from titans_miras import MemoraNormalizeMode

    assert MemoraNormalizeMode.SOFTMAX == "softmax"
    assert MemoraNormalizeMode.L1 == "l1"
    assert MemoraNormalizeMode.L2 == "l2"
