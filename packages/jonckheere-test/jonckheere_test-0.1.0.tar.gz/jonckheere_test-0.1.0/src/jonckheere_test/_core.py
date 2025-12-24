"""Core implementation of the Jonckheere-Terpstra test."""

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike
from scipy import stats


@dataclass
class JonckheereResult:
    """Result of a Jonckheere-Terpstra test."""

    statistic: float
    p_value: float
    alternative: str
    method: str
    mean: float | None = None
    variance: float | None = None
    z_score: float | None = None


def _jtpdf(group_sizes: np.ndarray) -> np.ndarray:
    """Compute exact PDF of JT statistic via convolution."""
    ng = len(group_sizes)
    cgsize = np.cumsum(group_sizes[::-1])[::-1]
    max_sum = int(np.sum(group_sizes[:-1] * cgsize[1:])) + 1

    pdf = np.array([1.0])
    for i in range(ng - 1):
        na, nb = int(group_sizes[i]), int(cgsize[i + 1])
        single = np.ones(nb + 1)
        mw_pdf = single.copy()
        for _ in range(na - 1):
            mw_pdf = np.convolve(mw_pdf, single)
        mw_pdf /= mw_pdf.sum()
        pdf = np.convolve(pdf, mw_pdf)

    result = np.zeros(max_sum)
    result[: len(pdf)] = pdf[:max_sum]
    return result / result.sum()


def _compute_jt(
    x: np.ndarray,
    group_sizes: np.ndarray,
    cumsum_sizes: np.ndarray,
    tie_sizes: np.ndarray,
):
    """Compute JT statistic, mean, and tie-corrected variance."""
    N = len(x)
    ng = len(group_sizes)
    n = group_sizes
    t = tie_sizes

    jt_sum = 0.0
    for i in range(ng - 1):
        na = group_sizes[i]
        ranks = stats.rankdata(x[cumsum_sizes[i] : N])
        jt_sum += ranks[:na].sum() - na * (na + 1) / 2

    jt_mean = (N * N - np.sum(n * n)) / 4

    # Tie-corrected variance
    term1 = (
        N * (N - 1) * (2 * N + 5)
        - np.sum(n * (n - 1) * (2 * n + 5))
        - np.sum(t * (t - 1) * (2 * t + 5))
    ) / 72

    if N > 2:
        term2 = (np.sum(n * (n - 1) * (n - 2)) * np.sum(t * (t - 1) * (t - 2))) / (
            36 * N * (N - 1) * (N - 2)
        )
    else:
        term2 = 0.0

    if N > 1:
        term3 = (np.sum(n * (n - 1)) * np.sum(t * (t - 1))) / (8 * N * (N - 1))
    else:
        term3 = 0.0

    jt_var = term1 + term2 + term3

    return 2 * jt_mean - jt_sum, jt_mean, jt_var


def _jt_raw(x: np.ndarray, group_sizes: np.ndarray, cumsum_sizes: np.ndarray) -> float:
    """Compute raw JT sum (before transformation)."""
    n, ng = len(x), len(group_sizes)
    jt_sum = 0.0
    for i in range(ng - 1):
        na = group_sizes[i]
        ranks = stats.rankdata(x[cumsum_sizes[i] : n])
        jt_sum += ranks[:na].sum() - na * (na + 1) / 2
    return jt_sum


def _permutation_pvalue(
    x: np.ndarray,
    group_sizes: np.ndarray,
    cumsum_sizes: np.ndarray,
    alternative: str,
    n_perm: int,
    rng: np.random.Generator,
) -> float:
    """Compute permutation p-value."""
    original = _jt_raw(x, group_sizes, cumsum_sizes)

    perms = rng.permuted(np.tile(x, (n_perm, 1)), axis=1)
    perm_stats = np.array([_jt_raw(p, group_sizes, cumsum_sizes) for p in perms])
    perm_stats[0] = original

    i_pval = np.mean(perm_stats <= original)
    d_pval = np.mean(perm_stats >= original)

    if alternative == "two-sided":
        return 2 * min(i_pval, d_pval, 0.5)
    return i_pval if alternative == "increasing" else d_pval


