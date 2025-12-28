# ruff: noqa: ERA001  # Commented parameters are either not implemented yet or depend on unfinished upstream/downstream modules.
import warnings
from typing import Any, cast, Literal

import logging
from dataclasses import dataclass, fields
from datetime import datetime, UTC
from pathlib import Path
import yaml
import json
import tyro
from tyro.conf import OmitArgPrefixes
import dacite
from dacite.config import Config as daConfig

RESULT_LEVEL = 25
logging.RESULT = RESULT_LEVEL  # type: ignore[attr-defined]  # This fails mypy; setattr fails ruff.

logging.addLevelName(RESULT_LEVEL, "RESULT")


def _result(self: logging.Logger, message: str, *args: object) -> None:
    if self.isEnabledFor(RESULT_LEVEL):
        self._log(RESULT_LEVEL, message, args)


logging.Logger.result = _result  # type: ignore[attr-defined]


# Config classes inheriting all settings from the original file.
@dataclass
class RunControlConfig:
    """Runtime control."""
    iteration_limit: int = 300  # Timeout iterations (one grounder-executor cycle is one iteration).
    time_limit: int = 3000  # Timeout in seconds.
    log_level: Literal['DEBUG', 'INFO', 'RESULT', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO'  # Log level.
    # grounding_steps: int = 4  # Per-grounding step limit. TODO: Unused; may no longer be needed.
    trace: bool = False  # Enable inference path tracing.
    semi_eval_with_equality: bool = True  # Consider equality axioms in semi-evaluation. Disable to reduce overhead.
    # This only partially disables related behavior. TODO: Possibly rename to inference_with_equality.
    interactive_query_mode: Literal["interactive", "first", "all"] = "first"  # Control interactive printing of solutions.
    # interactive = interactive, first = print first solution only, all = print all solutions.
    save_solutions: bool = False  # Record and return solutions; False logs only to terminal and logs.


@dataclass
class InferenceStrategyConfig:
    """Inference strategy and model behavior."""
    select_rules_num: int | Literal[-1] = -1  # Number of rules to select.
    select_facts_num: int | Literal[-1] = -1  # Number of facts to select; -1 means all facts.
    # premise_selection_strategy: Literal[''] = ''  # Premise selection algorithm. TODO: Unused.
    grounding_rule_strategy: Literal['SequentialCyclic', 'SequentialCyclicWithPriority'] = "SequentialCyclic"  # Rule selection strategy in grounding.
    # executing_sort_strategy: Literal[''] = ''  # Execution order strategy. TODO: Unused.
    grounding_term_strategy: Literal['Exhausted'] = "Exhausted"  # Term selection strategy in grounding.
    question_rule_interval: int = 1  # Insert a question rule every N rules; -1 uses total rule count as the interval.


@dataclass
class GrounderConfig:
    """Grounder-related parameters."""
    grounding_rules_num_every_step: int | Literal[-1] = -1
    grounding_facts_num_for_each_rule: int | Literal[-1] = -1
    allow_unify_with_nested_term: bool = True  # Allow Variables to be replaced by CompoundTerms.
    conceptual_fuzzy_unification: bool = True  # Use strict concept constraints to accelerate inference.
    # This depends on correct concept subsumption and full constant.belong_concept settings; beginners should use loose matching.


@dataclass
class ExecutorConfig:
    """Executor-related parameters."""
    executing_rule_num: int | Literal[-1] = -1
    executing_max_steps: int | Literal[-1] = -1
    anti_join_used_facts: bool = True  # Drop facts that were already produced (default True).
    # This records last-true results and anti-joins against current results to drop facts.
    # It can be inefficient when duplicates are rare, but speeds up heavy duplication.


@dataclass
class PathConfig:
    """Paths and resource dependencies."""
    rule_dir: str = './'
    fact_dir: str = './'
    log_dir: str = './log'


@dataclass
class KBConfig:
    """Knowledge-base related parameters."""
    fact_cache_size: int | Literal[-1] = -1


@dataclass
class Config:
    """Main entry point for al_inference_engine hyperparameters."""
    run: OmitArgPrefixes[RunControlConfig]
    strategy: OmitArgPrefixes[InferenceStrategyConfig]
    grounder: OmitArgPrefixes[GrounderConfig]
    executor: OmitArgPrefixes[ExecutorConfig]
    path: OmitArgPrefixes[PathConfig]
    engineering: OmitArgPrefixes[KBConfig]
    config: str | None = None  # Config file path.


def _load_config_file(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        if path.endswith(('.yaml', '.yml')):
            data = yaml.safe_load(f)
        elif path.endswith('.json'):
            data = json.load(f)
        else:
            raise ValueError("Unsupported config file format: must be .yaml, .yml, or .json")

    if not isinstance(data, dict):
        raise TypeError(f"Config file must contain a dict, got {type(data)}")
    return cast("dict[str, Any]", data)


def _save_config(config: dict[str, Any], path: str) -> None:
    with open(path, 'w', encoding='utf8') as f:
        yaml.dump(config, f, sort_keys=False)


def _init_logger(log_path: str | None = None,
                 run_id: str | None = None,
                 log_name: str = "run.log",
                 log_level: int = logging.INFO) -> logging.Logger:  # Literal is best but too verbose here.
    """
    Initialize the logging system; paths come from config.log_dir.
    Supports per-run log files by run_id.
    """
    if run_id is None:
        run_id = datetime.now(UTC).astimezone().strftime("%Y%m%d_%H%M%S")

    log_dir = Path(log_path) if log_path else Path("./log")
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{run_id}_{log_name}"

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Get the root logger and clear old handlers (avoid duplicate output).
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # File log handler.
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler.
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.setLevel(log_level)

    logger.info("Logger initialized at %s", log_file)

    return logger


def _init_config_cli() -> Config:
    """Initialize config and logging."""
    cli_config, unknown = tyro.cli(Config, return_unknown_args=True)  # Parse CLI args via tyro. HACK: may parse manually later.
    if unknown:
        warnings.warn(f"Unknown al_inference_engine parameters ignored: {unknown}", stacklevel=2)

    no_default_fields = [field.name for field in fields(Config) if field.default is field.default_factory]
    base_config: dict[str, dict[Any, Any]] = {k: {} for k in no_default_fields}  # Avoid errors if YAML misses child configs.
    # If child configs have new required fields, this still fails; we could recurse but treat it as unnecessary for now.
    file_config = base_config | _load_config_file(cli_config.config) if cli_config.config else base_config

    # Merge config file and CLI parameters.
    final_config, _ = tyro.cli(Config, return_unknown_args=True, default=dacite.from_dict(Config,
                                                                                          file_config,
                                                                                          config=daConfig(strict=True)))
    return final_config


def _build_config(user_config: Config | None = None,
                  config_file_path: str | None = None) -> Config:
    """Build a `Config` from CLI arguments, an in-code default, or a config file.

    This function provides a single entry point to construct the runtime configuration:
    - If `user_config` is provided, parse CLI overrides on top of it.
    - If `config_file_path` is provided, load the file config and allow CLI overrides.
    - Otherwise, initialize purely from CLI (and its config argument).

    :param user_config: A default `Config` instance to be used as the CLI default.
            Mutually exclusive with `config_file_path` (and also incompatible with
            `user_config.config` being set).
    :param config_file_path: Path to a config file (e.g., YAML/JSON). Mutually
            exclusive with `user_config`.
    :return: The final merged `Config` instance.

    :raises: ValueError: If `user_config` is used together with `config_file_path`
            or when `user_config.config` is set.
    """  # noqa: DOC501
    if user_config and (user_config.config or config_file_path):
        raise ValueError("default config instance and config file cannot be used together")

    if user_config:
        return tyro.cli(Config, default=user_config)  # Parameters passed programmatically.

    if config_file_path:
        file_config = _load_config_file(config_file_path)
        merged_config, _ = tyro.cli(Config, return_unknown_args=True, default=dacite.from_dict(Config,
                                                                                              file_config,
                                                                                              config=daConfig(strict=True)))
        return merged_config

    return _init_config_cli()


def init_config_logger(user_config: Config | None = None,
                       config_file_path: str | None = None,
                       *,
                       run_id: str | None = None,
                       log_name: str = "run.log") -> Config:
    """Initialize configuration and logger.

    This is the public entry point. It builds the final `Config` (from CLI/code/file)
    and initializes the logger under `config.path.log_dir`, then logs the final config.

    :param: user_config: A default `Config` instance to be used as the CLI default.
            Mutually exclusive with `config_file_path`.
    :param: config_file_path: Path to a config file. Mutually exclusive with `user_config`.
    :param: run_id: Optional run identifier used by the logger initializer.
    :param: log_name: Suffix of log file name ({run_id}_{log_name}). Defaults to "run.log".

    :return: The final merged `Config` instance.
    """
    config = _build_config(user_config, config_file_path)

    logger = _init_logger(config.path.log_dir,
                          run_id=run_id, log_name=log_name,
                          log_level=getattr(logging, config.run.log_level.upper(), logging.INFO))

    logger.info("Final Config:\n%s", yaml.dump(config.__dict__, sort_keys=False, allow_unicode=True))

    return config
