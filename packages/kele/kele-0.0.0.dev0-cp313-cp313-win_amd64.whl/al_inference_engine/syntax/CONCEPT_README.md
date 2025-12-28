# 概念（Concept）子集关系与类型校验说明

本引擎已支持 **概念的从属（子集）关系**，并在 Term（CompoundTerm）、Operator 等处的类型校验中自动考虑从属关系。

## 一、为什么需要子集关系？
在实际问题中，概念存在层级：如 `int ⊆ real`、`rational ⊆ real`。当某算子参数期望 `real`，传入 `int` 应被视为 **类型兼容**。

## 二、核心特性
- **O(1) 查询**：内部维护传递闭包 `_ancestors_inclusive / _descendants_inclusive`，`c1 ⊆ c2` 判定近似 O(1)。
- **增量更新**：录入一条 `child ⊆ parent` 后，自动更新所有相关祖先/后代的闭包集合。
- **通配概念**：若存在 `FREEVARANY_CONCEPT`，与其比较视为兼容。

## 三、用户友好录入方式（任选其一或组合）
1) **单条**：
由Concept类维护的函数
```python
Concept.add_subsumption("int", "real")
```
2) **批量列表**：
外部对add_subsumption的封装和调用
```python
add_subsumptions([
    ("int", "real"),
    ("rational", "real"),
])
```
3) **映射（子 -> 父列表）**：
外部对add_subsumption的封装和调用
```python
add_subsumptions_from_mapping({
    "int": ["real"],
    "rational": ["real"],
})
```
4) **字符串 DSL**（支持 `⊆` 与 `<=`，分隔：逗号/分号/换行）：
外部对add_subsumption的封装和调用
```python
add_subsumptions_from_string("""
    int ⊆ real, rational <= real;
    positive_int <= int
""")
```
5) **构造时指定父概念**：
```python
Concept("int", parents=["real"])
```
6) **链式设置父概念**：
```python
Concept("int").set_parents(["real"])
```

> 注：以上 API 都可混用，重复声明会被自动去重处理。

## 四、Term/Operator 的类型校验如何生效？
- **Operator** 定义入参/出参概念：
```python
plus = Operator("plus", input_concepts=["real", "real"], output_concept="real")
```
- **CompoundTerm** 构造时校验：
  - 若参数是 `Constant`，检查 `arg.belong_concept ⊆ 期望概念`；
  - 若参数是 `CompoundTerm`，检查 `arg.operator.output_concept ⊆ 期望概念`；
  - 若为 `HashableAndStringable`（如原始字面量），会被转换为 `Constant` 再校验。
- **子集规则自动生效**：如果期望 `real`，传 `int` 或 `positive_int`（且 `positive_int ⊆ int ⊆ real`）均合法。

## 五、示例
```python
Real = Concept("real")
Int = Concept("int", parents=["real"])
PosInt = Concept("positive_int", parents=["int"])

to_real = Operator("to_real", input_concepts=["int"], output_concept="real")

# 期望 int，传 positive_int 也可（因 positive_int ⊆ int）
t1 = CompoundTerm("to_real", [Constant(5, "positive_int")])  # 通过

t2 = CompoundTerm("to_real", [Constant(5, "real")])  # 抛出异常

register_concept_relations("int ⊆ real")

# 试图注册逆向边将报错
try:
    Concept.add_subsumption("real", "int")
except ValueError as e:
    print("阻止互为子集：", e)
```

## 六、跨模块/函数注册入口（不仅限于 Concept 声明）

除了在 `Concept` 上调用外，你也可以在任何地方通过以下入口录入子集关系：

### 1) 全局函数
```python
register_concept_subsumptions([("rational","real")])

register_concept_relations({
    "positive_int": ["int"],     # 映射：子 -> [父...]
    "int": ["real"],
})

register_concept_relations("int ⊆ real; positive_int <= int")  # 字符串 DSL
```

### 2) 装饰器（定义时注册）
```python
@with_concept_relations("int ⊆ real; rational <= real")
def setup_domain(): ...
```

### 3) 上下文管理器（进入作用域时注册）
```python
from base_classes import concept_relation_scope

with concept_relation_scope("""int ⊆ real
rational <= real"""):
    # 在该作用域内立即可用（注册是全局幂等的）
    ...
```
