"""Tests for ml_inspector.roc_curve"""

import numpy as np
import pytest
from plotly import graph_objs as go

from ml_inspector import plot_roc_curves


class TestROCCurve:
    def test_plot_roc_curves_binary(self, binary_predictions):
        y, y_prob_1, y_prob_2 = binary_predictions
        y_prob = {"Model 1": y_prob_1, "Model 2": y_prob_2}
        class_names = {0: "Class 0", 1: "Class 1"}
        fig = plot_roc_curves(y, y_prob, class_names=class_names)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 3
        assert fig.data[0]["name"] == "Class 1 (Model 1): AUC=1.00"
        assert fig.data[1]["name"] == "Class 1 (Model 2): AUC=0.75"
        assert fig.data[2]["name"] == "Random decision: AUC=0.50"

    def test_plot_roc_curves_multi_class(self, multiclass_predictions):
        y, y_prob_1, y_prob_2 = multiclass_predictions
        y_prob = {"Training": y_prob_1, "Test": y_prob_2}
        class_names = {0: "Class 0", 1: "Class 1", 2: "Class 2", 3: "Class 3"}
        fig = plot_roc_curves(y, y_prob, class_names=class_names)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 11
        assert fig.data[0]["name"] == "Class 0 (Training): AUC=1.00"
        assert fig.data[1]["name"] == "Class 1 (Training): AUC=1.00"
        assert fig.data[2]["name"] == "Class 2 (Training): AUC=1.00"
        assert fig.data[3]["name"] == "Class 3 (Training): AUC=1.00"
        assert fig.data[4]["name"] == "Micro-average ROC curve (Training): AUC=0.96"
        assert fig.data[5]["name"] == "Class 0 (Test): AUC=0.88"
        assert fig.data[-1]["name"] == "Random decision: AUC=0.50"

    def test_plot_roc_curves_error_single_class(self, binary_predictions):
        y, y_prob_1, y_prob_2 = binary_predictions
        y = np.array([0, 0, 0, 0, 0])
        y_prob = {"Model 1": y_prob_1, "Model 2": y_prob_2}
        with pytest.raises(ValueError) as ve:
            plot_roc_curves(y, y_prob)
        assert str(ve.value) == (
            "Metrics curves are not defined for less than two classes"
        )

    def test_plot_roc_curves_with_threshold(self, binary_predictions):
        y, y_prob_1, y_prob_2 = binary_predictions
        y_prob = {"Model 1": y_prob_1, "Model 2": y_prob_2}
        class_names = {0: "Class 0", 1: "Class 1"}
        fig = plot_roc_curves(
            y, y_prob, class_names=class_names, decision_threshold=0.4
        )
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 5
        assert fig.data[0]["name"] == "Decision threshold (40.0%)"
        assert fig.data[1]["name"] == "Class 1 (Model 1): AUC=1.00"
        assert fig.data[2]["name"] == "Decision threshold (40.0%)"
        assert fig.data[3]["name"] == "Class 1 (Model 2): AUC=0.75"
        assert fig.data[4]["name"] == "Random decision: AUC=0.50"

    def test_plot_roc_curves_with_array(self, binary_predictions):
        y, y_prob_1, _ = binary_predictions
        class_names = {0: "Class 0", 1: "Class 1"}
        fig = plot_roc_curves(y, y_prob_1, class_names=class_names)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2
        assert fig.data[0]["name"] == "Class 1 (Predictions): AUC=1.00"
        assert fig.data[1]["name"] == "Random decision: AUC=0.50"
