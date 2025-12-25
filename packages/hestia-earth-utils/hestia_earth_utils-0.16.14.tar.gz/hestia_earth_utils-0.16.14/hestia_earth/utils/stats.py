"""
Based on code by Cool Farm Tool: https://gitlab.com/MethodsCFT/coolfarm-soc/-/blob/main/src/cfasoc/builders.py
"""

import hashlib
from functools import reduce
from numpy import (
    cumsum,
    dot,
    full,
    linalg,
    hstack,
    random,
    mean,
    vstack,
    abs,
    array,
    concatenate,
    exp,
    float64,
    inf,
    pi,
    prod,
    sign,
    sqrt,
)
from numpy.typing import NDArray, DTypeLike
from typing import Union


def repeat_single(shape: tuple, value: float, dtype: DTypeLike = None) -> NDArray:
    """
    Repeat a single value to form an array of a defined shape.

    Parameters
    ----------
    shape : tuple
        Shape (rows, columns).
    value : float
        Value to be repeated.
    dtype : DTypeLike, optional
        The desired data-type for the array.

    Returns
    -------
    NDArray
        Array with repeated value.
    """
    return full(shape=shape, fill_value=value, dtype=dtype)


def repeat_array_as_columns(n_iterations: int, arr: NDArray) -> NDArray:
    """
    Repeat a numpy array horizontally as columns.

    Parameters
    ----------
    n_iterations : int
        Number of times the columns should be repeated.
    arr : NDArray
        Array to repeat.

    Returns
    -------
    NDArray
        Repeated array.
    """
    return hstack([arr for _ in range(n_iterations)])


def repeat_array_as_rows(n_iterations: int, arr: NDArray) -> NDArray:
    """
    Repeat a numpy array vertically as rows.

    Parameters
    ----------
    n_iterations : int
        Number of times the rows should be repeated.
    arr : NDArray
        Array to repeat.

    Returns
    -------
    NDArray
        Repeated array.
    """
    return vstack([arr for _ in range(n_iterations)])


def repeat_1d_array_as_columns(n_columns: int, column: NDArray) -> NDArray:
    """
    Repeat a column (NDArray) to form an array of a defined shape

    Parameters
    ----------
    n_columns : int
        How many times the column (NDArray) should be repeated.
    column : NDArray
        The column (NDArray) to be repeated.

    Returns
    -------
    NDArray
        Repeated array.
    """
    return vstack([column for _ in range(n_columns)]).transpose()


def discrete_uniform_1d(
    shape: tuple,
    low: float,
    high: float,
    seed: Union[int, random.Generator, None] = None,
) -> NDArray:
    """
    Sample from a discrete uniform distribution and produce an array of a specified shape.
    All rows in a specified column will have the same sample value, but each column will be different (1 dimensional
    variability).

    Parameters
    ----------
    shape : tuple
        Shape (rows, columns).
    low : float
        Lower bound of the discrete uniform distribution to be sampled.
    high : float
        Upper bound of the discrete uniform distribution to be sampled.
    seed : int | Generator | None, optional
        A seed to initialize the BitGenerator. If passed a Generator, it will be returned unaltered. If `None`, then
        fresh, unpredictable entropy will be pulled from the OS.

    Returns
    -------
    NDArray
        Array of samples with 1 dimensional variability.
    """
    n_rows, n_columns = shape
    rng = random.default_rng(seed)
    return repeat_array_as_rows(n_rows, rng.uniform(low=low, high=high, size=n_columns))


def discrete_uniform_2d(
    shape: tuple,
    low: float,
    high: float,
    seed: Union[int, random.Generator, None] = None,
) -> NDArray:
    """
    Sample from a discrete uniform distribution and produce an array of a specified shape.
    All rows and columns contain different sample values (2 dimensional variability).

    Parameters
    ----------
    shape : tuple
        Shape (rows, columns).
    low : float
        Lower bound of the discrete uniform distribution to be sampled.
    high : float
        Upper bound of the discrete uniform distribution to be sampled.
    seed : int | Generator | None, optional
        A seed to initialize the BitGenerator. If passed a Generator, it will be returned unaltered. If `None`, then
        fresh, unpredictable entropy will be pulled from the OS.

    Returns
    -------
    NDArray
        Array of samples with 2 dimensional variability.
    """
    rng = random.default_rng(seed)
    return rng.uniform(low=low, high=high, size=shape)


