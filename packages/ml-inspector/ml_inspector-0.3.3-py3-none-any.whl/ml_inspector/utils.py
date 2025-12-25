def remove_outliers(series, q_min=0.01, q_max=0.99, sigma_factor=1):
    """Removes the outliers from a pandas Series by selecting the values
    between a minimum and maximum quantiles to which can be added a
    number of standard deviations.

    :param pandas.Series series:
        The pandas Series for which to remove the outliers.
    :param float q_min:
        The lower quantile below which to filter values.
    :param float q_max:
        The higher quantile above which to filter values.
    :param float sigma_factor:
        The number of standard deviations to include above and below the higher
        and lower quantiles when filtering the data.

    :returns pandas.Series
        The pandas Series without its outliers.
    """
    lower_limit = series.quantile(q_min) - sigma_factor * series.std()
    upper_limit = series.quantile(q_max) + sigma_factor * series.std()
    return series[series.between(lower_limit, upper_limit)].copy()
