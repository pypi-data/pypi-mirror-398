from al_inference_engine.syntax import Rule
from .builtin_facts import example_assertion_1, example_formula_1

# Example Rules
example_rule_1 = Rule(
    head=example_assertion_1,
    body=example_assertion_1,
    priority=0.1,
)
example_rule_2 = Rule(
    head=example_assertion_1,
    body=example_formula_1,
    priority=0.5,
)