def triangular_1d(
    shape: tuple,
    low: float,
    high: float,
    mode: float,
    seed: Union[int, random.Generator, None] = None,
) -> NDArray:
    """
    Sample from a triangular distribution and produce an array of a specified shape.
    All rows in a specified column will have the same sample value, but each column will be different (1 dimensional
    variability).

    Parameters
    ----------
    shape : tuple
        Shape (rows, columns).
    low : float
        Lower bound of the triangular distribution to be sampled.
    high : float
        Upper bound of the triangular distribution to be sampled.
    mode : float
        Mode of the triangular distribution to be sampled.
    seed : int | Generator | None, optional
        A seed to initialize the BitGenerator. If passed a Generator, it will be returned unaltered. If `None`, then
        fresh, unpredictable entropy will be pulled from the OS.

    Returns
    -------
    NDArray
        Array of samples with 1 dimensional variability.
    """
    n_rows, n_columns = shape
    rng = random.default_rng(seed)
    return repeat_array_as_rows(
        n_rows, rng.triangular(left=low, mode=mode, right=high, size=n_columns)
    )


def triangular_2d(
    shape: tuple,
    low: float,
    high: float,
    mode: float,
    seed: Union[int, random.Generator, None] = None,
) -> NDArray:
    """
    Sample from a triangular distribution and produce an array of a specified shape.
    All rows and columns contain different sample values (2 dimensional variability).

    Parameters
    ----------
    shape : tuple
        Shape (rows, columns).
    low : float
        Lower bound of the triangular distribution to be sampled.
    high : float
        Upper bound of the triangular distribution to be sampled.
    mode : float
        Mode of the triangular distribution to be sampled.
    seed : int | Generator | None, optional
        A seed to initialize the BitGenerator. If passed a Generator, it will be returned unaltered. If `None`, then
        fresh, unpredictable entropy will be pulled from the OS.

    Returns
    -------
    NDArray
        Array of samples with 2 dimensional variability.
    """
    rng = random.default_rng(seed)
    return rng.triangular(left=low, mode=mode, right=high, size=shape)


def normal_1d(
    shape: tuple,
    mu: float,
    sigma: float,
    seed: Union[int, random.Generator, None] = None,
) -> NDArray:
    """
    Sample from a normal distribution and produce an array of a specified shape.
    All rows in a specified column will have the same sample value, but each column will be different (1 dimensional
    variability).

    Parameters
    ----------
    shape : tuple
        Shape (rows, columns).
    mu : float
        Mean of the normal distribution to be sampled.
    sigma : float
        Standard deviation of the normal distribution to be sampled.
    seed : int | Generator | None, optional
        A seed to initialize the BitGenerator. If passed a Generator, it will be returned unaltered. If `None`, then
        fresh, unpredictable entropy will be pulled from the OS.

    Returns
    -------
    NDArray
        Array of samples with 1 dimensional variability.
    """
    n_rows, n_columns = shape
    rng = random.default_rng(seed)
    return repeat_array_as_rows(n_rows, rng.normal(loc=mu, scale=sigma, size=n_columns))


def normal_2d(
    shape: tuple,
    mu: float,
    sigma: float,
    seed: Union[int, random.Generator, None] = None,
) -> NDArray:
    """
    Sample from a normal distribution and produce an array of a specified shape.
    All rows and columns contain different sample values (2 dimensional variability).

    Parameters
    ----------
    shape : tuple
        Shape (rows, columns).
    mu : float
        Mean of the normal distribution to be sampled.
    sigma : float
        Standard deviation of the normal distribution to be sampled.
    seed : int | Generator | None, optional
        A seed to initialize the BitGenerator. If passed a Generator, it will be returned unaltered. If `None`, then
        fresh, unpredictable entropy will be pulled from the OS.

    Returns
    -------
    NDArray
        Array of samples with 2 dimensional variability.
    """
    rng = random.default_rng(seed)
    return rng.normal(loc=mu, scale=sigma, size=shape)


