## 默认strategy

### SequentialCyclic
按顺序逐个选择规则，每次选1条。

### SequentialCyclicWithPriority
根据规则的priority排序后，按顺序逐个选择规则，每次选1条。

## 创建自己的strategy
1. 创建一个py文件，命名要求为`_<name>_strategy.py`；
2. 继承RuleSelectionStrategy类，并至少声明此Protocol要求的函数；
3. 使用`@register_strategy('<name>')`注册你的策略类，后续即可通过`grounding_rule_strategy`使用策略；
4. 注意调整`grounding_rule_strategy`的类型标注（增加Literal的候选值）。
