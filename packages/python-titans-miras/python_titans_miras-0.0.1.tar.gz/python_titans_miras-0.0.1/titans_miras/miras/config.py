"""
MIRAS (Memory-Informed Robust Attention Strategies) configuration.

This module defines the configuration classes for the MIRAS framework,
which provides different variants of the Titans neural memory architecture:
- DEFAULT: Original Titans with MSE loss
- YAAD: Huber loss for robustness to outliers
- MONETA: Generalized p-norms for bias and retention
- MEMORA: Probability map constraints for stable updates
"""

from enum import Enum
from pydantic import BaseModel, Field


class MIRASArchitecture(str, Enum):
    """
    MIRAS architecture variants.

    Enumeration of available MIRAS framework variants for neural memory.
    """

    DEFAULT = "default"
    YAAD = "yaad"
    MONETA = "moneta"
    MEMORA = "memora"


class MemoraNormalizeMode(str, Enum):
    """
    Normalization modes for MEMORA architecture.

    Controls how probability maps are normalized in the MEMORA variant.
    """

    SOFTMAX = "softmax"
    L1 = "l1"
    L2 = "l2"


class MIRASConfig(BaseModel):
    """
    Configuration for MIRAS framework variants.

    This configuration class allows customization of the MIRAS framework
    behavior, including architecture selection and variant-specific parameters.
    """

    yaad_delta: float = Field(
        default=1.0,
        description="Huber loss delta threshold; controls transition from quadratic to linear loss (for 'yaad' architecture)",
    )
    moneta_bias_p: float = Field(
        default=1.5,
        description="p-norm exponent for attentional bias computation (for 'moneta' architecture)",
    )
    moneta_gate_p: float = Field(
        default=1.5,
        description="p-norm exponent for retention gate computation (for 'moneta' architecture)",
    )
    moneta_regularization_weight: float = Field(
        default=0.01,
        description="weight for regularization term in moneta loss (for 'moneta' architecture)",
    )
    memora_temperature: float = Field(
        default=1.0,
        description="softmax temperature for probability map; lower values sharpen distribution (for 'memora' architecture)",
    )
    architecture: MIRASArchitecture = Field(
        default=MIRASArchitecture.DEFAULT,
        description="""MIRAS framework variant to use:
- 'default': Original Titans with MSE loss (baseline)
- 'yaad': Huber loss for robustness to outliers
- 'moneta': Generalized p-norms for bias and retention
- 'memora': Probability map constraints for stable updates""",
    )
    memora_normalize_mode: MemoraNormalizeMode = Field(
        default=MemoraNormalizeMode.L2,
        description="normalization mode for memora probability maps: 'softmax', 'l1', or 'l2' (for 'memora' architecture)",
    )
