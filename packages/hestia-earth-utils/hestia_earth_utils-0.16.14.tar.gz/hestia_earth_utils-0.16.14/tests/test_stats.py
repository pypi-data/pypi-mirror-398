from numpy import inf, sqrt
from numpy.testing import assert_almost_equal
from pytest import mark

from hestia_earth.utils.stats import (
    truncated_normal_1d,
    _calc_confidence_level,
    add_normal_distributions,
    calc_confidence_level_monte_carlo,
    calc_precision_monte_carlo,
    calc_required_iterations_monte_carlo,
    calc_z_critical,
    lerp_normal_distributions,
    subtract_normal_distributions,
)


def test_truncated_normal_1d():
    results = truncated_normal_1d(
        shape=(1, 10), mu=100, sigma=2, low=0, high=inf, seed=50
    )[0]
    assert len(results) == 10
    for result in results:
        assert result * 0.98 < result < result * 1.02, result


# confidence_level, n_sided, z_critical
CONFIDENCE_INTERVAL_PARAMS = [
    # 1 sided
    (0, 1, -inf),
    (50, 1, 0),
    (80, 1, 0.8416),
    (90, 1, 1.2816),
    (95, 1, 1.6449),
    (99, 1, 2.3263),
    (100, 1, inf),
    # 2 sided
    (0, 2, 0),
    (50, 2, 0.6745),
    (80, 2, 1.2816),
    (90, 2, 1.6449),
    (95, 2, 1.9600),
    (99, 2, 2.5758),
    (100, 2, inf),
]


@mark.parametrize(
    "confidence_level, n_sided, z_critical",
    CONFIDENCE_INTERVAL_PARAMS,
    ids=[f"z={z}, n={n}" for _, n, z in CONFIDENCE_INTERVAL_PARAMS],
)
def test_calc_confidence_level(confidence_level, n_sided, z_critical):
    result = _calc_confidence_level(z_critical, n_sided=n_sided)
    assert_almost_equal(result, confidence_level, decimal=2)


@mark.parametrize(
    "confidence_level, n_sided, z_critical",
    CONFIDENCE_INTERVAL_PARAMS,
    ids=[f"conf={conf}, n={n}" for conf, n, _ in CONFIDENCE_INTERVAL_PARAMS],
)
def test_calc_z_critical(confidence_level, n_sided, z_critical):
    result = calc_z_critical(confidence_level, n_sided=n_sided)
    assert_almost_equal(result, z_critical, decimal=4)


# confidence_level, n_iterations, precision, sd
MONTE_CARLO_PARAMS = [
    (95, 80767, 0.01, 1.45),
    (95, 1110, 0.01, 0.17),
    (99, 1917, 0.01, 0.17),
    (50, 102, 100.18, 1500),
]


@mark.parametrize(
    "confidence_level, n_iterations, precision, sd",
    MONTE_CARLO_PARAMS,
    ids=[f"n={n}, prec={prec}, sd={sd}" for _, n, prec, sd in MONTE_CARLO_PARAMS],
)
def test_calc_confidence_level_monte_carlo(
    confidence_level, n_iterations, precision, sd
):
    result = calc_confidence_level_monte_carlo(
        n_iterations,
        precision,
        sd,
    )
    assert_almost_equal(result, confidence_level, decimal=2)


@mark.parametrize(
    "confidence_level, n_iterations, precision, sd",
    MONTE_CARLO_PARAMS,
    ids=[
        f"conf={conf}, prec={prec}, sd={sd}" for conf, _, prec, sd in MONTE_CARLO_PARAMS
    ],
)
def test_calc_required_iterations_monte_carlo(
    confidence_level, n_iterations, precision, sd
):
    result = calc_required_iterations_monte_carlo(confidence_level, precision, sd)
    assert result == n_iterations


@mark.parametrize(
    "confidence_level, n_iterations, precision, sd",
    MONTE_CARLO_PARAMS,
    ids=[f"conf={conf}, n={n}, sd={sd}" for conf, n, _, sd in MONTE_CARLO_PARAMS],
)
def test_calc_precision_monte_carlo(confidence_level, n_iterations, precision, sd):
    result = calc_precision_monte_carlo(confidence_level, n_iterations, sd)
    assert_almost_equal(result, precision, decimal=2)


# mu_1, sigma_1, mu_2, sigma_2, rho, sum_mean, sum_sigma, diff_mean, diff_sigma
PARAMS_NORMAL_DIST = [
    # 2 standard normal distributions, perfectly negative correlation
    (0, 1, 0, 1, -1, 0, 0, 0, 2),
    # 2 standard normal distributions, negative correlation
    (0, 1, 0, 1, -0.5, 0, 1, 0, sqrt(3)),
    # 2 standard normal distributions, no correlation
    (0, 1, 0, 1, 0, 0, sqrt(2), 0, sqrt(2)),
    # 2 standard normal distributions, positive correlation
    (0, 1, 0, 1, 0.5, 0, sqrt(3), 0, 1),
    # 2 standard normal distributions, perfectly positive correlation
    (0, 1, 0, 1, 1, 0, 2, 0, 0),
    # different normal distributions, perfectly negative correlation
    (50000, 3000, 45000, 9000, -1, 95000, 6000, 5000, 12000),
    # different normal distributions, no correlation
    (50000, 3000, 45000, 9000, 0, 95000, sqrt(90000000), 5000, sqrt(90000000)),
    # different normal distributions, perfectly positive correlation
    (50000, 3000, 45000, 9000, 1, 95000, 12000, 5000, 6000),
]
IDS_ADD_NORMAL_DIST = [
    f"N({mu_1}, {sigma_1}^2) + N({mu_2}, {sigma_2}^2), rho: {rho}"
    for mu_1, sigma_1, mu_2, sigma_2, rho, *_ in PARAMS_NORMAL_DIST
]
IDS_SUBTRACT_DIST = [
    f"N({mu_1}, {sigma_1}^2) - N({mu_2}, {sigma_2}^2), rho: {rho}"
    for mu_1, sigma_1, mu_2, sigma_2, rho, *_ in PARAMS_NORMAL_DIST
]


