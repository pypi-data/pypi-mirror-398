"""支持断言逻辑的推理引擎"""
from al_inference_engine.main import InferenceEngine, QueryStructure
from al_inference_engine.config import (Config, RunControlConfig, InferenceStrategyConfig,
                                        GrounderConfig, ExecutorConfig, PathConfig, KBConfig)
from al_inference_engine.syntax.base_classes import Constant, Concept, Operator, Variable, CompoundTerm, Assertion, Formula, Rule

try:
    from ._version import version as __version__
except ImportError:
    __version__ = '0.0.0'

__all__ = [
    'Assertion',
    'CompoundTerm',
    'Concept',
    'Config',
    'Constant',
    'ExecutorConfig',
    'Formula',
    'GrounderConfig',
    'InferenceEngine',
    'InferenceStrategyConfig',
    'KBConfig',
    'Operator',
    'PathConfig',
    'QueryStructure',
    'Rule',
    'RunControlConfig',
    'Variable',
]
