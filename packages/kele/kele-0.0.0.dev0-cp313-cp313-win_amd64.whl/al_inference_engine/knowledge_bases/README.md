# 文字录入事实/规则库的设计文档

## FactBase

### 1. 概述

本设计针对知识推理系统中“事实库”（FactBase）提供一种**基于 YAML** 的文本存储格式。每条事实（Fact）以字符串形式录入，通过parser解析，
辅以元数据（Metadata）扩展。**Concepts** 与 **Operators** 在 Facts 部分声明前定义，确保所有使用到的概念与运算符均已定义、符合约束。

---

### 二、文档结构

```text
├─ Concepts:         # 列表，每项为一个概念定义
│     ├─ id          # 概念唯一标识，如 C001
│     ├─ name        # 概念名称，如 Person  # TODO: 后面可能会增加概念从属关系的录入
│     └─ description # 概念描述
│
├─ Operators:        # 列表，每项为一个运算符定义
│     ├─ id          # 运算符 ID，如 OP001
│     ├─ symbol      # 运算符符号或名称，如 born_in
│     ├─ input_type  # 输入约束，指定 subject/object 所属的 concept ID，列表
│     ├─ output_type # 输出约束，指定 subject/object 所属的 concept ID，仅有一个
│     └─ description # 运算符描述
│
└─ Facts:            # 列表，事实条目
      ├─ FactID      # 唯一 ID，如 F001
      ├─ content     # 事实内容，使用自然语言
      ├─ Metadata    # 可选，具体信息自由调整，如存放来源、时间、可信度等信息，可能不会被读入或需要自行在引擎上二次开发
      └─ description # 事实描述
```

---
### 三、字段详解

1. **Concepts**

   * **id**：建议`^C\d{3,}$` 格式，唯一且不可重复。
   * **name**：人类可读名称。
   * **description**：可选，对该概念的补充说明。

2. **Operators**

   * **id**：建议`^O\d{3,}$` 格式，唯一。
   * **symbol**：运算符或关系名。
   * **input_type**：可接受的概念 ID 列表或单值。
   * **output_type**：可接受的概念 ID 列表或单值。
   * **description**：可选。

3. **Facts**
   * **FactID**：格式 `^F\d{4,}$`。
   * **content**：字符串，其中使用到的operator必须是已声明的 Operator。
   * **Metadata**：可选。
   * **description**：可选。

---
### 四、示例

```yaml
# ───────────────────────────────────────────────────────────────────────────
# 顶层定义：先声明 Concepts（事实用到的实体/类型），再声明 Operators（可用的关系/运算符），最后才是具体的 Fact
# ───────────────────────────────────────────────────────────────────────────

# ───────────────────────────────────────────────────────────────────────────
# 下面是概念（concept）条目，概念必须提供概念名称
# ───────────────────────────────────────────────────────────────────────────
Concepts:
  # 每个 concept 有唯一 ID、名称及可选说明
  - id: C001
    name: "Person"
    description: "表示人类个体"
  - id: C002
    name: "Location"
    description: "地理位置"
  - id: C003
    name: "Organization"
  - id: C004
    name: "Bool"
# ───────────────────────────────────────────────────────────────────────────
# 下面是算子（operator）条目，仅允许使用上面定义过的concept
# ───────────────────────────────────────────────────────────────────────────
Operators:
  # 每个 operator 有唯一 ID、符号/名称、输入输出类型约束
  - id: OP001
    symbol: "born_in"
    input_type: 
      - C001
    output_type: C002
    description: "某人出生于何地"
  - id: OP002
    symbol: "membership"
    input_type: 
      - C001
      - C003
    output_type: C004
    description: "某人是否为组织成员"
# ───────────────────────────────────────────────────────────────────────────
# 下面是事实条目，仅允许使用上面定义过的operator
# ───────────────────────────────────────────────────────────────────────────
Facts:
  - FactID: F0001
    content: "born_in (Albert_Einstein) = German Empire"
    Metadata:
      source: "wikipedia.org/Albert_Einstein"
      created_at: "2025-07-10"
    description: "爱因斯坦出生于德国"
```


### 五、具体的读取、解析、校验流程介绍
work in process
