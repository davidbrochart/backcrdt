use std::cell::{RefCell, RefMut};
use std::collections::HashMap;
use std::path::Path;
use bytes::Bytes;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyInt, PyList, PyString, PyTuple};
use pyo3::exceptions::{PyRuntimeError, PyTypeError, PyValueError};

fn py_to_value(value: &Bound<'_, PyAny>) -> PyResult<crate::lib0::Value> {
    use crate::lib0::Number;

    if value.is_none() {
        return Ok(crate::lib0::Value::Null);
    }
    if let Ok(b) = value.extract::<bool>() {
        return Ok(crate::lib0::Value::Bool(b));
    }
    if let Ok(i) = value.extract::<i64>() {
        return Ok(crate::lib0::Value::Number(Number::Int(i)));
    }
    if let Ok(f) = value.extract::<f64>() {
        return Ok(crate::lib0::Value::Number(Number::Float(f)));
    }
    if let Ok(s) = value.extract::<String>() {
        return Ok(crate::lib0::Value::String(s));
    }
    if let Ok(list) = value.cast::<PyList>() {
        let mut items = Vec::with_capacity(list.len());
        for item in list.iter() {
            items.push(py_to_value(&item)?);
        }
        return Ok(crate::lib0::Value::Array(items));
    }
    if let Ok(tuple) = value.cast::<PyTuple>() {
        let mut items = Vec::with_capacity(tuple.len());
        for item in tuple.iter() {
            items.push(py_to_value(&item)?);
        }
        return Ok(crate::lib0::Value::Array(items));
    }
    if let Ok(dict) = value.cast::<PyDict>() {
        let mut map = HashMap::new();
        for (key, val) in dict.iter() {
            let k: String = key.extract()?;
            map.insert(k, py_to_value(&val)?);
        }
        return Ok(crate::lib0::Value::Object(map));
    }
    if let Ok(b) = value.extract::<Vec<u8>>() {
        return Ok(crate::lib0::Value::Bytes(Bytes::from(b)));
    }
    Err(PyTypeError::new_err(format!("Unsupported type: {}", value.get_type().name()?)))
}

fn py_to_in(value: &Bound<'_, PyAny>) -> PyResult<crate::In> {
    py_to_value(value).map(crate::In::Value)
}

fn value_to_py<'py>(value: &crate::lib0::Value, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
    match value {
        crate::lib0::Value::Null | crate::lib0::Value::Undefined => Ok(py.None().into_bound(py)),
        crate::lib0::Value::Bool(b) => {
            let v = pyo3::IntoPyObject::into_pyobject(*b, py)?;
            Ok((*v).clone().into_any())
        }
        crate::lib0::Value::Number(crate::lib0::Number::Int(i)) => {
            let v = pyo3::IntoPyObject::into_pyobject(*i, py)?;
            Ok((*v).clone().into_any())
        }
        crate::lib0::Value::Number(crate::lib0::Number::Float(f)) => {
            let v = pyo3::IntoPyObject::into_pyobject(*f, py)?;
            Ok((*v).clone().into_any())
        }
        crate::lib0::Value::String(s) => {
            let v = pyo3::IntoPyObject::into_pyobject(s.clone(), py)?;
            Ok((*v).clone().into_any())
        }
        crate::lib0::Value::Array(arr) => {
            let list = PyList::empty(py);
            for item in arr {
                let v = value_to_py(item, py)?;
                list.append(&v)?;
            }
            Ok(list.into_any())
        }
        crate::lib0::Value::Object(map) => {
            let dict = PyDict::new(py);
            for (k, v) in map {
                let val = value_to_py(v, py)?;
                dict.set_item(k.as_str(), val)?;
            }
            Ok(dict.into_any())
        }
        crate::lib0::Value::Bytes(b) => Ok(PyBytes::new(py, b).into_any()),
    }
}

pub enum Cell<'a, T> {
    Owned(T),
    Borrowed(&'a T),
}

impl<'a, T> AsRef<T> for Cell<'a, T> {
    fn as_ref(&self) -> &T {
        match self {
            Cell::Owned(v) => v,
            Cell::Borrowed(v) => *v,
        }
    }
}

impl<'a, T> AsMut<T> for Cell<'a, T> {
    fn as_mut(&mut self) -> &mut T {
        match self {
            Cell::Owned(v) => v,
            Cell::Borrowed(_) => {
                panic!("Transactions executed in context of observer callbacks cannot be used to modify document structure")
            }
        }
    }
}

#[pyclass(unsendable)]
pub struct _Transaction(RefCell<Option<Cell<'static, Transaction<'static>>>>);

impl<'doc> From<Transaction<'doc>> for _Transaction {
    fn from(txn: Transaction<'doc>) -> Self {
        let t: Transaction<'static> = unsafe { std::mem::transmute(txn) };
        _Transaction(RefCell::from(Some(Cell::Owned(t))))
    }
}

