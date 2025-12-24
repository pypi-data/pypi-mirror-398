"""Stable Beta distribution utilities.

This module implements numerically stable versions of Beta distribution
functions, particularly for the CDF and quantile (inverse CDF) functions.
These are critical for computing credible intervals.

The implementation uses:
- Log-space computation to avoid underflow/overflow
- Continued fractions for the incomplete beta function
- Symmetry properties for numerical stability
- Bisection for the quantile function
"""

import math

import numpy as np


def log_beta(a: float, b: float) -> float:
    """Compute log Beta(a,b) via lgamma, numerically stable.

    The Beta function is defined as:
        B(a,b) = Γ(a)Γ(b) / Γ(a+b)

    We compute it in log-space using the log-gamma function.

    Args:
        a: First parameter of Beta function (must be > 0).
        b: Second parameter of Beta function (must be > 0).

    Returns:
        Log of Beta(a, b).

    Example:
        >>> log_beta(2.0, 3.0)
        -2.995732...
    """
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def betacf(a: float, b: float, x: float, maxiter: int = 200) -> float:
    """Continued fraction for incomplete beta function.

    This is a core computational routine for the Beta CDF.
    Based on the Numerical Recipes implementation with
    modified Lentz's method.

    Args:
        a: First parameter.
        b: Second parameter.
        x: Evaluation point (0 <= x <= 1).
        maxiter: Maximum iterations (default: 200).

    Returns:
        Continued fraction value for the incomplete beta function.

    Raises:
        RuntimeError: If convergence is not achieved within maxiter iterations.

    Note:
        This is an internal function, not intended for direct use.
    """
    EPS = 3e-14

    am = 1.0
    bm = 1.0
    az = 1.0
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    bz = 1.0 - qab * x / qap

    for m in range(1, maxiter + 1):
        em = float(m)
        tem = em + em

        d = em * (b - em) * x / ((qam + tem) * (a + tem))
        ap = az + d * am
        bp = bz + d * bm

        d = -(a + em) * (qab + em) * x / ((a + tem) * (qap + tem))
        app = ap + d * az
        bpp = bp + d * bz

        aold = az
        am = ap / bpp
        bm = bp / bpp
        az = app / bpp
        bz = 1.0

        if abs(az - aold) < (EPS * abs(az)):
            return az

    raise RuntimeError(
        f"betacf did not converge after {maxiter} iterations for a={a}, b={b}, x={x}"
    )


def log_beta_cdf(x: float, a: float, b: float) -> float:
    """Compute log CDF of Beta(a,b) at x.

    Uses symmetry and continued fractions for numerical stability.

    The regularized incomplete beta function is:
        I_x(a,b) = B_x(a,b) / B(a,b)

    We compute this in log-space and use the symmetry relation:
        I_x(a,b) = 1 - I_(1-x)(b,a)

    to choose the more stable computation.

    Args:
        x: Evaluation point (0 <= x <= 1).
        a: First shape parameter (must be > 0).
        b: Second shape parameter (must be > 0).

    Returns:
        Log of CDF value at x.

    Example:
        >>> log_beta_cdf(0.5, 2.0, 2.0)
        -0.693147...  # log(0.5)
    """
    if x <= 0.0:
        return -1e300  # log(0) = -inf
    if x >= 1.0:
        return 0.0     # log(1) = 0

    lnB = log_beta(a, b)

    # Use symmetry for stability
    # If x is small relative to the mode, compute directly
    # Otherwise use 1 - I_(1-x)(b,a)
    if x < (a + 1.0) / (a + b + 2.0):
        cf = betacf(a, b, x)
        log_pref = a * math.log(x) + b * math.log(1.0 - x) - lnB - math.log(a)
        return log_pref + math.log(cf)
    else:
        cf = betacf(b, a, 1.0 - x)
        log_pref = b * math.log(1.0 - x) + a * math.log(x) - lnB - math.log(b)
        log_one_minus_I = log_pref + math.log(cf)
        return math.log1p(-math.exp(log_one_minus_I))


