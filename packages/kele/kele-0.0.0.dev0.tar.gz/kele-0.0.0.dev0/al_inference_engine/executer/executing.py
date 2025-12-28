import logging
from collections.abc import Sequence, Mapping
from typing import Literal

from al_inference_engine.config import RunControlConfig
from al_inference_engine.control import InferencePath
from al_inference_engine.control.status import MainLoopManager
from al_inference_engine.equality import Equivalence
from al_inference_engine.knowledge_bases import FactBase
from al_inference_engine.syntax import Question, FACT_TYPE, SankuManagementSystem, Variable, Constant, CompoundTerm
from al_inference_engine.syntax import _QuestionRule
from al_inference_engine.grounder import GroundedRule
from al_inference_engine.control import InferenceStatus, create_executor_manager
logger = logging.getLogger(__name__)


class Executor:
    """执行器，负责对 grounded rules 执行 check 并更新事实库。"""
    def __init__(self,  # noqa: PLR0913
                 equivalence: Equivalence,
                 sk_system_handler: SankuManagementSystem,
                 fact_base: FactBase,
                 *,
                 main_loop_manager: MainLoopManager | None = None,  # 仅用于更新主循环控制器。如在测试executor功能时可以为空
                 inference_path: InferencePath | None = None,  # 如在测试executor功能时可以为空
                 select_num: int = 5,
                 max_steps: int = 1000,
                 interactive_query_mode: Literal["interactive", "first", "all"] = "first"  # HACK: 考虑是否其余的通过args传递
                 ):
        """:param select_num: 每轮最多执行的 grounded rules 数量，-1 表示不限制。"""
        self.grounded_rules: Sequence[GroundedRule]
        self.select_num = int(1e9) if select_num == -1 else select_num
        # TODO: 此时的select num是从abstract rule层面进行选择的，但理想情况下能否进一步，对每个abstract rule选择其候选值。
        #  不过也要考虑到的是，这里的选择和grounder结束时的选择是接近重复的
        self.equivalence = equivalence
        self.sk_system_handler = sk_system_handler

        self.fact_base = fact_base  # 仅用于更新全局事实，不用于推理
        self.interactive_query_mode = interactive_query_mode

        # 创建执行器管理器
        self.executor_manager = create_executor_manager(equivalence, sk_system_handler, max_steps,
                                                        interactive_query_mode=self.interactive_query_mode)

        self.main_loop_manager = main_loop_manager

        self.inference_path = inference_path if inference_path is not None else InferencePath(args=RunControlConfig())  # FIXME: 只是
        # 为了本次PR改动不要太大的妥协，正常是executor要传一个args参的。另外这个参数None仅用于测试需求

    def get_equivalence(self) -> Equivalence:
        """获取等价关系处理器"""
        return self.equivalence

    def _sort_grounded_rules(self, question: Question) -> None:
        """
        将 grounded rules 按优先级排序，使更有价值的规则先被执行。
        """
        self.grounded_rules = self.grounded_rules   # TODO: 这里是要优化为更优策略的

    def execute(self, grounded_rules: Sequence[GroundedRule], question: Question) -> InferenceStatus:
        """
        执行 grounded rules 的 check 阶段，并更新事实库。

        会在每条规则执行后更新主循环状态，并在满足终止条件时返回。
        """
        logger.info("Starting execution for %s", question.description)

        self.grounded_rules = grounded_rules
        self._sort_grounded_rules(question)

        try:
            for i in range(min(self.select_num, len(self.grounded_rules))):
                grounding_result = grounded_rules[i].check_grounding()

                logger.info(
                    "Generate %s%i%s grounded rules from %s%s%s",
                    "\033[91m", len(grounding_result), "\033[0m",  # \033[91m红色，\033[0m黑色
                    "\033[96m", grounded_rules[i].rule, "\033[0m"  # \033[96m青绿色
                )

                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("all grounded rule text: %s", grounded_rules[i].print_all_grounded_rules())

                added_facts = self._update_facts(grounding_result)
                logger.info(
                    "%s%i%s new facts are derived from Rule %s%s%s",
                    "\033[91m", len(added_facts), "\033[0m",  # \033[91m红色，\033[0m黑色
                    "\033[96m", grounded_rules[i].rule, "\033[0m"  # \033[96m青绿色
                )

                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("new facts: %s", [str(f) for f in added_facts])

                if self.main_loop_manager and not isinstance(grounded_rules[i].rule, _QuestionRule):
                    self.main_loop_manager.update_normal_rule_activation(new_facts=added_facts, used_rule=grounded_rules[i].rule)

                solutions: list[Mapping[Variable, Constant | CompoundTerm]] = []
                question_rule: _QuestionRule | None = None

                if isinstance(grounded_rules[i].rule, _QuestionRule):
                    solutions, question_rule = grounded_rules[i].get_question_solutions()
                    has_solutions = len(solutions) > 0
                    if self.main_loop_manager:
                        self.main_loop_manager.mark_solutions_found(has_solutions=has_solutions)

                # 检查执行器状态
                status = self.executor_manager.check_status(new_facts=added_facts,
                                                            question=question,
                                                            solutions=solutions,
                                                            question_rule=question_rule
                                                            )
                logger.info("Step %d status: %s", self.executor_manager.step_num, status.log_message())
                self.executor_manager.next_step()

                if status.is_terminal_for_executor():
                    return status

        except SystemExit:
            logger.exception("Execution interrupted by SystemExit")
            return InferenceStatus.EXTERNALLY_INTERRUPTED

        return InferenceStatus.NO_MORE_RULES

    def _update_facts(self, new_facts: list[FACT_TYPE]) -> list[FACT_TYPE]:
        """
        更新事实库
        :param new_facts : 这一轮实例化的结果
        """
        added_facts = self.fact_base.add_facts(facts=new_facts)  # 更新事实库后就不需要单独更新等价类了
        self.sk_system_handler.update_facts(new_facts)

        return added_facts

    def reset(self) -> None:
        """当面向新问题推理时，对当前类进行reset"""
        self.executor_manager.reset_for_new_inference()
