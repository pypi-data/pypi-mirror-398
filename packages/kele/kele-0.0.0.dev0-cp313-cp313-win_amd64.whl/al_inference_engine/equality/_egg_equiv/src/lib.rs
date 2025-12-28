use std::{collections::HashSet};

use egg::{define_language, EGraph, Id, Symbol};
use pyo3::{exceptions::*, prelude::*};
use std::collections::HashMap;
use std::hash::{Hash, Hasher};

define_language! {
    pub enum EngineElem {
        Operator(Symbol),
        Constant(Symbol),
        "CompoundTerm" = CompoundTerm(Box<[Id]>),
        // 要求CompoundTerm的第一个元素是Operator
    }
}


// 用于储存python object，其中实现了hash和eq，调用的是python的hash和eq
struct PyObjKey {
    obj: Py<PyAny>, // 储存的时候使用Py<PyAny>的绑定版本，调用的时候需要unbind
    py_hash: isize, // 缓存 Python hash
}

impl PyObjKey {
    fn new(py: Python<'_>, obj: Py<PyAny>) -> PyResult<Self> {
        let bound = obj.into_bound(py);
        let h = bound.hash()?; // 调用 Python __hash__
        Ok(Self {
            obj: bound.unbind(), // 拿到可存储的 Py<PyAny>
            py_hash: h,
        })
    }
}

impl Clone for PyObjKey {
    fn clone(&self) -> Self {
        Python::attach(|py| Self {
            obj: self.obj.clone_ref(py),
            py_hash: self.py_hash,
        })
    }
}

impl PartialEq for PyObjKey {
    fn eq(&self, other: &Self) -> bool {
        Python::attach(|py| {
            let lhs = self.obj.bind(py);
            let rhs = other.obj.bind(py);
            match lhs.eq(&rhs) { // 调用 Python __eq__
                Ok(b) => b,
                Err(_) => false,
            }
        })
    }
}
impl Eq for PyObjKey {}

impl Hash for PyObjKey {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.py_hash.hash(state); // 使用缓存的 Python hash
    }
}


#[pyclass]
pub struct EggEquivalence {
    egraph: EGraph<EngineElem, ()>,

    /// 1. 每个 e-node (EngineElem) 出现过的所有 SyntaxType 写法
    node_terms: HashMap<EngineElem, HashSet<PyObjKey>>,

    /// 2. 每个 e-node 的“代表元”：第一次见到它时绑定的 SyntaxType
    node_rep: HashMap<EngineElem, Py<PyAny>>,

    trace: bool,
}

impl EggEquivalence {
    pub fn new(trace: bool) -> Self {
        let base: EGraph<EngineElem, ()> = EGraph::default();

        // 按照 trace 决定是否启用 explanations
        let egraph = if trace {
            base.with_explanations_enabled()
        } else {
            base
        };

        Self {
            egraph,
            node_terms: HashMap::new(),
            node_rep: HashMap::new(),
            trace: trace,
        }
    }
    /// 把某个 SyntaxType 的写法记到对应的 EngineElem 底下
    /// 如果engineElem已经存在，那么就加入到对应的hashmap，否则创建新的hashmap并注册engineElem
    fn record_term(&mut self, elem: &EngineElem, term: Bound<'_, PyAny>) {
        // 所有写法都收集起来，给 get_equiv_elem 用
        Python::attach(|py| {
            self.node_terms
                .entry(elem.clone())
                .or_insert_with(HashSet::new)
                .insert(PyObjKey::new(py, term.clone().unbind()).unwrap());
        });

        // 代表元：第一次见到这个 EngineElem 时绑定，不再修改。
        // 之所以有这个问题是因为不同syntaxtype可能对应同一个engineelem，因此需要这样记录
        self.node_rep
            .entry(elem.clone())
            .or_insert_with(|| term.unbind());
    }
    fn add_term_to_egraph(&mut self, py: Python<'_>, obj: Bound<'_, PyAny>) -> PyResult<Id> {
        // 将一个用dict形式表示的term添加到egraph中，并获取它的Id。如果它已经存在，那么直接获取Id
        let type_name = obj.get_type().name()?;

        if type_name == "Constant"{
            let name_obj = obj.getattr("name")?;
            let value = name_obj.str()?.to_str()?.to_owned();
            let belong_obj = obj.getattr("belong_concept")?;
            let belong_concept = belong_obj.str()?.to_str()?.to_owned();
            let constant_name = value + "::" + &belong_concept;  //  TODO: 一些地方有内存优化的余地
            let engine_elem = EngineElem::Constant(Symbol::from(constant_name.clone()));
            if let Some(id) = self.egraph.lookup(engine_elem.clone()) {
                self.record_term(&engine_elem, obj);
                return Ok(id);
            }
            else{
                self.record_term(&engine_elem, obj);
                let id = self.egraph.add(engine_elem);
                return Ok(id)
            }
        }
        if type_name == "Operator"{
            let name_obj = obj.getattr("name")?;
            let value = name_obj.str()?.to_str()?.to_owned();
            let operator_name = value.clone();
            let engine_elem = EngineElem::Operator(Symbol::from(operator_name.clone()));
            if let Some(id) = self.egraph.lookup(engine_elem.clone()) {
                self.record_term(&engine_elem, obj);
                return Ok(id);
            }
            else{
                self.record_term(&engine_elem, obj);
                let id = self.egraph.add(engine_elem);
                return Ok(id)
            }
        }
        if type_name == "CompoundTerm" || type_name == "AtomCompoundTerm"{
            let operator_obj = obj.getattr("operator").unwrap();
            let arguments_obj = obj.getattr("arguments").unwrap();
            let operator_id = self.add_term_to_egraph(py, operator_obj)?;
            let arguments_len = arguments_obj.len().unwrap();
            let mut children_ids: Vec<Id> = Vec::new();
            children_ids.push(operator_id); // CompoundTerm的第一个元素是Operator
            for argument in 0..arguments_len{
                let arg_obj = arguments_obj.get_item(argument).unwrap();
                let arg_id = self.add_term_to_egraph(py, arg_obj)?;
                children_ids.push(arg_id);
            }
            let engine_elem = EngineElem::CompoundTerm(children_ids.into_boxed_slice());
            if let Some(id) = self.egraph.lookup(engine_elem.clone()) {
                self.record_term(&engine_elem, obj);
                return Ok(id);
            }
            else{
                self.record_term(&engine_elem, obj);
                let id = self.egraph.add(engine_elem);
                return Ok(id)
            }
        }
        return Err(PyErr::new::<PyTypeError, _>(format!("Unsupported type: {}", type_name)));
    }
    fn reset(&mut self) {
        // 重新创建一个空的 egraph，并判断是否启用explanations
        let base: EGraph<EngineElem, ()> = EGraph::default();

        // 按照 trace 决定是否启用 explanations
        self.egraph = if self.trace {
            base.with_explanations_enabled()
        } else {
            base
        };

        // 清空辅助映射
        self.node_terms.clear();
        self.node_rep.clear();
    }
}


