"""Calibration curves for classification models."""

import logging

import numpy as np
import pandas as pd
import plotly.graph_objs as go
from plotly.colors import DEFAULT_PLOTLY_COLORS
from statsmodels.stats.proportion import proportion_confint

logger = logging.getLogger(__name__)


def plot_calibration_curves(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    class_names: dict = None,
    ci: float = 0.90,
    n_bins: int = 10,
):
    """Plots the calibration curve for predicted vs actual class probabilities for a
    binary or multi-class classification model.

    Args:
        y_true (array): An array containing the true outcomes.
        y_prob (array): An array containing the predicted probabilities.
        class_names (dict): A dictionary containing the name to display for each class
            (e.g. {1: "Class 1", 2: "Class 2", ...}).
        ci (float): The confidence interval to use for the calibration curve error bars.
        n_bins (int): The number of bins to build the calibration curve.

    Returns:
        go.Figure: The calibration curve.
    """
    classes = np.unique(y_true)
    if not class_names:
        class_names = {c: str(c) for c in classes}
    calibration_curves = calculate_calibration_curves(
        y_true, y_prob, class_names, ci, n_bins
    )
    plot = create_calibration_curve_plot(calibration_curves)
    layout = create_calibration_curve_layout()
    fig = go.Figure(plot, layout)
    return fig


def calculate_calibration_curves(
    y_true: np.ndarray, y_prob: np.ndarray, class_names: dict, ci: float, n_bins: int
):
    """Calculates the calibration curve for each class.

    Args:
        y_true (array): An array containing the true outcomes.
        y_prob (array): An array containing the predicted probabilities.
        class_names (dict): A dictionary containing the name to display for each class
            (e.g. {1: "Class 1", 2: "Class 2", ...}).
        ci (float): The confidence interval to use for the calibration curve error bars.
        n_bins (int): The number of bins to build the calibration curve.

    Returns:
        dict: A dictionary containing the calibration curve for each class.
    """
    df = pd.DataFrame({"y_true": y_true, "y_prob": [x for x in y_prob]})
    cal_curve = {}
    for i, c in enumerate(class_names):
        proba = [x[i] for x in y_prob]
        bins = np.linspace(0, 1, num=n_bins + 1)
        proba_bins = pd.cut(
            proba, bins=bins, labels=(bins[:-1] + bins[1:]) / 2, include_lowest=True
        ).astype(float)
        df["is_true_class"] = (df["y_true"] == c).astype(float)
        avg_class = df.groupby(proba_bins)["is_true_class"].mean()
        correct = df.groupby(proba_bins)["is_true_class"].sum()
        counts = df.groupby(proba_bins).size()
        ci_plus, ci_minus = proportion_confint(
            count=correct, nobs=counts, alpha=1 - ci, method="wilson"
        )
        cal_curve[class_names[c]] = {
            "predicted": avg_class.index,
            "actual": avg_class,
            "counts": counts.tolist(),
            "error_plus": (ci_plus - avg_class),
            "error_minus": (avg_class - ci_minus),
        }
    return cal_curve


def create_calibration_curve_plot(calibration_curves):
    """Creates the data for the calibration curves plot.

    :param dict calibration_curves:
        A dictionary containing the calibration curves to plot.

    :returns list:
        A list of plotly traces containing the calibration curves.
    """
    plots = [
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            line={"dash": "dash", "color": "black"},
            showlegend=False,
        )
    ]
    for i, c in enumerate(calibration_curves):
        color = DEFAULT_PLOTLY_COLORS[i]
        plots.append(
            go.Scatter(
                x=calibration_curves[c]["predicted"],
                y=calibration_curves[c]["actual"],
                mode="markers",
                error_y={
                    "type": "data",
                    "array": calibration_curves[c]["error_plus"],
                    "arrayminus": calibration_curves[c]["error_minus"],
                },
                marker_color=color,
                legendgroup=c,
                legendgrouptitle={"text": c},
                name="Probabilities",
            )
        )
        plots.append(
            go.Bar(
                x=calibration_curves[c]["predicted"],
                y=calibration_curves[c]["counts"],
                yaxis="y2",
                opacity=0.2,
                marker_color=color,
                legendgroup=c,
                name="Number of outcomes",
            )
        )
    return plots


def create_calibration_curve_layout():
    """Creates the layout for the calibration curves plot.

    :returns plotly.graph_objs.Layout:
        The layout for the plotly calibration curves plot.
    """
    layout = go.Layout(
        xaxis={"title": "Predicted probability", "range": [0, 1]},
        yaxis={"title": "Actual probability", "range": [0, 1]},
        yaxis2={
            "title": "Number of outcomes",
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
        },
        legend={"traceorder": "grouped", "orientation": "h", "y": -0.1},
        width=800,
        height=800,
    )
    return layout
