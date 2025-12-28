#[macro_export]
macro_rules! percentile_factory {
    ($name:ident, $float_type:ty, $ord_type:ident) => {
        #[pyfunction]
        #[pyo3(name = "percentile")]
        fn $name(sample: Vec<$float_type>, percentile: u8) -> PyResult<$float_type> {
            let wrapped: Vec<$ord_type> = sample.iter().map(|&x| $ord_type(x)).collect();
            let result = ks::percentile(&wrapped, percentile);
            Ok(result.0)
        }
    };
}
