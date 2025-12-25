"""ROC curves for classification models."""

import logging
from typing import Callable

import plotly.graph_objs as go
from sklearn.metrics import roc_curve

from ml_inspector._metrics_curves import MetricsCurves

logger = logging.getLogger(__name__).setLevel(logging.INFO)


class ROCCurves(MetricsCurves):
    """A class to display ROC curves."""

    def __init__(
        self,
        curve_name: str = "ROC",
        curve_function: Callable = roc_curve,
        xaxis: dict = {"index": 0, "name": "False Positive Rate", "range": (0, 1)},
        yaxis: dict = {"index": 1, "name": "True Positive Rate", "range": (0, 1)},
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


def plot_roc_curves(y_true, y_prob, class_names=None, decision_threshold=None):
    """Plots the ROC curves for a binary or multi-class classification model.

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
        The figure containing the ROC curves.
    """
    fig = ROCCurves().plot_curves(y_true, y_prob, class_names, decision_threshold)
    return fig
