# =============================================================================
from __future__ import annotations

from datetime import timedelta
import gc
import os
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import joblib
import numpy as np
import optuna
import pandas as pd
import torch
try:  # pragma: no cover
    import torch.distributed as dist  # type: ignore
except Exception:  # pragma: no cover
    dist = None  # type: ignore
import xgboost as xgb
from sklearn.metrics import log_loss, mean_tweedie_deviance
from sklearn.model_selection import KFold, ShuffleSplit
from sklearn.preprocessing import StandardScaler

import statsmodels.api as sm

from .config_preprocess import BayesOptConfig, OutputManager
from .models import FTTransformerSklearn, GraphNeuralNetSklearn, ResNetSklearn
from .utils import DistributedUtils, EPS, ensure_parent_dir

_XGB_CUDA_CHECKED = False
_XGB_HAS_CUDA = False


def _xgb_cuda_available() -> bool:
    # Best-effort check for XGBoost CUDA build; cached to avoid repeated checks.
    global _XGB_CUDA_CHECKED, _XGB_HAS_CUDA
    if _XGB_CUDA_CHECKED:
        return _XGB_HAS_CUDA
    _XGB_CUDA_CHECKED = True
    if not torch.cuda.is_available():
        _XGB_HAS_CUDA = False
        return False
    try:
        build_info = getattr(xgb, "build_info", None)
        if callable(build_info):
            info = build_info()
            for key in ("USE_CUDA", "use_cuda", "cuda"):
                if key in info:
                    val = info[key]
                    if isinstance(val, str):
                        _XGB_HAS_CUDA = val.strip().upper() in (
                            "ON", "YES", "TRUE", "1")
                    else:
                        _XGB_HAS_CUDA = bool(val)
                    return _XGB_HAS_CUDA
    except Exception:
        pass
    try:
        has_cuda = getattr(getattr(xgb, "core", None), "_has_cuda_support", None)
        if callable(has_cuda):
            _XGB_HAS_CUDA = bool(has_cuda())
            return _XGB_HAS_CUDA
    except Exception:
        pass
    _XGB_HAS_CUDA = False
    return False

# =============================================================================
# Trainer system
# =============================================================================


