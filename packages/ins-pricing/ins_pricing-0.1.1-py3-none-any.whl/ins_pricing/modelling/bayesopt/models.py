from __future__ import annotations

import copy
import hashlib
import math
import os
import time
from contextlib import nullcontext
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import optuna
import pandas as pd
import torch
import torch.distributed as dist
import torch.nn as nn
import torch.nn.functional as F
from sklearn.neighbors import NearestNeighbors
from torch.cuda.amp import autocast, GradScaler
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.nn.utils import clip_grad_norm_
from torch.utils.data import Dataset, TensorDataset

from .utils import DistributedUtils, EPS, IOUtils, TorchTrainerMixin

try:
    from torch_geometric.nn import knn_graph
    from torch_geometric.utils import add_self_loops, to_undirected
    _PYG_AVAILABLE = True
except Exception:
    knn_graph = None  # type: ignore
    add_self_loops = None  # type: ignore
    to_undirected = None  # type: ignore
    _PYG_AVAILABLE = False

try:
    import pynndescent
    _PYNN_AVAILABLE = True
except Exception:
    pynndescent = None  # type: ignore
    _PYNN_AVAILABLE = False

_GNN_MPS_WARNED = False

# =============================================================================
# ResNet model and sklearn-style wrapper
# =============================================================================

# ResNet model definition
# Residual block: two linear layers + ReLU + residual connection
# ResBlock inherits nn.Module
class ResBlock(nn.Module):
    def __init__(self, dim: int, dropout: float = 0.1,
                 use_layernorm: bool = False, residual_scale: float = 0.1,
                 stochastic_depth: float = 0.0
                 ):
        super().__init__()
        self.use_layernorm = use_layernorm

        if use_layernorm:
            Norm = nn.LayerNorm      # Normalize the last dimension
        else:
            def Norm(d): return nn.BatchNorm1d(d)  # Keep a switch to try BN

        self.norm1 = Norm(dim)
        self.fc1 = nn.Linear(dim, dim, bias=True)
        self.act = nn.ReLU(inplace=True)
        self.dropout = nn.Dropout(dropout) if dropout > 0.0 else nn.Identity()
        # Enable post-second-layer norm if needed: self.norm2 = Norm(dim)
        self.fc2 = nn.Linear(dim, dim, bias=True)

        # Residual scaling to stabilize early training
        self.res_scale = nn.Parameter(
            torch.tensor(residual_scale, dtype=torch.float32)
        )
        self.stochastic_depth = max(0.0, float(stochastic_depth))

    def _drop_path(self, x: torch.Tensor) -> torch.Tensor:
        if self.stochastic_depth <= 0.0 or not self.training:
            return x
        keep_prob = 1.0 - self.stochastic_depth
        if keep_prob <= 0.0:
            return torch.zeros_like(x)
        shape = (x.shape[0],) + (1,) * (x.ndim - 1)
        random_tensor = keep_prob + torch.rand(
            shape, dtype=x.dtype, device=x.device)
        binary_tensor = torch.floor(random_tensor)
        return x * binary_tensor / keep_prob

    def forward(self, x):
        # Pre-activation structure
        out = self.norm1(x)
        out = self.fc1(out)
        out = self.act(out)
        out = self.dropout(out)
        # If a second norm is enabled: out = self.norm2(out)
        out = self.fc2(out)
        # Apply residual scaling then add
        out = self.res_scale * out
        out = self._drop_path(out)
        return x + out

# ResNetSequential defines the full network


class ResNetSequential(nn.Module):
    # Input shape: (batch, input_dim)
    # Network: FC + norm + ReLU, stack residual blocks, output Softplus

    def __init__(self, input_dim: int, hidden_dim: int = 64, block_num: int = 2,
                 use_layernorm: bool = True, dropout: float = 0.1,
                 residual_scale: float = 0.1, stochastic_depth: float = 0.0,
                 task_type: str = 'regression'):
        super(ResNetSequential, self).__init__()

        self.net = nn.Sequential()
        self.net.add_module('fc1', nn.Linear(input_dim, hidden_dim))

        # Optional explicit normalization after the first layer:
        # For LayerNorm:
        #     self.net.add_module('norm1', nn.LayerNorm(hidden_dim))
        # Or BatchNorm:
        #     self.net.add_module('norm1', nn.BatchNorm1d(hidden_dim))

        # If desired, insert ReLU before residual blocks:
        # self.net.add_module('relu1', nn.ReLU(inplace=True))

        # Residual blocks
        drop_path_rate = max(0.0, float(stochastic_depth))
        for i in range(block_num):
            if block_num > 1:
                block_drop = drop_path_rate * (i / (block_num - 1))
            else:
                block_drop = drop_path_rate
            self.net.add_module(
                f'ResBlk_{i+1}',
                ResBlock(
                    hidden_dim,
                    dropout=dropout,
                    use_layernorm=use_layernorm,
                    residual_scale=residual_scale,
                    stochastic_depth=block_drop)
            )

        self.net.add_module('fc_out', nn.Linear(hidden_dim, 1))

        if task_type == 'classification':
            self.net.add_module('softplus', nn.Identity())
        else:
            self.net.add_module('softplus', nn.Softplus())

    def forward(self, x):
        if self.training and not hasattr(self, '_printed_device'):
            print(f">>> ResNetSequential executing on device: {x.device}")
            self._printed_device = True
        return self.net(x)

# Define the ResNet sklearn-style wrapper.