def truncated_normal_1d(
    shape: tuple,
    mu: float,
    sigma: float,
    low: float,
    high: float,
    seed: Union[int, random.Generator, None] = None,
) -> NDArray:
    """
    Sample from a truncated normal distribution and produce an array of a specified shape.
    All rows in a specified column will have the same sample value, but each column will be different (1 dimensional
    variability).

    Parameters
    ----------
    shape : tuple
        Shape (rows, columns).
    mu : float
        Mean of the normal distribution to be sampled.
    sigma : float
        Standard deviation of the normal distribution to be sampled.
    low : float
        Lower bound of the normal distribution to be sampled.
    high : float
        Upper bound of the normal distribution to be sampled.
    seed : int | Generator | None, optional
        A seed to initialize the BitGenerator. If passed a Generator, it will be returned unaltered. If `None`, then
        fresh, unpredictable entropy will be pulled from the OS.

    Returns
    -------
    NDArray
        Array of samples with 1 dimensional variability.
    """
    n_rows, n_columns = shape
    return repeat_array_as_rows(
        n_rows,
        truncnorm_rvs(a=low, b=high, loc=mu, scale=sigma, shape=n_columns, seed=seed),
    )


def truncated_normal_2d(
    shape: tuple,
    mu: float,
    sigma: float,
    low: float,
    high: float,
    seed: Union[int, random.Generator, None] = None,
) -> NDArray:
    """
    Sample from a truncated normal distribution and produce an array of a specified shape.
    All rows and columns contain different sample values (2 dimensional variability).

    Parameters
    ----------
    shape : tuple
        Shape (rows, columns).
    mu : float
        Mean of the normal distribution to be sampled.
    sigma : float
        Standard deviation of the normal distribution to be sampled.
    low : float
        Lower bound of the normal distribution to be sampled.
    high : float
        Upper bound of the normal distribution to be sampled.
    seed : int | Generator | None, optional
        A seed to initialize the BitGenerator. If passed a Generator, it will be returned unaltered. If `None`, then
        fresh, unpredictable entropy will be pulled from the OS.

    Returns
    -------
    NDArray
        Array of samples with 2 dimensional variability.
    """
    return truncnorm_rvs(a=low, b=high, loc=mu, scale=sigma, shape=shape, seed=seed)


def plus_minus_uncertainty_to_normal_1d(
    shape: tuple,
    value: float,
    uncertainty: float,
    confidence_interval: float = 95,
    seed: Union[int, random.Generator, None] = None,
) -> NDArray:
    """
    Return a normally distributed sample given a value and uncertainty expressed as +/- a percentage.

    All rows in a specified column will have the same sample value, but each column will be different (1 dimensional
    variability).

    This function has been written to serve Table 5.5b on Page 5.32, Tier 2 Steady State Method for Mineral Soils,
    Chapter 5 Cropland, 2019 Refinement to the 2006 IPCC Guidelines for National Greenhouse Gas Inventories. Table 5.5b
    notes:

        "Uncertainty is assumed to be ±75% for the N content estimates and ±50% for the lignin content estimates,
        expressed as a 95% confidence intervals."

    This function also serves Table 11.2 on Page 11.19, Tier 2 Steady State Method for Mineral Soils, Chapter 11 N2O
    Emissions from Managed Soils, and CO2 Emissions from Lime and Urea Application, 2019 Refinement to the 2006 IPCC
    Guidelines for National Greenhouse Gas Inventories.

    Parameters
    ----------
    shape : tuple
        Shape (rows, columns).
    value : float
        Reported value.
    uncertainty : float
        Uncertainty expressed as +/- a percentage.
    confidence_interval : float
        Confidence interval the uncertainty represents.
    seed : int | Generator | None, optional
        A seed to initialize the BitGenerator. If passed a Generator, it will be returned unaltered. If `None`, then
        fresh, unpredictable entropy will be pulled from the OS.

    Returns
    -------
    NDArray
        Array of samples with 1 dimensional variability.
    """
    n_rows, n_columns = shape
    n_sds = calc_z_critical(confidence_interval)
    sigma = (value * (uncertainty / 100)) / n_sds
    return repeat_array_as_rows(
        n_rows, normal_1d(shape=(1, n_columns), mu=value, sigma=sigma, seed=seed)
    )