class TrainerBase:
    def __init__(self, context: "BayesOptModel", label: str, model_name_prefix: str) -> None:
        self.ctx = context
        self.label = label
        self.model_name_prefix = model_name_prefix
        self.model = None
        self.best_params: Optional[Dict[str, Any]] = None
        self.best_trial = None
        self.study_name: Optional[str] = None
        self.enable_distributed_optuna: bool = False
        self._distributed_forced_params: Optional[Dict[str, Any]] = None

    def _dist_barrier(self, reason: str) -> None:
        """DDP barrier wrapper used by distributed Optuna.

        To debug "trial finished but next trial never starts" hangs, set these
        environment variables (either in shell or config.json `env`):
        - `BAYESOPT_DDP_BARRIER_DEBUG=1` to print barrier enter/exit per-rank
        - `BAYESOPT_DDP_BARRIER_TIMEOUT=300` to fail fast instead of waiting forever
        - `TORCH_DISTRIBUTED_DEBUG=DETAIL` and `NCCL_DEBUG=INFO` for PyTorch/NCCL logs
        """
        if dist is None:
            return
        try:
            if not getattr(dist, "is_available", lambda: False)():
                return
            if not dist.is_initialized():
                return
        except Exception:
            return

        timeout_seconds = int(os.environ.get("BAYESOPT_DDP_BARRIER_TIMEOUT", "1800"))
        debug_barrier = os.environ.get("BAYESOPT_DDP_BARRIER_DEBUG", "").strip() in {"1", "true", "TRUE", "yes", "YES"}
        rank = None
        world = None
        if debug_barrier:
            try:
                rank = dist.get_rank()
                world = dist.get_world_size()
                print(f"[DDP][{self.label}] entering barrier({reason}) rank={rank}/{world}", flush=True)
            except Exception:
                debug_barrier = False
        try:
            timeout = timedelta(seconds=timeout_seconds)
            backend = None
            try:
                backend = dist.get_backend()
            except Exception:
                backend = None

            # `monitored_barrier` is only implemented for GLOO; using it under NCCL
            # will raise and can itself trigger a secondary hang. Prefer an async
            # barrier with timeout for NCCL.
            monitored = getattr(dist, "monitored_barrier", None)
            if backend == "gloo" and callable(monitored):
                monitored(timeout=timeout)
            else:
                work = None
                try:
                    work = dist.barrier(async_op=True)
                except TypeError:
                    work = None
                if work is not None:
                    wait = getattr(work, "wait", None)
                    if callable(wait):
                        try:
                            wait(timeout=timeout)
                        except TypeError:
                            wait()
                    else:
                        dist.barrier()
                else:
                    dist.barrier()
            if debug_barrier:
                print(f"[DDP][{self.label}] exit barrier({reason}) rank={rank}/{world}", flush=True)
        except Exception as exc:
            print(
                f"[DDP][{self.label}] barrier failed during {reason}: {exc}",
                flush=True,
            )
            raise

    @property
    def config(self) -> BayesOptConfig:
        return self.ctx.config

    @property
    def output(self) -> OutputManager:
        return self.ctx.output_manager

    def _get_model_filename(self) -> str:
        ext = 'pkl' if self.label in ['Xgboost', 'GLM'] else 'pth'
        return f'01_{self.ctx.model_nme}_{self.model_name_prefix}.{ext}'

    def _resolve_optuna_storage_url(self) -> Optional[str]:
        storage = getattr(self.config, "optuna_storage", None)
        if not storage:
            return None
        storage_str = str(storage).strip()
        if not storage_str:
            return None
        if "://" in storage_str or storage_str == ":memory:":
            return storage_str
        path = Path(storage_str)
        path = path.resolve()
        ensure_parent_dir(str(path))
        return f"sqlite:///{path.as_posix()}"

    def _resolve_optuna_study_name(self) -> str:
        prefix = getattr(self.config, "optuna_study_prefix",
                         None) or "bayesopt"
        raw = f"{prefix}_{self.ctx.model_nme}_{self.model_name_prefix}"
        safe = "".join([c if c.isalnum() or c in "._-" else "_" for c in raw])
        return safe.lower()

    def tune(self, max_evals: int, objective_fn=None) -> None:
        # Generic Optuna tuning loop.
        if objective_fn is None:
            # If subclass doesn't provide objective_fn, default to cross_val.
            objective_fn = self.cross_val

        if self._should_use_distributed_optuna():
            self._distributed_tune(max_evals, objective_fn)
            return

        total_trials = max(1, int(max_evals))
        progress_counter = {"count": 0}

        def objective_wrapper(trial: optuna.trial.Trial) -> float:
            should_log = DistributedUtils.is_main_process()
            if should_log:
                current_idx = progress_counter["count"] + 1
                print(
                    f"[Optuna][{self.label}] Trial {current_idx}/{total_trials} started "
                    f"(trial_id={trial.number})."
                )
            try:
                result = objective_fn(trial)
            except RuntimeError as exc:
                if "out of memory" in str(exc).lower():
                    print(
                        f"[Optuna][{self.label}] OOM detected. Pruning trial and clearing CUDA cache."
                    )
                    self._clean_gpu()
                    raise optuna.TrialPruned() from exc
                raise
            finally:
                self._clean_gpu()
                if should_log:
                    progress_counter["count"] = progress_counter["count"] + 1
                    trial_state = getattr(trial, "state", None)
                    state_repr = getattr(trial_state, "name", "OK")
                    print(
                        f"[Optuna][{self.label}] Trial {progress_counter['count']}/{total_trials} finished "
                        f"(status={state_repr})."
                    )
            return result

        storage_url = self._resolve_optuna_storage_url()
        study_name = self._resolve_optuna_study_name()
        study_kwargs: Dict[str, Any] = {
            "direction": "minimize",
            "sampler": optuna.samplers.TPESampler(seed=self.ctx.rand_seed),
        }
        if storage_url:
            study_kwargs.update(
                storage=storage_url,
                study_name=study_name,
                load_if_exists=True,
            )

        study = optuna.create_study(**study_kwargs)
        self.study_name = getattr(study, "study_name", None)

        def checkpoint_callback(check_study: optuna.study.Study, _trial) -> None:
            # Persist best_params after each trial to allow safe resume.
            try:
                best = getattr(check_study, "best_trial", None)
                if best is None:
                    return
                best_params = getattr(best, "params", None)
                if not best_params:
                    return
                params_path = self.output.result_path(
                    f'{self.ctx.model_nme}_bestparams_{self.label.lower()}.csv'
                )
                pd.DataFrame(best_params, index=[0]).to_csv(
                    params_path, index=False)
            except Exception:
                return

        completed_states = (
            optuna.trial.TrialState.COMPLETE,
            optuna.trial.TrialState.PRUNED,
            optuna.trial.TrialState.FAIL,
        )
        completed = len(study.get_trials(states=completed_states))
        progress_counter["count"] = completed
        remaining = max(0, total_trials - completed)
        if remaining > 0:
            study.optimize(
                objective_wrapper,
                n_trials=remaining,
                callbacks=[checkpoint_callback],
            )
        self.best_params = study.best_params
        self.best_trial = study.best_trial

        # Save best params to CSV for reproducibility.
        params_path = self.output.result_path(
            f'{self.ctx.model_nme}_bestparams_{self.label.lower()}.csv'
        )
        pd.DataFrame(self.best_params, index=[0]).to_csv(
            params_path, index=False)

    def train(self) -> None:
        raise NotImplementedError

    def save(self) -> None:
        if self.model is None:
            print(f"[save] Warning: No model to save for {self.label}")
            return

        path = self.output.model_path(self._get_model_filename())
        if self.label in ['Xgboost', 'GLM']:
            joblib.dump(self.model, path)
        else:
            # PyTorch models can save state_dict or the full object.
            # Legacy behavior: ResNetTrainer saves state_dict; FTTrainer saves full object.
            if hasattr(self.model, 'resnet'):  # ResNetSklearn model
                torch.save(self.model.resnet.state_dict(), path)
            else:  # FTTransformerSklearn or other PyTorch model
                torch.save(self.model, path)

    def load(self) -> None:
        path = self.output.model_path(self._get_model_filename())
        if not os.path.exists(path):
            print(f"[load] Warning: Model file not found: {path}")
            return

        if self.label in ['Xgboost', 'GLM']:
            self.model = joblib.load(path)
        else:
            # PyTorch loading depends on the model structure.
            if self.label == 'ResNet' or self.label == 'ResNetClassifier':
                # ResNet requires reconstructing the skeleton; handled by subclass.
                pass
            else:
                # FT-Transformer serializes the whole object; load then move to device.
                loaded = torch.load(path, map_location='cpu')
                self._move_to_device(loaded)
                self.model = loaded

    def _move_to_device(self, model_obj):
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        if hasattr(model_obj, 'device'):
            model_obj.device = device
        if hasattr(model_obj, 'to'):
            model_obj.to(device)
        # Move nested submodules (ft/resnet/gnn) to the same device.
        if hasattr(model_obj, 'ft'):
            model_obj.ft.to(device)
        if hasattr(model_obj, 'resnet'):
            model_obj.resnet.to(device)
        if hasattr(model_obj, 'gnn'):
            model_obj.gnn.to(device)

    def _should_use_distributed_optuna(self) -> bool:
        if not self.enable_distributed_optuna:
            return False
        rank_env = os.environ.get("RANK")
        world_env = os.environ.get("WORLD_SIZE")
        local_env = os.environ.get("LOCAL_RANK")
        if rank_env is None or world_env is None or local_env is None:
            return False
        try:
            world_size = int(world_env)
        except Exception:
            return False
        return world_size > 1

    def _distributed_is_main(self) -> bool:
        return DistributedUtils.is_main_process()

    def _distributed_send_command(self, payload: Dict[str, Any]) -> None:
        if not self._should_use_distributed_optuna() or not self._distributed_is_main():
            return
        if dist is None:
            return
        DistributedUtils.setup_ddp()
        if not dist.is_initialized():
            return
        message = [payload]
        dist.broadcast_object_list(message, src=0)

    def _distributed_prepare_trial(self, params: Dict[str, Any]) -> None:
        if not self._should_use_distributed_optuna():
            return
        if not self._distributed_is_main():
            return
        if dist is None:
            return
        self._distributed_send_command({"type": "RUN", "params": params})
        if not dist.is_initialized():
            return
        # STEP 2 (DDP/Optuna): make sure all ranks start the trial together.
        self._dist_barrier("prepare_trial")

    def _distributed_worker_loop(self, objective_fn: Callable[[Optional[optuna.trial.Trial]], float]) -> None:
        if dist is None:
            print(
                f"[Optuna][Worker][{self.label}] torch.distributed unavailable. Worker exit.",
                flush=True,
            )
            return
        DistributedUtils.setup_ddp()
        if not dist.is_initialized():
            print(
                f"[Optuna][Worker][{self.label}] DDP init failed. Worker exit.",
                flush=True,
            )
            return
        while True:
            message = [None]
            dist.broadcast_object_list(message, src=0)
            payload = message[0]
            if not isinstance(payload, dict):
                continue
            cmd = payload.get("type")
            if cmd == "STOP":
                best_params = payload.get("best_params")
                if best_params is not None:
                    self.best_params = best_params
                break
            if cmd == "RUN":
                params = payload.get("params") or {}
                self._distributed_forced_params = params
                # STEP 2 (DDP/Optuna): align worker with rank0 before running objective_fn.
                self._dist_barrier("worker_start")
                try:
                    objective_fn(None)
                except optuna.TrialPruned:
                    pass
                except Exception as exc:
                    print(
                        f"[Optuna][Worker][{self.label}] Exception: {exc}", flush=True)
                finally:
                    self._clean_gpu()
                    # STEP 2 (DDP/Optuna): align worker with rank0 after objective_fn returns/raises.
                    self._dist_barrier("worker_end")

    def _distributed_tune(self, max_evals: int, objective_fn: Callable[[optuna.trial.Trial], float]) -> None:
        if dist is None:
            print(
                f"[Optuna][{self.label}] torch.distributed unavailable. Fallback to single-process.",
                flush=True,
            )
            prev = self.enable_distributed_optuna
            self.enable_distributed_optuna = False
            try:
                self.tune(max_evals, objective_fn)
            finally:
                self.enable_distributed_optuna = prev
            return
        DistributedUtils.setup_ddp()
        if not dist.is_initialized():
            rank_env = os.environ.get("RANK", "0")
            if str(rank_env) != "0":
                print(
                    f"[Optuna][{self.label}] DDP init failed on worker. Skip.",
                    flush=True,
                )
                return
            print(
                f"[Optuna][{self.label}] DDP init failed. Fallback to single-process.",
                flush=True,
            )
            prev = self.enable_distributed_optuna
            self.enable_distributed_optuna = False
            try:
                self.tune(max_evals, objective_fn)
            finally:
                self.enable_distributed_optuna = prev
            return
        if not self._distributed_is_main():
            self._distributed_worker_loop(objective_fn)
            return

        total_trials = max(1, int(max_evals))
        progress_counter = {"count": 0}

        def objective_wrapper(trial: optuna.trial.Trial) -> float:
            should_log = True
            if should_log:
                current_idx = progress_counter["count"] + 1
                print(
                    f"[Optuna][{self.label}] Trial {current_idx}/{total_trials} started "
                    f"(trial_id={trial.number})."
                )
            try:
                result = objective_fn(trial)
            except RuntimeError as exc:
                if "out of memory" in str(exc).lower():
                    print(
                        f"[Optuna][{self.label}] OOM detected. Pruning trial and clearing CUDA cache."
                    )
                    self._clean_gpu()
                    raise optuna.TrialPruned() from exc
                raise
            finally:
                self._clean_gpu()
                if should_log:
                    progress_counter["count"] = progress_counter["count"] + 1
                    trial_state = getattr(trial, "state", None)
                    state_repr = getattr(trial_state, "name", "OK")
                    print(
                        f"[Optuna][{self.label}] Trial {progress_counter['count']}/{total_trials} finished "
                        f"(status={state_repr})."
                    )
                # STEP 2 (DDP/Optuna): a trial-end sync point; debug with BAYESOPT_DDP_BARRIER_DEBUG=1.
                self._dist_barrier("trial_end")
            return result

        storage_url = self._resolve_optuna_storage_url()
        study_name = self._resolve_optuna_study_name()
        study_kwargs: Dict[str, Any] = {
            "direction": "minimize",
            "sampler": optuna.samplers.TPESampler(seed=self.ctx.rand_seed),
        }
        if storage_url:
            study_kwargs.update(
                storage=storage_url,
                study_name=study_name,
                load_if_exists=True,
            )
        study = optuna.create_study(**study_kwargs)
        self.study_name = getattr(study, "study_name", None)

        def checkpoint_callback(check_study: optuna.study.Study, _trial) -> None:
            try:
                best = getattr(check_study, "best_trial", None)
                if best is None:
                    return
                best_params = getattr(best, "params", None)
                if not best_params:
                    return
                params_path = self.output.result_path(
                    f'{self.ctx.model_nme}_bestparams_{self.label.lower()}.csv'
                )
                pd.DataFrame(best_params, index=[0]).to_csv(
                    params_path, index=False)
            except Exception:
                return

        completed_states = (
            optuna.trial.TrialState.COMPLETE,
            optuna.trial.TrialState.PRUNED,
            optuna.trial.TrialState.FAIL,
        )
        completed = len(study.get_trials(states=completed_states))
        progress_counter["count"] = completed
        remaining = max(0, total_trials - completed)
        try:
            if remaining > 0:
                study.optimize(
                    objective_wrapper,
                    n_trials=remaining,
                    callbacks=[checkpoint_callback],
                )
            self.best_params = study.best_params
            self.best_trial = study.best_trial
            params_path = self.output.result_path(
                f'{self.ctx.model_nme}_bestparams_{self.label.lower()}.csv'
            )
            pd.DataFrame(self.best_params, index=[0]).to_csv(
                params_path, index=False)
        finally:
            self._distributed_send_command(
                {"type": "STOP", "best_params": self.best_params})

    def _clean_gpu(self):
        gc.collect()
        if torch.cuda.is_available():
            device = None
            try:
                device = getattr(self, "device", None)
            except Exception:
                device = None
            if isinstance(device, torch.device):
                try:
                    torch.cuda.set_device(device)
                except Exception:
                    pass
            torch.cuda.empty_cache()
            do_ipc_collect = os.environ.get("BAYESOPT_CUDA_IPC_COLLECT", "").strip() in {"1", "true", "TRUE", "yes", "YES"}
            do_sync = os.environ.get("BAYESOPT_CUDA_SYNC", "").strip() in {"1", "true", "TRUE", "yes", "YES"}
            if do_ipc_collect:
                torch.cuda.ipc_collect()
            if do_sync:
                torch.cuda.synchronize()

    def _standardize_fold(self,
                          X_train: pd.DataFrame,
                          X_val: pd.DataFrame,
                          columns: Optional[List[str]] = None
                          ) -> Tuple[pd.DataFrame, pd.DataFrame, StandardScaler]:
        """Fit StandardScaler on the training fold and transform train/val features.

        Args:
            X_train: training features.
            X_val: validation features.
            columns: columns to scale (default: all).

        Returns:
            Scaled train/val features and the fitted scaler.
        """
        scaler = StandardScaler()
        cols = list(columns) if columns else list(X_train.columns)
        X_train_scaled = X_train.copy(deep=True)
        X_val_scaled = X_val.copy(deep=True)
        if cols:
            scaler.fit(X_train_scaled[cols])
            X_train_scaled[cols] = scaler.transform(X_train_scaled[cols])
            X_val_scaled[cols] = scaler.transform(X_val_scaled[cols])
        return X_train_scaled, X_val_scaled, scaler

    def cross_val_generic(
            self,
            trial: optuna.trial.Trial,
            hyperparameter_space: Dict[str, Callable[[optuna.trial.Trial], Any]],
            data_provider: Callable[[], Tuple[pd.DataFrame, pd.Series, Optional[pd.Series]]],
            model_builder: Callable[[Dict[str, Any]], Any],
            metric_fn: Callable[[pd.Series, np.ndarray, Optional[pd.Series]], float],
            sample_limit: Optional[int] = None,
            preprocess_fn: Optional[Callable[[
                pd.DataFrame, pd.DataFrame], Tuple[pd.DataFrame, pd.DataFrame]]] = None,
            fit_predict_fn: Optional[
                Callable[[Any, pd.DataFrame, pd.Series, Optional[pd.Series],
                          pd.DataFrame, pd.Series, Optional[pd.Series],
                          optuna.trial.Trial], np.ndarray]
            ] = None,
            cleanup_fn: Optional[Callable[[Any], None]] = None,
            splitter: Optional[Iterable[Tuple[np.ndarray, np.ndarray]]] = None) -> float:
        """Generic holdout/CV helper to reuse tuning workflows.

        Args:
            trial: current Optuna trial.
            hyperparameter_space: sampler dict keyed by parameter name.
            data_provider: callback returning (X, y, sample_weight).
            model_builder: callback to build a model per fold.
            metric_fn: loss/score function taking y_true, y_pred, weight.
            sample_limit: optional sample cap; random sample if exceeded.
            preprocess_fn: optional per-fold preprocessing (X_train, X_val).
            fit_predict_fn: optional custom fit/predict logic for validation.
            cleanup_fn: optional cleanup callback per fold.
            splitter: optional (train_idx, val_idx) iterator; defaults to ShuffleSplit.

        Returns:
            Mean validation metric across folds.
        """
        params: Optional[Dict[str, Any]] = None
        if self._distributed_forced_params is not None:
            params = self._distributed_forced_params
            self._distributed_forced_params = None
        else:
            if trial is None:
                raise RuntimeError(
                    "Missing Optuna trial for parameter sampling.")
            params = {name: sampler(trial)
                      for name, sampler in hyperparameter_space.items()}
            if self._should_use_distributed_optuna():
                self._distributed_prepare_trial(params)
        X_all, y_all, w_all = data_provider()
        if sample_limit is not None and len(X_all) > sample_limit:
            sampled_idx = X_all.sample(
                n=sample_limit,
                random_state=self.ctx.rand_seed
            ).index
            X_all = X_all.loc[sampled_idx]
            y_all = y_all.loc[sampled_idx]
            w_all = w_all.loc[sampled_idx] if w_all is not None else None

        split_iter = splitter or ShuffleSplit(
            n_splits=int(1 / self.ctx.prop_test),
            test_size=self.ctx.prop_test,
            random_state=self.ctx.rand_seed
        ).split(X_all)

        losses: List[float] = []
        for train_idx, val_idx in split_iter:
            X_train = X_all.iloc[train_idx]
            y_train = y_all.iloc[train_idx]
            X_val = X_all.iloc[val_idx]
            y_val = y_all.iloc[val_idx]
            w_train = w_all.iloc[train_idx] if w_all is not None else None
            w_val = w_all.iloc[val_idx] if w_all is not None else None

            if preprocess_fn:
                X_train, X_val = preprocess_fn(X_train, X_val)

            model = model_builder(params)
            try:
                if fit_predict_fn:
                    y_pred = fit_predict_fn(
                        model, X_train, y_train, w_train,
                        X_val, y_val, w_val, trial
                    )
                else:
                    fit_kwargs = {}
                    if w_train is not None:
                        fit_kwargs["sample_weight"] = w_train
                    model.fit(X_train, y_train, **fit_kwargs)
                    y_pred = model.predict(X_val)
                losses.append(metric_fn(y_val, y_pred, w_val))
            finally:
                if cleanup_fn:
                    cleanup_fn(model)
                self._clean_gpu()

        return float(np.mean(losses))

    # Prediction + caching logic.
    def _predict_and_cache(self,
                           model,
                           pred_prefix: str,
                           use_oht: bool = False,
                           design_fn=None,
                           predict_kwargs_train: Optional[Dict[str, Any]] = None,
                           predict_kwargs_test: Optional[Dict[str, Any]] = None,
                           predict_fn: Optional[Callable[..., Any]] = None) -> None:
        if design_fn:
            X_train = design_fn(train=True)
            X_test = design_fn(train=False)
        elif use_oht:
            X_train = self.ctx.train_oht_scl_data[self.ctx.var_nmes]
            X_test = self.ctx.test_oht_scl_data[self.ctx.var_nmes]
        else:
            X_train = self.ctx.train_data[self.ctx.factor_nmes]
            X_test = self.ctx.test_data[self.ctx.factor_nmes]

        predictor = predict_fn or model.predict
        preds_train = predictor(X_train, **(predict_kwargs_train or {}))
        preds_test = predictor(X_test, **(predict_kwargs_test or {}))
        preds_train = np.asarray(preds_train)
        preds_test = np.asarray(preds_test)

        if preds_train.ndim <= 1 or (preds_train.ndim == 2 and preds_train.shape[1] == 1):
            col_name = f'pred_{pred_prefix}'
            self.ctx.train_data[col_name] = preds_train.reshape(-1)
            self.ctx.test_data[col_name] = preds_test.reshape(-1)
            self.ctx.train_data[f'w_{col_name}'] = (
                self.ctx.train_data[col_name] *
                self.ctx.train_data[self.ctx.weight_nme]
            )
            self.ctx.test_data[f'w_{col_name}'] = (
                self.ctx.test_data[col_name] *
                self.ctx.test_data[self.ctx.weight_nme]
            )
            return

        # Vector outputs (e.g., embeddings) are expanded into pred_<prefix>_0.. columns.
        if preds_train.ndim != 2:
            raise ValueError(
                f"Unexpected prediction shape for '{pred_prefix}': {preds_train.shape}")
        if preds_test.ndim != 2 or preds_test.shape[1] != preds_train.shape[1]:
            raise ValueError(
                f"Train/test prediction dims mismatch for '{pred_prefix}': "
                f"{preds_train.shape} vs {preds_test.shape}")
        for j in range(preds_train.shape[1]):
            col_name = f'pred_{pred_prefix}_{j}'
            self.ctx.train_data[col_name] = preds_train[:, j]
            self.ctx.test_data[col_name] = preds_test[:, j]

    def _cache_predictions(self,
                           pred_prefix: str,
                           preds_train,
                           preds_test) -> None:
        preds_train = np.asarray(preds_train)
        preds_test = np.asarray(preds_test)
        if preds_train.ndim <= 1 or (preds_train.ndim == 2 and preds_train.shape[1] == 1):
            if preds_test.ndim > 1:
                preds_test = preds_test.reshape(-1)
            col_name = f'pred_{pred_prefix}'
            self.ctx.train_data[col_name] = preds_train.reshape(-1)
            self.ctx.test_data[col_name] = preds_test.reshape(-1)
            self.ctx.train_data[f'w_{col_name}'] = (
                self.ctx.train_data[col_name] *
                self.ctx.train_data[self.ctx.weight_nme]
            )
            self.ctx.test_data[f'w_{col_name}'] = (
                self.ctx.test_data[col_name] *
                self.ctx.test_data[self.ctx.weight_nme]
            )
            return

        if preds_train.ndim != 2:
            raise ValueError(
                f"Unexpected prediction shape for '{pred_prefix}': {preds_train.shape}")
        if preds_test.ndim != 2 or preds_test.shape[1] != preds_train.shape[1]:
            raise ValueError(
                f"Train/test prediction dims mismatch for '{pred_prefix}': "
                f"{preds_train.shape} vs {preds_test.shape}")
        for j in range(preds_train.shape[1]):
            col_name = f'pred_{pred_prefix}_{j}'
            self.ctx.train_data[col_name] = preds_train[:, j]
            self.ctx.test_data[col_name] = preds_test[:, j]

    def _resolve_best_epoch(self,
                            history: Optional[Dict[str, List[float]]],
                            default_epochs: int) -> int:
        if not history:
            return max(1, int(default_epochs))
        vals = history.get("val") or []
        if not vals:
            return max(1, int(default_epochs))
        best_idx = int(np.nanargmin(vals))
        return max(1, best_idx + 1)

    def _fit_predict_cache(self,
                           model,
                           X_train,
                           y_train,
                           sample_weight,
                           pred_prefix: str,
                           use_oht: bool = False,
                           design_fn=None,
                           fit_kwargs: Optional[Dict[str, Any]] = None,
                           sample_weight_arg: Optional[str] = 'sample_weight',
                           predict_kwargs_train: Optional[Dict[str, Any]] = None,
                           predict_kwargs_test: Optional[Dict[str, Any]] = None,
                           predict_fn: Optional[Callable[..., Any]] = None,
                           record_label: bool = True) -> None:
        fit_kwargs = fit_kwargs.copy() if fit_kwargs else {}
        if sample_weight is not None and sample_weight_arg:
            fit_kwargs.setdefault(sample_weight_arg, sample_weight)
        model.fit(X_train, y_train, **fit_kwargs)
        if record_label:
            self.ctx.model_label.append(self.label)
        self._predict_and_cache(
            model,
            pred_prefix,
            use_oht=use_oht,
            design_fn=design_fn,
            predict_kwargs_train=predict_kwargs_train,
            predict_kwargs_test=predict_kwargs_test,
            predict_fn=predict_fn)


