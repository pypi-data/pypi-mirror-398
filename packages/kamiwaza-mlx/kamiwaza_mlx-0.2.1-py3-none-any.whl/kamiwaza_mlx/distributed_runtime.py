"""Helpers for bootstrapping mlx.distributed for multi-node inference."""
from __future__ import annotations

import inspect
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

try:  # pragma: no cover - optional dependency when running CPU-only tests
    import mlx.distributed as _mlx_dist  # type: ignore
except Exception:  # pragma: no cover - handled gracefully at runtime
    _mlx_dist = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency when running CPU-only tests
    import mlx.core as _mx  # type: ignore
except Exception:  # pragma: no cover - handled gracefully at runtime
    _mx = None  # type: ignore[assignment]


def _filter_kwargs(func: Any, values: Mapping[str, Any]) -> Dict[str, Any]:
    """Return only kwargs accepted by *func* (best-effort introspection)."""

    if func is None:
        return {}
    try:
        sig = inspect.signature(func)
    except (TypeError, ValueError):  # pragma: no cover - builtins / C funcs
        return {k: v for k, v in values.items() if v is not None}
    accepted: Dict[str, Any] = {}
    for name in sig.parameters:
        if name in values and values[name] is not None:
            accepted[name] = values[name]
    return accepted


def _parse_env_file(path: Path) -> Dict[str, str]:
    """Parse a minimal .env style file into a dictionary."""

    data: Dict[str, str] = {}
    try:
        content = path.read_text()
    except FileNotFoundError:
        return data
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            data[key] = value
    return data


def _first_non_empty(*values: Optional[Any]) -> Optional[Any]:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                continue
            return cleaned
        return value
    return None


def _to_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
        return None
    try:
        return bool(value)
    except Exception:  # pragma: no cover - defensive
        return None


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return None


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return None


@dataclass
class DistributedConfig:
    enabled: bool
    rank: int
    world_size: int
    host: Optional[str]
    port: int
    timeout: float
    server_rank: int
    env_source: Optional[Path]

    @classmethod
    def from_sources(
        cls,
        args: Any,
        environ: Mapping[str, str],
        env_source: Optional[Path],
    ) -> "DistributedConfig":
        flag_arg = getattr(args, "distributed", None)
        env_enabled = _to_bool(
            _first_non_empty(
                environ.get("KAMI_DIST_ENABLED"),
                environ.get("MLX_DISTRIBUTED_ENABLED"),
            )
        )
        host = _first_non_empty(
            getattr(args, "distributed_host", None),
            environ.get("PAIRED_HOST"),
            environ.get("MLX_DISTRIBUTED_HOST"),
            environ.get("MLX_DIST_HOST"),
        )
        port = _to_int(
            _first_non_empty(
                getattr(args, "distributed_port", None),
                environ.get("PAIRED_PORT"),
                environ.get("MLX_DISTRIBUTED_PORT"),
            )
        ) or 17863
        world_size = _to_int(
            _first_non_empty(
                getattr(args, "distributed_world_size", None),
                environ.get("WORLD_SIZE"),
                environ.get("PAIRED_WORLD_SIZE"),
                environ.get("MLX_DISTRIBUTED_WORLD_SIZE"),
            )
        )
        rank = _to_int(
            _first_non_empty(
                getattr(args, "distributed_rank", None),
                environ.get("RANK"),
                environ.get("MLX_DISTRIBUTED_RANK"),
                environ.get("PAIRED_RANK"),
            )
        ) or 0
        server_rank = _to_int(
            _first_non_empty(
                getattr(args, "distributed_server_rank", None),
                environ.get("SERVER_RANK"),
                environ.get("MLX_DISTRIBUTED_SERVER_RANK"),
            )
        )
        if server_rank is None:
            server_rank = 0
        timeout = _to_float(
            _first_non_empty(
                getattr(args, "distributed_timeout", None),
                environ.get("MLX_DISTRIBUTED_TIMEOUT"),
                environ.get("DISTRIBUTED_TIMEOUT"),
            )
        ) or 120.0

        if world_size is None:
            # If we have a rendezvous host but no explicit world size, assume 2 nodes.
            world_size = 2 if host else 1
        world_size = max(world_size, 1)

        if flag_arg is not None:
            enabled = bool(flag_arg)
        elif env_enabled is not None:
            enabled = env_enabled
        else:
            enabled = bool(host) or world_size > 1

        return cls(
            enabled=enabled,
            rank=rank,
            world_size=world_size,
            host=str(host) if host is not None else None,
            port=port,
            timeout=timeout,
            server_rank=server_rank,
            env_source=env_source,
        )