class ResNetSklearn(TorchTrainerMixin, nn.Module):
    def __init__(self, model_nme: str, input_dim: int, hidden_dim: int = 64,
                 block_num: int = 2, batch_num: int = 100, epochs: int = 100,
                 task_type: str = 'regression',
                 tweedie_power: float = 1.5, learning_rate: float = 0.01, patience: int = 10,
                 use_layernorm: bool = True, dropout: float = 0.1,
                 residual_scale: float = 0.1,
                 stochastic_depth: float = 0.0,
                 weight_decay: float = 1e-4,
                 use_data_parallel: bool = True,
                 use_ddp: bool = False):
        super(ResNetSklearn, self).__init__()

        self.use_ddp = use_ddp
        self.is_ddp_enabled, self.local_rank, self.rank, self.world_size = (
            False, 0, 0, 1)

        if self.use_ddp:
            self.is_ddp_enabled, self.local_rank, self.rank, self.world_size = DistributedUtils.setup_ddp()

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.block_num = block_num
        self.batch_num = batch_num
        self.epochs = epochs
        self.task_type = task_type
        self.model_nme = model_nme
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.patience = patience
        self.use_layernorm = use_layernorm
        self.dropout = dropout
        self.residual_scale = residual_scale
        self.stochastic_depth = max(0.0, float(stochastic_depth))
        self.loss_curve_path: Optional[str] = None
        self.training_history: Dict[str, List[float]] = {
            "train": [], "val": []}
        self.use_data_parallel = bool(use_data_parallel)

        # Device selection: cuda > mps > cpu
        if self.is_ddp_enabled:
            self.device = torch.device(f'cuda:{self.local_rank}')
        elif torch.cuda.is_available():
            self.device = torch.device('cuda')
        elif torch.backends.mps.is_available():
            self.device = torch.device('mps')
        else:
            self.device = torch.device('cpu')

        # Tweedie power (unused for classification)
        if self.task_type == 'classification':
            self.tw_power = None
        elif 'f' in self.model_nme:
            self.tw_power = 1
        elif 's' in self.model_nme:
            self.tw_power = 2
        else:
            self.tw_power = tweedie_power

        # Build network (construct on CPU first)
        core = ResNetSequential(
            self.input_dim,
            self.hidden_dim,
            self.block_num,
            use_layernorm=self.use_layernorm,
            dropout=self.dropout,
            residual_scale=self.residual_scale,
            stochastic_depth=self.stochastic_depth,
            task_type=self.task_type
        )

        # ===== Multi-GPU: DataParallel vs DistributedDataParallel =====
        if self.is_ddp_enabled:
            core = core.to(self.device)
            core = DDP(core, device_ids=[
                       self.local_rank], output_device=self.local_rank)
            self.use_data_parallel = False
        elif use_data_parallel and (self.device.type == 'cuda') and (torch.cuda.device_count() > 1):
            if self.use_ddp and not self.is_ddp_enabled:
                print(
                    ">>> DDP requested but not initialized; falling back to DataParallel.")
            core = nn.DataParallel(core, device_ids=list(
                range(torch.cuda.device_count())))
            # DataParallel scatters inputs, but the primary device remains cuda:0.
            self.device = torch.device('cuda')
            self.use_data_parallel = True
        else:
            self.use_data_parallel = False

        self.resnet = core.to(self.device)

    # ================ Internal helpers ================
    @staticmethod
    def _validate_vector(arr, name: str, n_rows: int) -> None:
        if arr is None:
            return
        if isinstance(arr, pd.DataFrame):
            if arr.shape[1] != 1:
                raise ValueError(f"{name} must be 1d (single column).")
            length = len(arr)
        else:
            arr_np = np.asarray(arr)
            if arr_np.ndim == 0:
                raise ValueError(f"{name} must be 1d.")
            if arr_np.ndim > 2 or (arr_np.ndim == 2 and arr_np.shape[1] != 1):
                raise ValueError(f"{name} must be 1d or Nx1.")
            length = arr_np.shape[0]
        if length != n_rows:
            raise ValueError(
                f"{name} length {length} does not match X length {n_rows}."
            )

    def _validate_inputs(self, X, y, w, label: str) -> None:
        if X is None:
            raise ValueError(f"{label} X cannot be None.")
        n_rows = len(X)
        if y is None:
            raise ValueError(f"{label} y cannot be None.")
        self._validate_vector(y, f"{label} y", n_rows)
        self._validate_vector(w, f"{label} w", n_rows)

    def _build_train_val_tensors(self, X_train, y_train, w_train, X_val, y_val, w_val):
        self._validate_inputs(X_train, y_train, w_train, "train")
        if X_val is not None or y_val is not None or w_val is not None:
            if X_val is None or y_val is None:
                raise ValueError("validation X and y must both be provided.")
            self._validate_inputs(X_val, y_val, w_val, "val")

        def _to_numpy(arr):
            if hasattr(arr, "to_numpy"):
                return arr.to_numpy(dtype=np.float32, copy=False)
            return np.asarray(arr, dtype=np.float32)

        X_tensor = torch.as_tensor(_to_numpy(X_train))
        y_tensor = torch.as_tensor(_to_numpy(y_train)).view(-1, 1)
        w_tensor = (
            torch.as_tensor(_to_numpy(w_train)).view(-1, 1)
            if w_train is not None else torch.ones_like(y_tensor)
        )

        has_val = X_val is not None and y_val is not None
        if has_val:
            X_val_tensor = torch.as_tensor(_to_numpy(X_val))
            y_val_tensor = torch.as_tensor(_to_numpy(y_val)).view(-1, 1)
            w_val_tensor = (
                torch.as_tensor(_to_numpy(w_val)).view(-1, 1)
                if w_val is not None else torch.ones_like(y_val_tensor)
            )
        else:
            X_val_tensor = y_val_tensor = w_val_tensor = None
        return X_tensor, y_tensor, w_tensor, X_val_tensor, y_val_tensor, w_val_tensor, has_val

    def forward(self, x):
        # Handle SHAP NumPy input.
        if isinstance(x, np.ndarray):
            x_tensor = torch.as_tensor(x, dtype=torch.float32)
        else:
            x_tensor = x

        x_tensor = x_tensor.to(self.device)
        y_pred = self.resnet(x_tensor)
        return y_pred

    # ---------------- Training ----------------

    def fit(self, X_train, y_train, w_train=None,
            X_val=None, y_val=None, w_val=None, trial=None):

        X_tensor, y_tensor, w_tensor, X_val_tensor, y_val_tensor, w_val_tensor, has_val = \
            self._build_train_val_tensors(
                X_train, y_train, w_train, X_val, y_val, w_val)

        dataset = TensorDataset(X_tensor, y_tensor, w_tensor)
        dataloader, accum_steps = self._build_dataloader(
            dataset,
            N=X_tensor.shape[0],
            base_bs_gpu=(2048, 1024, 512),
            base_bs_cpu=(256, 128),
            min_bs=64,
            target_effective_cuda=2048,
            target_effective_cpu=1024
        )

        # Set sampler epoch at the start of each epoch to keep shuffling deterministic.
        if self.is_ddp_enabled and hasattr(dataloader.sampler, 'set_epoch'):
            self.dataloader_sampler = dataloader.sampler
        else:
            self.dataloader_sampler = None

        # === 4. Optimizer and AMP ===
        self.optimizer = torch.optim.Adam(
            self.resnet.parameters(),
            lr=self.learning_rate,
            weight_decay=float(self.weight_decay),
        )
        self.scaler = GradScaler(enabled=(self.device.type == 'cuda'))

        X_val_dev = y_val_dev = w_val_dev = None
        val_dataloader = None
        if has_val:
            # Build validation DataLoader.
            val_dataset = TensorDataset(
                X_val_tensor, y_val_tensor, w_val_tensor)
            # No backward pass in validation; batch size can be larger for throughput.
            val_dataloader = self._build_val_dataloader(
                val_dataset, dataloader, accum_steps)
            # Validation usually does not need a DDP sampler because we validate on the main process
            # or aggregate results. For simplicity, keep validation on a single GPU or the main process.

        is_data_parallel = isinstance(self.resnet, nn.DataParallel)

        def forward_fn(batch):
            X_batch, y_batch, w_batch = batch

            if not is_data_parallel:
                X_batch = X_batch.to(self.device, non_blocking=True)
            # Keep targets and weights on the main device for loss computation.
            y_batch = y_batch.to(self.device, non_blocking=True)
            w_batch = w_batch.to(self.device, non_blocking=True)

            y_pred = self.resnet(X_batch)
            return y_pred, y_batch, w_batch

        def val_forward_fn():
            total_loss = 0.0
            total_weight = 0.0
            for batch in val_dataloader:
                X_b, y_b, w_b = batch
                if not is_data_parallel:
                    X_b = X_b.to(self.device, non_blocking=True)
                y_b = y_b.to(self.device, non_blocking=True)
                w_b = w_b.to(self.device, non_blocking=True)

                y_pred = self.resnet(X_b)

                # Manually compute weighted loss for accurate aggregation.
                losses = self._compute_losses(
                    y_pred, y_b, apply_softplus=False)

                batch_weight_sum = torch.clamp(w_b.sum(), min=EPS)
                batch_weighted_loss_sum = (losses * w_b.view(-1)).sum()

                total_loss += batch_weighted_loss_sum.item()
                total_weight += batch_weight_sum.item()

            return total_loss / max(total_weight, EPS)

        clip_fn = None
        if self.device.type == 'cuda':
            def clip_fn(): return (self.scaler.unscale_(self.optimizer),
                                   clip_grad_norm_(self.resnet.parameters(), max_norm=1.0))

        # Under DDP, only the main process prints logs and saves models.
        if self.is_ddp_enabled and not DistributedUtils.is_main_process():
            # Non-main processes skip validation callback logging (handled inside _train_model).
            pass

        best_state, history = self._train_model(
            self.resnet,
            dataloader,
            accum_steps,
            self.optimizer,
            self.scaler,
            forward_fn,
            val_forward_fn if has_val else None,
            apply_softplus=False,
            clip_fn=clip_fn,
            trial=trial,
            loss_curve_path=getattr(self, "loss_curve_path", None)
        )

        if has_val and best_state is not None:
            self.resnet.load_state_dict(best_state)
        self.training_history = history

    # ---------------- Prediction ----------------

    def predict(self, X_test):
        self.resnet.eval()
        if isinstance(X_test, pd.DataFrame):
            X_np = X_test.to_numpy(dtype=np.float32, copy=False)
        else:
            X_np = np.asarray(X_test, dtype=np.float32)

        inference_cm = getattr(torch, "inference_mode", torch.no_grad)
        with inference_cm():
            y_pred = self(X_np).cpu().numpy()

        if self.task_type == 'classification':
            y_pred = 1 / (1 + np.exp(-y_pred))  # Sigmoid converts logits to probabilities.
        else:
            y_pred = np.clip(y_pred, 1e-6, None)
        return y_pred.flatten()

    # ---------------- Set Params ----------------

    def set_params(self, params):
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Parameter {key} not found in model.")
        return self


# =============================================================================
# FT-Transformer model and sklearn-style wrapper.
# =============================================================================
# Define FT-Transformer model structure.


class FeatureTokenizer(nn.Module):
    """Map numeric/categorical/geo tokens into transformer input tokens."""

    def __init__(
        self,
        num_numeric: int,
        cat_cardinalities,
        d_model: int,
        num_geo: int = 0,
        num_numeric_tokens: int = 1,
    ):
        super().__init__()

        self.num_numeric = num_numeric
        self.num_geo = num_geo
        self.has_geo = num_geo > 0

        if num_numeric > 0:
            if int(num_numeric_tokens) <= 0:
                raise ValueError("num_numeric_tokens must be >= 1 when numeric features exist.")
            self.num_numeric_tokens = int(num_numeric_tokens)
            self.has_numeric = True
            self.num_linear = nn.Linear(num_numeric, d_model * self.num_numeric_tokens)
        else:
            self.num_numeric_tokens = 0
            self.has_numeric = False

        self.embeddings = nn.ModuleList([
            nn.Embedding(card, d_model) for card in cat_cardinalities
        ])

        if self.has_geo:
            # Map geo tokens with a linear layer to avoid one-hot on raw strings; upstream is encoded/normalized.
            self.geo_linear = nn.Linear(num_geo, d_model)

    def forward(self, X_num, X_cat, X_geo=None):
        tokens = []

        if self.has_numeric:
            batch_size = X_num.shape[0]
            num_token = self.num_linear(X_num)
            num_token = num_token.view(batch_size, self.num_numeric_tokens, -1)
            tokens.append(num_token)

        for i, emb in enumerate(self.embeddings):
            tok = emb(X_cat[:, i])
            tokens.append(tok.unsqueeze(1))

        if self.has_geo:
            if X_geo is None:
                raise RuntimeError("Geo tokens are enabled but X_geo was not provided.")
            geo_token = self.geo_linear(X_geo)
            tokens.append(geo_token.unsqueeze(1))

        x = torch.cat(tokens, dim=1)
        return x

# Encoder layer with residual scaling.


class ScaledTransformerEncoderLayer(nn.Module):
    def __init__(self, d_model: int, nhead: int, dim_feedforward: int = 2048,
                 dropout: float = 0.1, residual_scale_attn: float = 1.0,
                 residual_scale_ffn: float = 1.0, norm_first: bool = True,
                 ):
        super().__init__()
        self.self_attn = nn.MultiheadAttention(
            embed_dim=d_model,
            num_heads=nhead,
            dropout=dropout,
            batch_first=True
        )

        # Feed-forward network.
        self.linear1 = nn.Linear(d_model, dim_feedforward)
        self.dropout = nn.Dropout(dropout)
        self.linear2 = nn.Linear(dim_feedforward, d_model)

        # Normalization and dropout.
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

        self.activation = nn.GELU()
        # If you prefer ReLU, set: self.activation = nn.ReLU()
        self.norm_first = norm_first

        # Residual scaling coefficients.
        self.res_scale_attn = residual_scale_attn
        self.res_scale_ffn = residual_scale_ffn

    def forward(self, src, src_mask=None, src_key_padding_mask=None):
        # Input tensor shape: (batch, seq_len, d_model).
        x = src

        if self.norm_first:
            # Pre-norm before attention.
            x = x + self._sa_block(self.norm1(x), src_mask,
                                   src_key_padding_mask)
            x = x + self._ff_block(self.norm2(x))
        else:
            # Post-norm (usually disabled).
            x = self.norm1(
                x + self._sa_block(x, src_mask, src_key_padding_mask))
            x = self.norm2(x + self._ff_block(x))

        return x

    def _sa_block(self, x, attn_mask, key_padding_mask):
        # Self-attention with residual scaling.
        attn_out, _ = self.self_attn(
            x, x, x,
            attn_mask=attn_mask,
            key_padding_mask=key_padding_mask,
            need_weights=False
        )
        return self.res_scale_attn * self.dropout1(attn_out)

    def _ff_block(self, x):
        # Feed-forward block with residual scaling.
        x2 = self.linear2(self.dropout(self.activation(self.linear1(x))))
        return self.res_scale_ffn * self.dropout2(x2)

