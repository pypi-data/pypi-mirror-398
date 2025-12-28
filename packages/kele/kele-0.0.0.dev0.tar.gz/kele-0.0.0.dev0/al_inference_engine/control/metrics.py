# metrics_typed.py
# pip install prometheus-client psutil
from __future__ import annotations

import functools
import json
import os
import time
import uuid
import warnings
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, ParamSpec, TypeVar, TYPE_CHECKING, Self

import psutil
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    push_to_gateway,
    start_http_server,
)
import logging

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Mapping

logger = logging.getLogger(__name__)

# 涉及到的主要metrics包括：cpu_percent: float; rss_mib: float; count: int; module: str; phase: str; duration_seconds: float


P = ParamSpec("P")
R = TypeVar("R")

type JSONValue = bool | int | float | str | list[JSONValue] | dict[str, JSONValue] | None
type JSONObject = dict[str, JSONValue]

__all__ = [
    "PhaseTimer",
    "RunRecorder",
    "end_run",
    "inc_iter",
    "init_metrics",
    "maybe_push",
    "measure",
    "observe_counts",
    "sample_process_gauges",
    "start_run",
]


def _now_iso() -> str:
    """此刻时间"""
    return datetime.now(UTC).astimezone().isoformat(timespec="seconds")


def _bytes_to_mib(n: int) -> float:
    return n / (1024 * 1024)


class RunRecorder:
    """
    把一次推理运行的关键过程与资源信息写入 JSON（metrics_logs/<run_id>.json）。

    - 使用 event 记录任意事件（统一用 timestamp、event 命名）。
    - 使用 observe_cpu_mem 记录 CPU/内存采样点（ cpu_percent 、 rss_mib ）。
    - 调用 end 收尾并记录（ started_at / ended_at 、峰值/均值等）。
    """

    def __init__(self, log_dir: str = "metrics_logs", run_id: str | None = None) -> None:
        """
        初始化一个运行记录器。
        """
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        self.run_id: str = run_id or (time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid1().hex[:6])
        self.log_dir: str = log_dir
        self.meta: dict[str, Any] = {
            "run_id": self.run_id,
            "started_at": _now_iso(),  # ISO 8601
        }
        self.events: list[JSONObject] = []
        self._cpu_percent_peaks: list[float] = []
        self._rss_mib_peaks: list[float] = []

        self._phase_totals: dict[tuple[str, str], float] = {}

        self._func_totals: dict[tuple[str, str], float] = {}

    def event(self, kind: str, /, **kwargs: Any) -> None:  # noqa: ANN401
        """记录一条通用事件"""
        self.events.append({"timestamp": _now_iso(), "event": kind, **kwargs})

    def observe_cpu_mem(self, cpu_pct: float, rss_bytes: int) -> None:
        """记录一次 CPU(%) 与 RSS(bytes) 采样，并存为事件（MiB 化）"""
        cpu_percent = cpu_pct
        rss_mib = _bytes_to_mib(rss_bytes)
        self._cpu_percent_peaks.append(cpu_percent)
        self._rss_mib_peaks.append(rss_mib)
        self.event("process_sample", cpu_percent=cpu_percent, rss_mib=rss_mib)

    def end(self, extra_meta: dict[str, Any] | None = None) -> str:
        """
        结束当前运行，汇总峰值指标并将记录保存。
        """
        self.meta["ended_at"] = _now_iso()
        if extra_meta:
            self.meta.update(extra_meta)
        if self._cpu_percent_peaks:
            self.meta["cpu_percent_max"] = max(self._cpu_percent_peaks)
            self.meta["cpu_percent_mean"] = sum(self._cpu_percent_peaks) / len(self._cpu_percent_peaks)
        if self._rss_mib_peaks:
            self.meta["rss_max_mib"] = max(self._rss_mib_peaks)

        if self._phase_totals:
            self.meta["phase_durations_seconds_total"] = [
                {"module": m, "phase": p, "duration_seconds_total": t}
                for (m, p), t in sorted(self._phase_totals.items())
            ]
            self.meta["all_phases_duration_seconds_total"] = sum(self._phase_totals.values())
        else:
            self.meta["all_phases_duration_seconds_total"] = "no running time"

        if self._func_totals:
            self.meta["function_durations_seconds_total"] = [
                {"module": m, "name": n, "duration_seconds_total": t}
                for (m, n), t in sorted(self._func_totals.items())
            ]
            self.meta["all_functions_duration_seconds_total"] = sum(self._func_totals.values())

        path = str(Path(self.log_dir) / f"{self.run_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"meta": self.meta, "events": self.events}, f, ensure_ascii=False, indent=4)

        logger.result("运行时间: %ss", self.meta['all_phases_duration_seconds_total'])  # type: ignore[attr-defined]

        return path

    def add_phase_duration(self, module: str, phase: str, seconds: float) -> None:
        """记录一次 phase 的持续时间"""
        key = (module, phase)
        self._phase_totals[key] = self._phase_totals.get(key, 0.0) + seconds

    def add_func_duration(self, module: str, name: str, seconds: float) -> None:
        """记录一次函数的持续时间（用于 JSON 汇总）"""
        key = (module, name)
        self._func_totals[key] = self._func_totals.get(key, 0.0) + seconds


# --------- 把所有“全局变量”折叠进一个 State 对象，避免 global 赋值（PLW0603） ---------
@dataclass
class _State:
    registry: CollectorRegistry | None = None
    pushgateway: str | None = None
    job: str = "al_inference"
    grouping: dict[str, str] = field(default_factory=dict)
    proc: psutil.Process = field(default_factory=lambda: psutil.Process(os.getpid()))

    # metrics
    h_func_lat: Histogram | None = None
    h_phase_lat: Histogram | None = None
    g_rss: Gauge | None = None
    g_cpu_pct: Gauge | None = None
    c_iter: Counter | None = None
    h_grounded_rules: Histogram | None = None
    h_facts_count: Histogram | None = None

    # run recorder
    run: RunRecorder | None = None


STATE = _State()


def _new_hist(
    name: str,
    help_: str,
    buckets: tuple[float, ...] | None = None,
    labels: tuple[str, ...] = (),
) -> Histogram:
    """构造一个直方图指标（要求先调用 init_metrics）"""
    if buckets is None:
        buckets = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, float("inf"))

    return Histogram(name, help_, labels, buckets=buckets, registry=STATE.registry)