class GNNTrainer(TrainerBase):
    def __init__(self, context: "BayesOptModel") -> None:
        super().__init__(context, 'GNN', 'GNN')
        self.model: Optional[GraphNeuralNetSklearn] = None
        self.enable_distributed_optuna = bool(context.config.use_gnn_ddp)

    def _build_model(self, params: Optional[Dict[str, Any]] = None) -> GraphNeuralNetSklearn:
        params = params or {}
        base_tw_power = self.ctx.default_tweedie_power()
        model = GraphNeuralNetSklearn(
            model_nme=f"{self.ctx.model_nme}_gnn",
            input_dim=len(self.ctx.var_nmes),
            hidden_dim=int(params.get("hidden_dim", 64)),
            num_layers=int(params.get("num_layers", 2)),
            k_neighbors=int(params.get("k_neighbors", 10)),
            dropout=float(params.get("dropout", 0.1)),
            learning_rate=float(params.get("learning_rate", 1e-3)),
            epochs=int(params.get("epochs", self.ctx.epochs)),
            patience=int(params.get("patience", 5)),
            task_type=self.ctx.task_type,
            tweedie_power=float(params.get("tw_power", base_tw_power or 1.5)),
            weight_decay=float(params.get("weight_decay", 0.0)),
            use_data_parallel=bool(self.ctx.config.use_gnn_data_parallel),
            use_ddp=bool(self.ctx.config.use_gnn_ddp),
            use_approx_knn=bool(self.ctx.config.gnn_use_approx_knn),
            approx_knn_threshold=int(self.ctx.config.gnn_approx_knn_threshold),
            graph_cache_path=self.ctx.config.gnn_graph_cache,
            max_gpu_knn_nodes=self.ctx.config.gnn_max_gpu_knn_nodes,
            knn_gpu_mem_ratio=float(self.ctx.config.gnn_knn_gpu_mem_ratio),
            knn_gpu_mem_overhead=float(
                self.ctx.config.gnn_knn_gpu_mem_overhead),
        )
        return model

    def cross_val(self, trial: optuna.trial.Trial) -> float:
        base_tw_power = self.ctx.default_tweedie_power()
        metric_ctx: Dict[str, Any] = {}

        def data_provider():
            data = self.ctx.train_oht_data if self.ctx.train_oht_data is not None else self.ctx.train_oht_scl_data
            assert data is not None, "Preprocessed training data is missing."
            return data[self.ctx.var_nmes], data[self.ctx.resp_nme], data[self.ctx.weight_nme]

        def model_builder(params: Dict[str, Any]):
            tw_power = params.get("tw_power", base_tw_power)
            metric_ctx["tw_power"] = tw_power
            return self._build_model(params)

        def preprocess_fn(X_train, X_val):
            X_train_s, X_val_s, _ = self._standardize_fold(
                X_train, X_val, self.ctx.num_features)
            return X_train_s, X_val_s

        def fit_predict(model, X_train, y_train, w_train, X_val, y_val, w_val, trial_obj):
            model.fit(
                X_train,
                y_train,
                w_train=w_train,
                X_val=X_val,
                y_val=y_val,
                w_val=w_val,
                trial=trial_obj,
            )
            return model.predict(X_val)

        def metric_fn(y_true, y_pred, weight):
            if self.ctx.task_type == 'classification':
                y_pred_clipped = np.clip(y_pred, EPS, 1 - EPS)
                return log_loss(y_true, y_pred_clipped, sample_weight=weight)
            y_pred_safe = np.maximum(y_pred, EPS)
            power = metric_ctx.get("tw_power", base_tw_power or 1.5)
            return mean_tweedie_deviance(
                y_true,
                y_pred_safe,
                sample_weight=weight,
                power=power,
            )

        # Keep GNN BO lightweight: sample during CV, use full data for final training.
        X_cap = data_provider()[0]
        sample_limit = min(200000, len(X_cap)) if len(X_cap) > 200000 else None

        param_space: Dict[str, Callable[[optuna.trial.Trial], Any]] = {
            "learning_rate": lambda t: t.suggest_float('learning_rate', 1e-4, 5e-3, log=True),
            "hidden_dim": lambda t: t.suggest_int('hidden_dim', 16, 128, step=16),
            "num_layers": lambda t: t.suggest_int('num_layers', 1, 4),
            "k_neighbors": lambda t: t.suggest_int('k_neighbors', 5, 30),
            "dropout": lambda t: t.suggest_float('dropout', 0.0, 0.3),
            "weight_decay": lambda t: t.suggest_float('weight_decay', 1e-6, 1e-2, log=True),
        }
        if self.ctx.task_type == 'regression' and self.ctx.obj == 'reg:tweedie':
            param_space["tw_power"] = lambda t: t.suggest_float(
                'tw_power', 1.0, 2.0)

        return self.cross_val_generic(
            trial=trial,
            hyperparameter_space=param_space,
            data_provider=data_provider,
            model_builder=model_builder,
            metric_fn=metric_fn,
            sample_limit=sample_limit,
            preprocess_fn=preprocess_fn,
            fit_predict_fn=fit_predict,
            cleanup_fn=lambda m: getattr(
                getattr(m, "gnn", None), "to", lambda *_args, **_kwargs: None)("cpu")
        )

    def train(self) -> None:
        if not self.best_params:
            raise RuntimeError("Run tune() first to obtain best GNN parameters.")

        data = self.ctx.train_oht_scl_data
        assert data is not None, "Preprocessed training data is missing."
        X_all = data[self.ctx.var_nmes]
        y_all = data[self.ctx.resp_nme]
        w_all = data[self.ctx.weight_nme]

        use_refit = bool(getattr(self.ctx.config, "final_refit", True))
        refit_epochs = None

        if 0.0 < float(self.ctx.prop_test) < 1.0 and len(X_all) >= 10:
            splitter = ShuffleSplit(
                n_splits=1,
                test_size=self.ctx.prop_test,
                random_state=self.ctx.rand_seed,
            )
            train_idx, val_idx = next(splitter.split(X_all))
            X_train = X_all.iloc[train_idx]
            y_train = y_all.iloc[train_idx]
            w_train = w_all.iloc[train_idx]
            X_val = X_all.iloc[val_idx]
            y_val = y_all.iloc[val_idx]
            w_val = w_all.iloc[val_idx]

            if use_refit:
                tmp_model = self._build_model(self.best_params)
                tmp_model.fit(
                    X_train,
                    y_train,
                    w_train=w_train,
                    X_val=X_val,
                    y_val=y_val,
                    w_val=w_val,
                    trial=None,
                )
                refit_epochs = int(getattr(tmp_model, "best_epoch", None) or self.ctx.epochs)
                getattr(getattr(tmp_model, "gnn", None), "to",
                        lambda *_args, **_kwargs: None)("cpu")
                self._clean_gpu()
            else:
                self.model = self._build_model(self.best_params)
                self.model.fit(
                    X_train,
                    y_train,
                    w_train=w_train,
                    X_val=X_val,
                    y_val=y_val,
                    w_val=w_val,
                    trial=None,
                )
        else:
            use_refit = False

        if use_refit:
            self.model = self._build_model(self.best_params)
            if refit_epochs is not None:
                self.model.epochs = int(refit_epochs)
            self.model.fit(
                X_all,
                y_all,
                w_train=w_all,
                X_val=None,
                y_val=None,
                w_val=None,
                trial=None,
            )
        elif self.model is None:
            self.model = self._build_model(self.best_params)
            self.model.fit(
                X_all,
                y_all,
                w_train=w_all,
                X_val=None,
                y_val=None,
                w_val=None,
                trial=None,
            )
        self.ctx.model_label.append(self.label)
        self._predict_and_cache(self.model, pred_prefix='gnn', use_oht=True)
        self.ctx.gnn_best = self.model

        # If geo_feature_nmes is set, refresh geo tokens for FT input.
        if self.ctx.config.geo_feature_nmes:
            self.prepare_geo_tokens(force=True)

    def ensemble_predict(self, k: int) -> None:
        if not self.best_params:
            raise RuntimeError("Run tune() first to obtain best GNN parameters.")
        data = self.ctx.train_oht_scl_data
        test_data = self.ctx.test_oht_scl_data
        if data is None or test_data is None:
            raise RuntimeError("Missing standardized data for GNN ensemble.")
        X_all = data[self.ctx.var_nmes]
        y_all = data[self.ctx.resp_nme]
        w_all = data[self.ctx.weight_nme]
        X_test = test_data[self.ctx.var_nmes]

        k = max(2, int(k))
        n_samples = len(X_all)
        if n_samples < k:
            print(
                f"[GNN Ensemble] n_samples={n_samples} < k={k}; skip ensemble.",
                flush=True,
            )
            return

        splitter = KFold(
            n_splits=k,
            shuffle=True,
            random_state=self.ctx.rand_seed,
        )
        preds_train_sum = np.zeros(n_samples, dtype=np.float64)
        preds_test_sum = np.zeros(len(X_test), dtype=np.float64)

        for train_idx, val_idx in splitter.split(X_all):
            model = self._build_model(self.best_params)
            model.fit(
                X_all.iloc[train_idx],
                y_all.iloc[train_idx],
                w_train=w_all.iloc[train_idx],
                X_val=X_all.iloc[val_idx],
                y_val=y_all.iloc[val_idx],
                w_val=w_all.iloc[val_idx],
                trial=None,
            )
            pred_train = model.predict(X_all)
            pred_test = model.predict(X_test)
            preds_train_sum += np.asarray(pred_train, dtype=np.float64)
            preds_test_sum += np.asarray(pred_test, dtype=np.float64)
            getattr(getattr(model, "gnn", None), "to",
                    lambda *_args, **_kwargs: None)("cpu")
            self._clean_gpu()

        preds_train = preds_train_sum / float(k)
        preds_test = preds_test_sum / float(k)
        self._cache_predictions("gnn", preds_train, preds_test)

    def prepare_geo_tokens(self, force: bool = False) -> None:
        """Train/update the GNN encoder for geo tokens and inject them into FT input."""
        geo_cols = list(self.ctx.config.geo_feature_nmes or [])
        if not geo_cols:
            return
        if (not force) and self.ctx.train_geo_tokens is not None and self.ctx.test_geo_tokens is not None:
            return

        result = self.ctx._build_geo_tokens()
        if result is None:
            return
        train_tokens, test_tokens, cols, geo_gnn = result
        self.ctx.train_geo_tokens = train_tokens
        self.ctx.test_geo_tokens = test_tokens
        self.ctx.geo_token_cols = cols
        self.ctx.geo_gnn_model = geo_gnn
        print(f"[GeoToken][GNNTrainer] Generated {len(cols)} dims and injected into FT.", flush=True)

    def save(self) -> None:
        if self.model is None:
            print(f"[save] Warning: No model to save for {self.label}")
            return
        path = self.output.model_path(self._get_model_filename())
        base_gnn = getattr(self.model, "_unwrap_gnn", lambda: None)()
        state = None if base_gnn is None else base_gnn.state_dict()
        payload = {
            "best_params": self.best_params,
            "state_dict": state,
        }
        torch.save(payload, path)

    def load(self) -> None:
        path = self.output.model_path(self._get_model_filename())
        if not os.path.exists(path):
            print(f"[load] Warning: Model file not found: {path}")
            return
        payload = torch.load(path, map_location='cpu')
        if not isinstance(payload, dict):
            raise ValueError(f"Invalid GNN checkpoint: {path}")
        params = payload.get("best_params") or {}
        state_dict = payload.get("state_dict")
        model = self._build_model(params)
        if params:
            model.set_params(dict(params))
        base_gnn = getattr(model, "_unwrap_gnn", lambda: None)()
        if base_gnn is not None and state_dict is not None:
            base_gnn.load_state_dict(state_dict, strict=False)
        self.model = model
        self.best_params = dict(params) if isinstance(params, dict) else None
        self.ctx.gnn_best = self.model


