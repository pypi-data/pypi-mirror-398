from typing import Callable

import numpy as np
import plotly.graph_objects as go
from plotly.colors import DEFAULT_PLOTLY_COLORS
from sklearn.metrics import auc
from sklearn.preprocessing import label_binarize


class MetricsCurves:
    """A class to display metrics curves for classification models.

    Args:
        curve_name (str): The name of the metrics to be displayed.
        curve_function (Callable): The function to calculate the metrics curve.
        xaxis (dict): A dictionary containing the x-axis information, including the
            index in the curve data, the name and the range.
        yaxis (dict): A dictionary containing the y-axis information, including the
            index in the curve data, the name and the range.
    """

    def __init__(
        self,
        curve_name: str,
        curve_function: Callable,
        xaxis: dict,
        yaxis: dict,
        reverse_thresholds: bool = False,
    ) -> None:
        self.curve_name = curve_name
        self.curve_function = curve_function
        self.xaxis = xaxis
        self.yaxis = yaxis
        self.reverse_thresholds = reverse_thresholds

    def plot_curves(
        self,
        y_true: np.ndarray,
        y_prob: dict[str, np.ndarray] | np.ndarray,
        class_names: dict | None = None,
        decision_threshold: float | None = None,
    ) -> go.Figure:
        """Plots the metrics curves based on the ground truth and predictions.

        Args:
            y_true (array): An array containing the true outcomes.
            y_prob (dict): A dictionary containing the predicted probablities for
                each class, together with their labels. For example:
                {"Train": [[0.3, 0.7], ...], "Test": [[0.4, 0.6], ...]}
                In case of binary classification, only the probablities
                for the positive class may be provided. For example:
                {"Model 1": [0.1, 0.4, ...], "Model 2": [0.2, 0.3, ...]}
                Alternatively, a single array may be provided. For example:
                [[0.1, 0.9], [0.2, 0.8], ...]
            class_names (dict): A dictionary containing the name to display
                for each class. For example: {0: "Class 0", 1: "Class 1", ...}).
            decision_threshold (float): The probablity above which the class
                is predicted (for binary classification models only).
        """
        y_prob = {"Predictions": y_prob} if isinstance(y_prob, np.ndarray) else y_prob
        classes = np.unique(y_true)
        if len(classes) < 2:
            raise ValueError("Metrics curves are not defined for less than two classes")
        curves_data = self.calculate_curves_data(y_true, y_prob, classes)
        if class_names is None:
            class_names = {c: str(c) for c in classes}
        fig = self.create_curves_plot(curves_data, class_names, decision_threshold)
        return fig

    def calculate_curves_data(
        self, y_true: np.ndarray, y_prob: dict[str, np.ndarray], classes: list
    ) -> dict[str, tuple]:
        """Calculates the metrics curves.

        Args:
            y_true (array): An array containing the true outcomes.
            y_prob (dict): A dictionary containing the predicted probablities for
                each class.
            classes (list): A list containing the class labels.

        Returns:
            dict: The metrics curves for each class.
        """
        curves_data = {}
        for k, values in y_prob.items():
            if len(classes) == 2:
                curves_data[k] = self.get_binary_curve(y_true, values)
            else:
                curves_data[k] = self.get_multiclass_curve(y_true, values, classes)
        return curves_data

    def get_binary_curve(self, y_true: np.ndarray, y_prob: np.ndarray) -> dict:
        """Calculates the metrics curve for binary classification models.

        Args:
            y_true (array): An array containing the true outcomes.
            y_prob (array): An array containing the predicted probablities. If y_prob
                contains probablities for both classes, the curve is calculated for
                the positive class.

        Returns:
            dict: The metrics curve data for the positive class.
        """
        curve_data = {}
        if y_prob.shape[1] == 2:
            y_prob = y_prob[:, 1]
        curve_data[1] = self.curve_function(y_true, y_prob)
        return curve_data

    def get_multiclass_curve(
        self, y_true: np.ndarray, y_prob: np.ndarray, classes: list
    ) -> dict:
        """Calculates the metrics curve for multi-class classification models for each
        class as well as for the micro-average.

        Args:
            y_true (array): An array containing the true outcomes.
            y_prob (array): An array containing the predicted probablities for each
                class.
            classes (list): A list containing the class labels.

        Returns:
            dict: The metrics curve data for each class and the micro-average.
        """
        curve_data = {}
        for i, c in enumerate(classes):
            curve_data[c] = self.curve_function(y_true == c, y_prob[:, i])
        curve_data["Average"] = self.curve_function(
            label_binarize(y_true, classes=classes).ravel(), y_prob.ravel()
        )
        return curve_data

    def create_curves_plot(self, curves: dict, class_names: list, threshold: float):
        """Generates a plotly figure of the metrics curves.

        Args:
            curves (dict): A dictionary containing the metrics curves to display.
            class_names (dict): A dictionary containing the name to display for each
                class. For example: {1: "Class 1", 2: "Class 2", ...}.
            threshold (float): The probablity above which the class is predicted
                (for binary classification models only).

        Returns:
            go.Figure: The figure containing the metrics curves.
        """
        data = self.create_curves_plot_data(curves, class_names, threshold)
        layout = self.create_curves_plot_layout()
        fig = go.Figure(data=data, layout=layout)
        return fig

    def create_curves_plot_data(
        self, curves: dict, class_names: dict, threshold: float
    ):
        """Creates the data for the metrics curves plot.

        Args:
            curves (dict): A dictionary containing the metrics curves to display.
            class_names (dict): A dictionary containing the name to display for each
                class. For example: {1: "Class 1", 2: "Class 2", ...}.
            threshold (float): The probablity above which the class is predicted
                (for binary classification models only).

        Returns:
            list: A list of scatter plots for the metrics curves.
        """
        class_names = class_names.copy()
        if len(class_names) > 2:
            class_names["Average"] = f"Micro-average {self.curve_name} curve"
        lines = ["solid", "dot", "dash", "longdash", "dashdot", "longdashdot"]
        data = []
        for j, type_curves in enumerate(curves):
            for i, c in enumerate(curves[type_curves]):
                curve = curves[type_curves][c]
                color = DEFAULT_PLOTLY_COLORS[i]
                if threshold:
                    showlegend = j == 0 and i == 0
                    data.append(
                        self.plot_threshold(
                            curve, threshold, color, showlegend, legendgroup=str(c)
                        )
                    )
                x_vals = curve[self.xaxis["index"]]
                y_vals = curve[self.yaxis["index"]]
                score = auc(x_vals, y_vals)
                name = f"{class_names[c]} ({type_curves}): AUC={score:.2f}"
                line = {"color": color, "dash": lines[j % len(lines)]}
                data.append(
                    go.Scatter(
                        x=x_vals, y=y_vals, line=line, name=name, legendgroup=str(c)
                    )
                )
        if hasattr(self, "add_random_decision"):
            data.append(self.add_random_decision(x_vals=x_vals, y_vals=y_vals))
        return data

    def plot_threshold(self, curve, threshold, color, showlegend, legendgroup):
        """Plots the decision threshold for binary classification models.

         Args:
            curve (tuple): The curve data as a function of the threshold value.
            threshold (float): The selected decision threshold for the model.
            color (str): The RGB color to display the decision threshold.
            showlegend (bool): A flag to show the legend for the decision threshold.
            legendgroup (str): The legend group to attach the decision threshold to.

        Returns:
            go.Scatter: A scatter plot for the decision threshold.
        """
        x_vals = curve[self.xaxis["index"]]
        y_vals = curve[self.yaxis["index"]]
        thresholds = curve[2]
        index = len([i for i in thresholds if i >= threshold])
        if self.reverse_thresholds:
            index = len(thresholds) - index
        y = y_vals[[index - 1]]
        x = x_vals[[index - 1]]
        params = {
            "line": {"color": "black", "width": 2, "dash": "dot"},
            "name": f"Decision threshold ({threshold:.1%})",
            "legendgroup": legendgroup,
            "mode": "markers",
            "marker": {"color": color, "size": 8},
        }
        return go.Scatter(x=x, y=y, showlegend=showlegend, **params)

    def create_curves_plot_layout(self):
        """Creates the layout for the metrics curves plot.

        Returns:
            go.Layout: The layout for the metrics curves plot.
        """
        layout = go.Layout(
            legend={"traceorder": "grouped", "orientation": "h", "y": -0.1},
            width=800,
            height=800,
            xaxis={"title_text": self.xaxis["name"], "range": self.xaxis["range"]},
            yaxis={"title_text": self.yaxis["name"], "range": self.yaxis["range"]},
        )
        return layout
