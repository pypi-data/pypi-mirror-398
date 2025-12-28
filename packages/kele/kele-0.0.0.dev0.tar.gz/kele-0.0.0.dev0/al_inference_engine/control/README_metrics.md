本文档由GPT5撰写。

# Metrics 使用说明

本模块提供了推理过程中的性能指标采集与记录功能，包括 **速度**、**CPU 占用**、**内存使用** 等。  
虽然目前速度是最主要的关注点，但也支持记录其他资源指标。

## 功能概览
- **指标类型**  
  - `duration_seconds`：代码或函数运行耗时（秒）
  - `cpu_percent`：CPU 占用百分比
  - `rss_mib`：进程占用内存（MiB）
  - 迭代次数、规则数、事实数等离散计数指标

- **记录方式**
  - **代码级**：使用 `PhaseTimer` 上下文管理器，手动分段计时
  - **函数级**：使用 `@measure` 装饰器，自动记录函数执行时间和资源占用
  - 可通过 `observe_counts`、`sample_process_gauges` 等函数采集自定义指标

- **结果存储**  
  默认保存在 **`metrics_logs`** 文件夹下，以 `run_id.json` 命名，包含运行元信息和事件记录。

## 快速开始

### 1. 初始化
```python
from metrics import init_metrics
init_metrics(port=14233, job="al_inference", grouping={"env": "dev"})
```

### 2. 开始与结束一次运行
```python
from metrics import start_run, end_run

run_id = start_run(log_dir="metrics_logs")
# ... 推理或业务逻辑 ...
end_run(extra_meta={"facts_final": 100, "rules_total": 50})
```

### 3. 代码级计时（阶段）
```python
from metrics import PhaseTimer

with PhaseTimer("grounding", module="pipeline"):
    do_grounding()
```

### 4. 函数级计时
```python
from metrics import measure

@measure("infer_step", module="inference")
def infer_step():
    # 推理步骤逻辑
    pass
```

### 5. 采集计数与进程状态
```python
from metrics import observe_counts, sample_process_gauges

observe_counts(grounded_rules=10, facts_count=200)
sample_process_gauges()
```

## 日志文件示例

一次运行的 `metrics_logs/20230801-120000-ab12cd.json` 文件内容示例：

```json
{
    "meta": {
        "run_id": "20230801-120000-ab12cd",
        "started_at": "2023-08-01T12:00:00+08:00",
        "ended_at": "2023-08-01T12:00:10+08:00",
        "cpu_percent_max": 85.3,
        "cpu_percent_mean": 42.7,
        "rss_max_mib": 512.4,
        "phase_durations_seconds_total": [
            {"module": "pipeline", "phase": "grounding", "duration_seconds_total": 2.53},
            {"module": "pipeline", "phase": "execute", "duration_seconds_total": 5.42}
        ],
        "all_phases_duration_seconds_total": 7.95,
        "function_durations_seconds_total": [
            {"module": "inference", "name": "main_infer", "duration_seconds_total": 8.02}
        ],
        "all_functions_duration_seconds_total": 8.02,
        "facts_final": 150,
        "rules_total": 200
    },
    "events": [
        {"timestamp": "2023-08-01T12:00:00+08:00", "event": "process_sample", "cpu_percent": 30.5, "rss_mib": 400.2},
        {"timestamp": "2023-08-01T12:00:02+08:00", "event": "phase_timing", "module": "pipeline", "phase": "grounding", "duration_seconds": 2.53},
        {"timestamp": "2023-08-01T12:00:07+08:00", "event": "phase_timing", "module": "pipeline", "phase": "execute", "duration_seconds": 5.42},
        {"timestamp": "2023-08-01T12:00:10+08:00", "event": "func_timing", "module": "inference", "name": "main_infer", "duration_seconds": 8.02}
    ]
}
```

## 备注
- 该模块可独立用于代码性能测试，也可集成至推理引擎或其他系统。
- 如需推送到 Prometheus Pushgateway，可在 `init_metrics` 中配置 `pushgateway` 参数。