# ---- 需要调取的函数 ----
def start_run(log_dir: str = "metrics_logs", run_id: str | None = None) -> str:
    """在一次完整推理前调用；初始化 RunRecorder 并返回 run_id"""
    STATE.run = RunRecorder(log_dir=log_dir, run_id=run_id)
    return STATE.run.run_id


def end_run(extra_meta: Mapping[str, JSONValue] | None = None) -> str | None:
    """在一次完整推理结束后调用；写入并返回 JSON 路径。若未 start_run 则返回 None"""
    if STATE.run:
        return STATE.run.end(dict(extra_meta) if extra_meta is not None else None)
    return None


def init_metrics(
    port: int | None = None,
    pushgateway: str | None = None,
    job: str = "al_inference",
    grouping: Mapping[str, str] | None = None,
) -> None:
    """
    初始化 Prometheus 指标。

    - 批处理：不指定   port  ，用 Pushgateway 推送。
    - 本地开发：指定   port  （如 8000），直接被 Prometheus scrape。

    上述两个是常用功能，不过我们都默认存储到json了，这两个基本没啥影响
    """
    STATE.registry = CollectorRegistry()
    STATE.pushgateway = pushgateway
    STATE.job = job
    STATE.grouping = dict(grouping or {})

    STATE.h_func_lat = _new_hist("func_latency_seconds", "Function/phase latency", labels=("module", "name"))
    STATE.h_phase_lat = _new_hist("phase_latency_seconds", "Inference phase latency", labels=("module", "phase"))
    STATE.g_rss = Gauge("process_rss_bytes", "Process RSS bytes", registry=STATE.registry)
    STATE.g_cpu_pct = Gauge("process_cpu_percent", "Process CPU percent", registry=STATE.registry)
    STATE.c_iter = Counter("inference_iterations_total", "Total inference iterations", ["module"], registry=STATE.registry)
    STATE.h_grounded_rules = _new_hist("grounded_rules_count", "Grounded rules per iteration")
    STATE.h_facts_count = _new_hist("facts_count_snapshot", "Facts count snapshot")

    # 由于过高的时间开销而移除。以后如果对内存敏感是，再考虑参数控制或者换其他的 tracemalloc.start()
    if port:
        start_http_server(port, registry=STATE.registry)


