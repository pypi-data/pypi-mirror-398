use crate::vectorized;
use libm_ext::trig;
use numpy::{PyArrayDyn, PyArrayMethods, PyReadonlyArrayDyn};
use pyo3::prelude::*;
#[cfg(feature = "stub_gen")]
use pyo3_stub_gen::derive::gen_stub_pyfunction;
use rayon::prelude::*;

/// Compute $\sin(\pi x)$ more accurately than `sin(pi*x)`, especially for large `x` (f64).
#[cfg_attr(feature = "stub_gen", gen_stub_pyfunction)]
#[pyfunction]
pub fn sinpi(x: f64) -> f64 {
    trig::sinpi(x)
}

/// Compute $\cos(\pi x)$ more accurately than `cos(pi*x)`, especially for large `x` (f64).
#[cfg_attr(feature = "stub_gen", gen_stub_pyfunction)]
#[pyfunction]
pub fn cospi(x: f64) -> f64 {
    trig::cospi(x)
}

/// Compute $\sin(\pi x)$ more accurately than `sin(pi*x)`, especially for large `x` (f32).
#[cfg_attr(feature = "stub_gen", gen_stub_pyfunction)]
#[pyfunction]
pub fn sinpif(x: f32) -> f32 {
    trig::sinpif(x)
}

/// Compute $\cos(\pi x)$ more accurately than `cos(pi*x)`, especially for large `x` (f32).
#[cfg_attr(feature = "stub_gen", gen_stub_pyfunction)]
#[pyfunction]
pub fn cospif(x: f32) -> f32 {
    trig::cospif(x)
}

/// Simultaneously compute [`sinpi`] and [`cospi`] (f64).
#[cfg_attr(feature = "stub_gen", gen_stub_pyfunction)]
#[pyfunction]
pub fn sincospi(x: f64) -> (f64, f64) {
    trig::sincospi(x)
}

/// Simultaneously compute [`sinpif`] and [`cospif`] (f32).
#[cfg_attr(feature = "stub_gen", gen_stub_pyfunction)]
#[pyfunction]
pub fn sincospif(x: f32) -> (f32, f32) {
    trig::sincospif(x)
}

vectorized!(
    (trig::sinpi, f64),
    (trig::cospi, f64),
    (trig::sinpif, f32),
    (trig::cospif, f32)
);