def beta_ppf(p: float, a: float, b: float, tol: float = 1e-10, maxiter: int = 200) -> float:
    """Compute Beta quantile function (inverse CDF) via bisection.

    The quantile function Q(p) is defined as:
        Q(p) = inf{x : CDF(x) >= p}

    We solve this via bisection on the log-CDF for numerical stability.

    Args:
        p: Probability (0 <= p <= 1).
        a: First shape parameter (must be > 0).
        b: Second shape parameter (must be > 0).
        tol: Tolerance for bisection convergence (default: 1e-10).
        maxiter: Maximum number of iterations (default: 200).

    Returns:
        Quantile value x such that CDF(x) ≈ p.

    Example:
        >>> beta_ppf(0.5, 2.0, 2.0)
        0.5
        >>> beta_ppf(0.025, 2.0, 2.0)  # 2.5th percentile
        0.145...
    """
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return 1.0

    lo, hi = 0.0, 1.0
    for _ in range(maxiter):
        mid = 0.5 * (lo + hi)
        cdf_mid = math.exp(log_beta_cdf(mid, a, b))

        if cdf_mid > p:
            hi = mid
        else:
            lo = mid

        if hi - lo < tol:
            return 0.5 * (lo + hi)

    raise RuntimeError(
        f"beta_ppf did not converge after {maxiter} iterations for p={p}, a={a}, b={b}"
    )


def beta_cdf(x: float, a: float, b: float) -> float:
    """Compute CDF of Beta(a,b) at x.

    Convenience wrapper around log_beta_cdf.

    Args:
        x: Evaluation point (0 <= x <= 1).
        a: First shape parameter (must be > 0).
        b: Second shape parameter (must be > 0).

    Returns:
        CDF value at x (probability).

    Example:
        >>> beta_cdf(0.5, 2.0, 2.0)
        0.5
    """
    return math.exp(log_beta_cdf(x, a, b))


def beta_quantiles(
    probs: np.ndarray, a: float, b: float, tol: float = 1e-10
) -> np.ndarray:
    """Compute multiple quantiles of Beta(a,b).

    Vectorized version of beta_ppf for computing multiple quantiles.

    Args:
        probs: Array of probabilities (0 <= p <= 1).
        a: First shape parameter (must be > 0).
        b: Second shape parameter (must be > 0).
        tol: Tolerance for bisection convergence (default: 1e-10).

    Returns:
        Array of quantile values.

    Example:
        >>> probs = np.array([0.025, 0.5, 0.975])
        >>> beta_quantiles(probs, 2.0, 2.0)
        array([0.145..., 0.5, 0.854...])
    """
    return np.array([beta_ppf(p, a, b, tol=tol) for p in probs])


def beta_mode(a: float, b: float) -> float:
    """Compute the mode of a Beta(a, b) distribution.

    The mode is the value that maximizes the probability density function.
    For Beta distributions, the mode depends on the shape parameters:

    - If a > 1 and b > 1: mode = (a-1)/(a+b-2) (interior mode)
    - If a > 1 and b ≤ 1: mode = 1.0 (mode at right boundary)
    - If a ≤ 1 and b > 1: mode = 0.0 (mode at left boundary)
    - If a ≤ 1 and b ≤ 1: the distribution is bimodal or uniform,
      we return the mean a/(a+b) as a fallback

    Args:
        a: First shape parameter (must be > 0).
        b: Second shape parameter (must be > 0).

    Returns:
        Mode of the Beta(a, b) distribution.

    Raises:
        ValueError: If a or b are not positive.

    Example:
        >>> beta_mode(2.0, 2.0)
        0.5
        >>> beta_mode(5.0, 2.0)
        0.666...
        >>> beta_mode(22.0, 0.99)  # b < 1, mode at boundary
        1.0
        >>> beta_mode(0.5, 5.0)  # a < 1, mode at boundary
        0.0
    """
    if a <= 0 or b <= 0:
        raise ValueError(f"Shape parameters must be positive, got a={a}, b={b}")

    if a > 1 and b > 1:
        # Interior mode
        return (a - 1) / (a + b - 2)
    elif a > 1 and b <= 1:
        # Mode at right boundary
        return 1.0
    elif a <= 1 and b > 1:
        # Mode at left boundary
        return 0.0
    else:
        # a ≤ 1 and b ≤ 1: bimodal or uniform
        # Return mean as fallback
        return a / (a + b)

