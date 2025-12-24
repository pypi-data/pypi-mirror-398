# jonckheere-test

[![PyPI version](https://badge.fury.io/py/jonckheere-test.svg)](https://pypi.org/project/jonckheere-test/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python implementation of the **Jonckheere-Terpstra test** for ordered alternatives in k independent samples.

## Overview

The Jonckheere-Terpstra test is a nonparametric statistical test used to determine whether there is a statistically significant trend across ordered groups. Unlike the Kruskal-Wallis test which only detects *any* difference between groups, the Jonckheere-Terpstra test specifically tests for an *ordered* alternative hypothesis—that the populations are either increasing or decreasing across groups.

### When to Use This Test

- You have **k ≥ 2 independent samples** (groups)
- The groups have a **natural ordering** (e.g., dosage levels, time points, severity grades)
- You want to test if there's an **increasing or decreasing trend** across groups
- Your data is at least **ordinal** (ranked)
- You prefer a **nonparametric** approach (no normality assumption)

## Installation

```bash
pip install jonckheere-test
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add jonckheere-test
```

## Quick Start

```python
import numpy as np
from jonckheere_test import jonckheere_test

# Sample data: scores across three treatment groups
control = [40, 35, 38, 43, 44, 41]
low_dose = [38, 40, 47, 44, 40, 42]
high_dose = [48, 40, 45, 43, 46, 44]

# Combine data and create group labels
data = np.concatenate([control, low_dose, high_dose])
groups = np.repeat([1, 2, 3], 6)

# Test for increasing trend
result = jonckheere_test(data, groups, alternative='increasing')

print(f"JT statistic: {result.statistic}")
print(f"p-value: {result.p_value:.4f}")
print(f"Method: {result.method}")
```

Output:
```
JT statistic: 79.0
p-value: 0.0207
Method: asymptotic
```

## Features

| Feature | Description |
|---------|-------------|
| **Exact p-values** | Computed via convolution for small samples (n ≤ 100) without ties |
| **Asymptotic approximation** | Normal approximation with tie-corrected variance for large samples or data with ties |
| **Permutation test** | Monte Carlo permutation test for any sample size |
| **Automatic method selection** | Intelligently chooses the best method based on your data |
| **Tie handling** | Proper variance correction when ties are present |

## API Reference

### `jonckheere_test(x, groups, alternative='two-sided', n_perm=None, random_state=None, method=None)`

Perform the Jonckheere-Terpstra test for ordered alternatives.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `x` | array-like | Sample data values |
| `groups` | array-like | Group labels (must be orderable). Values are sorted to determine group order |
| `alternative` | `'two-sided'`, `'increasing'`, or `'decreasing'` | The alternative hypothesis to test (default: `'two-sided'`) |
| `n_perm` | int, optional | Number of permutations for permutation test. If provided, uses permutation method |
| `random_state` | int, optional | Random seed for reproducibility (permutation test only) |
| `method` | `'exact'`, `'asymptotic'`, or `None` | Method for p-value computation. If `None`, automatically selected |

#### Returns

`JonckheereResult` dataclass with the following attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `statistic` | float | The JT test statistic (J) |
| `p_value` | float | The p-value for the test |
| `alternative` | str | The alternative hypothesis used |
| `method` | str | The method used: `'exact'`, `'asymptotic'`, or `'permutation'` |
| `mean` | float or None | Expected value of J under the null (asymptotic only) |
| `variance` | float or None | Variance of J under the null (asymptotic only) |
| `z_score` | float or None | Standardized test statistic (asymptotic only) |

#### Method Selection

When `method=None` (default), the function automatically selects:

1. **Permutation**: If `n_perm` is provided
2. **Asymptotic**: If n > 100 or ties are present
3. **Exact**: Otherwise (small samples without ties)

## Examples

### Testing for a Decreasing Trend

```python
# Data showing decreasing performance over time
time_1 = [95, 92, 88, 91, 94]
time_2 = [85, 82, 79, 83, 80]
time_3 = [72, 68, 75, 70, 71]

data = np.concatenate([time_1, time_2, time_3])
groups = np.repeat(['T1', 'T2', 'T3'], 5)

result = jonckheere_test(data, groups, alternative='decreasing')
print(f"p-value: {result.p_value:.4f}")  # Significant decreasing trend
```

### Using Permutation Test

```python
# For more robust p-values or when exact computation is too slow
result = jonckheere_test(
    data, 
    groups, 
    alternative='increasing',
    n_perm=10000,
    random_state=42  # For reproducibility
)
print(f"Permutation p-value: {result.p_value:.4f}")
```

### Forcing a Specific Method

```python
# Force asymptotic method even for small samples
result = jonckheere_test(data, groups, method='asymptotic')

# Access additional statistics
print(f"Expected value (μ): {result.mean}")
print(f"Variance (σ²): {result.variance:.2f}")
print(f"Z-score: {result.z_score:.2f}")
```

## Statistical Background

### The Test Statistic

The Jonckheere-Terpstra statistic J is computed as the sum of Mann-Whitney U statistics for all pairs of groups:

$$J = \sum_{i < j} U_{ij}$$

where $U_{ij}$ counts the number of times an observation from group $i$ is less than an observation from group $j$.

### Null Distribution

- **Exact method**: The null distribution is computed via convolution of individual Mann-Whitney distributions
- **Asymptotic method**: Uses normal approximation with:
  - Mean: $E(J) = \frac{N^2 - \sum n_i^2}{4}$
  - Variance: Includes corrections for ties

### Interpretation

- **Increasing alternative**: Tests if group medians increase with group order
- **Decreasing alternative**: Tests if group medians decrease with group order
- **Two-sided alternative**: Tests for any monotonic trend

## Dependencies

- Python ≥ 3.9
- NumPy ≥ 1.21
- SciPy ≥ 1.7

## References

- Jonckheere, A. R. (1954). "A distribution-free k-sample test against ordered alternatives". *Biometrika*, 41(1/2), 133-145.
- Terpstra, T. J. (1952). "The asymptotic normality and consistency of Kendall's test against trend". *Indagationes Mathematicae*, 14, 327-333.
- Hollander, M., Wolfe, D. A., & Chicken, E. (2014). *Nonparametric Statistical Methods* (3rd ed.). John Wiley & Sons. https://doi.org/10.1002/9781119196037

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Ariel Bereslavsky