def plus_minus_uncertainty_to_normal_2d(
    shape: tuple,
    value: float,
    uncertainty: float,
    confidence_interval: float = 95,
    seed: Union[int, random.Generator, None] = None,
) -> NDArray:
    """
    Return a normally distributed sample given a value and uncertainty expressed as +/- a percentage.

    All rows and columns contain different sample values (2 dimensional variability).

    This function has been written to serve Table 5.5b on Page 5.32, Tier 2 Steady State Method for Mineral Soils,
    Chapter 5 Cropland, 2019 Refinement to the 2006 IPCC Guidelines for National Greenhouse Gas Inventories. Table 5.5b
    notes:

        "Uncertainty is assumed to be ±75% for the N content estimates and ±50% for the lignin content estimates,
        expressed as a 95% confidence intervals."

    This function also serves Table 11.2 on Page 11.19, Tier 2 Steady State Method for Mineral Soils, Chapter 11 N2O
    Emissions from Managed Soils, and CO2 Emissions from Lime and Urea Application, 2019 Refinement to the 2006 IPCC
    Guidelines for National Greenhouse Gas Inventories.

    Parameters
    ----------
    shape : tuple
        Shape (rows, columns).
    value : float
        Reported value.
    uncertainty : float
        Uncertainty expressed as +/- a percentage.
    confidence_interval : float
        Confidence interval the uncertainty represents.
    seed : int | Generator | None, optional
        A seed to initialize the BitGenerator. If passed a Generator, it will be returned unaltered. If `None`, then
        fresh, unpredictable entropy will be pulled from the OS.

    Returns
    -------
    NDArray
        Array of samples with 2 dimensional variability.
    """
    n_sds = calc_z_critical(confidence_interval)
    sigma = (value * (uncertainty / 100)) / n_sds
    return normal_2d(shape=shape, mu=value, sigma=sigma, seed=seed)


def grouped_avg(arr: NDArray, n: int = 12) -> NDArray:
    """Row-wise averaging of numpy arrays. For example:
    1   2   3
    4   5   6
    7   8   9
    10  11  12
    13  14  15
    16  17  18

    if n = 6, becomes:
    8.5 9.5 10.5

    because:
    (1 + 4 + 7 + 10 + 13 + 16) / 6 = 8.5
    (2 + 5 + 8 + 11 + 14 + 17) / 6 = 9.5
    etc.

    if n = 2, becomes:
    2.5  3.5  4.5
    8.5  9.5  10.5
    14.5 15.5 16.5

    because:
    (in column 0) (1 + 4) / 2 = 2.5, (7 + 10) / 2 = 8.5, (13 + 16) / 2 = 14.5
    (in column 1) (2 + 5) / 2 = 3.5, (8 + 11) / 2 = 9.5, (14 + 17) / 2 = 15.5

    Source: https://stackoverflow.com/questions/30379311/fast-way-to-take-average-of-every-n-rows-in-a-npy-array

    Parameters
    ----------
    arr : NDArray
        Input array.
    n : int, optional
        Number of rows to average. Defaults to 12.

    Returns
    -------
    NDArray
        Output array
    """
    result = cumsum(arr, 0)[n - 1 :: n] / float(n)
    result[1:] = result[1:] - result[:-1]
    return result


def avg_run_in_columnwise(arr: NDArray, n: int):
    """
    Reduce the first `n` elements of each column in an array by averaging them, while leaving the rest of the array
    modified.

    Parameters
    ----------
    arr : NDArray
        Input array.
    n : int
        The number of run-in elements to average.

    Returns
    -------
    NDArray
        The new array where the first element in each column is an average of the run in elements.
    """
    run_in: NDArray = mean(arr[:n], 0)
    return vstack([run_in, arr[n:]])


def avg_run_in_rowwise(arr: NDArray, n: int):
    """
    Reduce the first `n` elements of each row in an array by averaging them, while leaving the rest of the array
    modified.

    Parameters
    ----------
    arr : NDArray
        Input array.
    n : int
        The number of run-in elements to average.

    Returns
    -------
    NDArray
        The new array where the first element in each row is an average of the run in elements.
    """
    return avg_run_in_columnwise(arr.transpose(), n).transpose()


