use pyo3::prelude::*;


/// Python glue for mokaccino library.
///
#[pymodule]
mod mokaccino {
    use std::mem::take;

    use h3o::CellIndex;
    use mokaccino_rust::prelude::{CNFQueryable, Qid};
    use pyo3::{
        exceptions::PyRuntimeError, prelude::*, types::{PyIterator, PyType}
    };
    #[cfg(feature = "stub-gen")]
    use pyo3_stub_gen::derive::*;

    /// A Mokaccino Query object, representing an interest
    /// in documents matching certain criteria.
    #[derive(Clone)]
    #[cfg_attr(feature = "stub-gen", gen_stub_pyclass)]
    #[pyclass]
    pub struct Query(mokaccino_rust::prelude::Query);


    #[cfg_attr(feature = "stub-gen", gen_stub_pymethods)]
    #[pymethods]
    impl Query {

        /// Parse the given query string into a Query object.
        /// 
        /// See mokaccino documentation for the query syntax, or individual
        /// methods to create Query objects.
        #[classmethod]
        fn parse(_cls: &Bound<'_, PyType>, s: &str) -> PyResult<Self> {
            s.parse::<mokaccino_rust::prelude::Query>()
                .map(|q| Self(q))
                .map_err(|e| PyRuntimeError::new_err(format!("Parse error: {}", e)))
        }

        /// Create a Query that matches documents where field `k` has value `v`.
        /// 
        /// This is the equivalent to parsing the query string `k:v`.
        #[classmethod]
        fn from_kv(_cls: &Bound<'_, PyType>, k: &str, v: &str) -> PyResult<Self> {
            Ok(Self(k.has_value(v)))
        }

        /// Create a Query that matches documents where field `k` has prefix `p`.
        /// 
        /// This is the equivalent to parsing the query string `k:p*`.
        #[classmethod]
        fn from_kprefix(_cls: &Bound<'_, PyType>, k: &str, p: &str) -> PyResult<Self> {
            Ok(Self(k.has_prefix(p)))
        }

        /// Create a Query that matches documents where field `k` as an integer
        /// is lower than the given `v` value.
        /// 
        /// This is the equivalent to parsing the query string `k<v`.
        #[classmethod]
        fn from_klt(_cls: &Bound<'_, PyType>, k: &str, v: i64) -> PyResult<Self> {
            Ok(Self(k.i64_lt(v)))
        }

        /// Create a Query that matches documents where field `k` as an integer
        /// is lower than or equal to the given `v` value.
        /// 
        /// This is the equivalent to parsing the query string `k<=v`.
        #[classmethod]
        fn from_kle(_cls: &Bound<'_, PyType>, k: &str, v: i64) -> PyResult<Self> {
            Ok(Self(k.i64_le(v)))
        }

        /// Create a Query that matches documents where field `k` as an integer
        /// is equal to the given `v` value.
        /// 
        /// This is the equivalent to parsing the query string `k=v`.
        #[classmethod]
        fn from_keq(_cls: &Bound<'_, PyType>, k: &str, v: i64) -> PyResult<Self> {
            Ok(Self(k.i64_eq(v)))
        }

        /// Create a Query that matches documents where field `k` as an integer
        /// is greater than or equal to the given `v` value.
        /// 
        /// This is the equivalent to parsing the query string `k>=v`.
        #[classmethod]
        fn from_kge(_cls: &Bound<'_, PyType>, k: &str, v: i64) -> PyResult<Self> {
            Ok(Self(k.i64_ge(v)))
        }

        /// Create a Query that matches documents where field `k` as an integer
        /// is greater than the given `v` value.
        /// 
        /// This is the equivalent to parsing the query string `k>v`.
        #[classmethod]
        fn from_kgt(_cls: &Bound<'_, PyType>, k: &str, v: i64) -> PyResult<Self> {
            Ok(Self(k.i64_gt(v)))
        }

        /// Create a Query that matches documents where field `k` is a location
        /// inside or equal to the given h3 cell.
        ///
        /// This is the equivalent to parsing the query string `k H3IN cell`.
        ///
        /// The cell must be a valid h3 index hexadecimal string.
        #[classmethod]
        fn from_h3in(_cls: &Bound<'_, PyType>, k: &str, cell: &str) -> PyResult<Self> {
            let cell_index = cell.parse::<CellIndex>().map_err(|e| {
                PyRuntimeError::new_err(format!("Invalid h3 cell index: {}", e))
            })?;
            Ok(Self(k.h3in(cell_index)))
        }

        /// Create a Query that matches documents NOT matching the given Query `q`.
        /// Alternatively, use the `~` operator before a Query object.
        /// 
        /// This is the equivalent to parsing the query string `NOT a:b` , or `NOT ( .. )`.
        #[classmethod]
        fn from_not(_cls: &Bound<'_, PyType>, q: &Self) -> PyResult<Self> {
            Ok(Self(!q.0.clone()))
        }

