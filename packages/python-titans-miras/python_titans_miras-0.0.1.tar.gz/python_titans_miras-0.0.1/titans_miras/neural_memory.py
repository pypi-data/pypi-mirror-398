from __future__ import annotations
from collections import namedtuple
from typing import Callable
import math
from itertools import zip_longest
from tensordict import TensorDict
from assoc_scan import AssocScan
import einx
from einops import einsum, rearrange, repeat, reduce, pack, unpack
from einops.layers.torch import Rearrange
import torch
from torch import (
    nn,
    no_grad,
    stack,
    cat,
    tensor,
    randn,
    where,
    arange,
    is_tensor,
)
from torch.func import functional_call, vmap, grad
from torch.utils._pytree import tree_map
import torch.nn.functional as F
import torch.nn as nn
from torch.nn import Linear, RMSNorm, Identity, ParameterList
from titans_miras.norm.residual_norm import ResidualNorm
from titans_miras.memory.memory_mlp import MemoryMLP
from titans_miras.miras import MIRAS, MIRASConfig
from titans_miras.norm.multihead_rms_norm import MultiheadRMSNorm
from titans_miras.config import NeuralMemoryConfig
from titans_miras.shared.utils import is_not_none, divisible_by, xnor
from titans_miras.miras.bias import LinearNoBias


def mem_state_detach(state: NeuralMemState):
    assert isinstance(state, NeuralMemState)
    state = tree_map(lambda t: t.detach() if is_tensor(t) else t, tuple(state))
    return NeuralMemState(*state)


def neural_memory_default(*args):
    for arg in args:
        if is_not_none(arg):
            return arg
    return None


def safe_cat(inputs, dim=-2):
    inputs = tuple(filter(is_not_none, inputs))
    if len(inputs) == 0:
        return None
    elif len(inputs) == 1:
        return inputs[0]
    return cat(inputs, dim=dim)


def is_empty_tensor(t):
    return t.numel() == 0


def dict_get_value_shapes(td):
    return [v.shape for k, v in td.items()]


def rearrange_dict_values(td, pattern, **kwargs):
    return td.apply(lambda t: rearrange(t, pattern, **kwargs))


def repeat_dict_values(td, pattern, **kwargs):
    return td.apply(lambda t: repeat(t, pattern, **kwargs))


def pair(v):
    return (v, v) if not isinstance(v, tuple) else v


def round_down_multiple(seq, mult):
    return seq // mult * mult


def round_up_multiple(seq, mult):
    return math.ceil(seq / mult) * mult


def pad_at_dim(t, pad, dim=-1, value=0.0):
    dims_from_right = (-dim - 1) if dim < 0 else (t.ndim - dim - 1)
    zeros = (0, 0) * dims_from_right
    return F.pad(t, (*zeros, *pad), value=value)


def pack_one_with_inverse(t, pattern):
    packed, packed_shape = pack([t], pattern)

    def inverse(out, inv_pattern=None):
        inv_pattern = neural_memory_default(inv_pattern, pattern)
        return unpack(out, packed_shape, inv_pattern)[0]

    return packed, inverse


def Sequential(*modules):
    modules = [*filter(is_not_none, modules)]
    if len(modules) == 0:
        return Identity()
    if len(modules) == 1:
        return modules[0]
    return nn.Sequential(*modules)


def _softclamp_max(t, max_value):
    """
    Soft clamping function for gradients.

    Applies a smooth tanh-based clamping to limit values to max_value.
    """
    half_max_value = max_value / 2
    return ((t / half_max_value).tanh() * half_max_value) + half_max_value


def softclamp_grad_norm(t, max_value):
    """
    Soft clamp gradient norms to max_value.

    This prevents gradient explosion while maintaining smooth gradients.
    """
    if is_empty_tensor(t):
        return t
    t, inverse = pack_one_with_inverse(t, "bn *")
    norm = t.norm(dim=-1, keepdim=True)
    clamped_norm = _softclamp_max(norm, max_value)
    t = t * (clamped_norm / norm)
    return inverse(t)


def newtonschulz5(t, steps=5, eps=1e-7, coefs=(3.4445, -4.7750, 2.0315)):
    """
    Spectral normalization using Newton-Schulz iteration.

    Spectral norms the surprise update with Newton-Schulz matrix iteration.
    Reference: Keller Jordan et al. from OSS w/ nanogpt, now being used for two works,
    Atlas and 'TTT done right'.

    Args:
        t: Input tensor to normalize
        steps: Number of Newton-Schulz iterations. Default is 5.
        eps: Small epsilon for numerical stability. Default is 1e-7.
        coefs: Coefficients for the iteration. Default is (3.4445, -4.7750, 2.0315).

    Returns:
        Spectrally normalized tensor
    """
    if t.ndim <= 3:
        return t
    shape = t.shape
    should_transpose = shape[-2] > shape[-1]
    if should_transpose:
        t = t.transpose(-1, -2)
    t, inv_pack = pack_one_with_inverse(t, "* i j")
    t = t / t.norm(dim=(-1, -2), keepdim=True).clamp(min=eps)
    a, b, c = coefs
    for _ in range(steps):
        A = t @ t.transpose(-1, -2)
        B = b * A + c * A @ A
        t = a * t + B @ t
    if should_transpose:
        t = t.transpose(-1, -2)
    return inv_pack(t)