class DistributedRuntime:
    """Runtime helper encapsulating mlx.distributed initialisation."""

    def __init__(
        self,
        config: DistributedConfig,
        *,
        logger: Optional[logging.Logger] = None,
        dist_module: Any = None,
        mx_module: Any = None,
    ) -> None:
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self._dist = dist_module if dist_module is not None else _mlx_dist
        self._mx = mx_module if mx_module is not None else _mx
        self.initialized = False
        self.mesh: Any = None

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    @property
    def rank(self) -> int:
        return self.config.rank

    @property
    def world_size(self) -> int:
        return self.config.world_size

    @property
    def is_active(self) -> bool:
        return self.enabled and self.initialized and self.world_size > 1

    @property
    def server_rank(self) -> int:
        return self.config.server_rank

    def initialize(self) -> bool:
        if not self.enabled:
            return False
        if self._dist is None:
            self.logger.warning(
                "mlx.distributed is not available – falling back to single-node execution."
            )
            return False
        is_initialized = getattr(self._dist, "is_initialized", None)
        if callable(is_initialized) and is_initialized():
            self.initialized = True
            self.logger.debug("mlx.distributed already initialised; reusing existing context.")
            return True

        init_fn = getattr(self._dist, "initialize", None)
        if not callable(init_fn):
            self.logger.warning(
                "mlx.distributed.initialize is missing – unable to enable distributed mode."
            )
            return False

        kwargs = _filter_kwargs(
            init_fn,
            {
                "rank": self.config.rank,
                "world_size": self.config.world_size,
                "host": self.config.host,
                "port": self.config.port,
                "timeout": self.config.timeout,
            },
        )
        try:
            init_fn(**kwargs)
        except Exception as exc:  # pragma: no cover - runtime failure path
            self.logger.error("Failed to initialise mlx.distributed: %s", exc)
            raise

        self.initialized = True
        self.logger.info(
            "Initialised mlx.distributed (rank %d/%d, host=%s, port=%d).",
            self.config.rank,
            self.config.world_size,
            self.config.host,
            self.config.port,
        )
        self._barrier("post-initialise")
        self._setup_default_mesh()
        return True

    def _setup_default_mesh(self) -> None:
        if not self.is_active or self._mx is None:
            return
        mesh_ctor = getattr(self._dist, "Mesh", None)
        set_mesh = getattr(self._mx, "set_default_mesh", None)
        if not callable(mesh_ctor) or not callable(set_mesh):
            return
        try:
            mesh_kwargs: Dict[str, Any] = _filter_kwargs(
                mesh_ctor,
                {
                    "shape": (self.world_size,),
                    "axis_names": ("data",),
                },
            )
            if not mesh_kwargs:
                mesh_kwargs = _filter_kwargs(mesh_ctor, {"devices": list(range(self.world_size))})
            mesh = mesh_ctor(**mesh_kwargs) if mesh_kwargs else mesh_ctor(self.world_size)
            set_mesh(mesh)
            self.mesh = mesh
            self.logger.info(
                "Configured default MLX mesh for %d-way distributed execution.", self.world_size
            )
        except Exception as exc:  # pragma: no cover - runtime failure path
            self.logger.warning("Unable to configure MLX distributed mesh: %s", exc)

    def _barrier(self, reason: str = "") -> None:
        if not self.enabled or self._dist is None:
            return
        barrier_fn = getattr(self._dist, "barrier", None)
        if not callable(barrier_fn):
            return
        kwargs = _filter_kwargs(barrier_fn, {"timeout": self.config.timeout})
        try:
            barrier_fn(**kwargs)
        except Exception as exc:  # pragma: no cover - runtime failure path
            if reason:
                self.logger.warning("Distributed barrier (%s) failed: %s", reason, exc)
            else:
                self.logger.warning("Distributed barrier failed: %s", exc)

    def barrier(self, reason: str = "") -> None:
        self._barrier(reason)

    def after_model_load(self, model: Any) -> None:
        if not self.is_active:
            return
        self._sync_parameters(model)
        self._barrier("post-model-load")

    def _sync_parameters(self, model: Any) -> None:
        if not self.is_active or model is None:
            return
        sync_fn = getattr(self._dist, "sync_module", None)
        if callable(sync_fn):
            try:
                kwargs = _filter_kwargs(
                    sync_fn,
                    {
                        "module": model,
                        "src": self.config.server_rank,
                    },
                )
                sync_fn(**kwargs)
                self.logger.debug("Synchronized model parameters via mlx.distributed.sync_module.")
                return
            except Exception as exc:  # pragma: no cover - runtime failure path
                self.logger.warning("sync_module failed; falling back to broadcast: %s", exc)

        broadcast_fn = getattr(self._dist, "broadcast", None)
        state_dict = getattr(model, "state_dict", None)
        if callable(broadcast_fn) and callable(state_dict):
            try:
                state = state_dict()
                for value in state.values():
                    array = getattr(value, "array", value)
                    kwargs = _filter_kwargs(
                        broadcast_fn,
                        {
                            "value": array,
                            "src": self.config.server_rank,
                        },
                    )
                    broadcast_fn(**kwargs)
                self.logger.debug("Synchronized model parameters via broadcast of state_dict.")
            except Exception as exc:  # pragma: no cover - runtime failure path
                self.logger.warning("Fallback broadcast of parameters failed: %s", exc)

    def should_host_server(self) -> bool:
        if not self.enabled:
            return True
        return self.config.rank == self.config.server_rank

    def worker_forever(self) -> None:
        if not self.enabled:
            return
        self.logger.info(
            "Distributed worker rank %d waiting for server shutdown signal.", self.config.rank
        )
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:  # pragma: no cover - allow ctrl-c during dev
            pass

    def shutdown(self) -> None:
        if not self.initialized or self._dist is None:
            return
        finalize_fn = getattr(self._dist, "finalize", None)
        if callable(finalize_fn):
            try:
                finalize_fn()
            except Exception:  # pragma: no cover - defensive
                pass
        self.initialized = False

    def describe(self) -> str:
        if not self.enabled:
            return "distributed=disabled"
        return (
            f"distributed(rank={self.config.rank}, world_size={self.config.world_size}, "
            f"server_rank={self.config.server_rank}, host={self.config.host}, port={self.config.port})"
        )


def setup_runtime(args: Any, logger: Optional[logging.Logger] = None) -> DistributedRuntime:
    """Load optional env vars, build config and initialise the distributed runtime."""

    logger = logger or logging.getLogger(__name__)

    env_file_arg = getattr(args, "distributed_env_file", None)
    env_source: Optional[Path] = None
    env_data: Dict[str, str] = {}
    candidate_paths: list[Path] = []
    if env_file_arg:
        candidate_paths.append(Path(env_file_arg).expanduser())
    default_env = Path.cwd() / ".env"
    candidate_paths.append(default_env)

    for path in candidate_paths:
        if not path or not path.exists():
            continue
        env_data = _parse_env_file(path)
        if env_data:
            env_source = path
            for key, value in env_data.items():
                os.environ.setdefault(key, value)
            logger.info("Loaded distributed environment variables from %s", path)
            break

    config = DistributedConfig.from_sources(args, os.environ, env_source)
    runtime = DistributedRuntime(config, logger=logger)
    runtime.initialize()
    if runtime.enabled:
        logger.info("Distributed runtime: %s", runtime.describe())
    return runtime


__all__ = ["DistributedRuntime", "DistributedConfig", "setup_runtime"]
