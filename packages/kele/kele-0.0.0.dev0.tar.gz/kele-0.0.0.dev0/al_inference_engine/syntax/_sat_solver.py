from __future__ import annotations

from typing import TYPE_CHECKING, cast

from bidict import bidict

from al_inference_engine.syntax import Assertion, Formula, FACT_TYPE, Rule, Concept, Constant
from pysat.formula import CNF
from pysat.solvers import Solver

atom_to_var: bidict[Assertion, int] = bidict()
cnf = CNF()


def _get_var_for_assertion(assertion: Assertion) -> int:
    if assertion not in atom_to_var:
        vid = len(atom_to_var) + 1
        atom_to_var[assertion] = vid
        return vid  # hack: 理想情况下应该写atom_to_var[assertion]，但此时assertion的hash太慢了
    return atom_to_var[assertion]


def to_pysat_cnf(facts: list[FACT_TYPE]) -> list[list[int]]:
    """
    输入已经是处理过cnf的了，只需要同等转换
    :raise ValueError: 如果输入的facts不符合CNF格式
    """  # noqa: DOC501
    pysat_program = []
    for clause in facts:
        if isinstance(clause, Assertion):
            pysat_clause = [_get_var_for_assertion(clause)]
        elif clause.connective == 'OR':
            if TYPE_CHECKING:
                clause.formula_right = cast('FACT_TYPE', clause.formula_right)

            lf = to_pysat_cnf([clause.formula_left])[0]
            rt = to_pysat_cnf([clause.formula_right])[0]

            pysat_clause = lf + rt
        elif clause.connective == 'NOT':
            if TYPE_CHECKING:  # 因为已经转了CNF格式，CNF格式内的NOT只可能出现在Assertion上
                clause.formula_left = cast('Assertion', clause.formula_left)

            if isinstance(clause.formula_left, Assertion):
                pysat_clause = [-_get_var_for_assertion(clause.formula_left)]
            else:  # HACK: 这里确实没必要检查，只是功能初期稳妥一下
                raise TypeError("CNF错误")
        else:
            raise ValueError("CNF转换错误")  # HACK: 这里确实没必要检查，只是功能初期稳妥一下

        pysat_program.append(pysat_clause)

    return pysat_program


def rule_to_cnf(rule: Rule) -> list[list[int]]:
    body = to_pysat_cnf(rule.body_units)
    head = to_pysat_cnf(rule.head_units)
    return head + body  # 只取head为True的情况


# -----------------
# 枚举所有模型并统计 Assertion 的可能取值

def get_models_for_rule(rule: Rule) -> dict[Assertion, list[bool]]:
    """
    对于一个Rule，从bool逻辑的角度找到所有可能的model，对应models变量；
    并具体分析assignment，以判断其中各个assertion是否可能取True或False，对应possible_values。
    HACK: 以后的优化余地是用信息更全面的models控制求解路径，而不是possible_values
    """
    cnf.extend(rule_to_cnf(rule))

    models = []
    possible_values = {atom: [False, False] for atom in atom_to_var}  # (bool, bool)分别表示某assertion是否在某个model中为True或False
    # 若在第一位为True，则表示存在一个model，那个model里此assertion为True；若第二位为True，表明存在一个model，此assertion为False。

    with Solver(name="glucose4", bootstrap_with=cnf) as solver:
        while solver.solve():
            model = solver.get_model()
            assignment = {}
            for atom, vid in atom_to_var.items():
                val = (vid in model)  # PySAT: 正整数 = True, 负整数 = False
                assignment[atom] = val

                possible_values[atom][0 if val else 1] = True

            models.append(assignment)
            # 阻断该model，因为SAT求解器会一个个返回。
            solver.add_clause([-lit for lit in model])

    return possible_values


if __name__ == '__main__':
    Points = Concept("Points")  # 点
    A = Constant("A", Points)
    B = Constant("B", Points)
    C = Constant("C", Points)
    D = Constant("D", Points)
    E = Constant("E", Points)

    a = Assertion(A, B)
    b = Assertion(C, D)
    c = Assertion(E, C)
    d = Assertion(E, D)

    rule = Rule(head=b, body=[a, Formula(c, 'IMPLIES', d)])

    cnf = CNF()
    cnf.extend(rule_to_cnf(rule))  # a → b

    possible_values = get_models_for_rule(rule)

    print("\n每个 Assertion 的可能取值：")  # noqa: T201
    for atom, vals in possible_values.items():
        print(f"{atom}: {vals}")  # noqa: T201  # 示例就print了，也不值得进测试