def default_adaptive_step_transform(adaptive_step, max_lr=1e-2):
    """
    Default adaptive step transform for neural memory learning rates.

    Transforms the adaptive step through sigmoid scaling to produce a learning rate
    in the range [0, max_lr].

    Args:
        adaptive_step: Raw adaptive step value
        max_lr: Maximum learning rate. Default is 1e-2.

    Returns:
        Transformed learning rate
    """
    return adaptive_step.sigmoid() * max_lr


NeuralMemState = namedtuple(
    "NeuralMemState",
    [
        "seq_index",
        "weights",
        "cache_store_segment",
        "states",
        "updates",
    ],
)


class AveragePool(nn.Module):
    def __init__(self, chunk_size):
        super().__init__()
        self.chunk_size = chunk_size

    def forward(self, x, chunk_size=None):
        chunk_size = neural_memory_default(chunk_size, self.chunk_size)
        return reduce(x, "b (n c) d -> b n d", "mean", c=chunk_size)


class AttentionPool(nn.Module):
    def __init__(self, dim, chunk_size):
        """
        taken from Enformer https://www.nature.com/articles/s41592-021-01252-x , in turn taken from somewhere else
        """
        super().__init__()
        self.chunk_size = chunk_size
        self.to_attn_logits = Linear(dim, dim)
        nn.init.zeros_(self.to_attn_logits.weight)
        nn.init.zeros_(self.to_attn_logits.bias)

    def forward(self, x, chunk_size=None):
        chunk_size = neural_memory_default(chunk_size, self.chunk_size)
        x = rearrange(x, "b (n c) d -> b n c d", c=chunk_size)
        attn_logits = self.to_attn_logits(x)
        attn = attn_logits.softmax(dim=-2)
        return reduce(x * attn, "b n c d -> b n d", "sum")


def SequentialLinearNoBias(dim: int, dim_inner: int, activation: nn.Module | None = None):
    """Create a Sequential of LinearNoBias optionally followed by an activation."""
    return Sequential(LinearNoBias(dim, dim_inner), activation)


