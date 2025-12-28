import logging
from collections.abc import Sequence
from typing import Literal, Any, ClassVar
from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field

from al_inference_engine.config import init_config_logger, Config
from al_inference_engine.control.grounding_selector import GroundingAtomTermWithWildCardSelector
from al_inference_engine.control.status import InferenceStatus
from al_inference_engine.executer import Executor
from al_inference_engine.grounder import Grounder, GroundedRule, GroundedRuleDS
from al_inference_engine.knowledge_bases import FactBase, RuleBase, load_ontologies
from al_inference_engine.control.metrics import PhaseTimer, observe_counts, init_metrics, \
    measure, end_run, start_run, inc_iter
from al_inference_engine.syntax import FACT_TYPE, Rule, SankuManagementSystem, Question, Variable, TERM_TYPE
from al_inference_engine.equality import Equivalence
from al_inference_engine.control import create_main_loop_manager, GroundingRuleSelector, InferencePath

logger = logging.getLogger(__name__)


class QueryStructure(BaseModel):
    """Query structure used as input when calling the inference engine."""
    premises: Sequence[FACT_TYPE]
    question: Sequence[FACT_TYPE]

    model_config: ClassVar = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
    )


class EngineRunResult(BaseModel):
    """Return structure from the inference engine."""
    model_config: ClassVar = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
    )

    status: InferenceStatus
    final_facts: list[FACT_TYPE]
    question: Question
    iterations: int
    executor_steps: int
    terminated_by: Literal["initial_check", "executor", "main_loop", "unknown"]

    # Control whether solutions are exposed externally; internal-only and excluded by default during serialization.
    # In other words, storing solutions is not part of the main inference process, but a user-friendly feature.
    solutions: list[Mapping[Variable, TERM_TYPE]] | None
    include_solutions: bool = Field(default=False, exclude=True)

    @property
    def has_solution(self) -> bool:
        """Return whether any solution exists."""
        return bool(self.solutions)

    @property
    def is_success(self) -> bool | None:  # None means unknown/undetermined
        """
        - SUCCESS with solutions -> success
        - FIXPOINT_REACHED / NO_MORE_RULES with solutions -> success (solutions are exhausted)
        - MAX_* / EXTERNALLY_INTERRUPTED with solutions -> only partial success
        """
        if self.include_solutions:
            if not self.has_solution:
                return False
            return self.status in {
                InferenceStatus.SUCCESS,
                InferenceStatus.FIXPOINT_REACHED,
                InferenceStatus.NO_MORE_RULES,
            } or self.status == InferenceStatus.CONFLICT_DETECTED

        return None  # FIXME: Success detection is incomplete; without solutions it cannot be determined.

    @property
    def is_partial_success(self) -> bool | None:  # None means unknown/undetermined
        """
        Has solutions, but stopped early due to resource limits or external interruption.
        There may be more solutions; no solutions does not imply failure.
        """
        if self.include_solutions:
            return self.has_solution and self.status in {
                InferenceStatus.MAX_STEPS_REACHED,
                InferenceStatus.MAX_ITERATIONS_REACHED,
                InferenceStatus.EXTERNALLY_INTERRUPTED,
            }

        return None  # FIXME: Success detection is incomplete; without solutions it cannot be determined.

    def log_message(self) -> str:
        """Build a log-friendly message."""
        msg = (f"Inference finished.\n"
               f"status={self.status}, success={self.is_success}, partial_success=={self.is_partial_success}, "
               f"terminated_by={self.terminated_by}, iterations={self.iterations}, facts_num={len(self.final_facts)}")

        # Only show the number of solutions when solutions are requested.
        if self.include_solutions:
            sol_num = len(self.solutions) if self.solutions is not None else 'null'
            msg += f", solutions_num={sol_num}"

        return msg

    def to_dict(self) -> dict[str, Any]:
        """Serialize with optional removal of non-essential fields."""
        if not self.include_solutions:
            return self.model_dump(exclude={"solutions"})
        return self.model_dump()


