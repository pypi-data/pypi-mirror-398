"""Truncated Beta distribution utilities.

This module implements numerically stable versions of truncated Beta distribution
functions, extending the standard Beta distribution to support truncation to
arbitrary intervals [lower, upper].

The truncated Beta distribution is defined as:
    f(x; α, β, a, b) = Beta(x; α, β) / Z  for x ∈ [a, b]
                     = 0                    otherwise

where Z = P(a ≤ X ≤ b) is the partition constant (normalization factor).

The standard Beta distribution is recovered when lower=0.0 and upper=1.0.

Implementation uses:
- Log-space computation for numerical stability
- The library's stable beta_cdf and beta_ppf functions
- Vectorization support for numpy arrays
"""

import math
import numpy as np

from proportions.distributions.beta import beta_cdf, beta_ppf


def log_truncated_beta_partition(
    alpha: float, beta_param: float, lower: float = 0.0, upper: float = 1.0
) -> float:
    """Compute log partition constant for truncated Beta distribution.

    The partition constant (normalization factor) is:
        Z = ∫[lower to upper] Beta(x; α, β) dx
          = CDF_Beta(upper; α, β) - CDF_Beta(lower; α, β)

    Args:
        alpha: First shape parameter of Beta distribution (must be > 0).
        beta_param: Second shape parameter of Beta distribution (must be > 0).
        lower: Lower truncation bound (default: 0.0, must be in [0, 1]).
        upper: Upper truncation bound (default: 1.0, must be in [0, 1]).

    Returns:
        Log of the partition constant log(Z).

    Raises:
        ValueError: If parameters are invalid or bounds are inconsistent.

    Example:
        >>> log_Z = log_truncated_beta_partition(2.0, 3.0, 0.2, 0.8)
        >>> # For no truncation, log(Z) should be 0
        >>> log_Z_full = log_truncated_beta_partition(2.0, 3.0, 0.0, 1.0)
        >>> abs(log_Z_full) < 1e-10
        True
    """
    if alpha <= 0:
        raise ValueError(f"alpha must be positive, got {alpha}")
    if beta_param <= 0:
        raise ValueError(f"beta_param must be positive, got {beta_param}")
    if not (0.0 <= lower < upper <= 1.0):
        raise ValueError(
            f"Must have 0 <= lower < upper <= 1, got lower={lower}, upper={upper}"
        )

    # Use the library's stable beta_cdf function
    cdf_upper = beta_cdf(upper, alpha, beta_param)
    cdf_lower = beta_cdf(lower, alpha, beta_param)

    # Compute partition in log-space for stability
    Z = cdf_upper - cdf_lower

    if Z <= 0:
        raise RuntimeError(
            f"Invalid partition constant Z={Z} for alpha={alpha}, beta={beta_param}, "
            f"lower={lower}, upper={upper}"
        )

    return math.log(Z)


def truncated_beta_partition(
    alpha: float, beta_param: float, lower: float = 0.0, upper: float = 1.0
) -> float:
    """Compute partition constant for truncated Beta distribution.

    Convenience wrapper around log_truncated_beta_partition.

    Args:
        alpha: First shape parameter of Beta distribution (must be > 0).
        beta_param: Second shape parameter of Beta distribution (must be > 0).
        lower: Lower truncation bound (default: 0.0, must be in [0, 1]).
        upper: Upper truncation bound (default: 1.0, must be in [0, 1]).

    Returns:
        The partition constant Z (probability mass in truncation interval).

    Example:
        >>> Z = truncated_beta_partition(2.0, 3.0, 0.2, 0.8)
        >>> 0 < Z < 1
        True
        >>> # No truncation should give Z = 1
        >>> Z_full = truncated_beta_partition(2.0, 3.0, 0.0, 1.0)
        >>> abs(Z_full - 1.0) < 1e-10
        True
    """
    return math.exp(log_truncated_beta_partition(alpha, beta_param, lower, upper))


def truncated_beta_pdf(
    x: float | np.ndarray,
    alpha: float,
    beta_param: float,
    lower: float = 0.0,
    upper: float = 1.0,
) -> float | np.ndarray:
    """Probability density function for truncated Beta distribution.

    The truncated Beta PDF is:
        f(x) = Beta_PDF(x; α, β) / Z  if lower ≤ x ≤ upper
             = 0                       otherwise

    where Z is the partition constant.

    Args:
        x: Points at which to evaluate the PDF (scalar or array).
        alpha: First shape parameter (must be > 0).
        beta_param: Second shape parameter (must be > 0).
        lower: Lower truncation bound (default: 0.0).
        upper: Upper truncation bound (default: 1.0).

    Returns:
        PDF values (same type as x: scalar or array).

    Example:
        >>> # Single value
        >>> pdf = truncated_beta_pdf(0.5, 2.0, 3.0, 0.2, 0.8)
        >>> pdf > 0
        True
        >>> # Array of values
        >>> import numpy as np
        >>> x_vals = np.array([0.1, 0.5, 0.9])
        >>> pdf_vals = truncated_beta_pdf(x_vals, 2.0, 3.0, 0.2, 0.8)
        >>> pdf_vals[0]  # Outside bounds
        0.0
        >>> pdf_vals[1] > 0  # Inside bounds
        True
    """
    from scipy.stats import beta

    # Get partition constant
    Z = truncated_beta_partition(alpha, beta_param, lower, upper)

    # Compute standard Beta PDF
    pdf_vals = beta.pdf(x, alpha, beta_param) / Z

    # Set to zero outside truncation bounds
    if np.isscalar(x):
        if x < lower or x > upper:
            return 0.0
        return float(pdf_vals)
    else:
        # Vectorized case
        pdf_vals = np.where((x >= lower) & (x <= upper), pdf_vals, 0.0)
        return pdf_vals