        /// Create a Query that matches documents matching ALL of the given Queries
        /// Alternatively, use the `&` operator between Query objects.
        /// 
        /// This is the equivalent to parsing the query string `a:b AND c:d AND (..) ...`
        #[classmethod]
        fn from_and(_cls: &Bound<'_, PyType>, iterable: &Bound<'_, PyAny>) -> PyResult<Self> {
            let mut items: Vec<mokaccino_rust::prelude::Query> = vec![];
            for item in PyIterator::from_object(iterable)? {
                let q: Self = item?.extract::<Query>()?;
                items.push(q.0);
            }
            Ok(Self(mokaccino_rust::prelude::Query::from_and(items)))
        }

        /// Create a Query that matches documents matching ANY of the given Queries
        /// Alternatively, use the `|` operator between Query objects.
        /// 
        /// This is the equivalent to parsing the query string `a:b OR c:d OR (..) ...`
        #[classmethod]
        fn from_or(_cls: &Bound<'_, PyType>, iterable: &Bound<'_, PyAny>) -> PyResult<Self> {
            let mut items: Vec<mokaccino_rust::prelude::Query> = vec![];
            for item in PyIterator::from_object(iterable)? {
                let q: Self = item?.extract::<Query>()?;
                items.push(q.0);
            }
            Ok(Self(mokaccino_rust::prelude::Query::from_or(items)))
        }

        fn __str__(&self) -> String{
            self.0.to_string()
        }

        fn __and__(&self, other: Self) -> PyResult<Self> {
            Ok(Self(self.0.clone() & other.0))
        }
 
        fn __or__(&self, other: Self) -> PyResult<Self> {
            Ok(Self(self.0.clone() | other.0))
        }

        fn __invert__(&self) -> PyResult<Self> {
            Ok(Self(! self.0.clone()))
        }


    }

    /// A Mokaccino Document object, representing a flat collection of field-value pairs. (all strings)
    /// There are no contraints on field names or values.
    #[derive(Clone)]
    #[cfg_attr(feature = "stub-gen", gen_stub_pyclass)]
    #[pyclass]
    pub struct Document(mokaccino_rust::prelude::Document);

    #[cfg_attr(feature = "stub-gen", gen_stub_pymethods)]
    #[pymethods]
    impl Document {
        #[new]
        fn new() -> Self {
            Self(mokaccino_rust::prelude::Document::new())
        }

        fn __str__(&self) -> String{
            format!("{:?}" , self.0 )
        }

        /// Return a new Document with the given field set to the given value.
        /// 
        /// This will leave this document empty, so you MUST use the returned value.
        pub fn with_value(&mut self, field: &str, value: &str) -> PyResult<Self> {
            let new_doc = take(&mut self.0).with_value(field, value);
            Ok(Self(new_doc))
        }

        /// Adds the given field,value to the document in place.
        pub fn add_value(&mut self, field: &str, value: &str) -> PyResult<()>{
            let new_doc = take(&mut self.0).with_value(field, value);
            self.0 = new_doc;
            Ok(())
        }

        /// Return a list of (field, value) pairs in this Document.
        pub fn field_values(&self) -> PyResult<Vec<(String, String)>> {
            Ok(self
                .0
                .field_values()
                .map(|(f, v)| (f.to_string(), v.to_string()))
                .collect())
        }

        /// Return a new Document merging this Document with another Document.
        pub fn merge_with(&self, other: &Document) -> PyResult<Self> {
            Ok(Self(self.0.merge_with(&other.0)))
        }
    }

    /// A Mokaccino Percolator object, representing an index of Queries
    /// against which Documents can be percolated.
    #[cfg_attr(feature = "stub-gen", gen_stub_pyclass)]
    #[pyclass]
    pub struct Percolator(mokaccino_rust::prelude::Percolator);

    #[cfg_attr(feature = "stub-gen", gen_stub_pymethods)]
    #[pymethods]
    impl Percolator {
        #[new]
        fn new() -> Self {
            Self(mokaccino_rust::prelude::Percolator::default())
        }

        /// Add a Query to the Percolator, returning its Qid.
        /// 
        /// The Qid can be used to identify the Query later, so you need
        /// to keep track of it in your application.
        fn add_query(&mut self, query: &Query) -> PyResult<Qid> {
            Ok(self.0.add_query(query.0.clone()))
        }

        /// Percolate the given Document against the Percolator,
        /// returning a list of Qids of matching Queries.
        fn percolate_list(&self, document: &Document) -> PyResult<Vec<Qid>> {
            Ok(self.0.percolate(&document.0).collect())
        }

        /// Serialize the Percolator to a JSON string.
        /// This is compatible with the Rust mokaccino library,
        /// allowing to build percolators in one language and use them in the other.
        fn to_json(&self) -> PyResult<String> {
            serde_json::to_string(&self.0).map_err(|e|
                PyRuntimeError::new_err(format!("Serialization error: {}", e))
            )
        }

        /// Deserialize a Percolator from a JSON string.
        #[classmethod]
        fn from_json(_cls: &Bound<'_, PyType>, json_str: &str) -> PyResult<Self> {
            let p: mokaccino_rust::prelude::Percolator = serde_json::from_str(json_str).map_err(|e|
                PyRuntimeError::new_err(format!("Deserialization error: {}", e))
            )?;
            Ok(Self(p))
        }
    }

}

#[cfg(feature = "stub-gen")]
use pyo3_stub_gen::define_stub_info_gatherer;
#[cfg(feature = "stub-gen")]
define_stub_info_gatherer!(stub_info);