#[pymethods]
impl EggEquivalence {
    #[new]
    fn py_new(trace: bool) -> Self {
        EggEquivalence::new(trace)
    }
    pub fn add_to_equiv(&mut self, py: Python<'_>, lhs: Bound<'_, PyAny>, rhs: Bound<'_, PyAny>){
        // 将lhs==rhs这个事实添加到egraph中
        let lhs_id = self.add_term_to_egraph(py, lhs).unwrap();
        let rhs_id = self.add_term_to_egraph(py, rhs).unwrap();

        // 如果启用了 trace，则使用带标签的 union 以便后续生成解释
        if self.trace {
            self.egraph.union_trusted(lhs_id, rhs_id, "input");
        } else {
            self.egraph.union(lhs_id, rhs_id);
        }
    }
    pub fn query_equivalence(&mut self, py: Python<'_>, term_l: Bound<'_, PyAny>, term_r: Bound<'_, PyAny>) -> bool {
        // 查询term_l是否等于term_r
        let lhs_id = self.add_term_to_egraph(py, term_l).unwrap();
        let rhs_id = self.add_term_to_egraph(py, term_r).unwrap();

        self.rebuild_egraph(); // 可能发生了add，需要重建

        return self.egraph.find(lhs_id) == self.egraph.find(rhs_id);
    }
    pub fn get_represent_id(&mut self, py: Python<'_>, term: Py<PyAny>) -> String {
        // 获取等价类的Id
        let term_id = self.add_term_to_egraph(py, term.bind(py).clone()).unwrap(); // 将term加入图中从而获得Id
        self.rebuild_egraph(); // 可能发生了add，需要重建
        let class_id = self.egraph.find(term_id);  // 获取e-class的ID

        // 返回 e-class ID 的 index
        class_id.to_string()  // 返回 e-class ID 作为 usize
    }
    pub fn get_represent_elem(&mut self, py: Python<'_>, term: Py<PyAny>) -> Py<PyAny> {
        // 获取等价类的代表元的ID，注意这是一个元素的Id
        let term_id = self.add_term_to_egraph(py, term.bind(py).clone()).unwrap(); // 将term加入图中从而获得Id
        self.rebuild_egraph(); // 可能发生了add，需要重建
        let class_id = self.egraph.find(term_id);
        let result_elem = self.egraph.id_to_node(class_id);
        self.node_rep.get(result_elem).unwrap().clone_ref(py)
    }
    pub fn get_equiv_elem(&mut self, py: Python<'_>, term: Py<PyAny>) -> Vec<Py<PyAny>> {   
        // 获得与一个元素等价的所有元素，返回的是元素的ID列表
        let term_id = self.add_term_to_egraph(py, term.bind(py).clone()).unwrap(); // 将term加入图中从而获得Id
        self.rebuild_egraph(); // 可能发生了add，需要重建
        let class_id = self.egraph.find(term_id); // 获得标准Id
        let eclass = &self.egraph[class_id];  // 获得对应的eclass
        let mut elem_list: Vec<Py<PyAny>> = Vec::new();
        for node in &eclass.nodes {
            if let Some(set) = self.node_terms.get(node) {
                for term_key in set {
                    elem_list.push(term_key.obj.clone_ref(py));
                }
            }
        }
        elem_list
    }    
    pub fn rebuild_egraph(&mut self) {
        // 重建egraph，这个操作通常在进行查询之前调用，维护graph的同余闭包
        if !self.egraph.clean {
            self.egraph.rebuild();
        }
    }
    pub fn clear(&mut self) {
        self.reset();
    }
}

#[pymodule]
fn egg_equiv(_py: Python, m: &Bound<PyModule>) -> PyResult<()> {
    m.add_class::<EggEquivalence>()?;
    Ok(())
}
