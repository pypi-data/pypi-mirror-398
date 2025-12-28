# KELE 推理引擎

[中文](README.zh.md) | [English](README.md)

<!-- Badges: If services are not configured, badges may show unknown/404; enable as needed. -->
[![License](https://img.shields.io/github/license/USTC-KnowledgeComputingLab/KELE.svg)](LICENSE)
[![Build](https://github.com/USTC-KnowledgeComputingLab/KELE/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/USTC-KnowledgeComputingLab/KELE/actions/workflows/release.yml)
![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://msg-bq.github.io/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Commit Message](https://img.shields.io/badge/commit%20message-style%20guide-yellow)](CONTRIBUTING.md)

---

KELE 是基于[断言逻辑](https://link.springer.com/chapter/10.1007/978-3-319-63703-7_9)的前向式推理引擎，其实现了断言逻辑的一个子集。

支持 **项级事实**、**可嵌套项**、**等词公理**、**含外部实现的算子**，与现代 Python（3.13+）生态良好集成。

> ⚠️ **项目状态**  \
> 预计在 **2025-12-31** 发布首个 `0.0.1b` 版本的 pip 包后，才会逐步承诺向后兼容。目前仓库仍在快速迭代中，**API/目录/文档可能变化**。

### ✨ 特性一览

- **项级事实与推理**：以项（Term）为中心组织与推理，适配等式知识
- **等词公理**：便捷表达等价关系，引擎内部自行维护
- **可嵌套复合项**：允许嵌套项，算子可互相嵌套构成更复杂的复合结构
- **算子的外部实现**：支持使用函数对算子进行自定义“实现”，如加法、解方程等

> 外部实现 ≈ Prolog 元谓词 / ASP 中 HEX external predicate（语义不完全相同，但使用体验相近）。

### 🔧 安装

#### 方式 A：PyPI（发布后启用）

目前可以直接从 action 处获取 build 好的 wheel 文件。

```bash
pip install kele
```

#### 方式 B：从源码构建

> **要求**：Python 3.13+；已安装 Rust toolchain（`rustup`）；Windows 需 MSVC（Visual Studio Build Tools）。

```bash
git clone https://github.com/USTC-KnowledgeComputingLab/KELE
cd KELE
uv sync
uv run maturin develop --skip-install  # 需预先安装 rust 和（Windows 上的）msvc
```

### 🚀 快速开始

> 完整示例见 `examples/relationship_quick_start.py`

```bash
uv run python examples/relationship_quick_start.py
# 输出：祖父母关系的推导结果（用于演示前向式推理）
```

### 🧩 核心语法一览

| 类型                | 作用/含义               | 示例/提示                                            |
| ----------------- |---------------------|--------------------------------------------------|
| `Concept`         | 一类具有共同性质的物体的集合      | `Person = Concept("Person")`                     |
| `Constant`        | 个体常量（属于某些概念）        | `alice = Constant("Alice", Person)`              |
| `Variable`        | 规则/查询中的占位符          | `X = Variable("X")`                              |
| `Operator`        | 将一系列值组成的元组映射到一个值上   | `parent(Person, Person) -> Bool`                 |
| `CompoundTerm`    | 由算子 + 参数构成的复合项      | `CompoundTerm(parent, [alice, bob])`             |
| `Assertion`       | “项 = 项”构成断言         | `Assertion(..., ...)`                     |
| `Formula`         | 用逻辑联结（AND/OR/…）组合断言 | `Formula(A, "AND", B)`                           |
| `Rule`            | 若干前提 ⇒ 结论           | `Rule(head=..., body=...)`              |
| `QueryStructure`  | 一次查询的输入（前提 + 问题）    | `QueryStructure(premises=[...], question=[...])` |
| `InferenceEngine` | 推理引擎核心              | `InferenceEngine(facts=[...], rules=[...])`      |

`examples/relationship_quick_start.py` 提供了一个「亲属关系推理」示例，展示 KELE 的核心块是如何组合在一起的：

1. 定义概念（`Concept`）与算子（`Operator`），例如 `Person`、`parent`、`grandparent`；
2. 写出初始事实（`Assertion`），例如 “Bob 是 Alice 的父/母亲”；
3. 写出规则（`Rule` + `Formula`），例如 “如果 parent(X, Y) 且 parent(Y, Z)，则 grandparent(X, Z)”；
4. 构造查询（`QueryStructure`），并交给 `InferenceEngine` 执行。

示意代码如下（省略了一些导入与细节，完整可运行版本见 `examples/relationship_quick_start.py`）：

```python
# 1. 定义概念与算子
Person = Concept("Person")
...

# 2. 写入事实
alice = Constant("Alice", Person)
...

facts = [
    # parent(Alice, Bob) = True
    Assertion(CompoundTerm(parent, [alice, bob]), true_const),
    ...
]

# 3. 定义规则 + 查询
rules = [Rule(
    head=...,
    body=...,
)]

engine = InferenceEngine(facts=facts, rules=rules)
query = QueryStructure(premises=facts, question=[...])  # 例如询问 grandparent(Alice, X)

print(engine.infer_query(query))
```

### 🧭 文档

* **Sphinx 文档**：

  * Read the Docs：WIP
  * 本地构建：`uv run sphinx-build -b html docs\source docs\build\html`

* **使用教程**：https://github.com/msg-bq/msg-bq.github.io

### 🗺️ Roadmap

WIP

### 🤝 参与贡献

欢迎 Issue/PR！请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，遵循相关规范；建议启用 `pre-commit`、`ruff`、`mypy`。

### 🪪 License

本项目使用 BSD 3-Clause 许可证，详见 [LICENSE](LICENSE)。
