"""
Trigonometric functions for computing sin(πx), cos(πx), and both simultaneously.

This module provides high-precision implementations of:

- :func:`sinpi` - Compute sin(πx)
- :func:`cospi` - Compute cos(πx)
- :func:`sincospi` - Compute both sin(πx) and cos(πx)

Why sinpi and cospi?
--------------------

Computing ``math.sin(math.pi * x)`` directly suffers from two problems:

1. **Representation error**: The constant π cannot be exactly represented in
   floating-point, so ``math.pi * x`` already introduces error before the
   sine computation.

2. **Argument reduction error**: For large ``x``, the standard ``sin`` function
   must reduce the argument modulo 2π, which accumulates significant error.

The ``sinpi(x)`` function avoids both issues by:

- Using argument reduction modulo 2 (exact for floating-point)
- Applying the factor of π inside the polynomial approximation with full precision

Accuracy
--------

- Typically within 1-2 ULP (Units in the Last Place)
- Uses double-double arithmetic for leading polynomial terms

Implementation
--------------

Based on the Julia Standard Library implementation, using minimax polynomial
approximations with double-double arithmetic for the leading terms.
"""

from libm_ext import _core


def sinpi(x: float) -> float:
    r"""
    Compute sin(πx) more accurately than ``math.sin(math.pi * x)``.

    This function computes sin(πx) with high precision, especially for large x
    where the standard approach would accumulate significant error.

    Parameters
    ----------
    x : float
        The input value.

    Returns
    -------
    float
        The value of sin(πx).

    Algorithm
    ---------

    **Step 1: Handle Special Cases**

    - If x is NaN or ±∞, return NaN.
    - If |x| ≥ 2⁵³ (the largest integer representable in f64), x is an even
      integer, so sin(πx) = 0 with the sign of x.

    **Step 2: Argument Reduction**

    Since sin(πx) has period 2, we reduce x to the interval [-1/4, 1/4] where
    the polynomial approximation is most accurate.

    Let n = round(2|x|), then compute the reduced argument:

        r = |x| - n/2 ∈ [-1/4, 1/4]

    The quadrant n mod 4 determines which trigonometric identity to use:

    ======== ============================
    n mod 4  Identity
    ======== ============================
    0        sin(πx) = sin(πr)
    1        sin(πx) = cos(πr)
    2        sin(πx) = -sin(πr)
    3        sin(πx) = -cos(πr)
    ======== ============================

    **Step 3: Polynomial Evaluation**

    For |r| ≤ 1/4, we use minimax polynomials:

    - sin(πr) ≈ r · P(r²) where P is a degree-7 polynomial
    - cos(πr) ≈ Q(r²) where Q is a degree-7 polynomial

    The polynomials are computed using Horner's method with double-double
    arithmetic for the leading terms to achieve nearly 1 ULP accuracy.

    **Step 4: Sign Adjustment**

    Since sin is an odd function, if x < 0, negate the result.

    Examples
    --------
    >>> from libm_ext import sinpi
    >>> sinpi(0.0)
    0.0
    >>> sinpi(0.5)
    1.0
    >>> sinpi(1.0)
    0.0
    >>> sinpi(-0.5)
    -1.0

    Notes
    -----
    - Returns NaN for infinite or NaN inputs.
    - For very large x (|x| ≥ 2⁵³), returns ±0.0.

    See Also
    --------
    cospi : Compute cos(πx)
    sincospi : Compute both sin(πx) and cos(πx)
    """
    return _core.sinpi(x)


def cospi(x: float) -> float:
    r"""
    Compute cos(πx) more accurately than ``math.cos(math.pi * x)``.

    This function computes cos(πx) with high precision, especially for large x
    where the standard approach would accumulate significant error.

    Parameters
    ----------
    x : float
        The input value.

    Returns
    -------
    float
        The value of cos(πx).

    Algorithm
    ---------

    **Step 1: Handle Special Cases**

    - If x is NaN or ±∞, return NaN.
    - If |x| ≥ 2⁵³ (the largest integer representable in f64), x is an even
      integer, so cos(πx) = 1.

    **Step 2: Argument Reduction**

    Since cos(πx) has period 2 and is even (cos(π(-x)) = cos(πx)), we reduce
    |x| to the interval [-1/4, 1/4] where the polynomial approximation is
    most accurate.

    Let n = round(2|x|), then compute the reduced argument:

        r = |x| - n/2 ∈ [-1/4, 1/4]

    The quadrant n mod 4 determines which trigonometric identity to use:

    ======== ============================
    n mod 4  Identity
    ======== ============================
    0        cos(πx) = cos(πr)
    1        cos(πx) = -sin(πr)
    2        cos(πx) = -cos(πr)
    3        cos(πx) = sin(πr)
    ======== ============================

    **Step 3: Polynomial Evaluation**

    For |r| ≤ 1/4, we use minimax polynomials with double-double arithmetic
    for the leading terms.

    Examples
    --------
    >>> from libm_ext import cospi
    >>> cospi(0.0)
    1.0
    >>> cospi(0.5)
    0.0
    >>> cospi(1.0)
    -1.0
    >>> cospi(2.0)
    1.0

    Notes
    -----
    - Returns NaN for infinite or NaN inputs.
    - For very large x (|x| ≥ 2⁵³), returns 1.0.

    See Also
    --------
    sinpi : Compute sin(πx)
    sincospi : Compute both sin(πx) and cos(πx)
    """
    return _core.cospi(x)


def sincospi(x: float) -> tuple[float, float]:
    r"""
    Simultaneously compute sin(πx) and cos(πx).

    This function computes both sin(πx) and cos(πx) in a single call, which is
    more efficient than calling :func:`sinpi` and :func:`cospi` separately since
    the argument reduction only needs to be done once.

    Parameters
    ----------
    x : float
        The input value.

    Returns
    -------
    tuple[float, float]
        A tuple (sin(πx), cos(πx)).

    Algorithm
    ---------

    Uses the same argument reduction as :func:`sinpi` and :func:`cospi`,
    computing both kernel functions and applying the appropriate signs based
    on the quadrant.

    ======== ================= =================
    n mod 4  sin(πx)           cos(πx)
    ======== ================= =================
    0        sin(πr)           cos(πr)
    1        cos(πr)           -sin(πr)
    2        -sin(πr)          -cos(πr)
    3        -cos(πr)          sin(πr)
    ======== ================= =================

    Examples
    --------
    >>> from libm_ext import sincospi
    >>> sincospi(0.0)
    (0.0, 1.0)
    >>> sincospi(0.5)
    (1.0, 0.0)
    >>> sincospi(0.25)  # doctest: +ELLIPSIS
    (0.707..., 0.707...)

    Notes
    -----
    - Returns (NaN, NaN) for infinite or NaN inputs.
    - More efficient than calling sinpi and cospi separately.

    See Also
    --------
    sinpi : Compute sin(πx)
    cospi : Compute cos(πx)
    """
    return _core.sincospi(x)
