from __future__ import annotations

from collections import defaultdict
from typing import Any, TYPE_CHECKING


if TYPE_CHECKING:
    from al_inference_engine.equality import Equivalence
    from al_inference_engine.grounder import GroundedRule
    from al_inference_engine.knowledge_bases import FactBase, RuleBase
    from al_inference_engine.syntax import Question, Rule, FACT_TYPE, Variable, Constant, CompoundTerm
    from collections.abc import Callable


class HookMixin:
    """
    提供模块自身注册hook和执行hook的 Mixin类，需要的模块可以直接继承它

    :ivar _hooks: 事件名称到钩子函数列表的映射。
    """
    def __init__(self) -> None:
        self._hooks: dict[str, list[Callable[..., None]]] = defaultdict(list)

    def register_hook(self, event_name: str, hook_fn: Callable[..., None]) -> None:
        """
        为指定事件注册钩子函数。

        :param event_name: 要监听的事件名称。
        :param hook_fn: 接受任意参数的可调用钩子函数。
        """
        self._hooks[event_name].append(hook_fn)

    def _run_hooks(self, event_name: str, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """
        执行所有注册到指定事件的钩子。

        :param event_name: 事件名称。
        :param args: 传递给钩子的所有位置参数。
        :param kwargs: 传递给钩子的所有关键字参数。
        """
        for hook in self._hooks.get(event_name, []):
            hook(*args, **kwargs)


class Callback:
    """回调接口——在推理各阶段采集指标的Hook"""

    def on_infer_start(
        self,
        question: Question,
        fact_base: FactBase,
        rule_base: RuleBase,
    ) -> None:
        """
        推理开始时调用

        :param question: 待推理的问题
        :param fact_base: 事实库
        :param rule_base: 规则库
        """

    def on_grounder_select_start(
        self,
        question: Question,
        fact_base: FactBase,
        rule_base: RuleBase,
    ) -> None:  # HACK: 参数可能需要包括grounder的选择策略？但有点没必要感觉，毕竟策略也不一定按str分类
        """
        Grounder选取前调用

        :param question: 待推理的问题
        :param fact_base: 事实库
        :param rule_base: 规则库
        """

    def on_grounder_select_end(
        self,
        selected_rule_terms_pair: list[tuple[Rule, list[FACT_TYPE]]],
        candidate_rules: RuleBase,
        fact_base: FactBase,
        question: Question,
    ) -> None:
        """
        Grounder 选取后调用。

        :param selected_rule_terms_pair: 与该规则匹配的事实列表
        :param candidate_rules: 本次 Grounder 考虑的所有候选规则列表，因为目前是直接从代码中选取，所以就约定为规则库即可
        :param question: 待推理的问题
        :param fact_base: 事实库列表
        """

    def on_binding_change(
        self,
        var_name: str,
        var_value: Constant | CompoundTerm
    ) -> None:
        """
        每次变量绑定/解绑时调用。这个函数暂且作为提示性作用，如果它在_RuleNode中起作用，日后可能会被on_rule_activation替代
        如果在其他节点或者说_TupleTable层面就起作用，那激活频率又太高了

        :param var_name: 变量名
        :param var_value: 变量值
        """

    def on_rule_activation(
        self,
        rule: Rule,
        var_dict: dict[Variable, Constant | CompoundTerm]
    ) -> None:
        """
        每次 RuleNode 被激活（进入执行）时调用。

        :param rule: 当前激活的规则
        :param var_dict: 每次传递一个实例化候选元组
        # risk: 能否思考这里计算推理深度depth: int 参数，或者与infer path联动
        """

    def on_executor_start(
        self,
        grounded_rules: list[GroundedRule],
        question: Question,
        equivalence: Equivalence,
    ) -> None:  # HACK: 参数可能需要包括executor的选择策略？但有点没必要感觉，毕竟策略也不一定按str分类
        """
        Executor 执行前调用。

        :param grounded_rules: 已实例化的规则列表
        :param question: 待推理的问题
        :param equivalence: 为规则检验提供支持的等价类
        """

    def on_executor_sorted(
        self,
        sorted_rules: list[GroundedRule],
        original_rules: list[GroundedRule],
        question: Question,
    ) -> None:
        """
        Executor 排序后调用。

        :param sorted_rules: 排序后的规则列表
        :param original_rules: 排序前的规则列表
        :param question: 待推理的问题
        """

    def on_executor_post(
        self,
        execution_results: Any,  # 包含一些新生成的事实，可能还有别的  # noqa: ANN401  # TODO: 细节待定
        question: Question,
    ) -> None:
        """
        Executor 执行后调用。

        :param execution_results: 执行返回的原始结果（包含路径、绑定信息等）
        :param question: 待推理的问题
        """

    def on_infer_end(
        self,
        final_result: Any,  # FIXME: 尚不清楚类型，同on_executor_post  # noqa: ANN401
        question: Question,
        metrics: Any  # noqa: ANN401  # FIXME: 细节待定
    ) -> None:
        """
        推理完成时调用，汇总全流程指标并评估准确率。

        :param final_result: 最终推理输出
        :param question: 待推理的问题
        :param metrics: 可能的各种对结果的评价等信息
        """


class CallbackManager:
    """通过这个类注册实例化后的Callback"""
    def __init__(self) -> None:
        self._callbacks: list[Callback] = []

    def register_callback(self, callback: Callback) -> None:
        """
        注册一个回调实例。
        :param callback: Callback的子类实例
        """
        self._callbacks.append(callback)

    def unregister_callback(self, callback: Callback) -> None:
        """
        注销一个回调实例。
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    # Infer start
    def on_infer_start(self, question: Question, fact_base: FactBase, rule_base: RuleBase) -> None:
        """对应Callback的on_infer_start"""
        for cb in self._callbacks:
            cb.on_infer_start(question, fact_base, rule_base)

    # Grounder selection hooks
    def on_grounder_select_start(self, question: Question, fact_base: FactBase, rule_base: RuleBase) -> None:
        """对应Callback的on_grounder_select_start"""
        for cb in self._callbacks:
            cb.on_grounder_select_start(question, fact_base, rule_base)

    def on_grounder_select_end(
        self,
        selected_rule_terms_pair: list[tuple[Rule, list[FACT_TYPE]]],
        candidate_rules: RuleBase,
        fact_base: FactBase,
        question: Question,
    ) -> None:
        """对应Callback的on_grounder_select_end"""
        for cb in self._callbacks:
            cb.on_grounder_select_end(selected_rule_terms_pair, candidate_rules, fact_base, question)

    # Binding hook
    def on_binding_change(self, var_name: str, var_value: Constant | CompoundTerm) -> None:
        """对应Callback的on_binding_change"""
        for cb in self._callbacks:
            cb.on_binding_change(var_name, var_value)

    # Rule activation
    def on_rule_activation(self, rule: Rule, var_dict: dict[Variable, Constant | CompoundTerm]) -> None:
        """对应Callback的on_rule_activation"""
        for cb in self._callbacks:
            cb.on_rule_activation(rule, var_dict)

    # Executor hooks
    def on_executor_start(self,
                          grounded_rules: list[GroundedRule],
                          question: Question,
                          equivalence: Equivalence) -> None:
        """对应Callback的on_executor_start"""
        for cb in self._callbacks:
            cb.on_executor_start(grounded_rules, question, equivalence)

    def on_executor_sorted(
        self,
        sorted_rules: list[GroundedRule],
        original_rules: list[GroundedRule],
        question: Question,
    ) -> None:
        """对应Callback的on_executor_sorted"""
        for cb in self._callbacks:
            cb.on_executor_sorted(sorted_rules, original_rules, question)

    def on_executor_post(self, execution_results: Any, question: Question) -> None:  # noqa: ANN401  # FIXME: 同Callback
        """对应Callback的on_executor_post"""
        for cb in self._callbacks:
            cb.on_executor_post(execution_results, question)

    # Infer end
    def on_infer_end(self, final_result: Any, question: Question, metrics: Any) -> None:  # noqa: ANN401  # FIXME: 同Callback
        """对应Callback的on_infer_end"""
        for cb in self._callbacks:
            cb.on_infer_end(final_result, question, metrics)