class NeuralMemory(nn.Module):
    """
    Neural Memory module implementing the Titans memory mechanism.

    This module stores and retrieves information using a small neural network (memory model)
    whose weights are updated online during the forward pass. The key insight is that
    memories are encoded in the weights of the memory model, and retrieval is performed
    by querying this model with learned queries.

    Key concepts:
    - Store: Updates memory model weights using gradient descent on a reconstruction loss
    - Retrieve: Queries the memory model to fetch stored information
    - MIRAS: Framework for different attention bias and retention strategies


    Attributes:

        retrieve_chunk_size (int): Chunk size for memory retrieval operations.
        store_chunk_size (int): Chunk size for memory storage operations.
        max_mem_layer_modulation (float): Max scaling factor for per-layer LR modulation.
        momentum_order (int): Order of momentum (1=first-order, 2=second-order, etc.).
        num_kv_per_token (int): Number of key-value pairs generated per input token.
        max_grad_norm (float): Softclamp threshold for gradient norms during storage.

        apply_spectral_norm_surprises (bool): Whether to apply spectral normalization to updates.
        include_zeroth_order_in_learned_combination (bool): Include raw gradient in momentum combination.
        use_accelerated_scan (bool): Use hardware-accelerated associative scan.

        miras (MIRAS): MIRAS framework for attentional bias and retention strategies.
        assoc_scan (AssocScan): Associative scan operator for parallel momentum/decay.
        retrieve_norm (Module): Pre-normalization for retrieval inputs.
        store_norm (Module): Pre-normalization for storage inputs.
        multihead_rmsnorm (Module): Post-normalization for retrieved values.
        q_norm (Module): Normalization applied to queries.
        k_norm (Module): Normalization applied to keys.
        split_heads (Rearrange): Reshape op to split into multiple heads.
        split_kv_heads (Rearrange): Reshape op to split KV pairs into heads.
        merge_heads (Rearrange): Reshape op to merge heads back together.
        combine_heads (Module): Linear projection after merging heads.
        retrieve_gate (Module | None): Optional gating for retrieved values.
        memory_model (Module): The neural network whose weights store memories.
        per_sample_grad_fn (Callable): Vmapped gradient function for per-sample updates.
        to_queries (Module): Projects input to query vectors for retrieval.
        to_keys (Module): Projects input to key vectors for storage.
        to_values (Module): Projects input to value vectors for storage.
        reduce_to_chunk_rep (Module): Reduces sequences to chunk representations.
        to_adaptive_step (Module): Predicts per-position adaptive learning rates.
        adaptive_step_transform (Callable): Transforms raw LR predictions (e.g., sigmoid).
        to_momentum (Module | None): Predicts per-chunk momentum coefficients.
        to_learned_momentum_combine (Module | None): Predicts weights for momentum orders.
        to_layer_modulation (Module | None): Predicts per-layer LR modulation factors.
        to_learned_weight_residual_mix (Module | None): Predicts cross-layer weight blend.
        to_decay_factor (Module): Predicts per-chunk weight decay factors.
        transition_gate (Parameter | None): Learned gate for residual-to-update transition.

    Initialization process:
        1. Configuration Setup: Copy and validate config, set up chunk sizes for store/retrieve
        2. MIRAS Framework Configuration: MIRAS defines the attentional bias (loss function) and
           retention gate for memory updates. Supports legacy loss functions for backward compat.
        3. Core Module Configuration: Batch size constraints, associative scan setup, and view
           handling
        4. Normalization Layers: Pre/post RMSNorm for inputs, and optional QK normalization
        5. Multi-Head Operations: Rearrange ops for splitting/merging heads, plus optional gating
        6. Memory Model Initialization: The memory model is a small network whose weights store
           memories. Defaults to MemoryMLP if not provided. Validated for correct I/O shape.
        7. Per-Sample Gradient Function: Creates a vmapped gradient function for computing
           per-sample gradients of the memory model. Uses MIRAS attentional bias as the loss
           function. This is the core of the "learning" that happens during memory storage.
        8. Query/Key/Value Projections: Linear projections to create queries (for retrieval) and
           keys/values (for storage). Supports multiple KV pairs per token.
        9. Chunk Reduction Strategy: How to reduce sequences into chunk representations for memory
           updates. Either average pooling or learned attention pooling.
        10. Adaptive Learning Rate: Learned per-position learning rate for memory updates.
            Transformed through adaptive_step_transform (default: sigmoid scaling).
        11. Momentum Configuration: Optional N-th order momentum for memory updates (like
            Adam/SGD momentum). Supports learned combination of multiple momentum orders.
        12. Per-Layer Learning Rate Modulation: Optional learned modulation of learning rate per
            memory model layer.
        13. Weight Residual and Gradient Constraints: Weight residual (blend previous layer's
            weights into current), gradient clipping (softclamp gradient norms for stability),
            spectral norm (normalize updates like Muon optimizer - Jordan et al.)
        14. Weight Decay and Transition Gate: Decay factor (learned forgetting for weight decay),
            transition gate (smooth transition from residual to full updates - helps with
            instability when decreasing neural mem batch size)
        15. Parameter Initialization: Initialize biases for adaptive step, momentum, and decay to
            sensible starting values if specified in config.
        16. Final Setup: Complete initialization
    """

    def __init__(
        self,
        config: NeuralMemoryConfig,
        activation: nn.Module | None = None,
        adaptive_step_transform: Callable[[torch.Tensor], torch.Tensor] | None = None,
        miras_config: MIRASConfig | None = None,
        model: nn.Module | None = None,
    ) -> None:
        super().__init__()

        _config = config.model_copy(deep=True)
        _config.dim_head = neural_memory_default(_config.dim_head, _config.dim)
        assert not (_config.heads == 1 and _config.dim_head != _config.dim)
        self.retrieve_chunk_size, self.store_chunk_size = pair(_config.chunk_size)

        if miras_config is not None:
            self.miras = MIRAS.from_config(miras_config)
        else:
            self.miras = MIRAS.default()

        if is_not_none(_config.batch_size):
            assert divisible_by(_config.batch_size, self.store_chunk_size)
        self.batch_size = _config.batch_size
        self.assoc_scan = AssocScan(use_accelerated=_config.use_accelerated_scan)
        self.qkv_receives_diff_views = _config.qkv_receives_diff_views

        self.retrieve_norm = Identity()
        self.store_norm = Identity()
        self.multihead_rmsnorm = Identity()
        self.q_norm = Identity()
        self.k_norm = Identity()
        if config.pre_rmsnorm:
            self.retrieve_norm = RMSNorm(config.dim)
            self.store_norm = RMSNorm(config.dim)
        if config.post_rmsnorm:
            self.multihead_rmsnorm = MultiheadRMSNorm(config.dim_head, config.heads)
        if config.qk_rmsnorm:
            self.q_norm = MultiheadRMSNorm(config.dim_head, config.heads)
            self.k_norm = MultiheadRMSNorm(config.dim_head, config.heads)

        dim_inner = _config.dim_head * _config.heads
        self.heads = _config.heads
        self.split_heads = Rearrange("b n (h d) -> b h n d", h=_config.heads)
        self.split_kv_heads = Rearrange("b n (h u d) -> b h (n u) d", h=_config.heads, u=_config.num_kv_per_token)
        self.merge_heads = Rearrange("b h n d -> b n (h d)")
        self.combine_heads = Identity()
        self.retrieve_gate = None
        if _config.heads > 1:
            self.combine_heads = LinearNoBias(dim_inner, _config.dim)
            self.retrieve_gate = Sequential(
                LinearNoBias(_config.dim, _config.heads),
                Rearrange("b n h -> b h n 1"),
                nn.Sigmoid(),
            )

        if not is_not_none(model):
            model = MemoryMLP(_config.dim_head, **_config.default_model_kwargs)

        assert not is_not_none(next(model.buffers(), None)), "model cannot have buffers for now"
        test_shape = (3, 2, _config.dim_head)
        with no_grad():
            try:
                test_input = randn(test_shape)
                mem_model_output = model(test_input)
            except:
                raise RuntimeError(f"memory model unable to accept a tensor of shape {test_shape}")
            assert mem_model_output.shape == test_shape, "output of memory model needs to be same shape as input"

        if _config.mem_model_norm_add_residual:
            model = ResidualNorm(dim=_config.dim_head, model=model)
        self.memory_model = model

        mem_model_params = dict(model.named_parameters())
        self.num_memory_parameter_tensors = len(mem_model_params)
        self.memory_model_parameter_names = [*mem_model_params.keys()]
        memory_model_parameters = [*mem_model_params.values()]
        if _config.per_head_learned_parameters:
            memory_model_parameters = [repeat(p, "... -> h ...", h=_config.heads) for p in memory_model_parameters]
        self.init_weight_shape = [p.shape for p in memory_model_parameters]
        self.memory_model_parameters = ParameterList(memory_model_parameters)
        self.per_head_learned_parameters = _config.per_head_learned_parameters
        self.chunk_size = _config.chunk_size

        def forward_and_loss(
            params: dict[str, torch.Tensor],
            inputs: torch.Tensor,
            loss_weights: torch.Tensor,
            target: torch.Tensor,
        ) -> tuple[torch.Tensor, torch.Tensor]:
            pred = functional_call(self.memory_model, params, inputs)
            loss = self.miras.attentional_bias(pred, target)
            weighted_loss = loss * loss_weights
            return weighted_loss.sum(), loss

        grad_fn = grad(forward_and_loss, has_aux=True)
        self.per_sample_grad_fn = vmap(grad_fn, in_dims=(0, 0, 0, 0))

        assert _config.num_kv_per_token > 0
        self.to_queries = SequentialLinearNoBias(dim=_config.dim, dim_inner=dim_inner, activation=activation)
        _seq_dim_inner = dim_inner * _config.num_kv_per_token
        self.to_keys = SequentialLinearNoBias(dim=_config.dim, dim_inner=_seq_dim_inner, activation=activation)
        self.to_values = SequentialLinearNoBias(dim=_config.dim, dim_inner=_seq_dim_inner, activation=activation)
        self.num_kv_per_token = _config.num_kv_per_token

        _config.chunk_size = self.store_chunk_size
        assert not (
            _config.attn_pool_chunks and _config.chunk_size == 1
        ), "`attn_pool_chunks` cannot be set to True if `chunk_size` is set to 1"
        if not _config.attn_pool_chunks:
            self.reduce_to_chunk_rep = AveragePool(chunk_size=_config.chunk_size)
        else:
            self.reduce_to_chunk_rep = AttentionPool(_config.dim, chunk_size=_config.chunk_size)

        self.to_adaptive_step = Sequential(
            Linear(config.dim, config.heads * config.num_kv_per_token),
            Rearrange("b n (h u) -> (b h) (n u)", u=config.num_kv_per_token),
        )
        if adaptive_step_transform is None:

            def adaptive_step_transform(adaptive_step):
                return default_adaptive_step_transform(
                    adaptive_step=adaptive_step,
                    max_lr=config.default_step_transform_max_lr,
                )

        self.adaptive_step_transform = adaptive_step_transform

        self.to_momentum = None
        if _config.momentum:
            self.to_momentum = Sequential(
                Linear(_config.dim, _config.heads * _config.momentum_order),
                Rearrange("b n (h o) -> o (b h) n 1", o=_config.momentum_order),
            )

        self.momentum_order = _config.momentum_order
        self.to_learned_momentum_combine = None
        if _config.learned_momentum_combine:
            assert _config.momentum
            assert (
                _config.momentum_order > 1
            ), "only second order momentum allowed for now, but may allow learned combination of zeroth"
            if _config.learned_combine_include_zeroth:
                _config.momentum_order += 1
            self.to_learned_momentum_combine = Sequential(
                Linear(_config.dim, _config.heads * _config.momentum_order),
                Rearrange("b n (h o) -> o (b h) n", h=_config.heads),
                nn.Softmax(dim=0),
            )
            self.include_zeroth_order_in_learned_combination = _config.learned_combine_include_zeroth

        self.to_layer_modulation = None
        if _config.per_parameter_lr_modulation:
            self.to_layer_modulation = Sequential(
                Linear(_config.dim, _config.heads * self.num_memory_parameter_tensors),
                Rearrange("b n (h w) -> w (b h) n", h=_config.heads),
                nn.Sigmoid(),
            )
        self.max_mem_layer_modulation = _config.max_mem_layer_modulation

        self.to_learned_weight_residual_mix = (
            Sequential(
                Linear(_config.dim, _config.heads),
                Rearrange("b n h -> b h n"),
                nn.Sigmoid(),
            )
            if _config.accept_weight_residual
            else None
        )
        self.max_grad_norm = _config.max_grad_norm
        self.apply_spectral_norm_surprises = _config.apply_spectral_norm_surprises

        self.to_decay_factor = Sequential(Linear(_config.dim, _config.heads), Rearrange("b n h -> (b h) n 1"))
        self.transition_gate = nn.Parameter(tensor(-5.0)) if _config.gated_transition else None

        if is_not_none(_config.init_adaptive_step_bias):
            linear = self.to_adaptive_step[0]
            nn.init.zeros_(linear.weight)
            nn.init.constant_(linear.bias, _config.init_adaptive_step_bias)
        if is_not_none(_config.init_momentum_bias):
            linear = self.to_momentum[0]
            nn.init.zeros_(linear.weight)
            nn.init.constant_(linear.bias, _config.init_momentum_bias)
        if is_not_none(_config.init_decay_bias):
            linear = self.to_decay_factor[0]
            nn.init.zeros_(linear.weight)
            nn.init.constant_(linear.bias, _config.init_decay_bias)

        self.use_accelerated_scan = _config.use_accelerated_scan
        self.register_buffer("zero", tensor(0.0), persistent=False)

    @property
    def memory_model_parameter_dict(self) -> TensorDict:
        """Get memory model parameters as a TensorDict keyed by parameter name."""
        return TensorDict(
            dict(
                zip(
                    self.memory_model_parameter_names,
                    self.memory_model_parameters,
                )
            )
        )

    def init_weights(self, batch: int) -> TensorDict:
        """
        Initialize memory model weights for a given batch size.

        Expands the learned initial parameters to have a batch dimension.
        If per_head_learned_parameters is True, each head has its own
        learned initialization; otherwise all heads share the same init.

        Args:
            batch: Batch size

        Returns:
            TensorDict of weights with shape [(batch * heads), ...]
        """
        if self.per_head_learned_parameters:
            weights = repeat_dict_values(self.memory_model_parameter_dict, "h ... -> (b h) ...", b=batch)
        else:
            weights = repeat_dict_values(
                self.memory_model_parameter_dict,
                "... -> bh ...",
                bh=batch * self.heads,
            )
        return weights

    def init_momentum(self, batch: int) -> TensorDict:
        """
        Initialize momentum buffers to zeros for a given batch size.

        Creates zero-initialized momentum tensors matching the memory model
        parameter shapes, with an additional dimension for momentum order.

        Args:
            batch: Batch size

        Returns:
            TensorDict of zero momentum with shape [order, (batch * heads), ...]
        """
        zeros = self.memory_model_parameter_dict.clone().zero_()
        if self.per_head_learned_parameters:
            zeros = repeat_dict_values(zeros, "h ... -> o (b h) ...", b=batch, o=self.momentum_order)
        else:
            zeros = repeat_dict_values(
                zeros,
                "... -> o bh ...",
                bh=batch * self.heads,
                o=self.momentum_order,
            )
        return zeros

    def store_memories(
        self,
        seq: torch.Tensor,
        weights: dict[str, torch.Tensor] | None = None,
        past_state: tuple[TensorDict, TensorDict] | None = None,
        seq_index: int = 0,
        prev_weights: TensorDict | None = None,
        mask: torch.Tensor | None = None,
        return_surprises: bool = True,
    ):
        """
        Store information into the neural memory by updating memory model weights.

        This is the "learning" phase where the memory model weights are updated via
        gradient descent to minimize a reconstruction loss (predicting values from keys).

        Args:
            seq: Input sequence to store [batch, seq_len, dim]
            weights: Current memory model weights (initialized if None)
            past_state: Previous (weights, momentum) state for continuity
            seq_index: Current position in the overall sequence
            prev_weights: Weights from previous layer (for cross-layer influence)
            mask: Boolean mask for selective storage (False = don't store)
            return_surprises: Whether to return surprise metrics

        Returns:
            updates: Updated weights at each chunk timestep
            next_store_state: State to pass to next call
            surprises: (optional) Tuple of (unweighted_loss, adaptive_lr)

        Storage process:
            1. Shape Extraction and Sequence Chunking: Split sequence into complete chunks;
               remainder is cached for next call. Only complete chunks can be used to update memory.
            2. Weight Initialization: Initialize memory model weights if not provided.
               Expand weights for computing surprise across chunks.
            3. Input Normalization and View Separation: Apply store norm. Handle case where K/V
               come from different views.
            4. Derive Learned Hyperparameters: Compute adaptive learning rate, decay factor,
               momentum, and layer-wise LR modulation from the input sequence.
            5. Key/Value Projection and Reshaping: Project to keys and values, split into heads,
               apply K norm, then reshape for chunked per-sample gradient computation.
            6. Adaptive LR Reshaping and Masking: Reshape adaptive LR to match chunked layout.
               Apply mask to zero out LR where storage should be disabled.
            7. Cross-Layer Weight Influence: Optionally blend in weights from the previous layer
               to allow cross-layer information flow in the surprise computation.
            8. Compute Per-Sample Gradients (The "Surprise"): This is the core learning step:
               compute gradients of reconstruction loss w.r.t. memory model weights. The gradient
               magnitude indicates how "surprised" the memory is by the new key-value pair.
            9. Gradient Post-Processing: Apply softclamp to limit gradient magnitude, restore
               dimensions, and apply per-layer LR modulation if configured.
            10. Initialize Past State: If no past state provided, initialize with current weights
                and zero momentum. W0 corresponds to initial weights in Figure 7 of TTT paper.
            11. Early Return for Incomplete Chunks: If sequence is shorter than chunk size, return
                current weights without any updates (remainder is cached for next call).
            12. Apply Momentum and Retention Gate: For each memory parameter: (1) Apply N-th order
                momentum via associative scan (eq 10), (2) Optionally spectral normalize updates
                (Muon-style), (3) Apply MIRAS retention gate for decay/forgetting (eq 13)
            13. Prepare Return State: Package the next state and return updates + state + surprises.
        """

        if self.qkv_receives_diff_views:
            _, batch, seq_len = seq.shape[:3]
        else:
            batch, seq_len = seq.shape[:2]

        heads, chunk_size, num_updates = (
            self.heads,
            self.store_chunk_size,
            self.num_kv_per_token,
        )

        round_down_seq_len = round_down_multiple(seq_len, chunk_size)
        num_chunks = round_down_seq_len // chunk_size
        seq, remainder = (
            seq[..., :round_down_seq_len, :],
            seq[..., round_down_seq_len:, :],
        )
        next_seq_len_index = seq_index + round_down_seq_len

        if not is_not_none(weights):
            weights = self.init_weights(batch)
        weights = TensorDict(weights)
        weights_for_surprise = repeat_dict_values(weights, "b ... -> b n ...", n=num_chunks)

        seq = self.store_norm(seq)
        values_seq = seq
        if self.qkv_receives_diff_views:
            seq, values_seq = seq

        adaptive_lr = self.to_adaptive_step(seq)
        adaptive_lr = self.adaptive_step_transform(adaptive_lr)
        chunked_seq = self.reduce_to_chunk_rep(seq, chunk_size=chunk_size)
        decay_factor = self.to_decay_factor(chunked_seq).sigmoid()

        need_layer_lr_mod = is_not_none(self.to_layer_modulation) and num_chunks > 0
        has_momentum = is_not_none(self.to_momentum)

        if has_momentum:
            adaptive_momentum = self.to_momentum(chunked_seq).sigmoid()
            learned_combine = is_not_none(self.to_learned_momentum_combine)
            if learned_combine:
                combine_momentums = self.to_learned_momentum_combine(chunked_seq)

        if need_layer_lr_mod:
            layer_lr_mod = self.to_layer_modulation(chunked_seq) * self.max_mem_layer_modulation

        keys = self.to_keys(seq)
        values = self.to_values(values_seq)
        keys, values = map(self.split_kv_heads, (keys, values))
        keys = self.k_norm(keys)

        keys, values = tuple(
            rearrange(
                t,
                "b h (n c u) d -> (b h n) (c u) d",
                c=chunk_size,
                u=num_updates,
            )
            for t in (keys, values)
        )

        adaptive_lr = rearrange(adaptive_lr, "b (n c u) -> (b n) (c u)", c=chunk_size, u=num_updates)

        if is_not_none(mask):
            mask = mask[..., :round_down_seq_len]
            mask = repeat(
                mask,
                "b (n c) -> (b h n) (c u)",
                h=heads,
                u=num_updates,
                c=chunk_size,
            )
            adaptive_lr = where(mask, adaptive_lr, 0.0)

        assert xnor(is_not_none(self.to_learned_weight_residual_mix), is_not_none(prev_weights))
        if is_not_none(prev_weights):
            start_index = math.ceil(seq_index / chunk_size)
            end_index = start_index + num_chunks
            prev_weights = prev_weights.apply(lambda t: t[:, start_index:end_index])

            if is_not_none(self.to_learned_weight_residual_mix) and num_chunks > 0:
                mix = self.to_learned_weight_residual_mix(chunked_seq)
                mix = rearrange(mix, "b h n -> (b h) n")
                prev_weights = prev_weights.apply(lambda t: einx.multiply("bh n, bh n ... -> bh n ...", mix, t))

            weights_for_surprise = weights_for_surprise + prev_weights

        weights_for_surprise = rearrange_dict_values(weights_for_surprise, "b n ... -> (b n) ...")

        grads, unweighted_mem_model_loss = self.per_sample_grad_fn(
            dict(weights_for_surprise), keys, adaptive_lr, values
        )
        grads = TensorDict(grads)

        adaptive_lr = rearrange(adaptive_lr, "(b h n) c -> b h (n c)", b=batch, h=heads)
        unweighted_mem_model_loss = rearrange(
            unweighted_mem_model_loss,
            "(b h n) c -> b h (n c)",
            b=batch,
            h=heads,
        )

        if is_not_none(self.max_grad_norm):
            grads = grads.apply(lambda t: softclamp_grad_norm(t, self.max_grad_norm))

        grads = rearrange_dict_values(grads, "(b n) ... -> b n ...", b=batch * heads)

        if need_layer_lr_mod:
            grads = TensorDict(
                {
                    name: einx.multiply("b h, b h ... -> b h ...", layer_lr_mod, t)
                    for layer_lr_mod, (name, t) in zip(layer_lr_mod, grads.items())
                }
            )

        surprises = grads.mul(-1)

        if not is_not_none(past_state):
            minibatch_init_weight = weights
            init_momentum = self.init_momentum(batch)
            past_state = (minibatch_init_weight, init_momentum)

        past_last_update, past_last_momentum = past_state

        if num_chunks == 0:
            updates = rearrange_dict_values(weights, "bh ... -> bh 1 ...")
            next_store_state = NeuralMemState(next_seq_len_index, weights, remainder, past_state, updates)
            output = (updates, next_store_state)
            if not return_surprises:
                return output
            return (*output, (unweighted_mem_model_loss, adaptive_lr))

        updates = TensorDict()
        next_last_update = TensorDict()
        next_last_momentum = TensorDict()

        for (param_name, surprise), (_, last_update) in zip(surprises.items(), past_last_update.items()):
            update = surprise

            if has_momentum:
                momentum = surprise
                momentums = []
                last_momentum = past_last_momentum[param_name]

                for one_adaptive_momentum, one_last_momentum in zip_longest(adaptive_momentum, last_momentum):
                    momentum = self.assoc_scan(one_adaptive_momentum, momentum, prev=one_last_momentum)
                    momentums.append(momentum)

                momentums = stack(momentums)
                next_last_momentum[param_name] = momentums[:, :, -1]

                if learned_combine and self.include_zeroth_order_in_learned_combination:
                    momentums = cat((rearrange(surprise, "... -> 1 ..."), momentums), dim=0)

                if not learned_combine:
                    update = momentums[-1]
                else:
                    update = einsum(
                        combine_momentums,
                        momentums,
                        "o b n, o b n ... -> b n ...",
                    )

            if self.apply_spectral_norm_surprises:
                update = newtonschulz5(update)

            update = self.miras.retention_gate(update, decay_factor, last_update)

            update = self.miras.retention_gate.combine_with_scan(
                self.assoc_scan, decay_factor, update, prev_state=last_update
            )

            updates[param_name] = update
            next_last_update[param_name] = update[:, -1]

        next_state = (next_last_update, next_last_momentum)
        next_store_state = NeuralMemState(next_seq_len_index, weights, remainder, next_state, updates)

        if not return_surprises:
            return updates, next_store_state
        return (
            updates,
            next_store_state,
            (unweighted_mem_model_loss, adaptive_lr),
        )

    def retrieve_memories(
        self,
        seq: torch.Tensor,
        weights: dict[str, torch.Tensor],
    ) -> torch.Tensor:
        """
        Retrieve information from neural memory by querying the memory model.

        The memory model's weights encode stored key-value associations.
        Retrieval is performed by passing learned queries through this model.
        When the memory model is a single linear layer, this is equivalent to
        the "fast weight" / linear attention mechanism (q @ kv^T).

        Args:
            seq: Query sequence [batch, seq_len, dim]
            weights: Memory model weights (may have time dimension for chunked weights)

        Returns:
            Retrieved values [batch, seq_len, dim]
        """

        chunk_size = self.retrieve_chunk_size
        weights_have_expanded_shape = dict_get_value_shapes(weights) != self.init_weight_shape
        batch, seq_len = seq.shape[:2]

        is_one_token = seq_len == 1
        is_one_weight = (not weights_have_expanded_shape) or next(iter(weights.values())).shape[1] == 1
        is_single_token_decode = is_one_token and is_one_weight

        if is_single_token_decode:
            chunk_size = 1

        need_pad = chunk_size > 1 or not is_one_weight
        if need_pad:
            seq = pad_at_dim(seq, (1, 0), dim=1)

        seq_len_plus_one = seq.shape[-2]
        next_seq_len = round_up_multiple(seq_len_plus_one, chunk_size)
        padding = next_seq_len - seq_len_plus_one
        seq = pad_at_dim(seq, (0, padding), dim=1)

        weights = TensorDict(weights)

        seq = self.retrieve_norm(seq)
        queries = self.to_queries(seq)
        queries = self.split_heads(queries)
        queries = self.q_norm(queries)

        if weights_have_expanded_shape:
            weights = rearrange_dict_values(weights, "b n ... -> (b n) ...")

        queries = rearrange(queries, "b h (n c) d -> (b h n) c d", c=chunk_size)
        values = functional_call(self.memory_model, dict(weights), queries)

        values = rearrange(values, "(b h n) c d -> b h (n c) d", b=batch, h=self.heads)
        values = self.multihead_rmsnorm(values)

        if is_not_none(self.retrieve_gate):
            values = values * self.retrieve_gate(seq)

        values = self.merge_heads(values)
        values = self.combine_heads(values)

        if need_pad:
            values = values[:, 1:]

        return values[:, :seq_len]

    def forward(
        self,
        seq: torch.Tensor,
        store_seq: torch.Tensor | None = None,
        state: NeuralMemState | None = None,
        detach_mem_state: bool = False,
        prev_weights: TensorDict | None = None,
        store_mask: torch.Tensor | None = None,
        return_surprises: bool = False,
        ttt_batch_size: int | None = None,
    ) -> (
        tuple[torch.Tensor, NeuralMemState]
        | tuple[torch.Tensor, NeuralMemState, tuple[torch.Tensor | None, torch.Tensor | None]]
    ):
        """
        Main forward pass: store new information and retrieve from memory.

        This orchestrates the store-then-retrieve pattern:
        1. Store: Update memory model weights with new key-value pairs
        2. Retrieve: Query updated memory to get context for current position

        Supports TTT-style batching where weights are only committed at batch
        boundaries (batch_size parameter), enabling mini-batch gradient descent
        within the forward pass.

        Args:
            seq: Input sequence [batch, seq_len, dim] (or [batch, dim] for single token)
            store_seq: Separate sequence for storage (defaults to seq)
            state: Previous NeuralMemState for stateful processing
            detach_mem_state: Whether to detach gradients from returned state
            prev_weights: Weights from previous layer for cross-layer influence
            store_mask: Boolean mask for selective storage
            return_surprises: Whether to return surprise metrics
            ttt_batch_size: Override batch size for TTT-style updates

        Returns:
            retrieved: Retrieved memory values [batch, seq_len, dim]
            next_state: Updated NeuralMemState for next call
            surprises: (optional) Tuple of surprise metrics
        """
        is_multi_input = self.qkv_receives_diff_views

        if seq.ndim == 2 or (is_multi_input and seq.ndim == 3):
            seq = rearrange(seq, "... b d -> ... b 1 d")
        is_single_token = seq.shape[-2] == 1

        if is_multi_input:
            retrieve_seq, seq = seq[0], seq[1:]
        else:
            retrieve_seq = seq

        if not is_not_none(state):
            state = (0, None, None, None, None)
        seq_index, weights, cache_store_seq, past_state, updates = state

        store_seq = neural_memory_default(store_seq, seq)
        if is_not_none(cache_store_seq):
            store_seq = safe_cat((cache_store_seq, store_seq))

        store_seq_len, chunk_size, batch_size = (
            store_seq.shape[-2],
            self.chunk_size,
            neural_memory_default(ttt_batch_size, self.batch_size),
        )
        need_update_weights = is_not_none(batch_size)

        if need_update_weights:
            update_after_final_store = divisible_by(seq_index + store_seq_len, batch_size)
            seq_range = arange(store_seq_len) + seq_index + 1
            batch_boundary = divisible_by(seq_range, batch_size)
            indices = seq_range[batch_boundary] - seq_index
            indices = F.pad(indices, (1, 0), value=0)
            if indices[-1] != store_seq_len:
                indices = F.pad(indices, (0, 1), value=store_seq_len)
            split_sizes = (indices[1:] - indices[:-1]).tolist()
            assert sum(split_sizes) == store_seq_len
        else:
            split_sizes = (store_seq_len,)
            update_after_final_store = False

        updates: TensorDict | None = None

        def accum_updates(past_updates: TensorDict | None, future_updates: TensorDict) -> TensorDict:
            if not is_not_none(past_updates):
                return future_updates
            return TensorDict(
                {
                    param_name: cat((past_update[:, :-1], future_update), dim=1)
                    for (param_name, past_update), (_, future_update) in zip(
                        past_updates.items(), future_updates.items()
                    )
                }
            )

        store_seqs = store_seq.split(split_sizes, dim=-2)
        if is_not_none(store_mask):
            store_masks = store_mask.split(split_sizes, dim=-1)
        else:
            store_masks = (None,) * len(split_sizes)

        surprises = (None, None)
        gate = None
        if is_not_none(self.transition_gate):
            gate = self.transition_gate.sigmoid()

        for ind, (store_seq_chunk, maybe_store_mask) in enumerate(zip(store_seqs, store_masks)):
            is_last = ind == (len(store_seqs) - 1)

            (
                next_updates,
                next_neural_mem_state,
                chunk_surprises,
            ) = self.store_memories(
                store_seq_chunk,
                weights,
                seq_index=seq_index,
                past_state=past_state,
                prev_weights=prev_weights,
                mask=maybe_store_mask,
                return_surprises=True,
            )

            weights = next_neural_mem_state.weights
            seq_index = next_neural_mem_state.seq_index
            past_state = next_neural_mem_state.states
            updates = accum_updates(updates, next_updates)
            surprises = tuple(safe_cat(args, dim=-1) for args in zip(surprises, chunk_surprises))

            if is_last and not update_after_final_store:
                continue

            last_update, last_momentum = past_state

            if is_not_none(gate):
                last_update = TensorDict(
                    {
                        param_name: one_weight.lerp(one_last_update, gate)
                        for (param_name, one_weight), (
                            _,
                            one_last_update,
                        ) in zip(weights.items(), last_update.items())
                    }
                )

            past_state = (last_update, last_momentum)
            weights = last_update
            next_neural_mem_state = next_neural_mem_state._replace(
                weights=weights,
                states=past_state,
            )

        next_neural_mem_state = next_neural_mem_state._replace(updates=updates)

        if is_single_token:
            last_update, _ = next_neural_mem_state.states
            updates = rearrange_dict_values(last_update, "b ... -> b 1 ...")

        retrieved = self.retrieve_memories(seq=retrieve_seq, weights=updates)

        if detach_mem_state:
            next_neural_mem_state = mem_state_detach(next_neural_mem_state)

        if return_surprises:
            retrieved, next_neural_mem_state, surprises

        return retrieved, next_neural_mem_state
