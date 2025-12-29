# kernel.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
from time import perf_counter
from types import MappingProxyType
from typing import Any, Callable, ClassVar, Generic, Iterable, Mapping, Optional, TypeVar
import uuid

from .psi import PsiDefinition

T = TypeVar("T")

Metadata = Mapping[str, Any]
RunIdFactory = Callable[[], str]
NowProvider = Callable[[], datetime]
PerfCounterProvider = Callable[[], float]


class FailureCode(str, Enum):
    OK = "OK"
    TASK_EXCEPTION = "TASK_EXCEPTION"
    INVALID_INPUT = "INVALID_INPUT"
    KERNEL_ERROR = "KERNEL_ERROR"


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {k: _freeze_value(v) for k, v in value.items()}
        )
    if isinstance(value, tuple):
        return tuple(_freeze_value(v) for v in value)
    if isinstance(value, list):
        return tuple(_freeze_value(v) for v in value)
    if isinstance(value, set):
        return frozenset(_freeze_value(v) for v in value)
    return value


def _format_dt(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonicalize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return _format_dt(value)
    if isinstance(value, PsiDefinition):
        return value.describe()
    if isinstance(value, Mapping):
        items = {}
        for key in sorted(value.keys(), key=lambda k: str(k)):
            items[str(key)] = _canonicalize_value(value[key])
        return items
    if isinstance(value, (list, tuple)):
        return [_canonicalize_value(v) for v in value]
    if isinstance(value, set):
        return sorted([_canonicalize_value(v) for v in value], key=lambda k: str(k))
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return {"__non_serializable__": type(value).__name__}


def _json_dumps(data: Any) -> str:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


@dataclass(frozen=True)
class ExecutionTrace(Generic[T]):
    """
    Immutable record of one kernel execution.

    Contract:
    - Never mutated after creation.
    - Field names and meanings are stable.
    - error and exception_repr are observational only.
    """

    run_id: str
    psi: PsiDefinition

    started_at: datetime
    finished_at: datetime
    runtime_ms: float

    success: bool
    failure_code: FailureCode
    output: Optional[T]
    error: Optional[str]
    exception_type: Optional[str]
    exception_repr: Optional[str]

    metadata: Metadata = field(default_factory=dict)
    kernel_meta: Metadata = field(default_factory=dict)

    DETERMINISTIC_FIELDS: ClassVar[tuple[str, ...]] = (
        "psi",
        "success",
        "failure_code",
        "exception_type",
    )
    OBSERVATIONAL_FIELDS: ClassVar[tuple[str, ...]] = (
        "run_id",
        "started_at",
        "finished_at",
        "runtime_ms",
        "error",
        "exception_repr",
        "output",
        "metadata",
        "kernel_meta",
    )

    def to_dict(self, *, include_observational: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {
            "psi": self.psi.describe(),
            "success": self.success,
            "failure_code": self.failure_code.value,
            "exception_type": self.exception_type,
        }

        if include_observational:
            data.update(
                {
                    "run_id": self.run_id,
                    "started_at": _format_dt(self.started_at),
                    "finished_at": _format_dt(self.finished_at),
                    "runtime_ms": self.runtime_ms,
                    "output": _canonicalize_value(self.output),
                    "error": self.error,
                    "exception_repr": self.exception_repr,
                    "metadata": _canonicalize_value(self.metadata),
                    "kernel_meta": _canonicalize_value(self.kernel_meta),
                }
            )

        return data

    def to_json(self, *, include_observational: bool = True) -> str:
        return _json_dumps(self.to_dict(include_observational=include_observational))

    def digest(self) -> str:
        payload = self.to_json(include_observational=False)
        return sha256(payload.encode("utf-8")).hexdigest()


class Kernel:
    """
    Minimal deterministic execution engine.

    Contract:
    - execute calls the task exactly once.
    - execute never raises, exceptions are captured in the trace.
    - Time is measured via a monotonic clock.
    - metadata is passed through and not interpreted.
    """

    def __init__(
        self,
        *,
        run_id_factory: Optional[RunIdFactory] = None,
        now_provider: Optional[NowProvider] = None,
        perf_counter_provider: Optional[PerfCounterProvider] = None,
        deterministic_mode: bool = False,
    ) -> None:
        self._deterministic_mode = deterministic_mode
        if deterministic_mode:
            self._run_id_factory = run_id_factory or (lambda: "deterministic")
            self._now_provider = now_provider or (lambda: datetime(1970, 1, 1, tzinfo=timezone.utc))
            self._perf_counter = perf_counter_provider or (lambda: 0.0)
        else:
            self._run_id_factory = run_id_factory or (lambda: uuid.uuid4().hex)
            self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))
            self._perf_counter = perf_counter_provider or perf_counter

    def execute(
        self,
        *,
        psi: PsiDefinition,
        task: Callable[..., T],
        metadata: Optional[Metadata] = None,
        **kwargs: Any,
    ) -> ExecutionTrace[T]:
        """
        Execute task once and return a trace. Never raises.
        """
        kernel_error: Optional[str] = None
        invalid_input = False

        if not isinstance(psi, PsiDefinition):
            kernel_error = "InvalidInput: psi must be PsiDefinition"
            invalid_input = True
            psi = PsiDefinition(psi_type="invalid", name="invalid", metadata={})
        if not callable(task):
            kernel_error = "InvalidInput: task must be callable"
            invalid_input = True

        started_at, err = self._safe_now(kernel_error)
        kernel_error = kernel_error or err
        start, err = self._safe_perf(kernel_error)
        kernel_error = kernel_error or err

        success = False
        output: Optional[T] = None
        error: Optional[str] = None
        exc_type: Optional[str] = None
        exc_repr: Optional[str] = None
        failure_code = FailureCode.OK

        try:
            if not invalid_input:
                output = task(**kwargs)
                success = True
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
            exc_type = exc.__class__.__name__
            exc_repr = repr(exc)
            failure_code = FailureCode.TASK_EXCEPTION

        finished_at, err = self._safe_now(kernel_error)
        kernel_error = kernel_error or err
        end, err = self._safe_perf(kernel_error)
        kernel_error = kernel_error or err

        runtime_ms = max((end - start) * 1000.0, 0.0)
        if self._deterministic_mode:
            runtime_ms = 0.0
        run_id, err = self._safe_run_id(kernel_error)
        kernel_error = kernel_error or err

        if kernel_error is not None:
            success = False
            output = None
            error = kernel_error
            exc_type = "KernelError"
            exc_repr = kernel_error
            failure_code = FailureCode.INVALID_INPUT if invalid_input else FailureCode.KERNEL_ERROR

        trace_metadata: dict[str, Any] = dict(metadata) if metadata is not None else {}
        frozen_metadata = _freeze_value(trace_metadata)

        kernel_meta = _freeze_value(
            {
                "run_id": run_id,
                "started_at": started_at,
                "finished_at": finished_at,
                "runtime_ms": runtime_ms,
                "failure_code": failure_code.value,
                "success": success,
            }
        )

        return ExecutionTrace(
            run_id=run_id,
            psi=psi,
            started_at=started_at,
            finished_at=finished_at,
            runtime_ms=runtime_ms,
            success=success,
            failure_code=failure_code,
            output=output,
            error=error,
            exception_type=exc_type,
            exception_repr=exc_repr,
            metadata=frozen_metadata,
            kernel_meta=kernel_meta,
        )

    def _safe_now(self, kernel_error: Optional[str]) -> tuple[datetime, Optional[str]]:
        if kernel_error is not None:
            return datetime(1970, 1, 1, tzinfo=timezone.utc), None
        try:
            return self._now_provider(), None
        except Exception as exc:  # noqa: BLE001
            return datetime(1970, 1, 1, tzinfo=timezone.utc), f"KernelError: now_provider failed: {exc.__class__.__name__}"

    def _safe_perf(self, kernel_error: Optional[str]) -> tuple[float, Optional[str]]:
        if kernel_error is not None:
            return 0.0, None
        try:
            return self._perf_counter(), None
        except Exception:  # noqa: BLE001
            return 0.0, "KernelError: perf_counter failed"

    def _safe_run_id(self, kernel_error: Optional[str]) -> tuple[str, Optional[str]]:
        if kernel_error is not None:
            return "invalid", None
        try:
            return self._run_id_factory(), None
        except Exception:  # noqa: BLE001
            return "invalid", "KernelError: run_id_factory failed"
