"""断言逻辑和推理引擎所需要的知识库相关结构"""
from .fact_base import FactBase
from .rule_base import RuleBase
from .ontology_base import load_ontologies

__all__ = ["FactBase", "RuleBase", 'load_ontologies']
