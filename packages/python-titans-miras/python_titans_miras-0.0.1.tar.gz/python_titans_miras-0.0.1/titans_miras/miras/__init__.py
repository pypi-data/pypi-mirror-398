"""
MIRAS Framework: Memory-Informed Retrieval and Storage

The MIRAS framework unifies sequence modeling through four key design choices:
1. Memory Architecture: Structure storing information (vector, matrix, or deep MLP)
2. Attentional Bias: Internal learning objective determining what to prioritize
3. Retention Gate: Memory regularizer balancing new learning vs. past knowledge
4. Memory Algorithm: Optimization algorithm for updating memory

This module implements:
- Base classes for AttentionalBias and RetentionGate
- Three MIRAS variants: YAAD, MONETA, MEMORA
- MIRAS for composing the framework components
"""

from __future__ import annotations
from typing import Literal
from titans_miras.miras.config import MIRASConfig
from titans_miras.miras.bias import AttentionalBias, MSEBias, HuberBias, GeneralizedNormBias
from titans_miras.miras.retention import (
    RetentionGate,
    MSERetentionGate,
    GeneralizedNormRetentionGate,
    ProbabilityMapRetentionGate,
)


class MIRAS:
    """
    Memory-Informed Retrieval and Storage framework.



    This class encapsulates the three key MIRAS settings:
    - The `attentional_bias` loss used to train the memory component.
    - The `retention_gate` mechanism for balancing old vs. new memory information.
    - The `memory_algorithm` specifies how the memory is updated (currently only 'gradient' is supported).

    Factory methods for common MIRAS variants:
        - `MIRAS.default`:   Original Titans (MSE loss + MSE gate)
        - `MIRAS.yaad`:      YAAD (Huber loss + MSE gate)
        - `MIRAS.moneta`:    MONETA (Generalized p-norm loss + Generalized p-norm gate)
        - `MIRAS.memora`:    MEMORA (MSE loss + probability map gate)

    Args:
        attentional_bias (AttentionalBias): The loss function or attentional bias to optimize.
        retention_gate (RetentionGate): The retention (forgetting) mechanism controlling memory updating.
        memory_algorithm (Literal["gradient"]): Algorithm to update memory (currently only "gradient").
    """

    def __init__(
        self,
        attentional_bias: AttentionalBias,
        retention_gate: RetentionGate,
        memory_algorithm: Literal["gradient"] = "gradient",
    ):
        self.attentional_bias = attentional_bias
        self.retention_gate = retention_gate
        self.memory_algorithm = memory_algorithm

    @classmethod
    def default(cls) -> "MIRAS":
        """
        Create the default MIRAS setup, matching the original Titans behavior
        with MSE loss and a standard MSE-based retention gate.
        """
        return cls(
            attentional_bias=MSEBias(),
            retention_gate=MSERetentionGate(),
        )

    @classmethod
    def yaad(cls, delta: float = 1.0) -> "MIRAS":
        """
        Create a YAAD variant MIRAS config using the Huber loss attentional bias
        (robust to outliers) and an MSE-based retention gate.

        Args:
            delta (float): Threshold for the Huber loss quadratic-to-linear transition.
        """
        return cls(
            attentional_bias=HuberBias(delta=delta),
            retention_gate=MSERetentionGate(),
        )

    @classmethod
    def moneta(
        cls,
        bias_p: float = 1.5,
        gate_p: float = 1.5,
        regularization_weight: float = 0.01,
    ) -> "MIRAS":
        """
        Create a MONETA variant MIRAS config using generalized p-norms.

        Args:
            bias_p (float): Norm order for the attentional bias (loss).
            gate_p (float): Norm order for the retention gate.
            regularization_weight (float): Retention gate regularization strength.
        """
        return cls(
            attentional_bias=GeneralizedNormBias(p=bias_p),
            retention_gate=GeneralizedNormRetentionGate(
                p=gate_p,
                regularization_weight=regularization_weight,
            ),
        )

    @classmethod
    def memora(
        cls,
        temperature: float = 1.0,
        normalize_mode: Literal["softmax", "l1", "l2"] = "l2",
    ) -> "MIRAS":
        """
        Create a MEMORA variant MIRAS config, constraining the retention dynamics to
        act like probability distributions (strict normalization).

        Args:
            temperature (float): Softmax temperature for probability map gate.
            normalize_mode (Literal): Normalization method - "softmax", "l1", or "l2".
        """
        return cls(
            attentional_bias=MSEBias(),
            retention_gate=ProbabilityMapRetentionGate(
                temperature=temperature,
                normalize_mode=normalize_mode,
            ),
        )

    @classmethod
    def from_config(cls, config: MIRASConfig) -> "MIRAS":
        """
        Create a MIRAS instance from a MIRASConfig dataclass.

        Dispatches to the appropriate variant based on `config.architecture`.
        """
        if config.architecture == "default":
            return cls.default()
        elif config.architecture == "yaad":
            return cls.yaad(delta=config.yaad_delta)
        elif config.architecture == "moneta":
            return cls.moneta(
                bias_p=config.moneta_bias_p,
                gate_p=config.moneta_gate_p,
                regularization_weight=config.moneta_regularization_weight,
            )
        elif config.architecture == "memora":
            return cls.memora(temperature=config.memora_temperature, normalize_mode=config.memora_normalize_mode)


__all__ = [
    "MIRAS",
    "AttentionalBias",
    "MSEBias",
    "HuberBias",
    "GeneralizedNormBias",
    "MSERetentionGate",
    "GeneralizedNormRetentionGate",
    "ProbabilityMapRetentionGate",
]