def gen_seed(node: dict, *args: tuple[str]) -> int:
    """
    Generate a seed based on a node's `@id` and optional args so that rng is the same each time the model is re-run.
    """
    node_id = node.get("@id", "")
    seed_str = "".join([node_id] + [str(arg) for arg in args])
    hashed = hashlib.shake_128(seed_str.encode(), usedforsecurity=False).hexdigest(4)
    return abs(int(hashed, 16))


def correlated_normal_2d(
    n_iterations: int,
    means: NDArray,
    sds: NDArray,
    correlation_matrix: NDArray,
    seed: Union[int, random.Generator, None] = None,
) -> NDArray:
    """
    Generate correlated random samples from a multivariate normal distribution with specified means, standard
    deviations, and a correlation matrix. Each row represents a different variable (e.g., different years), and each
    column represents a different iteration (sample).

    Parameters
    ----------
    n_iterations : int
        The number of samples (iterations) to generate for each variable.
    means : NDArray
        An array of mean values for each variable (row).
    sds : NDArray
        An array of standard deviations for each variable (row).
    correlation_matrix : NDArray
        A positive-definite matrix representing the correlations between the variables (rows).
    seed : int | Generator | None, optional
        A seed to initialize the BitGenerator. If passed a Generator, it will be returned unaltered. If `None`, then
        fresh, unpredictable entropy will be pulled from the OS.

    Returns
    -------
    NDArray
        A 2D array of shape (len(means), n_iterations), where each row corresponds to a different variable and each
        column corresponds to a sample iteration. The values in each row are correlated according to the provided
        correlation matrix.
    """
    # Generate independent random samples for each year
    shape = (len(means), n_iterations)
    independent_samples = normal_2d(shape, 0, 1, seed=seed)

    # Apply Cholesky decomposition to the correlation matrix
    cholesky_decomp = linalg.cholesky(correlation_matrix)

    # Apply Cholesky transformation to introduce correlation across years (rows) for each sample
    correlated_samples = dot(cholesky_decomp, independent_samples)

    # Scale by standard deviations and shift by means
    scaled_samples = correlated_samples * repeat_1d_array_as_columns(
        n_iterations, sds
    ) + repeat_1d_array_as_columns(n_iterations, means)

    return scaled_samples


def calc_z_critical(confidence_interval: float, n_sided: int = 2) -> float64:
    """
    Calculate the z-critical value from the confidence interval.

    Parameters
    ----------
    confidence_interval : float
        The confidence interval as a percentage between 0 and 100%.
    n_sided : int, optional
        The number of tails (default value = `2`).

    Returns
    -------
    float64
        The z-critical value as a floating point between 0 and infinity.
    """
    alpha = 1 - confidence_interval / 100
    return _normal_ppf(1 - alpha / n_sided)


def _normal_ppf(q: float64, tol: float64 = 1e-10) -> float64:
    """
    Calculates the percent point function (PPF), also known as the inverse cumulative distribution function (CDF), of a
    standard normal distribution using the Newton-Raphson method.

    Parameters
    ----------
    q : float64
        The quantile at which to evaluate the PPF.
    tol : float64, optional
        The tolerance for the Newton-Raphson method. Defaults to 1e-10.

    Returns
    -------
    float64
        The PPF value at the given quantile.
    """
    INITIAL_GUESS = 0
    MAX_ITER = 100

    def step(x):
        """Perform one step of the Newton-Raphson method."""
        x_new = x - (_normal_cdf(x) - q) / _normal_pdf(x)
        return x_new if abs(x_new - x) >= tol else x

    return (
        inf
        if q == 1
        else (
            -inf
            if q == 0
            else reduce(lambda x, _: step(x), range(MAX_ITER), INITIAL_GUESS)
        )
    )


def _normal_cdf(x: float64) -> float64:
    """
    Calculates the cumulative distribution function (CDF) of a standard normal distribution for a single value using a
    custom error function (erf).

    Parameters
    ----------
    x : float64
        The point at which to evaluate the CDF.

    Returns
    -------
    float64
        The CDF value at the given point.
    """
    return 0.5 * (1 + _erf(x / sqrt(2)))