@mark.parametrize(
    "mu_1, sigma_1, mu_2, sigma_2, rho, sum_mean, sum_sigma, _diff_mean, _diff_sigma",
    PARAMS_NORMAL_DIST,
    ids=IDS_ADD_NORMAL_DIST,
)
def test_add_normal_distributions(
    mu_1, sigma_1, mu_2, sigma_2, rho, sum_mean, sum_sigma, _diff_mean, _diff_sigma
):
    result = add_normal_distributions(mu_1, sigma_1, mu_2, sigma_2, rho)
    assert result == (sum_mean, sum_sigma)


@mark.parametrize(
    "mu_1, sigma_1, mu_2, sigma_2, rho, _sum_mean, _sum_sigma, diff_mean, diff_sigma",
    PARAMS_NORMAL_DIST,
    ids=IDS_SUBTRACT_DIST,
)
def test_subtract_normal_distributions(
    mu_1, sigma_1, mu_2, sigma_2, rho, _sum_mean, _sum_sigma, diff_mean, diff_sigma
):
    result = subtract_normal_distributions(mu_1, sigma_1, mu_2, sigma_2, rho)
    assert result == (diff_mean, diff_sigma)


# mu_1, sigma_1, mu_2, sigma_2, alpha, rho, Z_mean, Z_sigma
PARAMS_LERP_NORMAL_DIST = [
    # 2 standard normal distributions, perfectly negative correlation
    (0, 1, 0, 1, 0, -1, 0, 1),
    (0, 1, 0, 1, 0.5, -1, 0, 0),
    (0, 1, 0, 1, 1, -1, 0, 1),
    # 2 standard normal distributions, no correlation
    (0, 1, 0, 1, 0, 0, 0, 1),
    (0, 1, 0, 1, 0.5, 0, 0, sqrt(0.5)),
    (0, 1, 0, 1, 1, 0, 0, 1),
    # 2 standard normal distributions, perfectly positive correlation
    (0, 1, 0, 1, 0, 1, 0, 1),
    (0, 1, 0, 1, 0.5, 1, 0, 1),
    (0, 1, 0, 1, 1, 1, 0, 1),
    # different normal distributions, perfectly negative correlation
    (10000, 3000, 5000, 2500, -0.5, -1, 12500, 5750),
    (10000, 3000, 5000, 2500, 0, -1, 10000, 3000),
    (10000, 3000, 5000, 2500, 0.5, -1, 7500, 250),
    (10000, 3000, 5000, 2500, 1, -1, 5000, 2500),
    (10000, 3000, 5000, 2500, 1.5, -1, 2500, 5250),
    # different normal distributions, no correlation
    (10000, 3000, 5000, 2500, -0.5, 0, 12500, sqrt(21812500)),
    (10000, 3000, 5000, 2500, 0, 0, 10000, 3000),
    (10000, 3000, 5000, 2500, 0.5, 0, 7500, sqrt(3812500)),
    (10000, 3000, 5000, 2500, 1, 0, 5000, 2500),
    (10000, 3000, 5000, 2500, 1.5, 0, 2500, sqrt(16312500)),
    # different normal distributions, perfectly positive correlation
    (10000, 3000, 5000, 2500, -0.5, 1, 12500, 3250),
    (10000, 3000, 5000, 2500, 0, 1, 10000, 3000),
    (10000, 3000, 5000, 2500, 0.5, 1, 7500, 2750.0),
    (10000, 3000, 5000, 2500, 1, 1, 5000, 2500),
    (10000, 3000, 5000, 2500, 1.5, 1, 2500, 2250),
]
IDS_LERP_NORMAL_DIST = [
    f"N({mu_1}, {sigma_1}^2) - N({mu_2}, {sigma_2}^2), alpha: {alpha}, rho: {rho}"
    for mu_1, sigma_1, mu_2, sigma_2, alpha, rho, *_ in PARAMS_LERP_NORMAL_DIST
]


@mark.parametrize(
    "mu_1, sigma_1, mu_2, sigma_2, alpha, rho, Z_mean, Z_sigma",
    PARAMS_LERP_NORMAL_DIST,
    ids=IDS_LERP_NORMAL_DIST,
)
def test_lerp_normal_distributions(
    mu_1, sigma_1, mu_2, sigma_2, alpha, rho, Z_mean, Z_sigma
):
    result = lerp_normal_distributions(mu_1, sigma_1, mu_2, sigma_2, alpha, rho)
    assert result == (Z_mean, Z_sigma)