# FT-Transformer core model.


class FTTransformerCore(nn.Module):
    # Minimal FT-Transformer built from:
    #   1) FeatureTokenizer: convert numeric/categorical features to tokens;
    #   2) TransformerEncoder: model feature interactions;
    #   3) Pooling + MLP + Softplus: positive outputs for Tweedie/Gamma tasks.

    def __init__(self, num_numeric: int, cat_cardinalities, d_model: int = 64,
                 n_heads: int = 8, n_layers: int = 4, dropout: float = 0.1,
                 task_type: str = 'regression', num_geo: int = 0,
                 num_numeric_tokens: int = 1
                 ):
        super().__init__()

        self.num_numeric = int(num_numeric)
        self.cat_cardinalities = list(cat_cardinalities or [])

        self.tokenizer = FeatureTokenizer(
            num_numeric=num_numeric,
            cat_cardinalities=cat_cardinalities,
            d_model=d_model,
            num_geo=num_geo,
            num_numeric_tokens=num_numeric_tokens
        )
        scale = 1.0 / math.sqrt(n_layers)  # Recommended default.
        encoder_layer = ScaledTransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            residual_scale_attn=scale,
            residual_scale_ffn=scale,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=n_layers
        )
        self.n_layers = n_layers

        layers = [
            # If you need a deeper head, enable the sample layers below:
            # nn.LayerNorm(d_model),  # Extra normalization
            # nn.Linear(d_model, d_model),  # Extra fully connected layer
            # nn.GELU(),  # Activation
            nn.Linear(d_model, 1),
        ]

        if task_type == 'classification':
            # Classification outputs logits for BCEWithLogitsLoss.
            layers.append(nn.Identity())
        else:
            # Regression keeps positive outputs for Tweedie/Gamma.
            layers.append(nn.Softplus())

        self.head = nn.Sequential(*layers)

        # ---- Self-supervised reconstruction head (masked modeling) ----
        self.num_recon_head = nn.Linear(
            d_model, self.num_numeric) if self.num_numeric > 0 else None
        self.cat_recon_heads = nn.ModuleList([
            nn.Linear(d_model, int(card)) for card in self.cat_cardinalities
        ])

    def forward(
            self,
            X_num,
            X_cat,
            X_geo=None,
            return_embedding: bool = False,
            return_reconstruction: bool = False):

        # Inputs:
        #   X_num -> float32 tensor with shape (batch, num_numeric_features)
        #   X_cat -> long tensor with shape (batch, num_categorical_features)
        #   X_geo -> float32 tensor with shape (batch, geo_token_dim)

        if self.training and not hasattr(self, '_printed_device'):
            print(f">>> FTTransformerCore executing on device: {X_num.device}")
            self._printed_device = True

        # => tensor shape (batch, token_num, d_model)
        tokens = self.tokenizer(X_num, X_cat, X_geo)
        # => tensor shape (batch, token_num, d_model)
        x = self.encoder(tokens)

        # Mean-pool tokens, then send to the head.
        x = x.mean(dim=1)                      # => tensor shape (batch, d_model)

        if return_reconstruction:
            num_pred, cat_logits = self.reconstruct(x)
            cat_logits_out = tuple(
                cat_logits) if cat_logits is not None else tuple()
            if return_embedding:
                return x, num_pred, cat_logits_out
            return num_pred, cat_logits_out

        if return_embedding:
            return x

        # => tensor shape (batch, 1); Softplus keeps it positive.
        out = self.head(x)
        return out

    def reconstruct(self, embedding: torch.Tensor) -> Tuple[Optional[torch.Tensor], List[torch.Tensor]]:
        """Reconstruct numeric/categorical inputs from pooled embedding (batch, d_model)."""
        num_pred = self.num_recon_head(
            embedding) if self.num_recon_head is not None else None
        cat_logits = [head(embedding) for head in self.cat_recon_heads]
        return num_pred, cat_logits

# TabularDataset.


class TabularDataset(Dataset):
    def __init__(self, X_num, X_cat, X_geo, y, w):

        # Input tensors:
        #   X_num: torch.float32, shape=(N, num_numeric_features)
        #   X_cat: torch.long,   shape=(N, num_categorical_features)
        #   X_geo: torch.float32, shape=(N, geo_token_dim), can be empty
        #   y:     torch.float32, shape=(N, 1)
        #   w:     torch.float32, shape=(N, 1)

        self.X_num = X_num
        self.X_cat = X_cat
        self.X_geo = X_geo
        self.y = y
        self.w = w

    def __len__(self):
        return self.y.shape[0]

    def __getitem__(self, idx):
        return (
            self.X_num[idx],
            self.X_cat[idx],
            self.X_geo[idx],
            self.y[idx],
            self.w[idx],
        )


class MaskedTabularDataset(Dataset):
    def __init__(self,
                 X_num_masked: torch.Tensor,
                 X_cat_masked: torch.Tensor,
                 X_geo: torch.Tensor,
                 X_num_true: Optional[torch.Tensor],
                 num_mask: Optional[torch.Tensor],
                 X_cat_true: Optional[torch.Tensor],
                 cat_mask: Optional[torch.Tensor]):
        self.X_num_masked = X_num_masked
        self.X_cat_masked = X_cat_masked
        self.X_geo = X_geo
        self.X_num_true = X_num_true
        self.num_mask = num_mask
        self.X_cat_true = X_cat_true
        self.cat_mask = cat_mask

    def __len__(self):
        return self.X_num_masked.shape[0]

    def __getitem__(self, idx):
        return (
            self.X_num_masked[idx],
            self.X_cat_masked[idx],
            self.X_geo[idx],
            None if self.X_num_true is None else self.X_num_true[idx],
            None if self.num_mask is None else self.num_mask[idx],
            None if self.X_cat_true is None else self.X_cat_true[idx],
            None if self.cat_mask is None else self.cat_mask[idx],
        )

# Scikit-Learn style wrapper for FTTransformer.


