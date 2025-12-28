## 实现功能：等价类的查询
在文件夹equiv_class当中实现了等价类的查询功能：
1. equiv_class.equivalence.Equivalence类，这个类中一共有两个对外的方法，分别为：
    1. update_equiv_class：这个方法用于更新等价类，调用时请传入类型为：list[Assertion | Formula]的列表。此方法没有返回值

    2. query_equivalence：这个方法用于查询一系列事实，调用时请传入Assertion或者list[Assertion]。此方法将返回一个列表，列表中为每个Assertion返回一个对应的list[bool]
    
2. 在test文件夹中添加了少量单例测试，在每次修改代码后使用pytest测试可以初步确定是否有误
