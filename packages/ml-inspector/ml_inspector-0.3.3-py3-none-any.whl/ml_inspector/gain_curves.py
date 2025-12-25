"""Gain curves for classification models."""

import logging
from typing import Callable

import numpy as np
import pandas as pd
import plotly.graph_objs as go

from ml_inspector._metrics_curves import MetricsCurves

logger = logging.getLogger(__name__).setLevel(logging.INFO)


def calculate_gain_curve(y_true: np.ndarray, y_prob: np.ndarray) -> tuple:
    """Calculate the gain curve as a function of the threshold value.

    :param array y_true:
        An array containing the true binary outcomes (0s and 1s).
    :param array y_prob:
        An array containing the predicted probablities for the positive class.

    :returns tuple:
        A tuple containing:
        * the fractions of samples
        * the fractions of detected positive class samples
        * the corresponding thresholds
    """
    y_prob = pd.Series(np.array(y_prob)).sort_values(ascending=False)
    y_true = pd.Series(np.array(y_true)).reindex_like(y_prob)
    recalls = y_true.cumsum() / y_true.sum()
    fractions = [i / len(y_true) for i in range(len(y_true))]
    thresholds = y_prob
    return np.array(fractions), np.array(recalls), np.array(thresholds)


class GainCurves(MetricsCurves):
    """A class to display gain curves."""

    def __init__(
        self,
        curve_name: str = "Gain",
        curve_function: Callable = calculate_gain_curve,
        xaxis: dict = {"index": 0, "name": "Fraction selected", "range": (0, 1)},
        yaxis: dict = {"index": 1, "name": "Fraction detected", "range": (0, 1)},
    ) -> None:
        super().__init__(curve_name, curve_function, xaxis, yaxis)

    def add_random_decision(self, *args, **kwargs) -> go.Scatter:
        """Returns the metrics values for a random decision."""
        fig = go.Scatter(
            x=[0, 1],
            y=[0, 1],
            line={"color": "black", "dash": "dash"},
            name="Random decision: AUC=0.50",
            mode="lines",
        )
        return fig


def plot_gain_curves(y_true, y_prob, class_names=None, decision_threshold=None):
    """Plots the gain curves for a binary or multi-class classification model.

    :param array y_true:
        An array containing the true outcomes.
    :param dict y_prob:
        A dictionary containing the predicted probablities for each class, together
        with their labels. For example:
            {"Train": array([[0.3, 0.7], ...]), "Test": array([[0.4, 0.6], ...])}
        In case of binary classification, only the probablities
        for the positive class may be provided. For example:
            {"Model 1": array([0.1, 0.4]), "Model 2": array([0.2, 0.3])}
        Alternatively, a single array may be provided. For example:
            array([[0.1, 0.9], [0.2, 0.8], ...])
    :param dict class_names:
        A dictionary containing the name to display for each class. For example:
            {0: "Class 0", 1: "Class 1", ...}).
    :param dict decision_threshold:
        A dictionary containing the threshold indicating where the boolean decision is
        made from probablity predictions (for binary classification models) together
        with their labels. For example:
            {"Train": 0.5, "Test": 0.7}

    :returns plotly.graph_objs.Figure:
        The figure containing the gain curves.
    """
    fig = GainCurves().plot_curves(y_true, y_prob, class_names, decision_threshold)
    return fig
