from typing import overload
import warnings
from collections.abc import Sequence

from al_inference_engine.config import KBConfig
from al_inference_engine.syntax import Variable, Constant
from al_inference_engine.syntax.base_classes import Rule, Question, Formula, Assertion, CompoundTerm, _QuestionRule
from al_inference_engine.syntax.dnf_converter import RuleSafetyProcesser
from al_inference_engine.knowledge_bases.builtin_base.builtin_facts import true_const


class RuleBase:
    """存储所有abstract rule的总结构"""

    def __init__(self, rules_or_dir_or_path: Sequence[Rule] | str, args: KBConfig):
        if isinstance(rules_or_dir_or_path, str):
            self.rules = list(dict.fromkeys(self._read_rules(rules_or_dir_or_path)))
            # 使用list代替set，以保持输入的规则顺序、因为set后的随机顺序会引入
            # 不必要的不确定性，随意的排序也对于推理无益
        else:
            self.rules = list(dict.fromkeys(rules_or_dir_or_path))  # 加入去重操作

        self.rule_suffix: int = 1

        new_rules: list[Rule] = []
        for single_rule in self.rules:
            new_rules.extend(self._split_and_rename_rule(single_rule))
        self.rules = new_rules

        self.initial_sign: bool = False  # initial_rule_base后为True，和Fact base一样
        self.cur_rules: list[Rule] = []  # FactBase由于经常需要更新而用了set，而abstract rule不变，为了便捷用了list

        self.question_rule: list[_QuestionRule] = []  # 用于存储question转化成的rule，不干涉正常流程，不参与select等。

        self._var_counter = 0

        self._args = args

    def _read_rules(self, path: str) -> list[Rule]:
        """传入一个dir或文件，读取整个文件夹下面所有的文件或单个文件，文件格式需要py或yaml。TODO: 到时候需要约定字符串书写格式"""
        raise NotImplementedError

    def add_rule(self, rule: Rule) -> None:
        """可能用不到的函数，添加rule"""
        warnings.warn("暂时无法生效，当允许运行时增加rule这个feature时，需要在SelectionStrategy中加入add_rule、和对RuleCheckRule"
                      "酌情调整", stacklevel=2)
        if rule not in self.rules:
            splited_rules = self._split_and_rename_rule(rule)
            splited_rules = [self._preprocess_rule(rule) for rule in splited_rules]

            self.rules.extend(splited_rules)

    def get_rules(self) -> list[Rule]:
        """取出正在使用的所有rule，可能用于一些日志追踪等"""
        if self.initial_sign:
            return list(self.cur_rules)

        warnings.warn("Rule base has not been initialized yet.", stacklevel=2)
        return [r for r in self.rules if not isinstance(r, _QuestionRule)]

    def get_question_rules(self) -> list[_QuestionRule]:
        """取出所有由question转化来的规则"""
        return self.question_rule

    def _select_rules_from_current_question(self, question: Question, topn: int | None = None) -> list[Rule]:
        """
        根据当前问题的前提或目标问题选择一组规则。
        可选地，通过 'topn' 参数限制选择的规则数量。
        """
        # 由于选前k个而需要list或tuple一下  TODO: 另外：暂时将所有规则视为可能相关的规则，以后可以添加过滤逻辑或排序什么的。
        all_rules = list(self.rules)

        # 如果没有指定限制则返回所有规则。
        if topn is None or topn == -1 or topn >= len(all_rules):
            return all_rules

        return all_rules[:topn]

    def initial_rule_base(self, question: Question, topn: int | None = None) -> None:
        """作为整个解题流程开始前的一次筛选，需要选择充足的规则以免无法成功。可能Rule中本身带有和领域相关的标签"""
        if question.question:
            question_r = _QuestionRule.from_parts(head=Assertion.from_parts(_QuestionRule.QUESTION_SOLVED_FLAG, true_const),
                               body=question.question, name=_QuestionRule.QUESTIONRULE_NAME)
            splited = self._split_and_rename_rule(question_r)
            self.question_rule.extend(splited)

        selected_rules = self._select_rules_from_current_question(question, topn)
        self.cur_rules = [self._preprocess_rule(r) for r in selected_rules]
        self.initial_sign = True

    def reset_rule_base(self) -> None:
        """
        将RuleBase重置为其预初始化状态。清除所有活动规则并将initial_sign设置为False
        """
        self.cur_rules.clear()
        self.initial_sign = False

    def _preprocess_rule(self, rule: Rule) -> Rule:
        return self._rename_rule_vars(rule)

    def _rename_rule_vars(self, rule: Rule) -> Rule:
        """调用_random_variable_name对规则中的变量重命名"""
        var_map: dict[str, Variable] = {}  # 仅作为临时工作区
        new_head = self._generate_renamed_item(rule.head, var_map)
        new_body = self._generate_renamed_item(rule.body, var_map)

        return rule.replace(head=new_head, body=new_body)

    def _split_and_rename_rule[T1: Rule](self, rule: T1) -> Sequence[T1]:
        """给没有命名的规则一个代称，并处理 DNF 拆分"""
        origin_name = rule.name or f"rule_{self.rule_suffix}"
        self.rule_suffix += 1

        rule_spliter = RuleSafetyProcesser()
        splited_rules = rule_spliter.split_rule_and_process_safety(rule)

        if len(splited_rules) == 1:
            return splited_rules

        result = []
        for idx, single_rule in enumerate(splited_rules):
            new_name = f"{origin_name}_{idx + 1}"
            result.append(single_rule.replace(name=new_name))

        return result

    @overload
    def _generate_renamed_item(self, item: Variable, var_map: dict[str, Variable]) -> Variable: ...
    @overload
    def _generate_renamed_item(self, item: Constant, var_map: dict[str, Variable]) -> Constant: ...
    @overload
    def _generate_renamed_item(self, item: CompoundTerm, var_map: dict[str, Variable]) -> CompoundTerm: ...
    @overload
    def _generate_renamed_item(self, item: Assertion, var_map: dict[str, Variable]) -> Assertion: ...
    @overload
    def _generate_renamed_item(self, item: Formula, var_map: dict[str, Variable]) -> Formula: ...
    @overload
    def _generate_renamed_item(self, item: None, var_map: dict[str, Variable]) -> None: ...

    def _generate_renamed_item(self,
                               item: Formula | Assertion | CompoundTerm | Variable | Constant | None,
                               var_map: dict[str, Variable]) -> (
            Formula | Assertion | CompoundTerm | Variable | Constant | None):
        if isinstance(item, Variable):
            if item.name not in var_map:
                new_name = f"_v{self._var_counter}"
                self._var_counter += 1
                var_map[item.name] = item.create_renamed_variable(new_name)
                # risk: 两条规则里如果都用到了x，然后使用者使用了同一个x的instance，
                # 我们是否有理由认为它俩是一个x？（我认为不合理，所以我们应当不管instance，而只是取它的value本身。但这样会不会给使用者带来困惑？
                # 他可能刻意用了同一个instance，甚至在里面存了一些自定义的信息。但我们可能是直接丢弃然后换个了新名字新地址）
            return var_map[item.name]

        if isinstance(item, Constant):
            return item

        if isinstance(item, CompoundTerm):
            return CompoundTerm.from_parts(
                item.operator,
                tuple(self._generate_renamed_item(arg, var_map) for arg in item.arguments),
            )

        if isinstance(item, Assertion):
            return Assertion.from_parts(
                self._generate_renamed_item(item.lhs, var_map),
                self._generate_renamed_item(item.rhs, var_map),
            )

        if isinstance(item, Formula):
            return Formula(
                self._generate_renamed_item(item.formula_left, var_map),
                item.connective,
                self._generate_renamed_item(item.formula_right, var_map),
            )

        if item is None:
            return None

        raise ValueError(f"Unknown item type: {type(item)}")

    def __str__(self) -> str:
        rule_count = len(self.rules)

        show_topn = 5

        # 展示前5条规则
        preview_rules = ', '.join(str(rule) for rule in list(self.rules)[:5])
        if rule_count > show_topn:
            preview_rules += "..."

        return f"RuleBase with {rule_count} rules. First 5 rules: [{preview_rules}]"