def _normal_pvalue(z: float, alternative: str) -> float:
    """Compute p-value from z-score using normal approximation."""
    p = stats.norm.cdf(z)
    if alternative == "two-sided":
        return 2 * min(p, 1 - p, 0.5)
    return 1 - p if alternative == "increasing" else p


def jonckheere_test(
    x: ArrayLike,
    groups: ArrayLike,
    alternative: Literal["two-sided", "increasing", "decreasing"] = "two-sided",
    n_perm: int | None = None,
    random_state: int | None = None,
    method: Literal["exact", "asymptotic"] | None = None,
) -> JonckheereResult:
    """
    Jonckheere-Terpstra test for ordered alternatives.

    Parameters
    ----------
    x : array-like
        Sample data values.
    groups : array-like
        Group labels (must be orderable).
    alternative : {'two-sided', 'increasing', 'decreasing'}, default='two-sided'
        Alternative hypothesis.
    n_perm : int, optional
        Number of permutations for permutation test.
    random_state : int, optional
        Random seed for permutation test.
    method : {'exact', 'asymptotic'}, optional
        Method for p-value computation. If None, automatically selects based
        on sample size and presence of ties.

    Returns
    -------
    JonckheereResult
        Test result containing statistic, p_value, alternative, method,
        and optionally mean, variance, z_score (for asymptotic method).

    Examples
    --------
    >>> import numpy as np
    >>> from jonckheere_test import jonckheere_test
    >>> x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9])
    >>> groups = np.array([1, 1, 1, 2, 2, 2, 3, 3, 3])
    >>> result = jonckheere_test(x, groups, alternative='increasing')
    >>> result.p_value < 0.05
    True
    """
    x = np.asarray(x, dtype=np.float64)
    groups = np.asarray(groups)

    if len(x) != len(groups):
        raise ValueError("x and groups must have the same length")

    mask = np.isfinite(x)
    x, groups = x[mask], groups[mask]

    if len(x) == 0:
        raise ValueError("No valid observations")

    unique_groups = np.unique(groups)
    if len(unique_groups) <= 1:
        raise ValueError("Need at least two groups")

    group_map = {g: i for i, g in enumerate(unique_groups)}
    group_idx = np.array([group_map[g] for g in groups])
    order = np.argsort(group_idx)
    x_sorted = x[order]

    group_sizes = np.bincount(group_idx)
    cumsum_sizes = np.concatenate([[0], np.cumsum(group_sizes)])
    n = len(x_sorted)

    _, tie_sizes = np.unique(x_sorted, return_counts=True)
    has_ties = len(tie_sizes) != n

    jt_stat, jt_mean, jt_var = _compute_jt(x_sorted, group_sizes, cumsum_sizes, tie_sizes)

    result_method: str
    z: float | None = None
    mean_out: float | None = None
    var_out: float | None = None

    if n_perm is not None and method is None:
        rng = np.random.default_rng(random_state)
        p_value = _permutation_pvalue(
            x_sorted, group_sizes, cumsum_sizes, alternative, n_perm, rng
        )
        result_method = "permutation"

    elif n > 100 or has_ties or method == "asymptotic":
        z = (jt_stat - jt_mean) / np.sqrt(jt_var)
        p_value = _normal_pvalue(z, alternative)
        result_method = "asymptotic"
        mean_out = float(jt_mean)
        var_out = float(jt_var)

    elif method is None or method == "exact":
        try:
            pdf = _jtpdf(group_sizes)
            jt_int = int(jt_stat)
            d_pval = np.sum(pdf[: jt_int + 1])
            i_pval = 1 - np.sum(pdf[:jt_int])

            if alternative == "two-sided":
                p_value = 2 * min(i_pval, d_pval, 0.5)
            else:
                p_value = i_pval if alternative == "increasing" else d_pval
            result_method = "exact"

        except (MemoryError, OverflowError):
            z = (jt_stat - jt_mean) / np.sqrt(jt_var)
            p_value = _normal_pvalue(z, alternative)
            result_method = "asymptotic"
            mean_out = float(jt_mean)
            var_out = float(jt_var)
    else:
        raise ValueError("method must be 'exact', 'asymptotic', or None")

    return JonckheereResult(
        statistic=float(jt_stat),
        p_value=float(p_value),
        alternative=alternative,
        method=result_method,
        mean=mean_out,
        variance=var_out,
        z_score=float(z) if z is not None else None,
    )

