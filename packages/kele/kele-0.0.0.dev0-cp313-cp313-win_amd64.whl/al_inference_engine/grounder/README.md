# term-level grounding过程
在grounder文件夹中，我们实现了term-level的实例化过程。
## 各文件介绍

```text
├─ grouding.py:    # 整个结构的对外接口，通过实例化其中的Grounder类，并调用grounding_process方法，可以启动grounding过程
│
├─ grouded_rule_ds:
│     │
│     ├─ grounded_class.py:    # 文件中储存了GroundedRule类和GroundedRuleDs类，其中GroundedRule是我们进行grounding的基本单位，承担了unify过程和execute过程的方法
│     │
│     ├─ rule_check.py:        # 文件中有RuleCheckGraph类，这个类承担了构建图的方法
      │
      ├─ _grounded_ds_utils.py:# 包含将Term转化为AtomTerm的方法
      │
      └─ _nodes:               # 文件夹中储存了构建图的节点
            ├─_assertion.py:   # 文件夹中储存了AssertionNode类
            ├─_conn.py:        # 文件夹中储存了ConnectiveNode类
            ├─_op.py:          # 文件夹中储存了OperatorNode类
            ├─_root.py:        # 文件夹中储存了RootNode类
            ├─_rule.py:        # 文件夹中储存了RuleNode类
            ├─_term.py:        # 文件夹中储存了TermNode类
            ├─_tftable.py:     # 储存用于传递index的结构
            ├─_tupletable.py:  # 储存用于记录Variable取值的结构
```

## Node节点介绍

对于任意一个节点，它大致有如下的函数：
1. add_child：自底向上的过程是张图或者树，所以需要连边；
2. exec：每个节点有自己要执行的任务，比如Term要进行unify过程，比如Assertion要进行合并两个Term的变量替换候选值等。目前的名字是exec_*的格式；
3. pass：每个节点要把exec后的信息传递给子节点或某个公共地址，目前的名字是pass_*的格式。
4. _join: exec的一部分，用于合并两组变量替换。例如P(x) = Q(x)这个Assertion，P(x)可能匹配到的是x =1,2,3、Q(x)匹配到的是x = 2,3，那最终只能保留2, 3。如果规则是P(x) = Q(y)，那就要从x=1,2,3和y=2,3合并为(1,2), (1,3), (2, 2)......

## grounding流程介绍
grounding主要分为四个流程。
### 图的构建
首先，给定一个rule，我们会将其转化为一个图，用一个节点来表示一个term（AtomCompundTermNode），一个Assertion（AssertionNode）或者一个逻辑连接词（ConnectiveNode）

具体地，构建图的流程如下：
1. 将输入的规则body部分(常常是一个Formula)拆解为一系列的term，term对应的assertion，以及连接assertion的connective。
2. 将term拆解为**AtomCompoundTerm**，AtomCompoundTerm是这样的term：它的arguments列表里面没有其他term。换句话说，AtomCompoundTerm是**最简单的Term**，不存在复合结构。同时，对于一些本身有复合结构的term，我们**用标记符$F来代替复合结构**，使得它成为AtomCompoundTerm，从而可以按照AtomCompoundTerm来处理，用*AtomCompoundTermNode*来记录这些AtomCompoundTerm
3. AtomCompoundTermNode存在**其中一个是另外一个的子部分**的情况，这种时候，我们会**用一条边**来表示这种结构，这样就记录下了term的复合结构，在代码中，对于每个AtomCompoundTermNode，我们用一个列表记录它的所有子节点。对于最末尾的AtomCompoundTermNode，它会被连接到AssertionNode。
4. 在存在connective的情况下，我们通过将AssertionNode连接到**ConnectiveNode**来记录这个结构
5. 在图结构的末尾，我们连接**RuleNode**，用以表示匹配的终点

### unify过程

接下来，我们需要基于给定的Facts，确定Term中的Variable的可能取值。下面是详细的流程:
1. 每个AtomCompoundTermNode保有一个**freevar_table**表格，用于记录它的variables的可能取值列表
2. 我们类似前面的操作，将事实中出现的term拆解为AtomCompoundTerm(**即复合的term在标记后变成AtomCompoundTerm**)，并且将这些AtomCompoundTerm基于OperatorNode的匹配，传入同一个Operator的AtomCompoundTermNode中。
3. 这些AtomCompoundTerm会作为AtomCompoundTermNode的取值，如果满足下面三个条件
    1. Node对应位置为Variable，此时AtomCompoundTerm在相应位置的取值没有限制
    2. Node对应位置为$F，此时AtomCompoundTerm在相应位置的取值没有限制（Node也不会记录这个取值）
    3. Node对应位置为Constant，此时AtomCompoundTerm在相应位置的取值必须与AtomCompoundTermNode的取值相同
4. 将上面符合条件的AtomCompoundTerm记录在freevar_table表格中，记录方式是记录Node中所有Variable在符合条件的AtomCompoundTerm中的取值。注意，这里的Variable**不包含**复合结构中的Variable（**即$F占位符代替的Term中Variable的取值不会被记录**）

### pass与join过程

上面的unify过程已使得每个Node记录了它自己的freevar_table表格，但是我们期望得到的是一个在这个规则层面的全局freevar_table表格，用于记录所有Node中的Variable的可能取值，并基于这个总表进行后续的检查

于是我们有pass与join过程：

1. 从根节点开始，每个节点将自己的freevar_table和其父节点传递来的freevar_table，一起传递给自己的子节点，由子节点将他们记录下来
2. 上述过程在AssertionNode终止，接着单个AssertionNode合并得到自身的freevar_table，接着groundedrule将进一步计算所有AssertionNode的freevar_table的合并

此过程主要的目的是**去除绑定不一致的结果**，即我们要求在此Rule中同一个Variable的取值必须是一致的（这个要求的合理性基于：Rule通过DNF转化和拆解后已经不再有OR结构）

### check_grounding过程

接下来变量的取值已经记录在AssertionNode中了，我们已经可以开始检查，并将检查结果向下传递到RuleNode了。

具体地有以下步骤
1. AssertionNode获取总freevar_table中的一部分（即涉及到当前AssertionNode使用的Variable的列）
2. AssertionNode将它需要处理的Assertion中的Variable替换为Constant，然后对替换后的Assertion查询是否成立
3. 将1中得到的table拆成TrueTable和FalseTable两部分，记录在TfTable结构中，并向下传递
4. 接着将TfTables传递，每个ConnectiveNode需要依据自身的逻辑连接词（只处理AND, NOT两种，OR在DNF转化和规则拆解之后除去了）得到新的TfTable，

    i. AND的情况下union两侧的TrueTable得到新的TrueTable，其他的组合(TF,FT,FF)两两union得到FalseTable，并继续向下传递

    ii. NOT的情况下交换TrueTable和FalseTable，并继续向下传递

5. 将最后的结果传递给RuleNode，RuleNode基于TfTable中的TrueTable来生成新的事实