def _erf(x: float64) -> float64:
    """
    Approximates the error function of a standard normal distribution using a numerical approximation based on
    Abramowitz and Stegun formula 7.1.26.

    Parameters
    ----------
    x : float64
        The input value.

    Returns
    -------
    float64
        The approximated value of the error function.
    """
    # constants
    A_1 = 0.254829592
    A_2 = -0.284496736
    A_3 = 1.421413741
    A_4 = -1.453152027
    A_5 = 1.061405429
    P = 0.3275911

    # Save the sign of x
    sign_ = sign(x)
    x_ = abs(x)

    # A&S formula 7.1.26
    t = 1.0 / (1.0 + P * x_)
    y = 1.0 - (((((A_5 * t + A_4) * t) + A_3) * t + A_2) * t + A_1) * t * exp(-x_ * x_)

    return sign_ * y


def _normal_pdf(x: float64) -> float64:
    """
    Calculates the probability density function (PDF) of a standard normal distribution for a single value.

    Parameters
    ----------
    x : float64
        The point at which to evaluate the PDF.

    Returns
    -------
    float64
        The PDF value at the given point.
    """
    return 1 / sqrt(2 * pi) * exp(-0.5 * x**2)


def _calc_confidence_level(z_critical: float64, n_sided: int = 2) -> float64:
    """
    Calculate the confidence interval from the z-critical value.

    Parameters
    ----------
    z_critical_value : np.float64
        The confidence interval as a floating point number between 0 and infinity.
    n_sided : int, optional
        The number of tails (default value = `2`).

    Returns
    -------
    np.float64
        The confidence interval as a percentage between 0 and 100%.
    """
    alpha = (1 - _normal_cdf(z_critical)) * n_sided
    return (1 - alpha) * 100


def calc_required_iterations_monte_carlo(
    confidence_level: float, precision: float, sd: float
) -> int:
    """
    Calculate the number of iterations required for a Monte Carlo simulation to have a desired precision, subject to a
    given confidence level.

    Parameters
    ----------
    confidence_level : float
        The confidence level, as a percentage out of 100, that the precision should be subject too (i.e., we are x%
        sure that the sample mean deviates from the true populatation mean by less than the desired precision).
    precision : float
        The desired precision as a floating point value (i.e., if the Monte Carlo simulation will be used to estimate
        `organicCarbonPerHa` to a precision of 100 kg C ha-1 this value should be 100).
    sd : float
        The standard deviation of the sample. This can be estimated by running the model 500 times (a number that does
        not take too much time to run but is large enough for the sample standard deviation to converge reasonably
        well).

    Returns
    -------
    int
        The required number of iterations.
    """
    z_critical_value = calc_z_critical(confidence_level)
    return round(((sd * z_critical_value) / precision) ** 2)


def calc_confidence_level_monte_carlo(
    n_iterations: int, precision: float, sd: float
) -> float:
    """
    Calculate the confidence level that the sample mean calculated by the Monte Carlo simulation deviates from the
    true population mean by less than the desired precision.

    Parameters
    ----------
    n_iterations : int
        The number of iterations that the Monte Carlo simulation was run for.
    precision : float
        The desired precision as a floating point value (i.e., if the Monte Carlo simulation will be used to estimate
        `organicCarbonPerHa` to a precision of 100 kg C ha-1 this value should be 100).
    sd : float
        The standard deviation of the sample.

    Returns
    -------
    float
        The confidence level, as a percentage out of 100, that the precision should be subject too (i.e., we are x%
        sure that the sample mean deviates from the true populatation mean by less than the desired precision).
    """
    return _calc_confidence_level(precision * sqrt(n_iterations) / sd)


def calc_precision_monte_carlo(
    confidence_level: float, n_iterations: int, sd: float
) -> float:
    """
    Calculate the +/- precision of a Monte Carlo simulation for a desired confidence level.

    Parameters
    ----------
    confidence_level : float
        The confidence level, as a percentage out of 100, that the precision should be subject too (i.e., we are x%
        sure that the sample mean deviates from the true populatation mean by less than the desired precision).
    n_iterations : int
        The number of iterations that the Monte Carlo simulation was run for.
    sd : float
        The standard deviation of the sample.

    Returns
    -------
    float
        The precision of the sample mean estimated by the Monte Carlo model as a floating point value with the same
        units as the estimated mean.
    """
    z_critical = calc_z_critical(confidence_level)
    return (sd * z_critical) / sqrt(n_iterations)


