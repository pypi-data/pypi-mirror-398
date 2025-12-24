//! Utility functions
//!

/// Computes the polynomial $a_n x^n + a_{n-1}x^{n-1} + \cdots + a_1 x + a_0$ for given $x$.
///
/// # Arguments
/// - `coes` The coefficients vector $(a_0, a_1, \cdots, a_{n-1}, a_n)$
pub(crate) fn evalpoly(coes: &[f64], x: f64) -> f64 {
    coes.iter().rev().fold(0.0, |acc, coe| acc.mul_add(x, *coe))
}

#[cfg(test)]
macro_rules! assert_approx_eq {
    ($a:expr, $b:expr, $eps:expr) => {
        assert!(($a - $b).abs() < $eps, "assertion failed: `(left !== right)` \n left: `{:?}`, \n right: `{:?}`, \n diff: `{:?}`", $a, $b, ($a - $b).abs());
    };
}

#[cfg(test)]
pub(crate) use assert_approx_eq;