class XGBTrainer(TrainerBase):
    def __init__(self, context: "BayesOptModel") -> None:
        super().__init__(context, 'Xgboost', 'Xgboost')
        self.model: Optional[xgb.XGBModel] = None
        self._xgb_use_gpu = False
        self._xgb_gpu_warned = False

    def _build_estimator(self) -> xgb.XGBModel:
        use_gpu = bool(self.ctx.use_gpu and _xgb_cuda_available())
        self._xgb_use_gpu = use_gpu
        params = dict(
            objective=self.ctx.obj,
            random_state=self.ctx.rand_seed,
            subsample=0.9,
            tree_method='gpu_hist' if use_gpu else 'hist',
            enable_categorical=True,
            predictor='gpu_predictor' if use_gpu else 'cpu_predictor'
        )
        if self.ctx.use_gpu and not use_gpu and not self._xgb_gpu_warned:
            print(
                "[XGBoost] CUDA requested but not available; falling back to CPU.",
                flush=True,
            )
            self._xgb_gpu_warned = True
        if use_gpu:
            params['gpu_id'] = 0
            print(f">>> XGBoost using GPU ID: 0 (Single GPU Mode)")
        if self.ctx.task_type == 'classification':
            params.setdefault("eval_metric", "logloss")
            return xgb.XGBClassifier(**params)
        return xgb.XGBRegressor(**params)

    def _resolve_early_stopping_rounds(self, n_estimators: int) -> int:
        n_estimators = max(1, int(n_estimators))
        base = max(5, n_estimators // 10)
        return min(50, base)

    def _build_fit_kwargs(self,
                          w_train,
                          X_val=None,
                          y_val=None,
                          w_val=None,
                          n_estimators: Optional[int] = None) -> Dict[str, Any]:
        fit_kwargs = dict(self.ctx.fit_params or {})
        fit_kwargs.pop("sample_weight", None)
        fit_kwargs["sample_weight"] = w_train

        if "eval_set" not in fit_kwargs and X_val is not None and y_val is not None:
            fit_kwargs["eval_set"] = [(X_val, y_val)]
            if w_val is not None:
                fit_kwargs["sample_weight_eval_set"] = [w_val]

        if "eval_metric" not in fit_kwargs:
            fit_kwargs["eval_metric"] = "logloss" if self.ctx.task_type == 'classification' else "rmse"

        if "early_stopping_rounds" not in fit_kwargs and "eval_set" in fit_kwargs:
            rounds = self._resolve_early_stopping_rounds(n_estimators or 100)
            fit_kwargs["early_stopping_rounds"] = rounds

        fit_kwargs.setdefault("verbose", False)
        return fit_kwargs

    def ensemble_predict(self, k: int) -> None:
        if not self.best_params:
            raise RuntimeError("Run tune() first to obtain best XGB parameters.")
        k = max(2, int(k))
        X_all = self.ctx.train_data[self.ctx.factor_nmes]
        y_all = self.ctx.train_data[self.ctx.resp_nme].values
        w_all = self.ctx.train_data[self.ctx.weight_nme].values
        X_test = self.ctx.test_data[self.ctx.factor_nmes]
        n_samples = len(X_all)
        if n_samples < k:
            print(
                f"[XGB Ensemble] n_samples={n_samples} < k={k}; skip ensemble.",
                flush=True,
            )
            return

        splitter = KFold(
            n_splits=k,
            shuffle=True,
            random_state=self.ctx.rand_seed,
        )
        preds_train_sum = np.zeros(n_samples, dtype=np.float64)
        preds_test_sum = np.zeros(len(X_test), dtype=np.float64)

        for train_idx, val_idx in splitter.split(X_all):
            X_train = X_all.iloc[train_idx]
            y_train = y_all[train_idx]
            w_train = w_all[train_idx]
            X_val = X_all.iloc[val_idx]
            y_val = y_all[val_idx]
            w_val = w_all[val_idx]

            clf = self._build_estimator()
            clf.set_params(**self.best_params)
            fit_kwargs = self._build_fit_kwargs(
                w_train=w_train,
                X_val=X_val,
                y_val=y_val,
                w_val=w_val,
                n_estimators=self.best_params.get("n_estimators", 100),
            )
            clf.fit(X_train, y_train, **fit_kwargs)

            if self.ctx.task_type == 'classification':
                pred_train = clf.predict_proba(X_all)[:, 1]
                pred_test = clf.predict_proba(X_test)[:, 1]
            else:
                pred_train = clf.predict(X_all)
                pred_test = clf.predict(X_test)
            preds_train_sum += np.asarray(pred_train, dtype=np.float64)
            preds_test_sum += np.asarray(pred_test, dtype=np.float64)
            self._clean_gpu()

        preds_train = preds_train_sum / float(k)
        preds_test = preds_test_sum / float(k)
        self._cache_predictions("xgb", preds_train, preds_test)

    def cross_val(self, trial: optuna.trial.Trial) -> float:
        learning_rate = trial.suggest_float(
            'learning_rate', 1e-5, 1e-1, log=True)
        gamma = trial.suggest_float('gamma', 0, 10000)
        max_depth_max = max(
            3, int(getattr(self.config, "xgb_max_depth_max", 25)))
        n_estimators_max = max(
            10, int(getattr(self.config, "xgb_n_estimators_max", 500)))
        max_depth = trial.suggest_int('max_depth', 3, max_depth_max)
        n_estimators = trial.suggest_int(
            'n_estimators', 10, n_estimators_max, step=10)
        min_child_weight = trial.suggest_int(
            'min_child_weight', 100, 10000, step=100)
        reg_alpha = trial.suggest_float('reg_alpha', 1e-10, 1, log=True)
        reg_lambda = trial.suggest_float('reg_lambda', 1e-10, 1, log=True)
        if trial is not None:
            print(
                f"[Optuna][Xgboost] trial_id={trial.number} max_depth={max_depth} "
                f"n_estimators={n_estimators}",
                flush=True,
            )
        if max_depth >= 20 and n_estimators >= 300:
            raise optuna.TrialPruned(
                "XGB config is likely too slow (max_depth>=20 & n_estimators>=300)")
        clf = self._build_estimator()
        params = {
            'learning_rate': learning_rate,
            'gamma': gamma,
            'max_depth': max_depth,
            'n_estimators': n_estimators,
            'min_child_weight': min_child_weight,
            'reg_alpha': reg_alpha,
            'reg_lambda': reg_lambda
        }
        tweedie_variance_power = None
        if self.ctx.task_type != 'classification':
            if self.ctx.obj == 'reg:tweedie':
                tweedie_variance_power = trial.suggest_float(
                    'tweedie_variance_power', 1, 2)
                params['tweedie_variance_power'] = tweedie_variance_power
            elif self.ctx.obj == 'count:poisson':
                tweedie_variance_power = 1
            elif self.ctx.obj == 'reg:gamma':
                tweedie_variance_power = 2
            else:
                tweedie_variance_power = 1.5
        X_all = self.ctx.train_data[self.ctx.factor_nmes]
        y_all = self.ctx.train_data[self.ctx.resp_nme].values
        w_all = self.ctx.train_data[self.ctx.weight_nme].values

        losses: List[float] = []
        for train_idx, val_idx in self.ctx.cv.split(X_all):
            X_train = X_all.iloc[train_idx]
            y_train = y_all[train_idx]
            w_train = w_all[train_idx]
            X_val = X_all.iloc[val_idx]
            y_val = y_all[val_idx]
            w_val = w_all[val_idx]

            clf = self._build_estimator()
            clf.set_params(**params)
            fit_kwargs = self._build_fit_kwargs(
                w_train=w_train,
                X_val=X_val,
                y_val=y_val,
                w_val=w_val,
                n_estimators=n_estimators,
            )
            clf.fit(X_train, y_train, **fit_kwargs)

            if self.ctx.task_type == 'classification':
                y_pred = clf.predict_proba(X_val)[:, 1]
                y_pred = np.clip(y_pred, EPS, 1 - EPS)
                loss = log_loss(y_val, y_pred, sample_weight=w_val)
            else:
                y_pred = clf.predict(X_val)
                y_pred_safe = np.maximum(y_pred, EPS)
                loss = mean_tweedie_deviance(
                    y_val,
                    y_pred_safe,
                    sample_weight=w_val,
                    power=tweedie_variance_power,
                )
            losses.append(float(loss))
            self._clean_gpu()

        return float(np.mean(losses))

    def train(self) -> None:
        if not self.best_params:
            raise RuntimeError("Run tune() first to obtain best XGB parameters.")
        self.model = self._build_estimator()
        self.model.set_params(**self.best_params)
        use_refit = bool(getattr(self.ctx.config, "final_refit", True))
        predict_fn = None
        if self.ctx.task_type == 'classification':
            def _predict_proba(X, **_kwargs):
                return self.model.predict_proba(X)[:, 1]
            predict_fn = _predict_proba
        X_all = self.ctx.train_data[self.ctx.factor_nmes]
        y_all = self.ctx.train_data[self.ctx.resp_nme].values
        w_all = self.ctx.train_data[self.ctx.weight_nme].values

        use_split = 0.0 < float(self.ctx.prop_test) < 1.0 and len(X_all) >= 10
        if use_split:
            splitter = ShuffleSplit(
                n_splits=1,
                test_size=self.ctx.prop_test,
                random_state=self.ctx.rand_seed,
            )
            train_idx, val_idx = next(splitter.split(X_all))
            X_train = X_all.iloc[train_idx]
            y_train = y_all[train_idx]
            w_train = w_all[train_idx]
            X_val = X_all.iloc[val_idx]
            y_val = y_all[val_idx]
            w_val = w_all[val_idx]
            fit_kwargs = self._build_fit_kwargs(
                w_train=w_train,
                X_val=X_val,
                y_val=y_val,
                w_val=w_val,
                n_estimators=self.best_params.get("n_estimators", 100),
            )
            self.model.fit(X_train, y_train, **fit_kwargs)
            best_iter = getattr(self.model, "best_iteration", None)
            if use_refit and best_iter is not None:
                refit_model = self._build_estimator()
                refit_params = dict(self.best_params)
                refit_params["n_estimators"] = int(best_iter) + 1
                refit_model.set_params(**refit_params)
                refit_kwargs = dict(self.ctx.fit_params or {})
                refit_kwargs.setdefault("sample_weight", w_all)
                refit_kwargs.pop("eval_set", None)
                refit_kwargs.pop("sample_weight_eval_set", None)
                refit_kwargs.pop("early_stopping_rounds", None)
                refit_kwargs.pop("eval_metric", None)
                refit_kwargs.setdefault("verbose", False)
                refit_model.fit(X_all, y_all, **refit_kwargs)
                self.model = refit_model
        else:
            fit_kwargs = dict(self.ctx.fit_params or {})
            fit_kwargs.setdefault("sample_weight", w_all)
            self.model.fit(X_all, y_all, **fit_kwargs)

        self.ctx.model_label.append(self.label)
        self._predict_and_cache(
            self.model,
            pred_prefix='xgb',
            predict_fn=predict_fn
        )
        self.ctx.xgb_best = self.model


class GLMTrainer(TrainerBase):
    def __init__(self, context: "BayesOptModel") -> None:
        super().__init__(context, 'GLM', 'GLM')
        self.model = None

    def _select_family(self, tweedie_power: Optional[float] = None):
        if self.ctx.task_type == 'classification':
            return sm.families.Binomial()
        if self.ctx.obj == 'count:poisson':
            return sm.families.Poisson()
        if self.ctx.obj == 'reg:gamma':
            return sm.families.Gamma()
        power = tweedie_power if tweedie_power is not None else 1.5
        return sm.families.Tweedie(var_power=power, link=sm.families.links.log())

    def _prepare_design(self, data: pd.DataFrame) -> pd.DataFrame:
        # Add intercept to the statsmodels design matrix.
        X = data[self.ctx.var_nmes]
        return sm.add_constant(X, has_constant='add')

    def _metric_power(self, family, tweedie_power: Optional[float]) -> float:
        if isinstance(family, sm.families.Poisson):
            return 1.0
        if isinstance(family, sm.families.Gamma):
            return 2.0
        if isinstance(family, sm.families.Tweedie):
            return tweedie_power if tweedie_power is not None else getattr(family, 'var_power', 1.5)
        return 1.5

    def cross_val(self, trial: optuna.trial.Trial) -> float:
        param_space = {
            "alpha": lambda t: t.suggest_float('alpha', 1e-6, 1e2, log=True),
            "l1_ratio": lambda t: t.suggest_float('l1_ratio', 0.0, 1.0)
        }
        if self.ctx.task_type == 'regression' and self.ctx.obj == 'reg:tweedie':
            param_space["tweedie_power"] = lambda t: t.suggest_float(
                'tweedie_power', 1.0, 2.0)

        def data_provider():
            data = self.ctx.train_oht_data if self.ctx.train_oht_data is not None else self.ctx.train_oht_scl_data
            assert data is not None, "Preprocessed training data is missing."
            return data[self.ctx.var_nmes], data[self.ctx.resp_nme], data[self.ctx.weight_nme]

        def preprocess_fn(X_train, X_val):
            X_train_s, X_val_s, _ = self._standardize_fold(
                X_train, X_val, self.ctx.num_features)
            return self._prepare_design(X_train_s), self._prepare_design(X_val_s)

        metric_ctx: Dict[str, Any] = {}

        def model_builder(params):
            family = self._select_family(params.get("tweedie_power"))
            metric_ctx["family"] = family
            metric_ctx["tweedie_power"] = params.get("tweedie_power")
            return {
                "family": family,
                "alpha": params["alpha"],
                "l1_ratio": params["l1_ratio"],
                "tweedie_power": params.get("tweedie_power")
            }

        def fit_predict(model_cfg, X_train, y_train, w_train, X_val, y_val, w_val, _trial):
            glm = sm.GLM(y_train, X_train,
                         family=model_cfg["family"],
                         freq_weights=w_train)
            result = glm.fit_regularized(
                alpha=model_cfg["alpha"],
                L1_wt=model_cfg["l1_ratio"],
                maxiter=200
            )
            return result.predict(X_val)

        def metric_fn(y_true, y_pred, weight):
            if self.ctx.task_type == 'classification':
                y_pred_clipped = np.clip(y_pred, EPS, 1 - EPS)
                return log_loss(y_true, y_pred_clipped, sample_weight=weight)
            y_pred_safe = np.maximum(y_pred, EPS)
            return mean_tweedie_deviance(
                y_true,
                y_pred_safe,
                sample_weight=weight,
                power=self._metric_power(
                    metric_ctx.get("family"), metric_ctx.get("tweedie_power"))
            )

        return self.cross_val_generic(
            trial=trial,
            hyperparameter_space=param_space,
            data_provider=data_provider,
            model_builder=model_builder,
            metric_fn=metric_fn,
            preprocess_fn=preprocess_fn,
            fit_predict_fn=fit_predict,
            splitter=self.ctx.cv.split(self.ctx.train_oht_data[self.ctx.var_nmes]
                                       if self.ctx.train_oht_data is not None else self.ctx.train_oht_scl_data[self.ctx.var_nmes])
        )

    def train(self) -> None:
        if not self.best_params:
            raise RuntimeError("Run tune() first to obtain best GLM parameters.")
        tweedie_power = self.best_params.get('tweedie_power')
        family = self._select_family(tweedie_power)

        X_train = self._prepare_design(self.ctx.train_oht_scl_data)
        y_train = self.ctx.train_oht_scl_data[self.ctx.resp_nme]
        w_train = self.ctx.train_oht_scl_data[self.ctx.weight_nme]

        glm = sm.GLM(y_train, X_train, family=family,
                     freq_weights=w_train)
        self.model = glm.fit_regularized(
            alpha=self.best_params['alpha'],
            L1_wt=self.best_params['l1_ratio'],
            maxiter=300
        )

        self.ctx.glm_best = self.model
        self.ctx.model_label += [self.label]
        self._predict_and_cache(
            self.model,
            'glm',
            design_fn=lambda train: self._prepare_design(
                self.ctx.train_oht_scl_data if train else self.ctx.test_oht_scl_data
            )
        )

    def ensemble_predict(self, k: int) -> None:
        if not self.best_params:
            raise RuntimeError("Run tune() first to obtain best GLM parameters.")
        k = max(2, int(k))
        data = self.ctx.train_oht_scl_data
        if data is None:
            raise RuntimeError("Missing standardized data for GLM ensemble.")
        X_all = data[self.ctx.var_nmes]
        y_all = data[self.ctx.resp_nme]
        w_all = data[self.ctx.weight_nme]
        X_test = self.ctx.test_oht_scl_data
        if X_test is None:
            raise RuntimeError("Missing standardized test data for GLM ensemble.")

        n_samples = len(X_all)
        if n_samples < k:
            print(
                f"[GLM Ensemble] n_samples={n_samples} < k={k}; skip ensemble.",
                flush=True,
            )
            return

        X_all_design = self._prepare_design(data)
        X_test_design = self._prepare_design(X_test)
        tweedie_power = self.best_params.get('tweedie_power')
        family = self._select_family(tweedie_power)

        splitter = KFold(
            n_splits=k,
            shuffle=True,
            random_state=self.ctx.rand_seed,
        )
        preds_train_sum = np.zeros(n_samples, dtype=np.float64)
        preds_test_sum = np.zeros(len(X_test_design), dtype=np.float64)

        for train_idx, _val_idx in splitter.split(X_all):
            X_train = X_all_design.iloc[train_idx]
            y_train = y_all.iloc[train_idx]
            w_train = w_all.iloc[train_idx]

            glm = sm.GLM(y_train, X_train, family=family, freq_weights=w_train)
            result = glm.fit_regularized(
                alpha=self.best_params['alpha'],
                L1_wt=self.best_params['l1_ratio'],
                maxiter=300
            )
            pred_train = result.predict(X_all_design)
            pred_test = result.predict(X_test_design)
            preds_train_sum += np.asarray(pred_train, dtype=np.float64)
            preds_test_sum += np.asarray(pred_test, dtype=np.float64)

        preds_train = preds_train_sum / float(k)
        preds_test = preds_test_sum / float(k)
        self._cache_predictions("glm", preds_train, preds_test)


class ResNetTrainer(TrainerBase):
    def __init__(self, context: "BayesOptModel") -> None:
        if context.task_type == 'classification':
            super().__init__(context, 'ResNetClassifier', 'ResNet')
        else:
            super().__init__(context, 'ResNet', 'ResNet')
        self.model: Optional[ResNetSklearn] = None
        self.enable_distributed_optuna = bool(context.config.use_resn_ddp)

    def _resolve_input_dim(self) -> int:
        data = getattr(self.ctx, "train_oht_scl_data", None)
        if data is not None and getattr(self.ctx, "var_nmes", None):
            return int(data[self.ctx.var_nmes].shape[1])
        return int(len(self.ctx.var_nmes or []))

    def _build_model(self, params: Optional[Dict[str, Any]] = None) -> ResNetSklearn:
        params = params or {}
        power = params.get("tw_power", self.ctx.default_tweedie_power())
        if power is not None:
            power = float(power)
        resn_weight_decay = float(
            params.get(
                "weight_decay",
                getattr(self.ctx.config, "resn_weight_decay", 1e-4),
            )
        )
        return ResNetSklearn(
            model_nme=self.ctx.model_nme,
            input_dim=self._resolve_input_dim(),
            hidden_dim=int(params.get("hidden_dim", 64)),
            block_num=int(params.get("block_num", 2)),
            task_type=self.ctx.task_type,
            epochs=self.ctx.epochs,
            tweedie_power=power,
            learning_rate=float(params.get("learning_rate", 0.01)),
            patience=int(params.get("patience", 10)),
            use_layernorm=True,
            dropout=float(params.get("dropout", 0.1)),
            residual_scale=float(params.get("residual_scale", 0.1)),
            stochastic_depth=float(params.get("stochastic_depth", 0.0)),
            weight_decay=resn_weight_decay,
            use_data_parallel=self.ctx.config.use_resn_data_parallel,
            use_ddp=self.ctx.config.use_resn_ddp
        )

    # ========= Cross-validation (for BayesOpt) =========
    def cross_val(self, trial: optuna.trial.Trial) -> float:
        # ResNet CV focuses on memory control:
        #   - Create a ResNetSklearn per fold and release it immediately after.
        #   - Move model to CPU, delete, and call gc/empty_cache after each fold.
        #   - Optionally sample part of training data during BayesOpt to reduce memory.

        base_tw_power = self.ctx.default_tweedie_power()

        def data_provider():
            data = self.ctx.train_oht_data if self.ctx.train_oht_data is not None else self.ctx.train_oht_scl_data
            assert data is not None, "Preprocessed training data is missing."
            return data[self.ctx.var_nmes], data[self.ctx.resp_nme], data[self.ctx.weight_nme]

        metric_ctx: Dict[str, Any] = {}

        def model_builder(params):
            power = params.get("tw_power", base_tw_power)
            metric_ctx["tw_power"] = power
            params_local = dict(params)
            params_local["tw_power"] = power
            return self._build_model(params_local)

        def preprocess_fn(X_train, X_val):
            X_train_s, X_val_s, _ = self._standardize_fold(
                X_train, X_val, self.ctx.num_features)
            return X_train_s, X_val_s

        def fit_predict(model, X_train, y_train, w_train, X_val, y_val, w_val, trial_obj):
            model.fit(
                X_train, y_train, w_train,
                X_val, y_val, w_val,
                trial=trial_obj
            )
            return model.predict(X_val)

        def metric_fn(y_true, y_pred, weight):
            if self.ctx.task_type == 'regression':
                return mean_tweedie_deviance(
                    y_true,
                    y_pred,
                    sample_weight=weight,
                    power=metric_ctx.get("tw_power", base_tw_power)
                )
            return log_loss(y_true, y_pred, sample_weight=weight)

        sample_cap = data_provider()[0]
        max_rows_for_resnet_bo = min(100000, int(len(sample_cap)/5))

        return self.cross_val_generic(
            trial=trial,
            hyperparameter_space={
                "learning_rate": lambda t: t.suggest_float('learning_rate', 1e-6, 1e-2, log=True),
                "hidden_dim": lambda t: t.suggest_int('hidden_dim', 8, 32, step=2),
                "block_num": lambda t: t.suggest_int('block_num', 2, 10),
                "dropout": lambda t: t.suggest_float('dropout', 0.0, 0.3, step=0.05),
                "residual_scale": lambda t: t.suggest_float('residual_scale', 0.05, 0.3, step=0.05),
                "patience": lambda t: t.suggest_int('patience', 3, 12),
                "stochastic_depth": lambda t: t.suggest_float('stochastic_depth', 0.0, 0.2, step=0.05),
                **({"tw_power": lambda t: t.suggest_float('tw_power', 1.0, 2.0)} if self.ctx.task_type == 'regression' and self.ctx.obj == 'reg:tweedie' else {})
            },
            data_provider=data_provider,
            model_builder=model_builder,
            metric_fn=metric_fn,
            sample_limit=max_rows_for_resnet_bo if len(
                sample_cap) > max_rows_for_resnet_bo > 0 else None,
            preprocess_fn=preprocess_fn,
            fit_predict_fn=fit_predict,
            cleanup_fn=lambda m: getattr(
                getattr(m, "resnet", None), "to", lambda *_args, **_kwargs: None)("cpu")
        )

    # ========= Train final ResNet with best hyperparameters =========
    def train(self) -> None:
        if not self.best_params:
            raise RuntimeError("Run tune() first to obtain best ResNet parameters.")

        params = dict(self.best_params)
        use_refit = bool(getattr(self.ctx.config, "final_refit", True))
        data = self.ctx.train_oht_scl_data
        if data is None:
            raise RuntimeError("Missing standardized data for ResNet training.")
        X_all = data[self.ctx.var_nmes]
        y_all = data[self.ctx.resp_nme]
        w_all = data[self.ctx.weight_nme]

        refit_epochs = None
        if use_refit and 0.0 < float(self.ctx.prop_test) < 1.0 and len(X_all) >= 10:
            splitter = ShuffleSplit(
                n_splits=1,
                test_size=self.ctx.prop_test,
                random_state=self.ctx.rand_seed,
            )
            train_idx, val_idx = next(splitter.split(X_all))
            tmp_model = self._build_model(params)
            tmp_model.fit(
                X_all.iloc[train_idx],
                y_all.iloc[train_idx],
                w_all.iloc[train_idx],
                X_all.iloc[val_idx],
                y_all.iloc[val_idx],
                w_all.iloc[val_idx],
                trial=None,
            )
            refit_epochs = self._resolve_best_epoch(
                getattr(tmp_model, "training_history", None),
                default_epochs=int(self.ctx.epochs),
            )
            getattr(getattr(tmp_model, "resnet", None), "to",
                    lambda *_args, **_kwargs: None)("cpu")
            self._clean_gpu()

        self.model = self._build_model(params)
        if refit_epochs is not None:
            self.model.epochs = int(refit_epochs)
        self.best_params = params
        loss_plot_path = self.output.plot_path(
            f'loss_{self.ctx.model_nme}_{self.model_name_prefix}.png')
        self.model.loss_curve_path = loss_plot_path

        self._fit_predict_cache(
            self.model,
            X_all,
            y_all,
            sample_weight=w_all,
            pred_prefix='resn',
            use_oht=True,
            sample_weight_arg='w_train'
        )

        # Convenience wrapper for external callers.
        self.ctx.resn_best = self.model

    def ensemble_predict(self, k: int) -> None:
        if not self.best_params:
            raise RuntimeError("Run tune() first to obtain best ResNet parameters.")
        data = self.ctx.train_oht_scl_data
        test_data = self.ctx.test_oht_scl_data
        if data is None or test_data is None:
            raise RuntimeError("Missing standardized data for ResNet ensemble.")
        X_all = data[self.ctx.var_nmes]
        y_all = data[self.ctx.resp_nme]
        w_all = data[self.ctx.weight_nme]
        X_test = test_data[self.ctx.var_nmes]

        k = max(2, int(k))
        n_samples = len(X_all)
        if n_samples < k:
            print(
                f"[ResNet Ensemble] n_samples={n_samples} < k={k}; skip ensemble.",
                flush=True,
            )
            return

        splitter = KFold(
            n_splits=k,
            shuffle=True,
            random_state=self.ctx.rand_seed,
        )
        preds_train_sum = np.zeros(n_samples, dtype=np.float64)
        preds_test_sum = np.zeros(len(X_test), dtype=np.float64)

        for train_idx, val_idx in splitter.split(X_all):
            model = self._build_model(self.best_params)
            model.fit(
                X_all.iloc[train_idx],
                y_all.iloc[train_idx],
                w_all.iloc[train_idx],
                X_all.iloc[val_idx],
                y_all.iloc[val_idx],
                w_all.iloc[val_idx],
                trial=None,
            )
            pred_train = model.predict(X_all)
            pred_test = model.predict(X_test)
            preds_train_sum += np.asarray(pred_train, dtype=np.float64)
            preds_test_sum += np.asarray(pred_test, dtype=np.float64)
            getattr(getattr(model, "resnet", None), "to",
                    lambda *_args, **_kwargs: None)("cpu")
            self._clean_gpu()

        preds_train = preds_train_sum / float(k)
        preds_test = preds_test_sum / float(k)
        self._cache_predictions("resn", preds_train, preds_test)

    # ========= Save / Load =========
    # ResNet is saved as state_dict and needs a custom load path.
    # Save logic is implemented in TrainerBase (checks .resnet attribute).

    def load(self) -> None:
        # Load ResNet weights to the current device to match context.
        path = self.output.model_path(self._get_model_filename())
        if os.path.exists(path):
            resn_loaded = self._build_model(self.best_params)
            state_dict = torch.load(path, map_location='cpu')
            resn_loaded.resnet.load_state_dict(state_dict)

            self._move_to_device(resn_loaded)
            self.model = resn_loaded
            self.ctx.resn_best = self.model
        else:
            print(f"[ResNetTrainer.load] Model file not found: {path}")


class FTTrainer(TrainerBase):
    def __init__(self, context: "BayesOptModel") -> None:
        if context.task_type == 'classification':
            super().__init__(context, 'FTTransformerClassifier', 'FTTransformer')
        else:
            super().__init__(context, 'FTTransformer', 'FTTransformer')
        self.model: Optional[FTTransformerSklearn] = None
        self.enable_distributed_optuna = bool(context.config.use_ft_ddp)
        self._cv_geo_warned = False

    def _resolve_numeric_tokens(self) -> int:
        requested = getattr(self.ctx.config, "ft_num_numeric_tokens", None)
        return FTTransformerSklearn.resolve_numeric_token_count(
            self.ctx.num_features,
            self.ctx.cate_list,
            requested,
        )

    def _resolve_adaptive_heads(self,
                                d_model: int,
                                requested_heads: Optional[int] = None) -> Tuple[int, bool]:
        d_model = int(d_model)
        if d_model <= 0:
            raise ValueError(f"Invalid d_model={d_model}, expected > 0.")

        default_heads = max(2, d_model // 16)
        base_heads = default_heads if requested_heads is None else int(
            requested_heads)
        base_heads = max(1, min(base_heads, d_model))

        if d_model % base_heads == 0:
            return base_heads, False

        for candidate in range(min(d_model, base_heads), 0, -1):
            if d_model % candidate == 0:
                return candidate, True
        return 1, True

    def _build_geo_tokens_for_split(self,
                                    X_train: pd.DataFrame,
                                    X_val: pd.DataFrame,
                                    geo_params: Optional[Dict[str, Any]] = None):
        if not self.ctx.config.geo_feature_nmes:
            return None
        orig_train = self.ctx.train_data
        orig_test = self.ctx.test_data
        try:
            self.ctx.train_data = orig_train.loc[X_train.index].copy()
            self.ctx.test_data = orig_train.loc[X_val.index].copy()
            return self.ctx._build_geo_tokens(geo_params)
        finally:
            self.ctx.train_data = orig_train
            self.ctx.test_data = orig_test

    def cross_val_unsupervised(self, trial: Optional[optuna.trial.Trial]) -> float:
        """Optuna objective A: minimize validation loss for masked reconstruction."""
        param_space: Dict[str, Callable[[optuna.trial.Trial], Any]] = {
            "learning_rate": lambda t: t.suggest_float('learning_rate', 1e-5, 5e-3, log=True),
            "d_model": lambda t: t.suggest_int('d_model', 16, 128, step=16),
            "n_layers": lambda t: t.suggest_int('n_layers', 2, 8),
            "dropout": lambda t: t.suggest_float('dropout', 0.0, 0.3),
            "weight_decay": lambda t: t.suggest_float('weight_decay', 1e-6, 1e-2, log=True),
            "mask_prob_num": lambda t: t.suggest_float('mask_prob_num', 0.05, 0.4),
            "mask_prob_cat": lambda t: t.suggest_float('mask_prob_cat', 0.05, 0.4),
            "num_loss_weight": lambda t: t.suggest_float('num_loss_weight', 0.25, 4.0, log=True),
            "cat_loss_weight": lambda t: t.suggest_float('cat_loss_weight', 0.25, 4.0, log=True),
        }

        params: Optional[Dict[str, Any]] = None
        if self._distributed_forced_params is not None:
            params = self._distributed_forced_params
            self._distributed_forced_params = None
        else:
            if trial is None:
                raise RuntimeError(
                    "Missing Optuna trial for parameter sampling.")
            params = {name: sampler(trial)
                      for name, sampler in param_space.items()}
            if self._should_use_distributed_optuna():
                self._distributed_prepare_trial(params)

        X_all = self.ctx.train_data[self.ctx.factor_nmes]
        max_rows_for_ft_bo = min(1_000_000, int(len(X_all) / 2))
        if max_rows_for_ft_bo > 0 and len(X_all) > max_rows_for_ft_bo:
            X_all = X_all.sample(n=max_rows_for_ft_bo,
                                 random_state=self.ctx.rand_seed)

        splitter = ShuffleSplit(
            n_splits=1,
            test_size=self.ctx.prop_test,
            random_state=self.ctx.rand_seed
        )
        train_idx, val_idx = next(splitter.split(X_all))
        X_train = X_all.iloc[train_idx]
        X_val = X_all.iloc[val_idx]
        geo_train = geo_val = None
        if self.ctx.config.geo_feature_nmes:
            built = self._build_geo_tokens_for_split(X_train, X_val, params)
            if built is not None:
                geo_train, geo_val, _, _ = built
            elif not self._cv_geo_warned:
                print(
                    "[FTTrainer] Geo tokens unavailable for CV split; continue without geo tokens.",
                    flush=True,
                )
                self._cv_geo_warned = True

        d_model = int(params["d_model"])
        n_layers = int(params["n_layers"])
        num_numeric_tokens = self._resolve_numeric_tokens()
        token_count = num_numeric_tokens + len(self.ctx.cate_list)
        if geo_train is not None:
            token_count += 1
        approx_units = d_model * n_layers * max(1, token_count)
        if approx_units > 12_000_000:
            raise optuna.TrialPruned(
                f"config exceeds safe memory budget (approx_units={approx_units})")

        adaptive_heads, _ = self._resolve_adaptive_heads(
            d_model=d_model,
            requested_heads=params.get("n_heads")
        )

        mask_prob_num = float(params.get("mask_prob_num", 0.15))
        mask_prob_cat = float(params.get("mask_prob_cat", 0.15))
        num_loss_weight = float(params.get("num_loss_weight", 1.0))
        cat_loss_weight = float(params.get("cat_loss_weight", 1.0))

        model_params = dict(params)
        model_params["n_heads"] = adaptive_heads
        for k in ("mask_prob_num", "mask_prob_cat", "num_loss_weight", "cat_loss_weight"):
            model_params.pop(k, None)

        model = FTTransformerSklearn(
            model_nme=self.ctx.model_nme,
            num_cols=self.ctx.num_features,
            cat_cols=self.ctx.cate_list,
            task_type=self.ctx.task_type,
            epochs=self.ctx.epochs,
            patience=5,
            weight_decay=float(params.get("weight_decay", 0.0)),
            use_data_parallel=self.ctx.config.use_ft_data_parallel,
            use_ddp=self.ctx.config.use_ft_ddp,
            num_numeric_tokens=num_numeric_tokens,
        )
        model.set_params(model_params)
        try:
            return float(model.fit_unsupervised(
                X_train,
                X_val=X_val,
                trial=trial,
                geo_train=geo_train,
                geo_val=geo_val,
                mask_prob_num=mask_prob_num,
                mask_prob_cat=mask_prob_cat,
                num_loss_weight=num_loss_weight,
                cat_loss_weight=cat_loss_weight
            ))
        finally:
            getattr(getattr(model, "ft", None), "to",
                    lambda *_args, **_kwargs: None)("cpu")
            self._clean_gpu()

    def cross_val(self, trial: optuna.trial.Trial) -> float:
        # FT-Transformer CV also focuses on memory control:
        #   - Shrink search space to avoid oversized models.
        #   - Release GPU memory after each fold so the next trial can run.
        # Slightly shrink hyperparameter space to avoid oversized models.
        param_space: Dict[str, Callable[[optuna.trial.Trial], Any]] = {
            "learning_rate": lambda t: t.suggest_float('learning_rate', 1e-5, 5e-4, log=True),
            # "d_model": lambda t: t.suggest_int('d_model', 8, 64, step=8),
            "d_model": lambda t: t.suggest_int('d_model', 16, 128, step=16),
            "n_layers": lambda t: t.suggest_int('n_layers', 2, 8),
            "dropout": lambda t: t.suggest_float('dropout', 0.0, 0.2),
            "weight_decay": lambda t: t.suggest_float('weight_decay', 1e-6, 1e-2, log=True),
        }
        if self.ctx.task_type == 'regression' and self.ctx.obj == 'reg:tweedie':
            param_space["tw_power"] = lambda t: t.suggest_float(
                'tw_power', 1.0, 2.0)
        geo_enabled = bool(
            self.ctx.geo_token_cols or self.ctx.config.geo_feature_nmes)
        if geo_enabled:
            # Only tune GNN-related hyperparams when geo tokens are enabled.
            param_space.update({
                "geo_token_hidden_dim": lambda t: t.suggest_int('geo_token_hidden_dim', 16, 128, step=16),
                "geo_token_layers": lambda t: t.suggest_int('geo_token_layers', 1, 4),
                "geo_token_k_neighbors": lambda t: t.suggest_int('geo_token_k_neighbors', 5, 20),
                "geo_token_dropout": lambda t: t.suggest_float('geo_token_dropout', 0.0, 0.3),
                "geo_token_learning_rate": lambda t: t.suggest_float('geo_token_learning_rate', 1e-4, 5e-3, log=True),
            })

        metric_ctx: Dict[str, Any] = {}

        def data_provider():
            data = self.ctx.train_data
            return data[self.ctx.factor_nmes], data[self.ctx.resp_nme], data[self.ctx.weight_nme]

        def model_builder(params):
            d_model = int(params["d_model"])
            n_layers = int(params["n_layers"])
            num_numeric_tokens = self._resolve_numeric_tokens()
            token_count = num_numeric_tokens + len(self.ctx.cate_list)
            if geo_enabled:
                token_count += 1
            approx_units = d_model * n_layers * max(1, token_count)
            if approx_units > 12_000_000:
                print(
                    f"[FTTrainer] Trial pruned early: d_model={d_model}, n_layers={n_layers} -> approx_units={approx_units}")
                raise optuna.TrialPruned(
                    "config exceeds safe memory budget; prune before training")
            geo_params_local = {k: v for k, v in params.items()
                                if k.startswith("geo_token_")}

            tw_power = params.get("tw_power")
            if self.ctx.task_type == 'regression':
                base_tw = self.ctx.default_tweedie_power()
                if self.ctx.obj in ('count:poisson', 'reg:gamma'):
                    tw_power = base_tw
                elif tw_power is None:
                    tw_power = base_tw
            metric_ctx["tw_power"] = tw_power

            adaptive_heads, _ = self._resolve_adaptive_heads(
                d_model=d_model,
                requested_heads=params.get("n_heads")
            )

            return FTTransformerSklearn(
                model_nme=self.ctx.model_nme,
                num_cols=self.ctx.num_features,
                cat_cols=self.ctx.cate_list,
                d_model=d_model,
                n_heads=adaptive_heads,
                n_layers=n_layers,
                dropout=params["dropout"],
                task_type=self.ctx.task_type,
                epochs=self.ctx.epochs,
                tweedie_power=tw_power,
                learning_rate=params["learning_rate"],
                patience=5,
                weight_decay=float(params.get("weight_decay", 0.0)),
                use_data_parallel=self.ctx.config.use_ft_data_parallel,
                use_ddp=self.ctx.config.use_ft_ddp,
                num_numeric_tokens=num_numeric_tokens,
            ).set_params({"_geo_params": geo_params_local} if geo_enabled else {})

        def fit_predict(model, X_train, y_train, w_train, X_val, y_val, w_val, trial_obj):
            geo_train = geo_val = None
            if geo_enabled:
                geo_params = getattr(model, "_geo_params", {})
                built = self._build_geo_tokens_for_split(
                    X_train, X_val, geo_params)
                if built is not None:
                    geo_train, geo_val, _, _ = built
                elif not self._cv_geo_warned:
                    print(
                        "[FTTrainer] Geo tokens unavailable for CV split; continue without geo tokens.",
                        flush=True,
                    )
                    self._cv_geo_warned = True
            model.fit(
                X_train, y_train, w_train,
                X_val, y_val, w_val,
                trial=trial_obj,
                geo_train=geo_train,
                geo_val=geo_val
            )
            return model.predict(X_val, geo_tokens=geo_val)

        def metric_fn(y_true, y_pred, weight):
            if self.ctx.task_type == 'regression':
                return mean_tweedie_deviance(
                    y_true,
                    y_pred,
                    sample_weight=weight,
                    power=metric_ctx.get("tw_power", 1.5)
                )
            return log_loss(y_true, y_pred, sample_weight=weight)

        data_for_cap = data_provider()[0]
        max_rows_for_ft_bo = min(1000000, int(len(data_for_cap)/2))

        return self.cross_val_generic(
            trial=trial,
            hyperparameter_space=param_space,
            data_provider=data_provider,
            model_builder=model_builder,
            metric_fn=metric_fn,
            sample_limit=max_rows_for_ft_bo if len(
                data_for_cap) > max_rows_for_ft_bo > 0 else None,
            fit_predict_fn=fit_predict,
            cleanup_fn=lambda m: getattr(
                getattr(m, "ft", None), "to", lambda *_args, **_kwargs: None)("cpu")
        )

    def train(self) -> None:
        if not self.best_params:
            raise RuntimeError("Run tune() first to obtain best FT-Transformer parameters.")
        resolved_params = dict(self.best_params)
        d_model_value = resolved_params.get("d_model", 64)
        adaptive_heads, heads_adjusted = self._resolve_adaptive_heads(
            d_model=d_model_value,
            requested_heads=resolved_params.get("n_heads")
        )
        if heads_adjusted:
            print(f"[FTTrainer] Auto-adjusted n_heads from "
                  f"{resolved_params.get('n_heads')} to {adaptive_heads} "
                  f"(d_model={d_model_value}).")
        resolved_params["n_heads"] = adaptive_heads

        use_refit = bool(getattr(self.ctx.config, "final_refit", True))
        refit_epochs = None
        X_all = self.ctx.train_data[self.ctx.factor_nmes]
        y_all = self.ctx.train_data[self.ctx.resp_nme]
        w_all = self.ctx.train_data[self.ctx.weight_nme]
        if use_refit and 0.0 < float(self.ctx.prop_test) < 1.0 and len(X_all) >= 10:
            splitter = ShuffleSplit(
                n_splits=1,
                test_size=self.ctx.prop_test,
                random_state=self.ctx.rand_seed,
            )
            train_idx, val_idx = next(splitter.split(X_all))
            tmp_model = FTTransformerSklearn(
                model_nme=self.ctx.model_nme,
                num_cols=self.ctx.num_features,
                cat_cols=self.ctx.cate_list,
                task_type=self.ctx.task_type,
                use_data_parallel=self.ctx.config.use_ft_data_parallel,
                use_ddp=self.ctx.config.use_ft_ddp,
                num_numeric_tokens=self._resolve_numeric_tokens(),
                weight_decay=float(resolved_params.get("weight_decay", 0.0)),
            )
            tmp_model.set_params(resolved_params)
            geo_train_full = self.ctx.train_geo_tokens
            geo_train = None if geo_train_full is None else geo_train_full.iloc[train_idx]
            geo_val = None if geo_train_full is None else geo_train_full.iloc[val_idx]
            tmp_model.fit(
                X_all.iloc[train_idx],
                y_all.iloc[train_idx],
                w_all.iloc[train_idx],
                X_all.iloc[val_idx],
                y_all.iloc[val_idx],
                w_all.iloc[val_idx],
                trial=None,
                geo_train=geo_train,
                geo_val=geo_val,
            )
            refit_epochs = self._resolve_best_epoch(
                getattr(tmp_model, "training_history", None),
                default_epochs=int(self.ctx.epochs),
            )
            getattr(getattr(tmp_model, "ft", None), "to",
                    lambda *_args, **_kwargs: None)("cpu")
            self._clean_gpu()

        self.model = FTTransformerSklearn(
            model_nme=self.ctx.model_nme,
            num_cols=self.ctx.num_features,
            cat_cols=self.ctx.cate_list,
            task_type=self.ctx.task_type,
            use_data_parallel=self.ctx.config.use_ft_data_parallel,
            use_ddp=self.ctx.config.use_ft_ddp,
            num_numeric_tokens=self._resolve_numeric_tokens(),
            weight_decay=float(resolved_params.get("weight_decay", 0.0)),
        )
        if refit_epochs is not None:
            self.model.epochs = int(refit_epochs)
        self.model.set_params(resolved_params)
        self.best_params = resolved_params
        loss_plot_path = self.output.plot_path(
            f'loss_{self.ctx.model_nme}_{self.model_name_prefix}.png')
        self.model.loss_curve_path = loss_plot_path
        geo_train = self.ctx.train_geo_tokens
        geo_test = self.ctx.test_geo_tokens
        fit_kwargs = {}
        predict_kwargs_train = None
        predict_kwargs_test = None
        if geo_train is not None and geo_test is not None:
            fit_kwargs["geo_train"] = geo_train
            predict_kwargs_train = {"geo_tokens": geo_train}
            predict_kwargs_test = {"geo_tokens": geo_test}
        self._fit_predict_cache(
            self.model,
            self.ctx.train_data[self.ctx.factor_nmes],
            self.ctx.train_data[self.ctx.resp_nme],
            sample_weight=self.ctx.train_data[self.ctx.weight_nme],
            pred_prefix='ft',
            sample_weight_arg='w_train',
            fit_kwargs=fit_kwargs,
            predict_kwargs_train=predict_kwargs_train,
            predict_kwargs_test=predict_kwargs_test
        )
        self.ctx.ft_best = self.model

    def ensemble_predict(self, k: int) -> None:
        if not self.best_params:
            raise RuntimeError("Run tune() first to obtain best FT-Transformer parameters.")
        k = max(2, int(k))
        X_all = self.ctx.train_data[self.ctx.factor_nmes]
        y_all = self.ctx.train_data[self.ctx.resp_nme]
        w_all = self.ctx.train_data[self.ctx.weight_nme]
        X_test = self.ctx.test_data[self.ctx.factor_nmes]
        n_samples = len(X_all)
        if n_samples < k:
            print(
                f"[FT Ensemble] n_samples={n_samples} < k={k}; skip ensemble.",
                flush=True,
            )
            return

        geo_train_full = self.ctx.train_geo_tokens
        geo_test_full = self.ctx.test_geo_tokens

        resolved_params = dict(self.best_params)
        default_d_model = getattr(self.model, "d_model", 64)
        adaptive_heads, _ = self._resolve_adaptive_heads(
            d_model=resolved_params.get("d_model", default_d_model),
            requested_heads=resolved_params.get("n_heads")
        )
        resolved_params["n_heads"] = adaptive_heads

        splitter = KFold(
            n_splits=k,
            shuffle=True,
            random_state=self.ctx.rand_seed,
        )
        preds_train_sum = np.zeros(n_samples, dtype=np.float64)
        preds_test_sum = np.zeros(len(X_test), dtype=np.float64)

        for train_idx, val_idx in splitter.split(X_all):
            model = FTTransformerSklearn(
                model_nme=self.ctx.model_nme,
                num_cols=self.ctx.num_features,
                cat_cols=self.ctx.cate_list,
                task_type=self.ctx.task_type,
                use_data_parallel=self.ctx.config.use_ft_data_parallel,
                use_ddp=self.ctx.config.use_ft_ddp,
                num_numeric_tokens=self._resolve_numeric_tokens(),
                weight_decay=float(resolved_params.get("weight_decay", 0.0)),
            )
            model.set_params(resolved_params)

            geo_train = geo_val = None
            if geo_train_full is not None:
                geo_train = geo_train_full.iloc[train_idx]
                geo_val = geo_train_full.iloc[val_idx]

            model.fit(
                X_all.iloc[train_idx],
                y_all.iloc[train_idx],
                w_all.iloc[train_idx],
                X_all.iloc[val_idx],
                y_all.iloc[val_idx],
                w_all.iloc[val_idx],
                trial=None,
                geo_train=geo_train,
                geo_val=geo_val,
            )

            pred_train = model.predict(X_all, geo_tokens=geo_train_full)
            pred_test = model.predict(X_test, geo_tokens=geo_test_full)
            preds_train_sum += np.asarray(pred_train, dtype=np.float64)
            preds_test_sum += np.asarray(pred_test, dtype=np.float64)
            getattr(getattr(model, "ft", None), "to",
                    lambda *_args, **_kwargs: None)("cpu")
            self._clean_gpu()

        preds_train = preds_train_sum / float(k)
        preds_test = preds_test_sum / float(k)
        self._cache_predictions("ft", preds_train, preds_test)

    def train_as_feature(self, pred_prefix: str = "ft_feat", feature_mode: str = "prediction") -> None:
        """Train FT-Transformer only to generate features (not recorded as final model)."""
        if not self.best_params:
            raise RuntimeError("Run tune() first to obtain best FT-Transformer parameters.")
        self.model = FTTransformerSklearn(
            model_nme=self.ctx.model_nme,
            num_cols=self.ctx.num_features,
            cat_cols=self.ctx.cate_list,
            task_type=self.ctx.task_type,
            use_data_parallel=self.ctx.config.use_ft_data_parallel,
            use_ddp=self.ctx.config.use_ft_ddp,
            num_numeric_tokens=self._resolve_numeric_tokens(),
        )
        resolved_params = dict(self.best_params)
        adaptive_heads, heads_adjusted = self._resolve_adaptive_heads(
            d_model=resolved_params.get("d_model", self.model.d_model),
            requested_heads=resolved_params.get("n_heads")
        )
        if heads_adjusted:
            print(f"[FTTrainer] Auto-adjusted n_heads from "
                  f"{resolved_params.get('n_heads')} to {adaptive_heads} "
                  f"(d_model={resolved_params.get('d_model', self.model.d_model)}).")
        resolved_params["n_heads"] = adaptive_heads
        self.model.set_params(resolved_params)
        self.best_params = resolved_params

        geo_train = self.ctx.train_geo_tokens
        geo_test = self.ctx.test_geo_tokens
        fit_kwargs = {}
        predict_kwargs_train = None
        predict_kwargs_test = None
        if geo_train is not None and geo_test is not None:
            fit_kwargs["geo_train"] = geo_train
            predict_kwargs_train = {"geo_tokens": geo_train}
            predict_kwargs_test = {"geo_tokens": geo_test}

        if feature_mode not in ("prediction", "embedding"):
            raise ValueError(
                f"Unsupported feature_mode='{feature_mode}', expected 'prediction' or 'embedding'.")
        if feature_mode == "embedding":
            predict_kwargs_train = dict(predict_kwargs_train or {})
            predict_kwargs_test = dict(predict_kwargs_test or {})
            predict_kwargs_train["return_embedding"] = True
            predict_kwargs_test["return_embedding"] = True

        self._fit_predict_cache(
            self.model,
            self.ctx.train_data[self.ctx.factor_nmes],
            self.ctx.train_data[self.ctx.resp_nme],
            sample_weight=self.ctx.train_data[self.ctx.weight_nme],
            pred_prefix=pred_prefix,
            sample_weight_arg='w_train',
            fit_kwargs=fit_kwargs,
            predict_kwargs_train=predict_kwargs_train,
            predict_kwargs_test=predict_kwargs_test,
            record_label=False
        )

    def pretrain_unsupervised_as_feature(self,
                                         pred_prefix: str = "ft_uemb",
                                         params: Optional[Dict[str,
                                                               Any]] = None,
                                         mask_prob_num: float = 0.15,
                                         mask_prob_cat: float = 0.15,
                                         num_loss_weight: float = 1.0,
                                         cat_loss_weight: float = 1.0) -> None:
        """Self-supervised pretraining (masked reconstruction) and cache embeddings."""
        self.model = FTTransformerSklearn(
            model_nme=self.ctx.model_nme,
            num_cols=self.ctx.num_features,
            cat_cols=self.ctx.cate_list,
            task_type=self.ctx.task_type,
            use_data_parallel=self.ctx.config.use_ft_data_parallel,
            use_ddp=self.ctx.config.use_ft_ddp,
            num_numeric_tokens=self._resolve_numeric_tokens(),
        )
        resolved_params = dict(params or {})
        # Reuse supervised tuning structure params unless explicitly overridden.
        if not resolved_params and self.best_params:
            resolved_params = dict(self.best_params)

        # If params include masked reconstruction fields, they take precedence.
        mask_prob_num = float(resolved_params.pop(
            "mask_prob_num", mask_prob_num))
        mask_prob_cat = float(resolved_params.pop(
            "mask_prob_cat", mask_prob_cat))
        num_loss_weight = float(resolved_params.pop(
            "num_loss_weight", num_loss_weight))
        cat_loss_weight = float(resolved_params.pop(
            "cat_loss_weight", cat_loss_weight))

        adaptive_heads, heads_adjusted = self._resolve_adaptive_heads(
            d_model=resolved_params.get("d_model", self.model.d_model),
            requested_heads=resolved_params.get("n_heads")
        )
        if heads_adjusted:
            print(f"[FTTrainer] Auto-adjusted n_heads from "
                  f"{resolved_params.get('n_heads')} to {adaptive_heads} "
                  f"(d_model={resolved_params.get('d_model', self.model.d_model)}).")
        resolved_params["n_heads"] = adaptive_heads
        if resolved_params:
            self.model.set_params(resolved_params)

        loss_plot_path = self.output.plot_path(
            f'loss_{self.ctx.model_nme}_FTTransformerUnsupervised.png')
        self.model.loss_curve_path = loss_plot_path

        # Build a simple holdout split for pretraining early stopping.
        X_all = self.ctx.train_data[self.ctx.factor_nmes]
        idx = np.arange(len(X_all))
        splitter = ShuffleSplit(
            n_splits=1,
            test_size=self.ctx.prop_test,
            random_state=self.ctx.rand_seed
        )
        train_idx, val_idx = next(splitter.split(idx))
        X_tr = X_all.iloc[train_idx]
        X_val = X_all.iloc[val_idx]

        geo_all = self.ctx.train_geo_tokens
        geo_tr = geo_val = None
        if geo_all is not None:
            geo_tr = geo_all.loc[X_tr.index]
            geo_val = geo_all.loc[X_val.index]

        self.model.fit_unsupervised(
            X_tr,
            X_val=X_val,
            geo_train=geo_tr,
            geo_val=geo_val,
            mask_prob_num=mask_prob_num,
            mask_prob_cat=mask_prob_cat,
            num_loss_weight=num_loss_weight,
            cat_loss_weight=cat_loss_weight
        )

        geo_train_full = self.ctx.train_geo_tokens
        geo_test_full = self.ctx.test_geo_tokens
        predict_kwargs_train = {"return_embedding": True}
        predict_kwargs_test = {"return_embedding": True}
        if geo_train_full is not None and geo_test_full is not None:
            predict_kwargs_train["geo_tokens"] = geo_train_full
            predict_kwargs_test["geo_tokens"] = geo_test_full

        self._predict_and_cache(
            self.model,
            pred_prefix=pred_prefix,
            predict_kwargs_train=predict_kwargs_train,
            predict_kwargs_test=predict_kwargs_test
        )


# =============================================================================
