"""Learning curves for classification and regression models."""

import logging

import numpy as np
import plotly.graph_objs as go
from plotly.colors import DEFAULT_PLOTLY_COLORS
from sklearn.model_selection import learning_curve
from statsmodels.stats.proportion import proportion_confint

logger = logging.getLogger(__name__)


def plot_learning_curves(
    estimator,
    X,
    y,
    scoring,
    nb_points=10,
    cv=5,
    ci=0.90,
    n_jobs=-1,
):
    """Displays the learning curve for the training data and the cross-validation data
    as a function of the number of samples in the training data.

    :type estimator: A sklearn estimator.
    :param estimator:
        The estimator for which to plot the learning curve.
    :param pandas.DataFrame X:
        A pandas DataFrame containing the features for training the estimator.
    :param pandas.Series y:
        A pandas Series containing the training target variable on which
        to train the estimator.
    :param str scoring:
        A sklearn keyword for the metric used to evaluate the estimator performance.
    :param int nb_points:
        The number of points in the learning curve.
    :param int cv:
        The number of cross-validation folds to use.
    :param int n_jobs:
        The number of parallel jobs to use to evaluate the cross validation score.
    """
    train_sizes, train_scores, val_scores = learning_curve(
        estimator,
        X,
        y,
        cv=cv,
        n_jobs=n_jobs,
        scoring=scoring,
        shuffle=True,
        train_sizes=np.linspace(1 / nb_points, 1.0, nb_points),
    )
    train_scores, val_scores = train_scores.mean(axis=1), val_scores.mean(axis=1)
    plot = create_learning_curves_plot_data(train_sizes, train_scores, val_scores, ci)
    layout = create_learning_curves_plot_layout(scoring)
    fig = go.Figure(plot, layout)
    return fig


def create_learning_curves_plot(train_sizes, train_scores, val_scores, scoring):
    """Generates a plotly figure for the learning curve.

    :param array train_sizes:
        An array containing the training sizes used to generate the learning curve.
    :param array train_scores:
        A 2D array containing the training scores (one per cross-validation fold)
        for each training size.
    :param array val_scores:
        A 2D array containing the validation scores (one per cross-validation fold)
        for each training size.
    :param str scoring:
        A sklearn keyword for the metric used to evaluate the estimator performance.

    :returns plotly.graph_objs.Figure:
        The figure containing the learning curves.
    """
    data = create_learning_curves_plot_data(train_sizes, train_scores, val_scores)
    layout = create_learning_curves_plot_layout(scoring)
    fig = go.Figure(data=data, layout=layout)
    return fig


def create_learning_curves_plot_data(train_sizes, train_scores, val_scores, ci):
    """Creates the data for the plotly learning curve plot.

    :param array train_sizes:
        An array containing the training sizes used to generate the learning curve.
    :param array train_scores:
        A 2D array containing the training scores (one per cross-validation fold)
        for each training size.
    :param array val_scores:
        A 2D array containing the validation scores (one per cross-validation fold)
        for each training size.

    :returns list:
        A list of plotly traces containing the learning curve.
    """
    train_ci_lower, train_ci_upper = get_wilson_ci(train_sizes, train_scores, ci)
    val_ci_lower, val_ci_upper = get_wilson_ci(train_sizes, val_scores, ci)
    plot_data = [
        go.Scatter(
            x=train_sizes,
            y=train_scores,
            error_y={
                "type": "data",
                "array": train_ci_upper,
                "arrayminus": train_ci_lower,
            },
            name="Training score",
            mode="lines+markers",
            marker={"color": DEFAULT_PLOTLY_COLORS[0]},
        ),
        go.Scatter(
            x=train_sizes,
            y=val_scores,
            error_y={"type": "data", "array": val_ci_upper, "arrayminus": val_ci_lower},
            name="Validation score",
            mode="lines+markers",
            marker={"color": DEFAULT_PLOTLY_COLORS[1]},
        ),
    ]
    return plot_data


def get_wilson_ci(sizes, scores, ci):
    """Returns the Wilson confidence interval for a given proportion.

    :returns float:
        The Wilson confidence interval.
    """
    all_negative = False
    if all(scores < 0):
        scores = -scores
        all_negative = True
    ci = [
        proportion_confint(count=score * size, nobs=size, alpha=1 - ci, method="wilson")
        for size, score in zip(sizes, scores)
    ]
    ci_lower_diff = scores - np.array(ci)[:, 0]
    ci_upper_diff = np.array(ci)[:, 1] - scores
    if all_negative:
        ci_lower_diff = -ci_lower_diff
        ci_upper_diff = -ci_upper_diff
    return ci_lower_diff, ci_upper_diff


def create_learning_curves_plot_layout(scoring):
    """Creates the layout for the plotly learning curve plot.

    :param str scoring:
        The name of the metrics for generating the learning curve.

    :returns plotly.graph_objs.Layout:
        The layout for the plotly learning curve plot.
    """
    layout = go.Layout(
        width=800,
        height=600,
        xaxis={"title_text": "Training set size"},
        yaxis={"title_text": f"Score ({scoring})"},
        legend={"orientation": "h", "y": -0.1},
    )
    return layout