impl<'doc> From<&Transaction<'doc>> for _Transaction {
    fn from(txn: &Transaction<'doc>) -> Self {
        let t: &Transaction<'static> = unsafe { std::mem::transmute(txn) };
        _Transaction(RefCell::from(Some(Cell::Borrowed(t))))
    }
}

impl _Transaction {
    pub fn transaction(&self) -> RefMut<'_, Option<Cell<'static, Transaction<'static>>>> {
        self.0.borrow_mut()
    }
}

#[pymethods]
impl _Transaction {
    pub fn commit(&mut self, py: Python<'_>) -> PyResult<()> {
        //self.transaction().as_mut().unwrap().as_mut().commit(None).unwrap();
        let mut guard = self.transaction();
        let cell = guard.take().expect("Transaction already consumed");
        match cell {
            Cell::Owned(txn) => { txn.commit(None).unwrap(); }
            Cell::Borrowed(_) => {
                panic!("Cannot commit a borrowed transaction");
            }
        }
        // Check if any Python exception was raised during commit (e.g., in callbacks)
        if let Some(err) = pyo3::PyErr::take(py) {
            return Err(err);
        }
        Ok(())
    }

    pub fn drop(&self) {
        self.0.replace(None);
    }

    fn get_update(&mut self) -> PyResult<Vec<u8>> {
        let mut _t = self.transaction();
        let t = _t.as_mut().unwrap().as_mut();
        t.diff_update(&StateVector::default(), Encoding::V1)
            .map_err(|e| PyRuntimeError::new_err(format!("Cannot get update: {}", e)))
    }

    fn apply_update(&mut self, update: &Bound<'_, PyBytes>) -> PyResult<()> {
        let mut _t = self.transaction();
        let t = _t.as_mut().unwrap().as_mut();
        t.apply_update(update.as_bytes(), Encoding::V1)
            .map_err(|e| PyRuntimeError::new_err(format!("Cannot apply update: {}", e)))
    }

    fn mount_text(&self, py: Python<'_>, name: &str, multi_doc: &Bound<'_, _MultiDoc>, doc_id: &str) -> PyResult<Py<_Text>> {
        let text: Unmounted<Text> = Unmounted::root(name.to_owned());
        let pytext: Py<_Text> = Py::new(py, _Text::from(text, multi_doc.clone().unbind(), doc_id.to_owned()))?;
        Ok(pytext)
    }

    fn mount_map(&self, py: Python<'_>, name: &str, multi_doc: &Bound<'_, _MultiDoc>, doc_id: &str) -> PyResult<Py<_Map>> {
        let map: Unmounted<Map> = Unmounted::root(name.to_owned());
        let pymap: Py<_Map> = Py::new(py, _Map::from(map, multi_doc.clone().unbind(), doc_id.to_owned()))?;
        Ok(pymap)
    }
}

#[pyclass(unsendable)]
pub struct _Text {
    pub text: Unmounted<Text>,
    pub multi_doc: Py<_MultiDoc>,
    pub doc_id: String,
}

impl _Text {
    pub fn from(text: Unmounted<Text>, multi_doc: Py<_MultiDoc>, doc_id: String) -> Self {
        _Text { text, multi_doc, doc_id }
    }
}

#[pymethods]
impl _Text {
    fn to_string<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyString>> {
        let multi_doc = self.multi_doc.borrow(py);
        let txn = multi_doc
            .multi_doc
            .transact(&self.doc_id)
            .map_err(|e| PyRuntimeError::new_err(format!("Cannot create transaction: {}", e)))?;
        let text = self
            .text
            .mount(&txn)
            .map_err(|e| PyRuntimeError::new_err(format!("Cannot mount text: {}", e)))?;
        let s = text.to_string();
        Ok(PyString::new(py, &s))
    }

    fn insert(&self, txn: &mut _Transaction, index: usize, chunk: &str) -> PyResult<()> {
        let mut _t = txn.transaction();
        let mut t = _t.as_mut().unwrap().as_mut();
        let mut text = self
            .text
            .mount_mut(&mut t)
            .map_err(|e| PyRuntimeError::new_err(format!("Cannot mount text: {}", e)))?;
        text.insert(index, chunk)
            .map_err(|e| PyRuntimeError::new_err(format!("Cannot insert into text: {}", e)))?;
        Ok(())
    }
}

#[pyclass(unsendable)]
pub struct _Map{
    pub map: Unmounted<Map>,
    pub multi_doc: Py<_MultiDoc>,
    pub doc_id: String,
}

impl _Map {
    pub fn from(map: Unmounted<Map>, multi_doc: Py<_MultiDoc>, doc_id: String) -> Self {
        _Map { map, multi_doc, doc_id }
    }
}

