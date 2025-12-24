import numpy as np
import pytest

from jonckheere_test import jonckheere_test


class TestJonckheereTerpstra:
    def test_hundal_example_6_2(self):
        """
        Test against the Hundal (1969) data provided in Example 6.2.
        Verifies J-statistic, variance, standardized statistic, and p-values.
        """
        # Data from Table 6.6
        group_a = [40, 35, 38, 43, 44, 41]  # Control (no information)
        group_b = [38, 40, 47, 44, 40, 42]  # Group B (rough information)
        group_c = [48, 40, 45, 43, 46, 44]  # Group C (accurate information)

        data = np.concatenate([group_a, group_b, group_c])
        groups = np.repeat([1, 2, 3], 6)

        result = jonckheere_test(data, groups, alternative="increasing")

        # 1. Verify the J Statistic (Equation 6.13)
        # Expected: U12=22, U13=30.5, U23=26.5 -> J = 79
        assert result.statistic == 79, "The J statistic should be 79."

        # 2. Verify the Null Expected Value
        # E_0(J) = [(18^2 - (6^2 + 6^2 + 6^2))/4] = 54
        assert result.mean == 54, "The null expected value should be 54."

        # 3. Verify the Ties-Corrected Variance
        # Var_0(J) = 150.29
        assert result.variance == pytest.approx(150.29, abs=0.01), \
            "The ties-corrected variance should be approx 150.29"

        # 4. Verify the Standardized Statistic J*
        # J* = (79 - 54) / sqrt(150.29) = 2.04
        assert result.z_score == pytest.approx(2.04, abs=0.01), \
            "The standardized statistic J* should be approx 2.04"

        # 5. Verify P-values
        if result.method == "exact":
            assert result.p_value == pytest.approx(0.0231, abs=0.0001), \
                "Exact p-value should be 0.0231"
        elif result.method == "asymptotic":
            assert result.p_value == pytest.approx(0.0207, abs=0.0001), \
                "Asymptotic p-value should be 0.0207"

    def test_increasing_trend(self):
        """Test detection of increasing trend."""
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9])
        groups = np.array([1, 1, 1, 2, 2, 2, 3, 3, 3])

        result = jonckheere_test(x, groups, alternative="increasing")
        assert result.p_value < 0.01

    def test_no_trend(self):
        """Test no significant trend in random data."""
        rng = np.random.default_rng(42)
        x = rng.standard_normal(30)
        groups = np.repeat([1, 2, 3], 10)

        result = jonckheere_test(x, groups, alternative="two-sided")
        assert result.p_value > 0.05

    def test_permutation_method(self):
        """Test permutation method runs correctly."""
        x = np.array([1, 2, 3, 4, 5, 6])
        groups = np.array([1, 1, 2, 2, 3, 3])

        result = jonckheere_test(x, groups, n_perm=1000, random_state=42)
        assert result.method == "permutation"
        assert result.p_value < 0.1

    def test_invalid_inputs(self):
        """Test error handling for invalid inputs."""
        with pytest.raises(ValueError):
            jonckheere_test([1, 2, 3], [1, 2])  # Mismatched lengths

        with pytest.raises(ValueError):
            jonckheere_test([], [])  # Empty input

        with pytest.raises(ValueError):
            jonckheere_test([1, 2, 3], [1, 1, 1])  # Single group
