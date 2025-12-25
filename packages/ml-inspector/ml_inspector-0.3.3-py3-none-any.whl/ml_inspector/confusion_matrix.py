"""Functions for plotting confusion matrix for classification models."""

import numpy as np
import plotly.graph_objs as go
from plotly.colors import DEFAULT_PLOTLY_COLORS
from sklearn.metrics import confusion_matrix


def plot_confusion_matrix(y_true, y_pred, class_names):
    """Plots the confusion matrix for a multi class clasification model.
    Normalization can be applied by setting `normalize=True`.

    :param pandas.Series y_true:
        A pandas Series containing the true target values.
    :param pandas.Series y_pred:
        A pandas Series containing the predicted target values.
    :param dict class_names:
        A dictionary containing the name to display for each class
        (e.g. {1: "Class 1", 2: "Class 2", ...}).

    :returns plotly.graph_objs.Figure:
        The figure containing the confusion matrix.
    """
    cm = calculate_confusion_matrix(y_true, y_pred, class_names)
    plot_data = create_plot_data(cm, class_names)
    layout = create_plot_layout(cm, class_names)
    fig = go.Figure(data=plot_data, layout=layout)
    return fig


def calculate_confusion_matrix(y_true, y_pred, class_names):
    """Creates the confusion matrix based on the actual and predicted values for
    each class.

    :param pandas.Series y_true:
        A pandas Series containing the true target values.
    :param pandas.Series y_pred:
        A pandas Series containing the predicted target values.
    :param dict class_names:
        A dictionary containing the name to display for each class
        (e.g. {1: "Class 1", 2: "Class 2", ...}).

    :returns array:
        The confusion matrix.
    """
    class_values = list(class_names.keys())
    cm = confusion_matrix(y_true, y_pred, labels=class_values)
    cm = cm[::-1]
    return cm


def create_plot_data(cm, class_names):
    """Creates the plot data for the confusion matrix.

    :param array cm:
        The confusion matrix.
    :param dict class_names:
        A dictionary containing the name to display for each class
        (e.g. {1: "Class 1", 2: "Class 2", ...}).

    :returns go.Heatmap:
        The plot data for the plotly confusion matrix.
    """
    labels = list(class_names.values())
    return [
        go.Heatmap(
            z=np.identity(len(class_names))[::-1],
            y=labels[::-1],
            x=labels,
            text=cm,
            colorscale=[[0, DEFAULT_PLOTLY_COLORS[3]], [1, DEFAULT_PLOTLY_COLORS[2]]],
            opacity=0.4,
            showscale=False,
            xgap=5,
            ygap=5,
        )
    ]


def create_plot_layout(cm, class_names):
    """Creates the layout for the confusion matrix.

    :param array cm:
        The confusion matrix.
    :param dict class_names:
        A dictionary containing the name to display for each class
        (e.g. {1: "Class 1", 2: "Class 2", ...}).

    :returns plotly.graph_objs.Layout:
        The layout for the confusion matrix plot.
    """
    annotations = create_confusion_matrix_annotations(cm, class_names)
    layout = go.Layout(
        xaxis={
            "title": "Predicted Outcome",
            "side": "top",
            "domain": (0.1, 1.0),
            "showgrid": False,
        },
        yaxis={"title": "Actual Outcome", "showgrid": False},
        annotations=annotations,
        height=600,
        width=800,
    )
    return layout


def create_confusion_matrix_annotations(cm, class_names):
    """Creates the annotations for the plotly confusion matrix plot.
    The value of the confusion matrix at each point is annotated onto the plot.

    :param array cm:
        The confusion matrix.
    :param dict class_names:
        A dictionary containing the name to display for each class
        (e.g. {1: "Class 1", 2: "Class 2", ...}).

    :returns list:
        A list of dictionaries specifiying the annotations for
        the confusion matrix plot.
    """
    labels = list(class_names.values())
    annotations = []
    total = np.sum(cm, axis=None)
    for i, row in enumerate(cm):
        for j, value in enumerate(row):
            annotations.append(
                {
                    "x": labels[j],
                    "y": labels[::-1][i],
                    "font": {"color": "black"},
                    "text": "<b> {:d}  <br> ({:.1%}) </b>".format(value, value / total),
                    "showarrow": False,
                }
            )
    return annotations
