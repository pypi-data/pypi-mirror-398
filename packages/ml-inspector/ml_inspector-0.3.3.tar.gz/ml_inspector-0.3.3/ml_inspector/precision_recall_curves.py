"""Precision-Recall curves for classification models."""

import logging
from typing import Callable

import plotly.graph_objs as go
from sklearn.metrics import precision_recall_curve

from ml_inspector._metrics_curves import MetricsCurves

logger = logging.getLogger(__name__).setLevel(logging.INFO)


class PRCurves(MetricsCurves):

    def __init__(
        self,
        curve_name: str = "Precision-Recall",
        curve_function: Callable = precision_recall_curve,
        xaxis: dict = {"index": 1, "name": "Recall", "range": (0, 1)},
        yaxis: dict = {"index": 0, "name": "Precision", "range": (0, 1)},
        reverse_thresholds: bool = True,
    ) -> None:
        super().__init__(curve_name, curve_function, xaxis, yaxis, reverse_thresholds)

    def add_random_decision(self, y_vals, *args, **kwargs) -> go.Scatter:
        """Returns the metrics values for a random decision.

        Args:
        """
        fig = go.Scatter(
            x=[0, 1],
            y=[min(y_vals), min(y_vals)],
            line={"color": "black", "dash": "dash"},
            name=f"Random decision: AUC={min(y_vals):.2f}",
            mode="lines",
        )
        return fig


def plot_precision_recall_curves(
    y_true, y_prob, class_names=None, decision_threshold=None
):
    """Plots the Precision-Recall curves for a binary or multi-class classification
    model.

    :param array y_true:
        An array containing the true outcomes.
    :param dict y_prob:
        A dictionary containing the predicted probablities for each class, together
        with their labels. For example:
            {"Train": array([[0.3, 0.7], ...]), "Test": array([[0.4, 0.6], ...])}
        In case of binary classification, only the probablities
        for the positive class may be provided. For example:
            {"Model 1": array([0.1, 0.4, ...]), "Model 2": array([0.2, 0.3, ...])}
    :param dict class_names:
        A dictionary containing the name to display for each class. For example:
            {0: "Class 0", 1: "Class 1", ...}).
    :param dict decision_threshold:
        A dictionary containing the threshold indicating where the boolean decision is
        made from probablity predictions (for binary classification models) together
        with their labels. For example:
            {"Train": 0.5, "Test": 0.7}

    :returns plotly.graph_objs.Figure:
        The figure containing the Precision-Recall curves.
    """
    fig = PRCurves().plot_curves(y_true, y_prob, class_names, decision_threshold)
    return fig