def truncnorm_rvs(
    a: float,
    b: float,
    loc: float,
    scale: float,
    shape: Union[int, tuple[int, ...]],
    seed: Union[int, random.Generator, None] = None,
) -> NDArray:
    """
    Generate random samples from a truncated normal distribution. Unlike the `scipy` equivalent, the `a` and `b` values
    are the abscissae at which we wish to truncate the distribution (as opposed to the number of standard deviations
    from `loc`).

    Parameters
    ----------
    a : float
        The lower bound of the distribution.
    b : float
        The upper bound of the distribution.
    loc : float
        Mean ("centre") of the distribution.
    scale : float
        Standard deviation (spread or "width") of the distribution. Must be non-negative.
    size : int | tuple[int, ...]
        Output shape. If the given shape is, e.g., (m, n, k), then m * n * k samples are drawn.
    seed : int | Generator | None, optional
        A seed to initialize the BitGenerator. If passed a Generator, it will be returned unaltered. If `None`, then
        fresh, unpredictable entropy will be pulled from the OS.

    Returns
    -------
    NDArray
        Array of samples.
    """
    size = prod(shape)
    samples = array([])
    rng = random.default_rng(seed)

    while samples.size < size:
        samples_temp = rng.normal(loc, scale, (size - samples.size) * 2)
        valid_samples = samples_temp[(a <= samples_temp) & (samples_temp <= b)]
        samples = concatenate([samples, valid_samples])

    return samples[:size].reshape(shape)


def add_normal_distributions(
    mu_1: float, sigma_1: float, mu_2: float, sigma_2: float, rho: float = 0
) -> tuple[float, float]:
    """
    Add together two normal distributions, with optional correlation.

    Given two normal distributions **X<sub>1</sub> ~ N(mu<sub>1</sub>, sigma<sub>1</sub><sup>2</sup>)** and
    **X<sub>2</sub> ~ N(mu<sub>2</sub>, sigma<sub>2</sub><sup>2</sup>)**, this function calculates the resulting mean
    and standard deviation of the sum **Z = X<sub>1</sub> + X<sub>2</sub>**, taking into account the correlation
    between them.

    n.b. Positive correlations (`rho` > `0`) increase the standard deviation of **Z** because positively correlated
    variables tend to move together, increasing combined uncertainty. Negative correlations (`rho` < `0`) reduces the
    standard deviation since the variables move in opposite directions, cancelling out some of the variability.
    Independant variables (`rho` = `0`) result in an intermediate level of uncertainty.

    Parameters
    ----------
    mu_1 : float
        Mean of the first normal distribution (X<sub>1</sub>).
    sigma_1 : float
        Standard deviation of the first normal distribution (X<sub>1</sub>).
    mu_2 : float
        Mean of the second normal distribution (X<sub>2</sub>).
    sigma_2 : float
        Standard deviation of the second normal distribution (X<sub>2</sub>).
    rho : float, optional
        Correlation coefficient between **X<sub>1</sub>** and **X<sub>2</sub>**. `rho` must be a value between -1
        (perfectly negative correlation) and 1 (perfectly positive correlation). Default is 0 (independent variables).

    Returns
    -------
    tuple[float, float]
        A tuple in the shape `(mu_sum, sigma_sum)` containing the mean and standard deviation of the distribution
        **Z = X<sub>1</sub> + X<sub>2</sub>**.
    """
    mu_sum = mu_1 + mu_2
    sigma_sum = sqrt(sigma_1**2 + sigma_2**2 + 2 * rho * sigma_1 * sigma_2)
    return mu_sum, sigma_sum


