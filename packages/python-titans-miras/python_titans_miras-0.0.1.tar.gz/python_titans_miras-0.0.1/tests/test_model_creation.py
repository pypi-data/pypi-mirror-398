"""Test model creation and basic forward passes."""

import pytest
import torch


def test_create_transformer_config():
    """Test creating a TransformerConfig."""
    from titans_miras import TransformerConfig, NeuralMemoryConfig

    config = TransformerConfig(
        num_tokens=256,
        dim=64,
        depth=2,
        segment_len=16,
        neural_mem=NeuralMemoryConfig(dim=64, heads=2),
    )

    assert config.num_tokens == 256
    assert config.dim == 64
    assert config.depth == 2
    assert config.segment_len == 16


def test_create_miras_config():
    """Test creating MIRASConfig for each variant."""
    from titans_miras import MIRASConfig, MIRASArchitecture, MemoraNormalizeMode

    # Default
    default_config = MIRASConfig(architecture=MIRASArchitecture.DEFAULT)
    assert default_config.architecture == MIRASArchitecture.DEFAULT

    # YAAD
    yaad_config = MIRASConfig(
        architecture=MIRASArchitecture.YAAD,
        yaad_delta=1.5,
    )
    assert yaad_config.architecture == MIRASArchitecture.YAAD
    assert yaad_config.yaad_delta == 1.5

    # MONETA
    moneta_config = MIRASConfig(
        architecture=MIRASArchitecture.MONETA,
        moneta_bias_p=2.0,
        moneta_gate_p=2.0,
    )
    assert moneta_config.architecture == MIRASArchitecture.MONETA
    assert moneta_config.moneta_bias_p == 2.0

    # MEMORA
    memora_config = MIRASConfig(
        architecture=MIRASArchitecture.MEMORA,
        memora_temperature=0.5,
        memora_normalize_mode=MemoraNormalizeMode.SOFTMAX,
    )
    assert memora_config.architecture == MIRASArchitecture.MEMORA
    assert memora_config.memora_temperature == 0.5


def test_miras_from_config():
    """Test creating MIRAS instance from config."""
    from titans_miras import MIRAS, MIRASConfig, MIRASArchitecture

    # Test each variant
    for arch in MIRASArchitecture:
        config = MIRASConfig(architecture=arch)
        miras = MIRAS.from_config(config)
        assert miras is not None
        assert miras.attentional_bias is not None
        assert miras.retention_gate is not None


def test_miras_factory_methods():
    """Test MIRAS factory methods."""
    from titans_miras import MIRAS

    # Test all factory methods
    default_miras = MIRAS.default()
    assert default_miras is not None

    yaad_miras = MIRAS.yaad(delta=1.0)
    assert yaad_miras is not None

    moneta_miras = MIRAS.moneta(bias_p=1.5, gate_p=1.5)
    assert moneta_miras is not None

    memora_miras = MIRAS.memora(temperature=1.0)
    assert memora_miras is not None


def test_memory_mlp_creation():
    """Test creating a MemoryMLP."""
    from titans_miras import MemoryMLP

    model = MemoryMLP(dim=64, depth=2)
    assert model is not None

    # Test forward pass
    x = torch.randn(2, 16, 64)
    out = model(x)
    assert out.shape == x.shape


@pytest.mark.slow
def test_transformer_creation():
    """Test creating a MACTransformer."""
    from titans_miras import (
        MACTransformer,
        TransformerConfig,
        NeuralMemoryConfig,
    )

    config = TransformerConfig(
        num_tokens=256,
        dim=64,
        depth=2,
        segment_len=16,
        neural_mem=NeuralMemoryConfig(dim=64, heads=2),
    )

    model = MACTransformer(config=config)
    assert model is not None


@pytest.mark.slow
def test_transformer_forward():
    """Test forward pass through MACTransformer."""
    from titans_miras import (
        MACTransformer,
        TransformerConfig,
        NeuralMemoryConfig,
    )

    config = TransformerConfig(
        num_tokens=256,
        dim=64,
        depth=2,
        segment_len=16,
        neural_mem=NeuralMemoryConfig(dim=64, heads=2),
    )

    model = MACTransformer(config=config)

    # Test forward pass
    x = torch.randint(0, 256, (1, 32))
    logits = model(x)

    assert logits.shape == (1, 32, 256)


@pytest.mark.slow
def test_transformer_with_loss():
    """Test forward pass with loss computation."""
    from titans_miras import (
        MACTransformer,
        TransformerConfig,
        NeuralMemoryConfig,
    )

    config = TransformerConfig(
        num_tokens=256,
        dim=64,
        depth=2,
        segment_len=16,
        neural_mem=NeuralMemoryConfig(dim=64, heads=2),
    )

    model = MACTransformer(config=config)

    # Test forward pass with loss
    x = torch.randint(0, 256, (1, 32))
    loss = model(x, return_loss=True)

    assert loss.ndim == 0  # Scalar loss
    assert loss.item() > 0  # Loss should be positive
