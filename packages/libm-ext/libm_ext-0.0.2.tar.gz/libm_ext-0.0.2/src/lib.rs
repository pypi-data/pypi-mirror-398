use pyo3::prelude::*;

pub mod trig;

macro_rules! register_functions {
    // 匹配 a::b::c 形式
    ($m:ident, $($p1:ident::$p2:ident::$func:ident),* $(,)?) => {
        $(
            $m.add_function(wrap_pyfunction!($p1::$p2::$func, $m)?)?;
        )*
    };
    // 匹配 a::b 形式
    ($m:ident, $($p1:ident::$func:ident),* $(,)?) => {
        $(
            $m.add_function(wrap_pyfunction!($p1::$func, $m)?)?;
        )*
    };
    // 匹配单独的 a 形式
    ($m:ident, $($func:ident),* $(,)?) => {
        $(
            $m.add_function(wrap_pyfunction!($func, $m)?)?;
        )*
    };
}

macro_rules! vectorized {
    ($(($p:ident::$func:ident, $typ:ty)),* $(,)?) => {
        $(
            paste::paste! {
                #[cfg_attr(feature = "stub_gen", gen_stub_pyfunction)]
                #[pyfunction]
                pub fn [<$func _vectorized_serial>]<'py>(
                    py: Python<'py>,
                    v: PyReadonlyArrayDyn<'py, $typ>,
                ) -> Bound<'py, PyArrayDyn<$typ>> {
                        let v = v.as_array();
                        let res = v.mapv($p::$func);
                        use numpy::IntoPyArray;
                        res.into_pyarray(py)
                }

                #[cfg_attr(feature = "stub_gen", gen_stub_pyfunction)]
                #[pyfunction]
                pub fn [<$func _vectorized_parallel>]<'py>(
                    py: Python<'py>,
                    v: PyReadonlyArrayDyn<'py, $typ>,
                ) -> PyResult<Bound<'py, PyArrayDyn<$typ>>> {
                    let v_slice = v.as_slice()?;
                    let dims = v.dims();
                    let result_array = unsafe { PyArrayDyn::<$typ>::new(py, dims, false) };
                    let result_slice = unsafe { result_array.as_slice_mut()? };
                    result_slice
                        .par_iter_mut()
                        .zip(v_slice.par_iter())
                        .for_each(|(result, x)| *result = $p::$func(*x));
                    Ok(result_array)
                }
            }
        )*
    };
}

pub(crate) use vectorized;

#[pymodule]
fn _core(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    rayon::ThreadPoolBuilder::new()
        .num_threads(num_cpus::get())
        .build_global()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    register_functions!(
        m,
        trig::sinpi,
        trig::cospi,
        trig::sinpif,
        trig::cospif,
        trig::sincospi,
        trig::sincospif,
        trig::sinpi_vectorized_serial,
        trig::sinpi_vectorized_parallel,
        trig::cospi_vectorized_serial,
        trig::cospi_vectorized_parallel,
        trig::sinpif_vectorized_serial,
        trig::sinpif_vectorized_parallel,
        trig::cospif_vectorized_serial,
        trig::cospif_vectorized_parallel,
    );
    Ok(())
}

#[cfg(feature = "stub_gen")]
pyo3_stub_gen::define_stub_info_gatherer!(stub_info);