def subtract_normal_distributions(
    mu_1: float, sigma_1: float, mu_2: float, sigma_2: float, rho: float = 0
) -> tuple[float, float]:
    """
    Subtract a normal distribution from another, with optional correlation.

    Given two normal distributions **X<sub>1</sub> ~ N(mu<sub>1</sub>, sigma<sub>1</sub><sup>2</sup>)** and
    **X<sub>2</sub> ~ N(mu<sub>2</sub>, sigma<sub>2</sub><sup>2</sup>)**, this function calculates the resulting mean
    and standard deviation of the difference **Z = X<sub>1</sub> - X<sub>2</sub>**, taking into account the correlation
    between them.

    n.b. Positive correlations (`rho` > `0`) reduce the standard deviation of **Z** because positively correlated
    variables tend to move together, cancelling out some of the variability when subtracted. Negative correlations
    (`rho` < `0`) increase the standard deviation since the variables move in opposite directions, amplifying the
    variability when subtracted. Independant variables (`rho` = `0`) result in an intermediate level of uncertainty.

    Parameters
    ----------
    mu_1 : float
        Mean of the first normal distribution (X<sub>1</sub>).
    sigma_1 : float
        Standard deviation of the first normal distribution (X<sub>1</sub>).
    mu_2 : float
        Mean of the second normal distribution (X<sub>2</sub>).
    sigma_2 : float
        Standard deviation of the second normal distribution (X<sub>2</sub>).
    rho : float, optional
        Correlation coefficient between **X<sub>1</sub>** and **X<sub>2</sub>**. `rho` must be a value between -1
        (perfectly negative correlation) and 1 (perfectly positive correlation). Default is 0 (independent variables).

    Returns
    -------
    tuple[float, float]
        A tuple in the shape `(mu_diff, sigma_diff)` containing the mean and standard deviation of the distribution
        **Z = X<sub>1</sub> - X<sub>2</sub>**.
    """
    mu_sum = mu_1 - mu_2
    sigma_sum = sqrt(sigma_1**2 + sigma_2**2 - 2 * rho * sigma_1 * sigma_2)
    return mu_sum, sigma_sum


def lerp_normal_distributions(
    mu_1: float,
    sigma_1: float,
    mu_2: float,
    sigma_2: float,
    alpha: float,
    rho: float = 0,
) -> tuple[float, float]:
    """
    Linearly interpolate between two normal distributions, with optional correlation.

    Given two normal distributions **X<sub>1</sub> ~ N(mu<sub>1</sub>, sigma<sub>1</sub><sup>2</sup>)** and
    **X<sub>2</sub> ~ N(mu<sub>2</sub>, sigma<sub>2</sub><sup>2</sup>)**, this function calculates the resulting mean
    and standard deviation of the interpolated distribution **Z = (1 - alpha) * X<sub>1</sub> + alpha * X<sub>2</sub>**,
    taking into account the correlation between them.

    n.b. Positive correlations (`rho` > `0`) increase the standard deviation of **Z** because positively correlated
    variables tend to move together, increasing combined uncertainty. Negative correlations (`rho` < `0`) reduces the
    standard deviation since the variables move in opposite directions, cancelling out some of the variability.
    Independant variables (`rho` = `0`) result in an intermediate level of uncertainty.

    Parameters
    ----------
    mu_1 : float
        Mean of the first normal distribution (X<sub>1</sub>).
    sigma_1 : float
        Standard deviation of the first normal distribution (X<sub>1</sub>).
    mu_2 : float
        Mean of the second normal distribution (X<sub>2</sub>).
    sigma_2 : float
        Standard deviation of the second normal distribution (X<sub>2</sub>).
    alpha : float
        Interpolation factor (0 <= alpha <= 1). A value of 0 results in X1, a value of 1 results in X2, and values
        between 0 and 1 interpolate between the two. Values of below 0 and above 1 will extrapolate beyond the
        X<sub>1</sub> and X<sub>2</sub> respectively.
    rho : float, optional
        Correlation coefficient between **X<sub>1</sub>** and **X<sub>2</sub>**. `rho` must be a value between -1
        (perfectly negative correlation) and 1 (perfectly positive correlation). Default is 0 (independent variables).

    Returns
    -------
    tuple[float, float]
        A tuple in the shape `(mu_Z sigma_Z)` containing the mean and standard deviation of the distribution
        **Z = (1 - alpha) * X<sub>1</sub> + alpha * X<sub>2</sub>**.
    """
    mu_Z = (1 - alpha) * mu_1 + alpha * mu_2
    var_Z = (
        ((1 - alpha) ** 2) * sigma_1**2
        + (alpha**2) * sigma_2**2
        + 2 * alpha * (1 - alpha) * rho * sigma_1 * sigma_2
    )
    sigma_Z = sqrt(var_Z)
    return mu_Z, sigma_Z