class FTTransformerSklearn(TorchTrainerMixin, nn.Module):

    # sklearn-style wrapper:
    #   - num_cols: numeric feature column names
    #   - cat_cols: categorical feature column names (label-encoded to [0, n_classes-1])

    @staticmethod
    def resolve_numeric_token_count(num_cols, cat_cols, requested: Optional[int]) -> int:
        num_cols_count = len(num_cols or [])
        if num_cols_count == 0:
            return 0
        if requested is not None:
            count = int(requested)
            if count <= 0:
                raise ValueError("num_numeric_tokens must be >= 1 when numeric features exist.")
            return count
        return max(1, num_cols_count)

    def __init__(self, model_nme: str, num_cols, cat_cols, d_model: int = 64, n_heads: int = 8,
                 n_layers: int = 4, dropout: float = 0.1, batch_num: int = 100, epochs: int = 100,
                 task_type: str = 'regression',
                 tweedie_power: float = 1.5, learning_rate: float = 1e-3, patience: int = 10,
                 weight_decay: float = 0.0,
                 use_data_parallel: bool = True,
                 use_ddp: bool = False,
                 num_numeric_tokens: Optional[int] = None
                 ):
        super().__init__()

        self.use_ddp = use_ddp
        self.is_ddp_enabled, self.local_rank, self.rank, self.world_size = (
            False, 0, 0, 1)
        if self.use_ddp:
            self.is_ddp_enabled, self.local_rank, self.rank, self.world_size = DistributedUtils.setup_ddp()

        self.model_nme = model_nme
        self.num_cols = list(num_cols)
        self.cat_cols = list(cat_cols)
        self.num_numeric_tokens = self.resolve_numeric_token_count(
            self.num_cols,
            self.cat_cols,
            num_numeric_tokens,
        )
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.dropout = dropout
        self.batch_num = batch_num
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.task_type = task_type
        self.patience = patience
        if self.task_type == 'classification':
            self.tw_power = None  # No Tweedie power for classification.
        elif 'f' in self.model_nme:
            self.tw_power = 1.0
        elif 's' in self.model_nme:
            self.tw_power = 2.0
        else:
            self.tw_power = tweedie_power

        if self.is_ddp_enabled:
            self.device = torch.device(f"cuda:{self.local_rank}")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")
        self.cat_cardinalities = None
        self.cat_categories = {}
        self.cat_maps: Dict[str, Dict[Any, int]] = {}
        self.cat_str_maps: Dict[str, Dict[str, int]] = {}
        self._num_mean = None
        self._num_std = None
        self.ft = None
        self.use_data_parallel = bool(use_data_parallel)
        self.num_geo = 0
        self._geo_params: Dict[str, Any] = {}
        self.loss_curve_path: Optional[str] = None
        self.training_history: Dict[str, List[float]] = {
            "train": [], "val": []}

    def _build_model(self, X_train):
        num_numeric = len(self.num_cols)
        cat_cardinalities = []

        if num_numeric > 0:
            num_arr = X_train[self.num_cols].to_numpy(
                dtype=np.float32, copy=False)
            num_arr = np.nan_to_num(num_arr, nan=0.0, posinf=0.0, neginf=0.0)
            mean = num_arr.mean(axis=0).astype(np.float32, copy=False)
            std = num_arr.std(axis=0).astype(np.float32, copy=False)
            std = np.where(std < 1e-6, 1.0, std).astype(np.float32, copy=False)
            self._num_mean = mean
            self._num_std = std
        else:
            self._num_mean = None
            self._num_std = None

        self.cat_maps = {}
        self.cat_str_maps = {}
        for col in self.cat_cols:
            cats = X_train[col].astype('category')
            categories = cats.cat.categories
            self.cat_categories[col] = categories           # Store full category list from training.
            self.cat_maps[col] = {cat: i for i, cat in enumerate(categories)}
            if categories.dtype == object or pd.api.types.is_string_dtype(categories.dtype):
                self.cat_str_maps[col] = {str(cat): i for i, cat in enumerate(categories)}

            card = len(categories) + 1                      # Reserve one extra class for unknown/missing.
            cat_cardinalities.append(card)

        self.cat_cardinalities = cat_cardinalities

        core = FTTransformerCore(
            num_numeric=num_numeric,
            cat_cardinalities=cat_cardinalities,
            d_model=self.d_model,
            n_heads=self.n_heads,
            n_layers=self.n_layers,
            dropout=self.dropout,
            task_type=self.task_type,
            num_geo=self.num_geo,
            num_numeric_tokens=self.num_numeric_tokens
        )
        use_dp = use_data_parallel and (self.device.type == "cuda") and (torch.cuda.device_count() > 1)
        if self.is_ddp_enabled:
            core = core.to(self.device)
            core = DDP(core, device_ids=[
                       self.local_rank], output_device=self.local_rank, find_unused_parameters=True)
            self.use_data_parallel = False
        elif use_dp:
            if self.use_ddp and not self.is_ddp_enabled:
                print(
                    ">>> DDP requested but not initialized; falling back to DataParallel.")
            core = nn.DataParallel(core, device_ids=list(
                range(torch.cuda.device_count())))
            self.device = torch.device("cuda")
            self.use_data_parallel = True
        else:
            self.use_data_parallel = False
        self.ft = core.to(self.device)

    def _encode_cats(self, X):
        # Input DataFrame must include all categorical feature columns.
        # Return int64 array with shape (N, num_categorical_features).

        if not self.cat_cols:
            return np.zeros((len(X), 0), dtype='int64')

        n_rows = len(X)
        n_cols = len(self.cat_cols)
        X_cat_np = np.empty((n_rows, n_cols), dtype='int64')
        for idx, col in enumerate(self.cat_cols):
            categories = self.cat_categories[col]
            mapping = self.cat_maps.get(col)
            if mapping is None:
                mapping = {cat: i for i, cat in enumerate(categories)}
                self.cat_maps[col] = mapping
            unknown_idx = len(categories)
            series = X[col]
            codes = series.map(mapping)
            unmapped = series.notna() & codes.isna()
            if unmapped.any():
                try:
                    series_cast = series.astype(categories.dtype)
                except Exception:
                    series_cast = None
                if series_cast is not None:
                    codes = series_cast.map(mapping)
                    unmapped = series_cast.notna() & codes.isna()
            if unmapped.any():
                str_map = self.cat_str_maps.get(col)
                if str_map is None:
                    str_map = {str(cat): i for i, cat in enumerate(categories)}
                    self.cat_str_maps[col] = str_map
                codes = series.astype(str).map(str_map)
            codes = codes.fillna(unknown_idx).astype(
                "int64", copy=False).to_numpy()
            X_cat_np[:, idx] = codes
        return X_cat_np

    def _build_train_tensors(self, X_train, y_train, w_train, geo_train=None):
        return self._tensorize_split(X_train, y_train, w_train, geo_tokens=geo_train)

    def _build_val_tensors(self, X_val, y_val, w_val, geo_val=None):
        return self._tensorize_split(X_val, y_val, w_val, geo_tokens=geo_val, allow_none=True)

    @staticmethod
    def _validate_vector(arr, name: str, n_rows: int) -> None:
        if arr is None:
            return
        if isinstance(arr, pd.DataFrame):
            if arr.shape[1] != 1:
                raise ValueError(f"{name} must be 1d (single column).")
            length = len(arr)
        else:
            arr_np = np.asarray(arr)
            if arr_np.ndim == 0:
                raise ValueError(f"{name} must be 1d.")
            if arr_np.ndim > 2 or (arr_np.ndim == 2 and arr_np.shape[1] != 1):
                raise ValueError(f"{name} must be 1d or Nx1.")
            length = arr_np.shape[0]
        if length != n_rows:
            raise ValueError(
                f"{name} length {length} does not match X length {n_rows}."
            )

    def _tensorize_split(self, X, y, w, geo_tokens=None, allow_none: bool = False):
        if X is None:
            if allow_none:
                return None, None, None, None, None, False
            raise ValueError("Input features X must not be None.")
        if not isinstance(X, pd.DataFrame):
            raise ValueError("X must be a pandas DataFrame.")
        missing_cols = [
            col for col in (self.num_cols + self.cat_cols) if col not in X.columns
        ]
        if missing_cols:
            raise ValueError(f"X is missing required columns: {missing_cols}")
        n_rows = len(X)
        if y is not None:
            self._validate_vector(y, "y", n_rows)
        if w is not None:
            self._validate_vector(w, "w", n_rows)

        num_np = X[self.num_cols].to_numpy(dtype=np.float32, copy=False)
        if not num_np.flags["OWNDATA"]:
            num_np = num_np.copy()
        num_np = np.nan_to_num(num_np, nan=0.0,
                               posinf=0.0, neginf=0.0, copy=False)
        if self._num_mean is not None and self._num_std is not None and num_np.size:
            num_np = (num_np - self._num_mean) / self._num_std
        X_num = torch.as_tensor(num_np)
        if self.cat_cols:
            X_cat = torch.as_tensor(self._encode_cats(X), dtype=torch.long)
        else:
            X_cat = torch.zeros((X_num.shape[0], 0), dtype=torch.long)

        if geo_tokens is not None:
            geo_np = np.asarray(geo_tokens, dtype=np.float32)
            if geo_np.shape[0] != n_rows:
                raise ValueError(
                    "geo_tokens length does not match X rows.")
            if geo_np.ndim == 1:
                geo_np = geo_np.reshape(-1, 1)
        elif self.num_geo > 0:
            raise RuntimeError("geo_tokens must not be empty; prepare geo tokens first.")
        else:
            geo_np = np.zeros((X_num.shape[0], 0), dtype=np.float32)
        X_geo = torch.as_tensor(geo_np)

        y_tensor = torch.as_tensor(
            y.to_numpy(dtype=np.float32, copy=False) if hasattr(
                y, "to_numpy") else np.asarray(y, dtype=np.float32)
        ).view(-1, 1) if y is not None else None
        if y_tensor is None:
            w_tensor = None
        elif w is not None:
            w_tensor = torch.as_tensor(
                w.to_numpy(dtype=np.float32, copy=False) if hasattr(
                    w, "to_numpy") else np.asarray(w, dtype=np.float32)
            ).view(-1, 1)
        else:
            w_tensor = torch.ones_like(y_tensor)
        return X_num, X_cat, X_geo, y_tensor, w_tensor, y is not None

    def fit(self, X_train, y_train, w_train=None,
            X_val=None, y_val=None, w_val=None, trial=None,
            geo_train=None, geo_val=None):

        # Build the underlying model on first fit.
        self.num_geo = geo_train.shape[1] if geo_train is not None else 0
        if self.ft is None:
            self._build_model(X_train)

        X_num_train, X_cat_train, X_geo_train, y_tensor, w_tensor, _ = self._build_train_tensors(
            X_train, y_train, w_train, geo_train=geo_train)
        X_num_val, X_cat_val, X_geo_val, y_val_tensor, w_val_tensor, has_val = self._build_val_tensors(
            X_val, y_val, w_val, geo_val=geo_val)

        # --- Build DataLoader ---
        dataset = TabularDataset(
            X_num_train, X_cat_train, X_geo_train, y_tensor, w_tensor
        )

        dataloader, accum_steps = self._build_dataloader(
            dataset,
            N=X_num_train.shape[0],
            base_bs_gpu=(2048, 1024, 512),
            base_bs_cpu=(256, 128),
            min_bs=64,
            target_effective_cuda=2048,
            target_effective_cpu=1024
        )

        if self.is_ddp_enabled and hasattr(dataloader.sampler, 'set_epoch'):
            self.dataloader_sampler = dataloader.sampler
        else:
            self.dataloader_sampler = None

        optimizer = torch.optim.Adam(
            self.ft.parameters(),
            lr=self.learning_rate,
            weight_decay=float(getattr(self, "weight_decay", 0.0)),
        )
        scaler = GradScaler(enabled=(self.device.type == 'cuda'))

        X_num_val_dev = X_cat_val_dev = y_val_dev = w_val_dev = None
        val_dataloader = None
        if has_val:
            val_dataset = TabularDataset(
                X_num_val, X_cat_val, X_geo_val, y_val_tensor, w_val_tensor
            )
            val_dataloader = self._build_val_dataloader(
                val_dataset, dataloader, accum_steps)

        is_data_parallel = isinstance(self.ft, nn.DataParallel)

        def forward_fn(batch):
            X_num_b, X_cat_b, X_geo_b, y_b, w_b = batch

            if not is_data_parallel:
                X_num_b = X_num_b.to(self.device, non_blocking=True)
                X_cat_b = X_cat_b.to(self.device, non_blocking=True)
                X_geo_b = X_geo_b.to(self.device, non_blocking=True)
            y_b = y_b.to(self.device, non_blocking=True)
            w_b = w_b.to(self.device, non_blocking=True)

            y_pred = self.ft(X_num_b, X_cat_b, X_geo_b)
            return y_pred, y_b, w_b

        def val_forward_fn():
            total_loss = 0.0
            total_weight = 0.0
            for batch in val_dataloader:
                X_num_b, X_cat_b, X_geo_b, y_b, w_b = batch
                if not is_data_parallel:
                    X_num_b = X_num_b.to(self.device, non_blocking=True)
                    X_cat_b = X_cat_b.to(self.device, non_blocking=True)
                    X_geo_b = X_geo_b.to(self.device, non_blocking=True)
                y_b = y_b.to(self.device, non_blocking=True)
                w_b = w_b.to(self.device, non_blocking=True)

                y_pred = self.ft(X_num_b, X_cat_b, X_geo_b)

                # Manually compute validation loss.
                losses = self._compute_losses(
                    y_pred, y_b, apply_softplus=False)

                batch_weight_sum = torch.clamp(w_b.sum(), min=EPS)
                batch_weighted_loss_sum = (losses * w_b.view(-1)).sum()

                total_loss += batch_weighted_loss_sum.item()
                total_weight += batch_weight_sum.item()

            return total_loss / max(total_weight, EPS)

        clip_fn = None
        if self.device.type == 'cuda':
            def clip_fn(): return (scaler.unscale_(optimizer),
                                   clip_grad_norm_(self.ft.parameters(), max_norm=1.0))

        best_state, history = self._train_model(
            self.ft,
            dataloader,
            accum_steps,
            optimizer,
            scaler,
            forward_fn,
            val_forward_fn if has_val else None,
            apply_softplus=False,
            clip_fn=clip_fn,
            trial=trial,
            loss_curve_path=getattr(self, "loss_curve_path", None)
        )

        if has_val and best_state is not None:
            self.ft.load_state_dict(best_state)
        self.training_history = history

    def fit_unsupervised(self,
                         X_train,
                         X_val=None,
                         trial: Optional[optuna.trial.Trial] = None,
                         geo_train=None,
                         geo_val=None,
                         mask_prob_num: float = 0.15,
                         mask_prob_cat: float = 0.15,
                         num_loss_weight: float = 1.0,
                         cat_loss_weight: float = 1.0) -> float:
        """Self-supervised pretraining via masked reconstruction (supports raw string categories)."""
        self.num_geo = geo_train.shape[1] if geo_train is not None else 0
        if self.ft is None:
            self._build_model(X_train)

        X_num, X_cat, X_geo, _, _, _ = self._tensorize_split(
            X_train, None, None, geo_tokens=geo_train, allow_none=True)
        has_val = X_val is not None
        if has_val:
            X_num_val, X_cat_val, X_geo_val, _, _, _ = self._tensorize_split(
                X_val, None, None, geo_tokens=geo_val, allow_none=True)
        else:
            X_num_val = X_cat_val = X_geo_val = None

        N = int(X_num.shape[0])
        num_dim = int(X_num.shape[1])
        cat_dim = int(X_cat.shape[1])
        device_type = self._device_type()

        gen = torch.Generator()
        gen.manual_seed(13 + int(getattr(self, "rank", 0)))

        base_model = self.ft.module if hasattr(self.ft, "module") else self.ft
        cardinals = getattr(base_model, "cat_cardinalities", None) or []
        unknown_idx = torch.tensor(
            [int(c) - 1 for c in cardinals], dtype=torch.long).view(1, -1)

        means = None
        if num_dim > 0:
            # Keep masked fill values on the same scale as model inputs (may be normalized in _tensorize_split).
            means = X_num.to(dtype=torch.float32).mean(dim=0, keepdim=True)

        def _mask_inputs(X_num_in: torch.Tensor,
                         X_cat_in: torch.Tensor,
                         generator: torch.Generator):
            n_rows = int(X_num_in.shape[0])
            num_mask_local = None
            cat_mask_local = None
            X_num_masked_local = X_num_in
            X_cat_masked_local = X_cat_in
            if num_dim > 0:
                num_mask_local = (torch.rand(
                    (n_rows, num_dim), generator=generator) < float(mask_prob_num))
                X_num_masked_local = X_num_in.clone()
                if num_mask_local.any():
                    X_num_masked_local[num_mask_local] = means.expand_as(
                        X_num_masked_local)[num_mask_local]
            if cat_dim > 0:
                cat_mask_local = (torch.rand(
                    (n_rows, cat_dim), generator=generator) < float(mask_prob_cat))
                X_cat_masked_local = X_cat_in.clone()
                if cat_mask_local.any():
                    X_cat_masked_local[cat_mask_local] = unknown_idx.expand_as(
                        X_cat_masked_local)[cat_mask_local]
            return X_num_masked_local, X_cat_masked_local, num_mask_local, cat_mask_local

        X_num_true = X_num if num_dim > 0 else None
        X_cat_true = X_cat if cat_dim > 0 else None
        X_num_masked, X_cat_masked, num_mask, cat_mask = _mask_inputs(
            X_num, X_cat, gen)

        dataset = MaskedTabularDataset(
            X_num_masked, X_cat_masked, X_geo,
            X_num_true, num_mask,
            X_cat_true, cat_mask
        )
        dataloader, accum_steps = self._build_dataloader(
            dataset,
            N=N,
            base_bs_gpu=(2048, 1024, 512),
            base_bs_cpu=(256, 128),
            min_bs=64,
            target_effective_cuda=2048,
            target_effective_cpu=1024
        )
        if self.is_ddp_enabled and hasattr(dataloader.sampler, 'set_epoch'):
            self.dataloader_sampler = dataloader.sampler
        else:
            self.dataloader_sampler = None

        optimizer = torch.optim.Adam(
            self.ft.parameters(),
            lr=self.learning_rate,
            weight_decay=float(getattr(self, "weight_decay", 0.0)),
        )
        scaler = GradScaler(enabled=(device_type == 'cuda'))

        def _batch_recon_loss(num_pred, cat_logits, num_true_b, num_mask_b, cat_true_b, cat_mask_b, device):
            loss = torch.zeros((), device=device, dtype=torch.float32)

            if num_pred is not None and num_true_b is not None and num_mask_b is not None:
                num_mask_b = num_mask_b.to(dtype=torch.bool)
                if num_mask_b.any():
                    diff = num_pred - num_true_b
                    mse = diff * diff
                    loss = loss + float(num_loss_weight) * \
                        mse[num_mask_b].mean()

            if cat_logits and cat_true_b is not None and cat_mask_b is not None:
                cat_mask_b = cat_mask_b.to(dtype=torch.bool)
                cat_losses: List[torch.Tensor] = []
                for j, logits in enumerate(cat_logits):
                    mask_j = cat_mask_b[:, j]
                    if not mask_j.any():
                        continue
                    targets = cat_true_b[:, j]
                    cat_losses.append(
                        F.cross_entropy(logits, targets, reduction='none')[
                            mask_j].mean()
                    )
                if cat_losses:
                    loss = loss + float(cat_loss_weight) * \
                        torch.stack(cat_losses).mean()
            return loss

        train_history: List[float] = []
        val_history: List[float] = []
        best_loss = float("inf")
        best_state = None
        patience_counter = 0
        is_ddp_model = isinstance(self.ft, DDP)

        clip_fn = None
        if self.device.type == 'cuda':
            def clip_fn(): return (scaler.unscale_(optimizer),
                                   clip_grad_norm_(self.ft.parameters(), max_norm=1.0))

        for epoch in range(1, int(self.epochs) + 1):
            if self.dataloader_sampler is not None:
                self.dataloader_sampler.set_epoch(epoch)

            self.ft.train()
            optimizer.zero_grad()
            epoch_loss_sum = 0.0
            epoch_count = 0.0

            for step, batch in enumerate(dataloader):
                is_update_step = ((step + 1) % accum_steps == 0) or \
                    ((step + 1) == len(dataloader))
                sync_cm = self.ft.no_sync if (
                    is_ddp_model and not is_update_step) else nullcontext
                with sync_cm():
                    with autocast(enabled=(device_type == 'cuda')):
                        X_num_b, X_cat_b, X_geo_b, num_true_b, num_mask_b, cat_true_b, cat_mask_b = batch
                        X_num_b = X_num_b.to(self.device, non_blocking=True)
                        X_cat_b = X_cat_b.to(self.device, non_blocking=True)
                        X_geo_b = X_geo_b.to(self.device, non_blocking=True)
                        num_true_b = None if num_true_b is None else num_true_b.to(
                            self.device, non_blocking=True)
                        num_mask_b = None if num_mask_b is None else num_mask_b.to(
                            self.device, non_blocking=True)
                        cat_true_b = None if cat_true_b is None else cat_true_b.to(
                            self.device, non_blocking=True)
                        cat_mask_b = None if cat_mask_b is None else cat_mask_b.to(
                            self.device, non_blocking=True)

                        num_pred, cat_logits = self.ft(
                            X_num_b, X_cat_b, X_geo_b, return_reconstruction=True)
                        batch_loss = _batch_recon_loss(
                            num_pred, cat_logits, num_true_b, num_mask_b, cat_true_b, cat_mask_b, device=X_num_b.device)
                        local_bad = 0 if bool(torch.isfinite(batch_loss)) else 1
                        global_bad = local_bad
                        if dist.is_initialized():
                            bad = torch.tensor(
                                [local_bad],
                                device=batch_loss.device,
                                dtype=torch.int32,
                            )
                            dist.all_reduce(bad, op=dist.ReduceOp.MAX)
                            global_bad = int(bad.item())

                        if global_bad:
                            msg = (
                                f"[FTTransformerSklearn.fit_unsupervised] non-finite loss "
                                f"(epoch={epoch}, step={step}, loss={batch_loss.detach().item()})"
                            )
                            should_log = (not dist.is_initialized()
                                          or DistributedUtils.is_main_process())
                            if should_log:
                                print(msg, flush=True)
                                print(
                                    f"  X_num: finite={bool(torch.isfinite(X_num_b).all())} "
                                    f"min={float(X_num_b.min().detach().cpu()) if X_num_b.numel() else 0.0:.3g} "
                                    f"max={float(X_num_b.max().detach().cpu()) if X_num_b.numel() else 0.0:.3g}",
                                    flush=True,
                                )
                                if X_geo_b is not None:
                                    print(
                                        f"  X_geo: finite={bool(torch.isfinite(X_geo_b).all())} "
                                        f"min={float(X_geo_b.min().detach().cpu()) if X_geo_b.numel() else 0.0:.3g} "
                                        f"max={float(X_geo_b.max().detach().cpu()) if X_geo_b.numel() else 0.0:.3g}",
                                        flush=True,
                                    )
                            if trial is not None:
                                raise optuna.TrialPruned(msg)
                            raise RuntimeError(msg)
                        loss_for_backward = batch_loss / float(accum_steps)
                    scaler.scale(loss_for_backward).backward()

                if is_update_step:
                    if clip_fn is not None:
                        clip_fn()
                    scaler.step(optimizer)
                    scaler.update()
                    optimizer.zero_grad()

                epoch_loss_sum += float(batch_loss.detach().item()) * \
                    float(X_num_b.shape[0])
                epoch_count += float(X_num_b.shape[0])

            train_history.append(epoch_loss_sum / max(epoch_count, 1.0))

            if has_val and X_num_val is not None and X_cat_val is not None and X_geo_val is not None:
                should_compute_val = (not dist.is_initialized()
                                      or DistributedUtils.is_main_process())
                loss_tensor_device = self.device if device_type == 'cuda' else torch.device(
                    "cpu")
                val_loss_tensor = torch.zeros(1, device=loss_tensor_device)

                if should_compute_val:
                    self.ft.eval()
                    with torch.no_grad(), autocast(enabled=(device_type == 'cuda')):
                        val_bs = min(
                            int(dataloader.batch_size * max(1, accum_steps)), int(X_num_val.shape[0]))
                        total_val = 0.0
                        total_n = 0.0
                        for start in range(0, int(X_num_val.shape[0]), max(1, val_bs)):
                            end = min(
                                int(X_num_val.shape[0]), start + max(1, val_bs))
                            X_num_v_true_cpu = X_num_val[start:end]
                            X_cat_v_true_cpu = X_cat_val[start:end]
                            X_geo_v = X_geo_val[start:end].to(
                                self.device, non_blocking=True)
                            gen_val = torch.Generator()
                            gen_val.manual_seed(10_000 + epoch + start)
                            X_num_v_cpu, X_cat_v_cpu, val_num_mask, val_cat_mask = _mask_inputs(
                                X_num_v_true_cpu, X_cat_v_true_cpu, gen_val)
                            X_num_v_true = X_num_v_true_cpu.to(
                                self.device, non_blocking=True)
                            X_cat_v_true = X_cat_v_true_cpu.to(
                                self.device, non_blocking=True)
                            X_num_v = X_num_v_cpu.to(
                                self.device, non_blocking=True)
                            X_cat_v = X_cat_v_cpu.to(
                                self.device, non_blocking=True)
                            val_num_mask = None if val_num_mask is None else val_num_mask.to(
                                self.device, non_blocking=True)
                            val_cat_mask = None if val_cat_mask is None else val_cat_mask.to(
                                self.device, non_blocking=True)
                            num_pred_v, cat_logits_v = self.ft(
                                X_num_v, X_cat_v, X_geo_v, return_reconstruction=True)
                            loss_v = _batch_recon_loss(
                                num_pred_v, cat_logits_v,
                                X_num_v_true if X_num_v_true.numel() else None, val_num_mask,
                                X_cat_v_true if X_cat_v_true.numel() else None, val_cat_mask,
                                device=X_num_v.device
                            )
                            if not torch.isfinite(loss_v):
                                total_val = float("inf")
                                total_n = 1.0
                                break
                            total_val += float(loss_v.detach().item()
                                               ) * float(end - start)
                            total_n += float(end - start)
                    val_loss_tensor[0] = total_val / max(total_n, 1.0)

                if dist.is_initialized():
                    dist.broadcast(val_loss_tensor, src=0)
                val_loss_value = float(val_loss_tensor.item())
                prune_now = False
                prune_msg = None
                if not np.isfinite(val_loss_value):
                    prune_now = True
                    prune_msg = (
                        f"[FTTransformerSklearn.fit_unsupervised] non-finite val loss "
                        f"(epoch={epoch}, val_loss={val_loss_value})"
                    )
                val_history.append(val_loss_value)

                if val_loss_value < best_loss:
                    best_loss = val_loss_value
                    best_state = {
                        k: (v.clone() if isinstance(
                            v, torch.Tensor) else copy.deepcopy(v))
                        for k, v in self.ft.state_dict().items()
                    }
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if best_state is not None and patience_counter >= int(self.patience):
                        break

                if trial is not None and (not dist.is_initialized() or DistributedUtils.is_main_process()):
                    trial.report(val_loss_value, epoch)
                    if trial.should_prune():
                        prune_now = True

                if dist.is_initialized():
                    flag = torch.tensor(
                        [1 if prune_now else 0],
                        device=loss_tensor_device,
                        dtype=torch.int32,
                    )
                    dist.broadcast(flag, src=0)
                    prune_now = bool(flag.item())

                if prune_now:
                    if prune_msg:
                        raise optuna.TrialPruned(prune_msg)
                    raise optuna.TrialPruned()

        self.training_history = {"train": train_history, "val": val_history}
        self._plot_loss_curve(self.training_history, getattr(
            self, "loss_curve_path", None))
        if has_val and best_state is not None:
            self.ft.load_state_dict(best_state)
        return float(best_loss if has_val else (train_history[-1] if train_history else 0.0))

    def predict(self, X_test, geo_tokens=None, batch_size: Optional[int] = None, return_embedding: bool = False):
        # X_test must include all numeric/categorical columns; geo_tokens is optional.

        self.ft.eval()
        X_num, X_cat, X_geo, _, _, _ = self._tensorize_split(
            X_test, None, None, geo_tokens=geo_tokens, allow_none=True)

        num_rows = X_num.shape[0]
        if num_rows == 0:
            return np.empty(0, dtype=np.float32)

        device = self.device if isinstance(
            self.device, torch.device) else torch.device(self.device)

        def resolve_batch_size(n_rows: int) -> int:
            if batch_size is not None:
                return max(1, min(int(batch_size), n_rows))
            # Estimate a safe batch size based on model size to avoid attention OOM.
            token_cnt = self.num_numeric_tokens + len(self.cat_cols)
            if self.num_geo > 0:
                token_cnt += 1
            approx_units = max(1, token_cnt * max(1, self.d_model))
            if device.type == 'cuda':
                if approx_units >= 8192:
                    base = 512
                elif approx_units >= 4096:
                    base = 1024
                else:
                    base = 2048
            else:
                base = 512
            return max(1, min(base, n_rows))

        eff_batch = resolve_batch_size(num_rows)
        preds: List[torch.Tensor] = []

        inference_cm = getattr(torch, "inference_mode", torch.no_grad)
        with inference_cm():
            for start in range(0, num_rows, eff_batch):
                end = min(num_rows, start + eff_batch)
                X_num_b = X_num[start:end].to(device, non_blocking=True)
                X_cat_b = X_cat[start:end].to(device, non_blocking=True)
                X_geo_b = X_geo[start:end].to(device, non_blocking=True)
                pred_chunk = self.ft(
                    X_num_b, X_cat_b, X_geo_b, return_embedding=return_embedding)
                preds.append(pred_chunk.cpu())

        y_pred = torch.cat(preds, dim=0).numpy()

        if return_embedding:
            return y_pred

        if self.task_type == 'classification':
            # Convert logits to probabilities.
            y_pred = 1 / (1 + np.exp(-y_pred))
        else:
            # Model already has softplus; optionally apply log-exp smoothing: y_pred = log(1 + exp(y_pred)).
            y_pred = np.clip(y_pred, 1e-6, None)
        return y_pred.ravel()

    def set_params(self, params: dict):

        # Keep sklearn-style behavior.
        # Note: changing structural params (e.g., d_model/n_heads) requires refit to take effect.

        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Parameter {key} not found in model.")
        return self