def maybe_push() -> None:
    """若配置了 Pushgateway，则推送当前注册表中的指标。注：由于我个人倾向于json记录，此函数并未被引擎仓库使用，但不妨保留"""
    if STATE.pushgateway and STATE.registry:
        push_to_gateway(
            STATE.pushgateway,
            job=STATE.job,
            registry=STATE.registry,
            grouping_key=STATE.grouping,
        )


def sample_process_gauges() -> None:
    """
    采样一次进程 RSS/CPU 指标，写入对应 Gauge，并记录至运行日志（若有）。
    需要先调用 init_metrics  初始化 Gauge。
    """
    if STATE.g_rss is None or STATE.g_cpu_pct is None:
        warnings.warn("Gauges not initialized, skipping sample_process_gauges", stacklevel=2)
        return
    rss: int = STATE.proc.memory_info().rss
    STATE.g_rss.set(rss)
    cpu: float = STATE.proc.cpu_percent(interval=None)
    STATE.g_cpu_pct.set(cpu)
    if STATE.run:
        STATE.run.observe_cpu_mem(cpu_pct=cpu, rss_bytes=rss)


def measure(name: str, module: str | None = None, *, skip_process_gauges: bool = True,
            skip_envent_record: bool = True) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    装饰器/上下文：记录函数耗时并采样一次进程指标。

    Examples
    --------
    >>> @measure("step", module="pipeline")
    ... def work(x: int) -> int:
    ...     return x * 2
    """
    resolved_module = module or __name__

    def _decor(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def _wrap(*a: P.args, **k: P.kwargs) -> R:
            t0 = time.perf_counter()
            try:
                return f(*a, **k)
            finally:
                dt = time.perf_counter() - t0

                if STATE.h_func_lat is not None:
                    STATE.h_func_lat.labels(module=resolved_module, name=name).observe(dt)
                if not skip_process_gauges:
                    sample_process_gauges()
                if STATE.run:
                    STATE.run.add_func_duration(resolved_module, name, dt)
                    if not skip_envent_record:
                        STATE.run.event("func_timing", module=resolved_module, name=name, duration_seconds=dt)

        return _wrap

    return _decor


class PhaseTimer:
    """
    上下文管理器：用于手动分段计时并采样进程指标。

    使用示例::

        with PhaseTimer("retrieve", module="pipeline"):
            do_retrieve()
    """

    def __init__(self, phase: str, module: str | None = None, *, skip_process_gauges: bool = True,
                 skip_envent_record: bool = True, skip_count_record: bool = True) -> None:
        self.phase: str = phase
        self.module: str = module or __name__
        self.t0: float | None = None
        self.skip_process_gauges: bool = skip_process_gauges
        self.skip_envent_record: bool = skip_envent_record

    def __enter__(self) -> Self:
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]  # noqa: ANN001
        if self.t0 is None:
            return
        dt = time.perf_counter() - self.t0

        if STATE.h_phase_lat is not None:
            STATE.h_phase_lat.labels(module=self.module, phase=self.phase).observe(dt)
        if not self.skip_process_gauges:
            sample_process_gauges()
        if STATE.run:
            STATE.run.add_phase_duration(self.module, self.phase, dt)
            if not self.skip_envent_record:
                STATE.run.event("phase_timing", module=self.module, phase=self.phase, duration_seconds=dt)
        return


def observe_counts(grounded_rules: int | None = None, facts_count: int | None = None) -> None:
    """
    记录离散计数类指标（例如每次 grounding 的规则数、事实库快照大小）。
    若未初始化相应的直方图，调用将被忽略。
    """
    if grounded_rules is not None and STATE.h_grounded_rules is not None:
        STATE.h_grounded_rules.observe(float(grounded_rules))
        if STATE.run:
            STATE.run.event("grounded_rules", count=grounded_rules)
    if facts_count is not None and STATE.h_facts_count is not None:
        STATE.h_facts_count.observe(float(facts_count))
        if STATE.run:
            STATE.run.event("facts_count", count=facts_count)


def inc_iter(module: str) -> None:
    """将指定   module   的推理迭代次数自增 1。未初始化则忽略。"""
    if STATE.c_iter is None:
        return
    STATE.c_iter.labels(module=module).inc()