#[pymethods]
impl _Map {
    fn insert<'py>(&self, txn: &mut _Transaction, key: &str, value: &Bound<'_, PyAny>) -> PyResult<()> {
        let mut _t = txn.transaction();
        let mut t = _t.as_mut().unwrap().as_mut();
        let mut map = self
            .map
            .mount_mut(&mut t)
            .map_err(|e| PyRuntimeError::new_err(format!("Cannot mount map: {}", e)))?;
        let in_val = py_to_in(value)?;
        let _ = map.insert(key, in_val);
        Ok(())
    }

    fn to_py<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let multi_doc = self.multi_doc.borrow(py);
        let txn = multi_doc
            .multi_doc
            .transact(&self.doc_id)
            .map_err(|e| PyRuntimeError::new_err(format!("Cannot create transaction: {}", e)))?;
        let map = self
            .map
            .mount(&txn)
            .map_err(|e| PyRuntimeError::new_err(format!("Cannot mount map: {}", e)))?;
        let value = map
            .to_value()
            .map_err(|e| PyRuntimeError::new_err(format!("Cannot get value: {}", e)))?;
        match value {
            crate::lib0::Value::Object(obj) => {
                let dict = PyDict::new(py);
                for (k, v) in &obj {
                    let val = value_to_py(v, py)?;
                    dict.set_item(k.as_str(), val)?;
                }
                Ok(dict)
            }
            _ => {
                let dict = PyDict::new(py);
                Ok(dict)
            }
        }
    }

    fn insert_text_prelim<'py>(
        &self,
        py: Python<'py>,
        txn: &mut _Transaction,
        key: &str,
    ) -> PyResult<Py<_Text>> {
        let mut _t = txn.transaction();
        let mut t = _t.as_mut().unwrap().as_mut();
        let mut map = self
            .map
            .mount_mut(&mut t)
            .map_err(|e| PyRuntimeError::new_err(format!("Cannot mount map: {}", e)))?;
        let text: Unmounted<Text> = map
            .insert(key, crate::types::text::TextPrelim::default())
            .map_err(|e| PyRuntimeError::new_err(format!("Cannot insert text: {}", e)))?;
        let py_text = Py::new(py, _Text::from(text, self.multi_doc.clone_ref(py), self.doc_id.clone()))?;
        Ok(py_text)
    }
}

//#[pymethods]
//impl _Map {
//    fn to_string<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyString>> {
//        let multi_doc = self.multi_doc.borrow(py);
//        let txn = multi_doc
//            .multi_doc
//            .transact(&self.doc_id)
//            .map_err(|e| PyRuntimeError::new_err(format!("Cannot create transaction: {}", e)))?;
//        let map = self
//            .map
//            .mount(&txn)
//            .map_err(|e| PyRuntimeError::new_err(format!("Cannot mount map: {}", e)))?;
//        let s = map.to_string();
//        Ok(PyString::new(py, &s))
//    }
//}

#[pyclass]
pub struct _MultiDoc {
    pub multi_doc: MultiDoc,
}

impl _MultiDoc {
    pub fn from(multi_doc: MultiDoc) -> Self {
        _MultiDoc { multi_doc }
    }
}

#[pymethods]
impl _MultiDoc {
    #[new]
    fn new(client_id: &Bound<'_, PyAny>, max_dbs: u32, map_size: usize, dir_path: &str) -> PyResult<Self> {
        let _client_id: Option<ClientID>;
        if client_id.is_none() {
            _client_id = None;
        } else {
            let _client_id_int: u32 = client_id.cast::<PyInt>()
                .map_err(|_| PyValueError::new_err("client_id must be an integer"))?
                .extract()
                .map_err(|_| PyValueError::new_err("client_id must be a valid u32"))?;
            _client_id = ClientID::new(_client_id_int.into());
        }
        let env = crate::lmdb::Env::builder()
            .max_dbs(max_dbs)
            .map_size(map_size)
            .open(Path::new(dir_path), 0o600)
            .unwrap();
        let multi_doc = MultiDoc::new(env, _client_id);
        Ok(_MultiDoc { multi_doc })
    }

    fn create_transaction(&self, py: Python<'_>, doc_id: &str) -> PyResult<Py<_Transaction>> {
        let result = self.multi_doc.transact_mut(&doc_id);
        match result {
            Ok(txn) => {
                let t: Py<_Transaction> = Py::new(py, _Transaction::from(txn))?;
                return Ok(t);
            },
            Err(e) => {
                eprintln!("Error: {}", e);
                return Err(PyRuntimeError::new_err("Already in a transaction"));
            }
        }
    }
}

#[pymodule]
fn _backcrdt(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<_MultiDoc>()?;
    m.add_class::<_Transaction>()?;
    m.add_class::<_Text>()?;
    m.add_class::<_Map>()?;
    Ok(())
}