# =============================================================================
# Simplified GNN implementation.
# =============================================================================


class SimpleGraphLayer(nn.Module):
    def __init__(self, in_dim: int, out_dim: int, dropout: float = 0.1):
        super().__init__()
        self.linear = nn.Linear(in_dim, out_dim)
        self.activation = nn.ReLU(inplace=True)
        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        # Message passing with normalized sparse adjacency: A_hat * X * W.
        h = torch.sparse.mm(adj, x)
        h = self.linear(h)
        h = self.activation(h)
        return self.dropout(h)


class SimpleGNN(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2,
                 dropout: float = 0.1, task_type: str = 'regression'):
        super().__init__()
        layers = []
        dim_in = input_dim
        for _ in range(max(1, num_layers)):
            layers.append(SimpleGraphLayer(
                dim_in, hidden_dim, dropout=dropout))
            dim_in = hidden_dim
        self.layers = nn.ModuleList(layers)
        self.output = nn.Linear(hidden_dim, 1)
        if task_type == 'classification':
            self.output_act = nn.Identity()
        else:
            self.output_act = nn.Softplus()
        self.task_type = task_type
        # Keep adjacency as a buffer for DataParallel copies.
        self.register_buffer("adj_buffer", torch.empty(0))

    def forward(self, x: torch.Tensor, adj: Optional[torch.Tensor] = None) -> torch.Tensor:
        adj_used = adj if adj is not None else getattr(
            self, "adj_buffer", None)
        if adj_used is None or adj_used.numel() == 0:
            raise RuntimeError("Adjacency is not set for GNN forward.")
        h = x
        for layer in self.layers:
            h = layer(h, adj_used)
        h = torch.sparse.mm(adj_used, h)
        out = self.output(h)
        return self.output_act(out)


