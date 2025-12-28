# KELE Inference Engine

[English](README.md) | [中文](README.zh.md)

<!-- Badges: If services are not configured, badges may show unknown/404; enable as needed. -->
[![License](https://img.shields.io/github/license/USTC-KnowledgeComputingLab/KELE.svg)](LICENSE)
[![Build](https://github.com/USTC-KnowledgeComputingLab/KELE/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/USTC-KnowledgeComputingLab/KELE/actions/workflows/release.yml)
![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://msg-bq.github.io/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Commit Message](https://img.shields.io/badge/commit%20message-style%20guide-yellow)](CONTRIBUTING.md)

---

KELE is a forward-chaining inference engine based on [Assertion Logic](https://link.springer.com/chapter/10.1007/978-3-319-63703-7_9), implementing a subset of the logic.

It supports **term-level facts**, **nested terms**, **equivalence axioms**, and **operators with functions**, and integrates well with modern Python (3.13+).

> ⚠️ **Project status**  \
> Backward compatibility will be considered after the first `0.0.1b` pip release (planned for **2025-12-31**). The repository is under development, so **APIs/directories/docs may change**.

### ✨ Features

- **Term-level facts and reasoning**: term-centric organization and inference, suited for equality knowledge
- **Equivalence axioms**: convenient equivalence expressions with internal maintenance
- **Nested compound terms**: operators can nest to build complex structures
- **Implement functions for operators**: implement functions for operators (e.g., arithmetic, equation solving)

> Implement functions for operators ≈ Prolog meta-predicates / ASP HEX external predicates (not identical semantics, similar usage).

### 🔍 Matching semantics

- **Loose matching**: treat subsumption as "intersection" matching, without input/constraint distinction
- **Concept overlap check**: returns whether there is a non-empty common concept set aligned
- **Mismatch handling**: incompatible

### 🔧 Installation

#### Option A: PyPI (after release)

For now, you can download a built wheel from GitHub Actions.

```bash
pip install kele
```

#### Option B: Build from source

> **Requirements**: Python 3.13+; Rust toolchain (`rustup`); on Windows, MSVC (Visual Studio Build Tools).

```bash
git clone https://github.com/USTC-KnowledgeComputingLab/KELE
cd KELE
uv sync
uv run maturin develop --skip-install  # install rust and MSVC (Windows) beforehand
```

### 🚀 Quick start

> Full example: `examples/relationship_quick_start.py`

```bash
uv run python examples/relationship_quick_start.py
# Output: grandparent relation inference result (forward-chaining demo)
```

### 🧩 Core syntax at a glance

| Type              | Meaning                                     | Example/Hint                                         |
| ----------------- |---------------------------------------------| ---------------------------------------------------- |
| `Concept`         | Group of objects sharing something in common | `Person = Concept("Person")`                        |
| `Constant`        | Object (belongs to concepts)                | `alice = Constant("Alice", Person)`                 |
| `Variable`        | Placeholder in rules/queries                | `X = Variable("X")`                                 |
| `Operator`        | Map a tuple of objects into a single one    | `parent(Person, Person) -> Bool`                     |
| `CompoundTerm`    | Operator + arguments                        | `CompoundTerm(parent, [alice, bob])`                 |
| `Assertion`       | “term = term” assertion                     | `Assertion(..., ...)`           |
| `Formula`         | Combine assertions with AND/OR/…            | `Formula(A, "AND", B)`                              |
| `Rule`            | body → head                                 | `Rule(head=..., body=...)`                  |
| `QueryStructure`  | Query input (premises + question)           | `QueryStructure(premises=[...], question=[...])`     |
| `InferenceEngine` | Engine core                                 | `InferenceEngine(facts=[...], rules=[...])`          |

`examples/relationship_quick_start.py` shows a family-relation inference example, illustrating how the pieces fit together:

1. Define concepts (`Concept`) and operators (`Operator`), such as `Person`, `parent`, `grandparent`.
2. Add initial facts (`Assertion`), e.g. “Bob is Alice’s parent”.
3. Write rules (`Rule` + `Formula`), e.g. “if parent(X, Y) and parent(Y, Z), then grandparent(X, Z)”.
4. Build a query (`QueryStructure`) and run `InferenceEngine`.

Example snippet (imports/details omitted; see `examples/relationship_quick_start.py` for a runnable version):

```python
# 1. Define concepts and operators
Person = Concept("Person")
...

# 2. Add facts
alice = Constant("Alice", Person)
...

facts = [
    # parent(Alice, Bob) = True
    Assertion(CompoundTerm(parent, [alice, bob]), true_const),
    ...
]

# 3. Define rules + query
rules = [Rule(
    head=...,
    body=...,
)]

engine = InferenceEngine(facts=facts, rules=rules)
query = QueryStructure(premises=facts, question=[...])  # e.g., ask for grandparent(Alice, X)

print(engine.infer_query(query))
```

### 🧭 Documentation

* **Sphinx docs**:

  * Read the Docs: WIP
  * Build locally: `uv run sphinx-build -b html docs\source docs\build\html`

* **Tutorial**: https://github.com/msg-bq/msg-bq.github.io

### 🗺️ Roadmap

WIP

### 🤝 Contributing

Issues/PRs welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md), and consider enabling `pre-commit`, `ruff`, and `mypy`.

### 🪪 License

This project uses the BSD 3-Clause license. See [LICENSE](LICENSE).