class InferenceEngine:
    """Inference engine main program that wraps grounding + executing."""

    def __init__(self,  # noqa: PLR0913
                 facts: Sequence[FACT_TYPE] | str | None,
                 rules: Sequence[Rule] | str | None,
                 *,
                 concept_dir_or_path: str = 'knowledge_bases/builtin_base/builtin_concepts.py',
                 operator_dir_or_path: str = 'knowledge_bases/builtin_base/builtin_operators.py',
                 user_config: Config | None = None,
                 config_file_path: str | None = None,  # TODO: Consider moving custom log file into Config.
                 ) -> None:
        """
        Initialize the inference engine with initial facts and rules.
        If facts and rules are None, use the default initial facts and rules.
        """
        self.args = init_config_logger(user_config, config_file_path)

        def _get_source_info(obj: Sequence[FACT_TYPE] | Sequence[Rule] | str | None, name: str) -> str:
            if isinstance(obj, str):  # Note that str is also a Sequence.
                return f"{name} from file: {obj}"
            if isinstance(obj, Sequence):
                return f"{name} from list, length={len(obj)}"
            if obj is None:
                return f"{name} is None"

            raise TypeError(f"Unsupported type for obj: {type(obj).__name__}")

        logger.info("Initializing inference engine: Load %s; Load %s",
                    _get_source_info(facts, "facts"),
                    _get_source_info(rules, "rules"))

        self.equivalence = Equivalence(args=self.args)
        sk_system_handler = SankuManagementSystem()
        # TODO: Knowledge base declarations may require db_url from args; not implemented yet.

        facts = self.args.path.fact_dir if facts is None else facts
        rules = self.args.path.rule_dir if rules is None else rules

        try:
            load_ontologies(concept_dir_or_path=concept_dir_or_path,
                            operator_dir_or_path=operator_dir_or_path)

            # selector
            self.rule_selector = GroundingRuleSelector(strategy=self.args.strategy.grounding_rule_strategy,
                                                       question_rule_interval=self.args.strategy.question_rule_interval)

            self.term_selector = GroundingAtomTermWithWildCardSelector(equivalence=self.equivalence,
                                                                       args=self.args)

            # knowledge base
            self.fact_base = FactBase(initial_facts_or_dir_or_path=facts,
                                      equivalence_handler=self.equivalence,
                                      term_selector=self.term_selector,
                                      sk_system_handler=sk_system_handler,
                                      args=self.args.engineering)
            # only one global fact_base is maintained.

            self.rule_base = RuleBase(rules, args=self.args.engineering)

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Fact base created with %s facts", len(self.fact_base.facts))

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Rule base created with %s rules", len(self.rule_base.rules))
            logger.info("Inference engine created successfully.")

        except Exception:
            logger.exception("Initialization failed: ontologies_path=(concept=%s, operator=%s)\n(facts=%s, rules=%s)",
                             concept_dir_or_path,
                             operator_dir_or_path,
                             facts[:2] if facts else None,
                             rules[:2] if rules else None)
            raise

        # Create the main loop manager.
        self.main_loop_manager = create_main_loop_manager(
            self.equivalence,
            sk_system_handler,
            max_iterations=self.args.run.iteration_limit,
            interactive_query_mode=self.args.run.interactive_query_mode
        )

        # Create the Grounder.
        grounded_structure = GroundedRuleDS(equivalence=self.equivalence, sk_system_handler=sk_system_handler, args=self.args)
        # FIXME: Extract DS into a standalone component.
        self.grounder = Grounder(fact_base=self.fact_base,
                                 rule_base=self.rule_base,
                                 rule_selector=self.rule_selector,
                                 term_selector=self.term_selector,
                                 grounded_structure=grounded_structure,
                                 rules_num_every_step=self.args.grounder.grounding_rules_num_every_step,  # TODO: Can
                                 # wrap these into args as a grounder config type; keep separate to avoid conflicts.
                                 facts_num_for_each_rule=self.args.grounder.grounding_facts_num_for_each_rule)

        self.inference_path = InferencePath(self.args.run)
        if self.args.run.trace:
            # Pass in the equivalence handler to trace paths.
            self.inference_path.set_equivalence(self.equivalence)

        self.executor = Executor(equivalence=self.equivalence,
                                 sk_system_handler=sk_system_handler,
                                 fact_base=self.fact_base,
                                 main_loop_manager=self.main_loop_manager,
                                 inference_path=self.inference_path,
                                 select_num=self.args.executor.executing_rule_num,
                                 max_steps=self.args.executor.executing_max_steps,
                                 interactive_query_mode=self.args.run.interactive_query_mode)  # TODO: These are not the same subclass.
        # The design could be improved; also consider wrapping these into args.

        # Track whether the engine has completed at least one inference run.
        self._has_previous_run: bool = False

        # Initialize metrics monitoring.
        init_metrics(job="al_inference", grouping={"env": "dev"})

    def _infer(self, question: Question) -> EngineRunResult:
        """Run a full forward-chaining inference cycle."""
        mod = __name__
        # Initial snapshot.
        observe_counts(facts_count=len(self.fact_base.get_facts()))

        logger.info("InferenceEngine: Starting full inference...")

        # Check whether the question can be answered before the loop starts.
        current_facts = self.fact_base.get_facts()
        initial_status = self.main_loop_manager.check_status(current_facts, question)

        if initial_status.is_terminal_for_main_loop():
            logger.info("Initial check result: %s", initial_status.log_message())

            return EngineRunResult(
                status=initial_status,
                solutions=[{}],  # The question already exists in facts; treat {} as a "true" solution for display.
                final_facts=current_facts,
                question=question,
                iterations=self.main_loop_manager.iteration,
                executor_steps=self.executor.executor_manager.step_num,
                terminated_by="initial_check",
                include_solutions=self.args.run.save_solutions,
            )

        final_status: InferenceStatus | None = None
        terminated_by: Literal['initial_check', 'executor', 'main_loop', 'unknown']

        while True:
            inc_iter(mod)

            logger.info("Inference iteration %s...", self.main_loop_manager.iteration)

            at_fixpoint = self.main_loop_manager.is_at_fixpoint()
            self.rule_selector.set_at_fixpoint(at_fixpoint=at_fixpoint)

            # Grounding process produce instantiated rules (based on current facts)
            with PhaseTimer("grounding", module=mod):
                grounded_rules: Sequence[GroundedRule] = self.grounder.grounding_process(question=question)
            observe_counts(grounded_rules=len(grounded_rules), facts_count=len(grounded_rules))

            if not grounded_rules:
                logger.info("Inference iteration %s: No new groundings found.", self.main_loop_manager.iteration)
                continue

            with PhaseTimer("execute", module=mod):
                exec_status = self.executor.execute(grounded_rules=grounded_rules, question=question)

            if exec_status.is_terminal_for_main_loop():
                logger.result("Inference terminated due to executor: %s", exec_status.log_message())  # type: ignore[attr-defined]
                terminated_by = "executor"
                final_status = exec_status

                logger.info("Executing: %i rules", len(grounded_rules))  # Placeholder: may be grounding/executing.
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("Executing rules: %s", [str(r.rule) for r in grounded_rules])

                break

            with PhaseTimer("main_check", module=mod):  # Unified check for all termination conditions.
                main_status = self.main_loop_manager.check_status([], question)
            # main checks facts before the loop, executor checks new facts, so pass an empty fact list here.

            if main_status.is_terminal_for_main_loop():
                logger.result("Main loop terminating: %s", main_status.log_message())  # type: ignore[attr-defined]
                terminated_by = "main_loop"
                final_status = main_status
                break

            # Move to the next iteration.
            self.main_loop_manager.next_iteration()

        facts = self.fact_base.get_facts()
        observe_counts(facts_count=len(facts))
        logger.result("Total facts when terminal: %s", len(facts))  # type: ignore[attr-defined]

        return EngineRunResult(
            status=final_status,
            solutions=None,  # FIXME: Update later; pending reported changes in an upcoming PR.
            final_facts=facts,
            question=question,
            iterations=self.main_loop_manager.iteration,
            executor_steps=self.executor.executor_manager.step_num,
            terminated_by=terminated_by,
            include_solutions=self.args.run.save_solutions,
        )

    @measure("infer_query", module="inference")
    def infer_query(self, query: QueryStructure, *, resume: bool = False) -> EngineRunResult:  # TODO: Between runs,
        # EngineRunResult is still returned per call; last result can be treated as authoritative.
        """
        Public interface for the inference engine: accept QueryStructure and return results.
        :param resume: Set True to continue a previous run after injecting new facts externally.
            HACK: logs are split into two files, so timing stats will be inaccurate.
        :raise: ValueError: The first call must have resume=False.
            If resume=True is used before any inference run, ValueError is raised.
        """  # noqa: DOC501
        start_run(log_dir="metrics_logs")  # Start a new metrics record per outer call.

        try:
            if not resume:
                self._reset()
            elif not self._has_previous_run:
                # Attempting resume without any prior run is invalid.
                raise ValueError(
                    "Invalid use of `resume=True` when"
                    "no previous inference run is available to continue from. "
                    "Please set resume=False when calling infer_query(...) first."
                )

            self._has_previous_run = True  # At least one inference run completed.

            premises = query.premises
            question = Question(premises=premises, question=query.question)  # TODO: Consider internal-only Question
            # and avoid storing premises to reduce duplication with QueryStructure.

            if not resume:  # Redundant check, but keeps the flow clearer.
                self._initial_engine(question=question, premises=premises)
            else:
                self.main_loop_manager.initial_manager(normal_rules=None, resume=resume)  # If continue_infer is added
                # everywhere, this branch could be omitted.

            engine_result = self._infer(question=question)
            logger.result(engine_result.log_message())  # type: ignore[attr-defined]

            return engine_result

        finally:
            end_run(extra_meta={
                "facts_final": len(self.fact_base.get_facts()),
                "rules_total": len(self.rule_base.rules),
            })

    def get_facts(self) -> list[FACT_TYPE]:
        """Return facts used (selected by initial_fact_base) and all derived facts."""
        return self.fact_base.get_facts()

    def _reset(self) -> None:
        self.fact_base.reset_fact_base()
        self.rule_base.reset_rule_base()

        self.equivalence.clear()
        self.grounder.reset()
        self.executor.reset()

        self.main_loop_manager.reset()
        self.inference_path.reset()

        # Reset resume flag.
        self._has_previous_run = False

    def _initial_engine(self, question: Question, premises: Sequence[FACT_TYPE]) -> None:
        self.fact_base.initial_fact_base(question=question, topn=self.args.strategy.select_facts_num)
        self.fact_base.add_facts(facts=premises, force_add=True)

        self.rule_base.initial_rule_base(question=question, topn=self.args.strategy.select_rules_num)

        self.term_selector.update_terms(facts=self.fact_base.get_facts())
        self.rule_selector.set_rules(normal_rules=self.rule_base.get_rules(),
                                     question_rules=self.rule_base.get_question_rules())  # HACK: Not linked to fact base.

        self.main_loop_manager.initial_manager(normal_rules=self.rule_base.get_rules())

        if self.args.run.trace:
            for f in self.fact_base.get_facts():
                self.inference_path.add_infer_edge(consequent=f)  # FIXME: Keep change small for this PR; later use list
                # types and revert to Assertion, or at least include a CNF split.

    def _return_infer_path(self):  # type: ignore[no-untyped-def]  # noqa: ANN202  # FIXME: Return type is unclear.
        """
        When returning inference paths, related data must be stored. This might need a global hash-backed linked list,
        updated each time a rule fires successfully.
        FIXME: Another concern is depth_limit. We need fast lookups to control fact/rule selection to avoid exceeding
        limit steps (rather than failing when a path hits the limit). This may be delegated to select, or postponed to v3+.
        """
        raise NotImplementedError


if __name__ == '__main__':
    logger.info("Inference Engine Started")