def truncated_beta_cdf(
    x: float | np.ndarray,
    alpha: float,
    beta_param: float,
    lower: float = 0.0,
    upper: float = 1.0,
) -> float | np.ndarray:
    """Cumulative distribution function for truncated Beta distribution.

    The truncated Beta CDF is:
        F(x) = [CDF_Beta(x) - CDF_Beta(lower)] / Z  for x ∈ [lower, upper]
             = 0                                      for x < lower
             = 1                                      for x > upper

    where Z is the partition constant.

    Args:
        x: Points at which to evaluate the CDF (scalar or array).
        alpha: First shape parameter (must be > 0).
        beta_param: Second shape parameter (must be > 0).
        lower: Lower truncation bound (default: 0.0).
        upper: Upper truncation bound (default: 1.0).

    Returns:
        CDF values (same type as x: scalar or array).

    Example:
        >>> # At lower bound, CDF = 0
        >>> cdf = truncated_beta_cdf(0.2, 2.0, 3.0, 0.2, 0.8)
        >>> abs(cdf) < 1e-10
        True
        >>> # At upper bound, CDF = 1
        >>> cdf = truncated_beta_cdf(0.8, 2.0, 3.0, 0.2, 0.8)
        >>> abs(cdf - 1.0) < 1e-10
        True
    """
    # Get partition constant
    Z = truncated_beta_partition(alpha, beta_param, lower, upper)

    # Get standard Beta CDF values
    cdf_lower = beta_cdf(lower, alpha, beta_param)
    cdf_x = beta_cdf(x, alpha, beta_param) if np.isscalar(x) else np.array(
        [beta_cdf(xi, alpha, beta_param) for xi in x]
    )

    # Compute truncated CDF
    cdf_vals = (cdf_x - cdf_lower) / Z

    # Handle boundaries
    if np.isscalar(x):
        if x < lower:
            return 0.0
        elif x > upper:
            return 1.0
        return float(cdf_vals)
    else:
        # Vectorized case
        cdf_vals = np.where(x < lower, 0.0, cdf_vals)
        cdf_vals = np.where(x > upper, 1.0, cdf_vals)
        return cdf_vals


def truncated_beta_ppf(
    q: float | np.ndarray,
    alpha: float,
    beta_param: float,
    lower: float = 0.0,
    upper: float = 1.0,
    tol: float = 1e-10,
) -> float | np.ndarray:
    """Percent point function (inverse CDF) for truncated Beta distribution.

    Given a quantile q ∈ [0, 1], find x such that CDF(x) = q.

    The transformation is:
        q_adjusted = CDF_Beta(lower) + q * Z
        x = PPF_Beta(q_adjusted)

    where Z is the partition constant.

    Args:
        q: Quantile values between 0 and 1 (scalar or array).
        alpha: First shape parameter (must be > 0).
        beta_param: Second shape parameter (must be > 0).
        lower: Lower truncation bound (default: 0.0).
        upper: Upper truncation bound (default: 1.0).
        tol: Tolerance for numerical computations (default: 1e-10).

    Returns:
        Values x such that CDF(x) = q (same type as q).

    Example:
        >>> # Median of truncated distribution
        >>> median = truncated_beta_ppf(0.5, 2.0, 3.0, 0.2, 0.8)
        >>> 0.2 <= median <= 0.8
        True
        >>> # q=0 gives lower bound
        >>> x = truncated_beta_ppf(0.0, 2.0, 3.0, 0.3, 0.7)
        >>> abs(x - 0.3) < 1e-10
        True
    """
    # Get CDF values at truncation bounds
    cdf_lower = beta_cdf(lower, alpha, beta_param)
    cdf_upper = beta_cdf(upper, alpha, beta_param)
    Z = cdf_upper - cdf_lower

    # Transform quantile to untruncated Beta quantile
    if np.isscalar(q):
        if q <= 0.0:
            return lower
        elif q >= 1.0:
            return upper

        adjusted_q = cdf_lower + q * Z
        result = beta_ppf(adjusted_q, alpha, beta_param, tol=tol)

        # Ensure result is within bounds (handle numerical errors)
        return float(np.clip(result, lower, upper))
    else:
        # Vectorized case
        adjusted_q = cdf_lower + q * Z
        result = np.array([beta_ppf(qi, alpha, beta_param, tol=tol) for qi in adjusted_q])

        # Handle boundary cases
        result = np.where(q <= 0.0, lower, result)
        result = np.where(q >= 1.0, upper, result)

        # Ensure all results are within bounds
        return np.clip(result, lower, upper)