class GraphNeuralNetSklearn(TorchTrainerMixin, nn.Module):
    def __init__(self, model_nme: str, input_dim: int, hidden_dim: int = 64,
                 num_layers: int = 2, k_neighbors: int = 10, dropout: float = 0.1,
                 learning_rate: float = 1e-3, epochs: int = 100, patience: int = 10,
                 task_type: str = 'regression', tweedie_power: float = 1.5,
                 weight_decay: float = 0.0,
                 use_data_parallel: bool = False, use_ddp: bool = False,
                 use_approx_knn: bool = True, approx_knn_threshold: int = 50000,
                 graph_cache_path: Optional[str] = None,
                 max_gpu_knn_nodes: Optional[int] = None,
                 knn_gpu_mem_ratio: float = 0.9,
                 knn_gpu_mem_overhead: float = 2.0,
                 knn_cpu_jobs: Optional[int] = -1) -> None:
        super().__init__()
        self.model_nme = model_nme
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.k_neighbors = max(1, k_neighbors)
        self.dropout = dropout
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.epochs = epochs
        self.patience = patience
        self.task_type = task_type
        self.use_approx_knn = use_approx_knn
        self.approx_knn_threshold = approx_knn_threshold
        self.graph_cache_path = Path(
            graph_cache_path) if graph_cache_path else None
        self.max_gpu_knn_nodes = max_gpu_knn_nodes
        self.knn_gpu_mem_ratio = max(0.0, min(1.0, knn_gpu_mem_ratio))
        self.knn_gpu_mem_overhead = max(1.0, knn_gpu_mem_overhead)
        self.knn_cpu_jobs = knn_cpu_jobs
        self._knn_warning_emitted = False
        self._adj_cache_meta: Optional[Dict[str, Any]] = None
        self._adj_cache_key: Optional[Tuple[Any, ...]] = None
        self._adj_cache_tensor: Optional[torch.Tensor] = None

        if self.task_type == 'classification':
            self.tw_power = None
        elif 'f' in self.model_nme:
            self.tw_power = 1.0
        elif 's' in self.model_nme:
            self.tw_power = 2.0
        else:
            self.tw_power = tweedie_power

        self.ddp_enabled = False
        self.local_rank = int(os.environ.get("LOCAL_RANK", 0))
        self.data_parallel_enabled = False
        self._ddp_disabled = False

        if use_ddp:
            world_size = int(os.environ.get("WORLD_SIZE", "1"))
            if world_size > 1:
                print(
                    "[GNN] DDP training is not supported; falling back to single process.",
                    flush=True,
                )
                self._ddp_disabled = True
                use_ddp = False

        # DDP only works with CUDA; fall back to single process if init fails.
        if use_ddp and torch.cuda.is_available():
            ddp_ok, local_rank, _, _ = DistributedUtils.setup_ddp()
            if ddp_ok:
                self.ddp_enabled = True
                self.local_rank = local_rank
                self.device = torch.device(f'cuda:{local_rank}')
            else:
                self.device = torch.device('cuda')
        elif torch.cuda.is_available():
            if self._ddp_disabled:
                self.device = torch.device(f'cuda:{self.local_rank}')
            else:
                self.device = torch.device('cuda')
        elif torch.backends.mps.is_available():
            self.device = torch.device('cpu')
            global _GNN_MPS_WARNED
            if not _GNN_MPS_WARNED:
                print(
                    "[GNN] MPS backend does not support sparse ops; falling back to CPU.",
                    flush=True,
                )
                _GNN_MPS_WARNED = True
        else:
            self.device = torch.device('cpu')
        self.use_pyg_knn = self.device.type == 'cuda' and _PYG_AVAILABLE

        self.gnn = SimpleGNN(
            input_dim=self.input_dim,
            hidden_dim=self.hidden_dim,
            num_layers=self.num_layers,
            dropout=self.dropout,
            task_type=self.task_type
        ).to(self.device)

        # DataParallel copies the full graph to each GPU and splits features; good for medium graphs.
        if (not self.ddp_enabled) and use_data_parallel and (self.device.type == 'cuda') and (torch.cuda.device_count() > 1):
            self.data_parallel_enabled = True
            self.gnn = nn.DataParallel(
                self.gnn, device_ids=list(range(torch.cuda.device_count())))
            self.device = torch.device('cuda')

        if self.ddp_enabled:
            self.gnn = DDP(
                self.gnn,
                device_ids=[self.local_rank],
                output_device=self.local_rank,
                find_unused_parameters=False
            )

    @staticmethod
    def _validate_vector(arr, name: str, n_rows: int) -> None:
        if arr is None:
            return
        if isinstance(arr, pd.DataFrame):
            if arr.shape[1] != 1:
                raise ValueError(f"{name} must be 1d (single column).")
            length = len(arr)
        else:
            arr_np = np.asarray(arr)
            if arr_np.ndim == 0:
                raise ValueError(f"{name} must be 1d.")
            if arr_np.ndim > 2 or (arr_np.ndim == 2 and arr_np.shape[1] != 1):
                raise ValueError(f"{name} must be 1d or Nx1.")
            length = arr_np.shape[0]
        if length != n_rows:
            raise ValueError(
                f"{name} length {length} does not match X length {n_rows}."
            )

    def _unwrap_gnn(self) -> nn.Module:
        if isinstance(self.gnn, (DDP, nn.DataParallel)):
            return self.gnn.module
        return self.gnn

    def _set_adj_buffer(self, adj: torch.Tensor) -> None:
        base = self._unwrap_gnn()
        if hasattr(base, "adj_buffer"):
            base.adj_buffer = adj
        else:
            base.register_buffer("adj_buffer", adj)

    def _graph_cache_meta(self, X_df: pd.DataFrame) -> Dict[str, Any]:
        row_hash = pd.util.hash_pandas_object(X_df, index=False).values
        idx_hash = pd.util.hash_pandas_object(X_df.index, index=False).values
        col_sig = ",".join(map(str, X_df.columns))
        hasher = hashlib.sha256()
        hasher.update(row_hash.tobytes())
        hasher.update(idx_hash.tobytes())
        hasher.update(col_sig.encode("utf-8", errors="ignore"))
        knn_config = {
            "k_neighbors": int(self.k_neighbors),
            "use_approx_knn": bool(self.use_approx_knn),
            "approx_knn_threshold": int(self.approx_knn_threshold),
            "use_pyg_knn": bool(self.use_pyg_knn),
            "pynndescent_available": bool(_PYNN_AVAILABLE),
            "max_gpu_knn_nodes": (
                None if self.max_gpu_knn_nodes is None else int(self.max_gpu_knn_nodes)
            ),
            "knn_gpu_mem_ratio": float(self.knn_gpu_mem_ratio),
            "knn_gpu_mem_overhead": float(self.knn_gpu_mem_overhead),
        }
        return {
            "n_samples": int(X_df.shape[0]),
            "n_features": int(X_df.shape[1]),
            "hash": hasher.hexdigest(),
            "knn_config": knn_config,
        }

    def _graph_cache_key(self, X_df: pd.DataFrame) -> Tuple[Any, ...]:
        return (
            id(X_df),
            id(getattr(X_df, "_mgr", None)),
            id(X_df.index),
            X_df.shape,
            tuple(map(str, X_df.columns)),
            X_df.attrs.get("graph_cache_key"),
        )

    def invalidate_graph_cache(self) -> None:
        self._adj_cache_meta = None
        self._adj_cache_key = None
        self._adj_cache_tensor = None

    def _load_cached_adj(self,
                         X_df: pd.DataFrame,
                         meta_expected: Optional[Dict[str, Any]] = None) -> Optional[torch.Tensor]:
        if self.graph_cache_path and self.graph_cache_path.exists():
            if meta_expected is None:
                meta_expected = self._graph_cache_meta(X_df)
            try:
                payload = torch.load(self.graph_cache_path,
                                     map_location=self.device)
            except Exception as exc:
                print(
                    f"[GNN] Failed to load cached graph from {self.graph_cache_path}: {exc}")
                return None
            if isinstance(payload, dict) and "adj" in payload:
                meta_cached = payload.get("meta")
                if meta_cached == meta_expected:
                    return payload["adj"].to(self.device)
                print(
                    f"[GNN] Cached graph metadata mismatch; rebuilding: {self.graph_cache_path}")
                return None
            if isinstance(payload, torch.Tensor):
                print(
                    f"[GNN] Cached graph missing metadata; rebuilding: {self.graph_cache_path}")
                return None
            print(
                f"[GNN] Invalid cached graph format; rebuilding: {self.graph_cache_path}")
        return None

    def _build_edge_index_cpu(self, X_np: np.ndarray) -> torch.Tensor:
        n_samples = X_np.shape[0]
        k = min(self.k_neighbors, max(1, n_samples - 1))
        n_neighbors = min(k + 1, n_samples)
        use_approx = (self.use_approx_knn or n_samples >=
                      self.approx_knn_threshold) and _PYNN_AVAILABLE
        indices = None
        if use_approx:
            try:
                nn_index = pynndescent.NNDescent(
                    X_np,
                    n_neighbors=n_neighbors,
                    random_state=0
                )
                indices, _ = nn_index.neighbor_graph
            except Exception as exc:
                print(
                    f"[GNN] Approximate kNN failed ({exc}); falling back to exact search.")
                use_approx = False

        if indices is None:
            nbrs = NearestNeighbors(
                n_neighbors=n_neighbors,
                algorithm="auto",
                n_jobs=self.knn_cpu_jobs,
            )
            nbrs.fit(X_np)
            _, indices = nbrs.kneighbors(X_np)

        indices = np.asarray(indices)
        rows = np.repeat(np.arange(n_samples), n_neighbors).astype(
            np.int64, copy=False)
        cols = indices.reshape(-1).astype(np.int64, copy=False)
        mask = rows != cols
        rows = rows[mask]
        cols = cols[mask]
        rows_base = rows
        cols_base = cols
        self_loops = np.arange(n_samples, dtype=np.int64)
        rows = np.concatenate([rows_base, cols_base, self_loops])
        cols = np.concatenate([cols_base, rows_base, self_loops])

        edge_index_np = np.stack([rows, cols], axis=0)
        edge_index = torch.as_tensor(edge_index_np, device=self.device)
        return edge_index

    def _build_edge_index_gpu(self, X_tensor: torch.Tensor) -> torch.Tensor:
        if not self.use_pyg_knn or knn_graph is None or add_self_loops is None or to_undirected is None:
            # Defensive: check use_pyg_knn before calling.
            raise RuntimeError(
                "GPU graph builder requested but PyG is unavailable.")

        n_samples = X_tensor.size(0)
        k = min(self.k_neighbors, max(1, n_samples - 1))

        # knn_graph runs on GPU to avoid CPU graph construction bottlenecks.
        edge_index = knn_graph(
            X_tensor,
            k=k,
            loop=False
        )
        edge_index = to_undirected(edge_index, num_nodes=n_samples)
        edge_index, _ = add_self_loops(edge_index, num_nodes=n_samples)
        return edge_index

    def _log_knn_fallback(self, reason: str) -> None:
        if self._knn_warning_emitted:
            return
        if (not self.ddp_enabled) or self.local_rank == 0:
            print(f"[GNN] Falling back to CPU kNN builder: {reason}")
        self._knn_warning_emitted = True

    def _should_use_gpu_knn(self, n_samples: int, X_tensor: torch.Tensor) -> bool:
        if not self.use_pyg_knn:
            return False

        reason = None
        if self.max_gpu_knn_nodes is not None and n_samples > self.max_gpu_knn_nodes:
            reason = f"node count {n_samples} exceeds max_gpu_knn_nodes={self.max_gpu_knn_nodes}"
        elif self.device.type == 'cuda' and torch.cuda.is_available():
            try:
                device_index = self.device.index
                if device_index is None:
                    device_index = torch.cuda.current_device()
                free_mem, total_mem = torch.cuda.mem_get_info(device_index)
                feature_bytes = X_tensor.element_size() * X_tensor.nelement()
                required = int(feature_bytes * self.knn_gpu_mem_overhead)
                budget = int(free_mem * self.knn_gpu_mem_ratio)
                if required > budget:
                    required_gb = required / (1024 ** 3)
                    budget_gb = budget / (1024 ** 3)
                    reason = (f"requires ~{required_gb:.2f} GiB temporary GPU memory "
                              f"but only {budget_gb:.2f} GiB free on cuda:{device_index}")
            except Exception:
                # On older versions or some environments, mem_get_info may be unavailable; default to trying GPU.
                reason = None

        if reason:
            self._log_knn_fallback(reason)
            return False
        return True

    def _normalized_adj(self, edge_index: torch.Tensor, num_nodes: int) -> torch.Tensor:
        values = torch.ones(edge_index.shape[1], device=self.device)
        adj = torch.sparse_coo_tensor(
            edge_index.to(self.device), values, (num_nodes, num_nodes))
        adj = adj.coalesce()

        deg = torch.sparse.sum(adj, dim=1).to_dense()
        deg_inv_sqrt = torch.pow(deg + 1e-8, -0.5)
        row, col = adj.indices()
        norm_values = deg_inv_sqrt[row] * adj.values() * deg_inv_sqrt[col]
        adj_norm = torch.sparse_coo_tensor(
            adj.indices(), norm_values, size=adj.shape)
        return adj_norm

    def _tensorize_split(self, X, y, w, allow_none: bool = False):
        if X is None and allow_none:
            return None, None, None
        if not isinstance(X, pd.DataFrame):
            raise ValueError("X must be a pandas DataFrame for GNN.")
        n_rows = len(X)
        if y is not None:
            self._validate_vector(y, "y", n_rows)
        if w is not None:
            self._validate_vector(w, "w", n_rows)
        X_np = X.to_numpy(dtype=np.float32, copy=False) if hasattr(
            X, "to_numpy") else np.asarray(X, dtype=np.float32)
        X_tensor = torch.as_tensor(
            X_np, dtype=torch.float32, device=self.device)
        if y is None:
            y_tensor = None
        else:
            y_np = y.to_numpy(dtype=np.float32, copy=False) if hasattr(
                y, "to_numpy") else np.asarray(y, dtype=np.float32)
            y_tensor = torch.as_tensor(
                y_np, dtype=torch.float32, device=self.device).view(-1, 1)
        if w is None:
            w_tensor = torch.ones(
                (len(X), 1), dtype=torch.float32, device=self.device)
        else:
            w_np = w.to_numpy(dtype=np.float32, copy=False) if hasattr(
                w, "to_numpy") else np.asarray(w, dtype=np.float32)
            w_tensor = torch.as_tensor(
                w_np, dtype=torch.float32, device=self.device).view(-1, 1)
        return X_tensor, y_tensor, w_tensor

    def _build_graph_from_df(self, X_df: pd.DataFrame, X_tensor: Optional[torch.Tensor] = None) -> torch.Tensor:
        if not isinstance(X_df, pd.DataFrame):
            raise ValueError("X must be a pandas DataFrame for graph building.")
        meta_expected = None
        cache_key = None
        if self.graph_cache_path:
            meta_expected = self._graph_cache_meta(X_df)
            if self._adj_cache_meta == meta_expected and self._adj_cache_tensor is not None:
                cached = self._adj_cache_tensor
                if cached.device != self.device:
                    cached = cached.to(self.device)
                    self._adj_cache_tensor = cached
                return cached
        else:
            cache_key = self._graph_cache_key(X_df)
            if self._adj_cache_key == cache_key and self._adj_cache_tensor is not None:
                cached = self._adj_cache_tensor
                if cached.device != self.device:
                    cached = cached.to(self.device)
                    self._adj_cache_tensor = cached
                return cached
        X_np = None
        if X_tensor is None:
            X_np = X_df.to_numpy(dtype=np.float32, copy=False)
            X_tensor = torch.as_tensor(
                X_np, dtype=torch.float32, device=self.device)
        if self.graph_cache_path:
            cached = self._load_cached_adj(X_df, meta_expected=meta_expected)
            if cached is not None:
                self._adj_cache_meta = meta_expected
                self._adj_cache_key = None
                self._adj_cache_tensor = cached
                return cached
        use_gpu_knn = self._should_use_gpu_knn(X_df.shape[0], X_tensor)
        if use_gpu_knn:
            edge_index = self._build_edge_index_gpu(X_tensor)
        else:
            if X_np is None:
                X_np = X_df.to_numpy(dtype=np.float32, copy=False)
            edge_index = self._build_edge_index_cpu(X_np)
        adj_norm = self._normalized_adj(edge_index, X_df.shape[0])
        if self.graph_cache_path:
            try:
                IOUtils.ensure_parent_dir(str(self.graph_cache_path))
                torch.save({"adj": adj_norm.cpu(), "meta": meta_expected}, self.graph_cache_path)
            except Exception as exc:
                print(
                    f"[GNN] Failed to cache graph to {self.graph_cache_path}: {exc}")
            self._adj_cache_meta = meta_expected
            self._adj_cache_key = None
        else:
            self._adj_cache_meta = None
            self._adj_cache_key = cache_key
        self._adj_cache_tensor = adj_norm
        return adj_norm

    def fit(self, X_train, y_train, w_train=None,
            X_val=None, y_val=None, w_val=None,
            trial: Optional[optuna.trial.Trial] = None):

        X_train_tensor, y_train_tensor, w_train_tensor = self._tensorize_split(
            X_train, y_train, w_train, allow_none=False)
        has_val = X_val is not None and y_val is not None
        if has_val:
            X_val_tensor, y_val_tensor, w_val_tensor = self._tensorize_split(
                X_val, y_val, w_val, allow_none=False)
        else:
            X_val_tensor = y_val_tensor = w_val_tensor = None

        adj_train = self._build_graph_from_df(X_train, X_train_tensor)
        adj_val = self._build_graph_from_df(
            X_val, X_val_tensor) if has_val else None
        # DataParallel needs adjacency cached on the model to avoid scatter.
        self._set_adj_buffer(adj_train)

        base_gnn = self._unwrap_gnn()
        optimizer = torch.optim.Adam(
            base_gnn.parameters(),
            lr=self.learning_rate,
            weight_decay=float(getattr(self, "weight_decay", 0.0)),
        )
        scaler = GradScaler(enabled=(self.device.type == 'cuda'))

        best_loss = float('inf')
        best_state = None
        patience_counter = 0
        best_epoch = None

        for epoch in range(1, self.epochs + 1):
            epoch_start_ts = time.time()
            self.gnn.train()
            optimizer.zero_grad()
            with autocast(enabled=(self.device.type == 'cuda')):
                if self.data_parallel_enabled:
                    y_pred = self.gnn(X_train_tensor)
                else:
                    y_pred = self.gnn(X_train_tensor, adj_train)
                loss = self._compute_weighted_loss(
                    y_pred, y_train_tensor, w_train_tensor, apply_softplus=False)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            clip_grad_norm_(self.gnn.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()

            val_loss = None
            if has_val:
                self.gnn.eval()
                if self.data_parallel_enabled and adj_val is not None:
                    self._set_adj_buffer(adj_val)
                with torch.no_grad(), autocast(enabled=(self.device.type == 'cuda')):
                    if self.data_parallel_enabled:
                        y_val_pred = self.gnn(X_val_tensor)
                    else:
                        y_val_pred = self.gnn(X_val_tensor, adj_val)
                    val_loss = self._compute_weighted_loss(
                        y_val_pred, y_val_tensor, w_val_tensor, apply_softplus=False)
                if self.data_parallel_enabled:
                    # Restore training adjacency.
                    self._set_adj_buffer(adj_train)

                is_best = val_loss is not None and val_loss < best_loss
                best_loss, best_state, patience_counter, stop_training = self._early_stop_update(
                    val_loss, best_loss, best_state, patience_counter, base_gnn,
                    ignore_keys=["adj_buffer"])
                if is_best:
                    best_epoch = epoch

                prune_now = False
                if trial is not None:
                    trial.report(val_loss, epoch)
                    if trial.should_prune():
                        prune_now = True

                if dist.is_initialized():
                    flag = torch.tensor(
                        [1 if prune_now else 0],
                        device=self.device,
                        dtype=torch.int32,
                    )
                    dist.broadcast(flag, src=0)
                    prune_now = bool(flag.item())

                if prune_now:
                    raise optuna.TrialPruned()
                if stop_training:
                    break

            should_log = (not dist.is_initialized()
                          or DistributedUtils.is_main_process())
            if should_log:
                elapsed = int(time.time() - epoch_start_ts)
                if val_loss is None:
                    print(
                        f"[GNN] Epoch {epoch}/{self.epochs} loss={float(loss):.6f} elapsed={elapsed}s",
                        flush=True,
                    )
                else:
                    print(
                        f"[GNN] Epoch {epoch}/{self.epochs} loss={float(loss):.6f} "
                        f"val_loss={float(val_loss):.6f} elapsed={elapsed}s",
                        flush=True,
                    )

        if best_state is not None:
            base_gnn.load_state_dict(best_state, strict=False)
        self.best_epoch = int(best_epoch or self.epochs)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        self.gnn.eval()
        X_tensor, _, _ = self._tensorize_split(
            X, None, None, allow_none=False)
        adj = self._build_graph_from_df(X, X_tensor)
        if self.data_parallel_enabled:
            self._set_adj_buffer(adj)
        inference_cm = getattr(torch, "inference_mode", torch.no_grad)
        with inference_cm():
            if self.data_parallel_enabled:
                y_pred = self.gnn(X_tensor).cpu().numpy()
            else:
                y_pred = self.gnn(X_tensor, adj).cpu().numpy()
        if self.task_type == 'classification':
            y_pred = 1 / (1 + np.exp(-y_pred))
        else:
            y_pred = np.clip(y_pred, 1e-6, None)
        return y_pred.ravel()

    def encode(self, X: pd.DataFrame) -> np.ndarray:
        """Return per-sample node embeddings (hidden representations)."""
        base = self._unwrap_gnn()
        base.eval()
        X_tensor, _, _ = self._tensorize_split(X, None, None, allow_none=False)
        adj = self._build_graph_from_df(X, X_tensor)
        if self.data_parallel_enabled:
            self._set_adj_buffer(adj)
        inference_cm = getattr(torch, "inference_mode", torch.no_grad)
        with inference_cm():
            h = X_tensor
            layers = getattr(base, "layers", None)
            if layers is None:
                raise RuntimeError("GNN base module does not expose layers.")
            for layer in layers:
                h = layer(h, adj)
            h = torch.sparse.mm(adj, h)
        return h.detach().cpu().numpy()

    def set_params(self, params: Dict[str, Any]):
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Parameter {key} not found in GNN model.")
        # Rebuild the backbone after structural parameter changes.
        self.gnn = SimpleGNN(
            input_dim=self.input_dim,
            hidden_dim=self.hidden_dim,
            num_layers=self.num_layers,
            dropout=self.dropout,
            task_type=self.task_type
        ).to(self.device)
        return self
