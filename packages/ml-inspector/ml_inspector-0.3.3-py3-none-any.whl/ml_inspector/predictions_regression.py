"""Functions to display machine learning model predictions."""

import numpy as np
from plotly import graph_objs as go
from plotly.colors import DEFAULT_PLOTLY_COLORS


def plot_regression_predictions(
    y_true: np.ndarray, y_pred: np.ndarray, show_density: bool = False
):
    """Display the distribution of classification model predictions using violinplots.
    For binary classification, only the predicted probability distributions for
    the positive class is provided. For multiple classification predictions, the
    predicted probability distributions are provided for each combination of
    true and predicted classes (N x N distributions, where N is the number of
    classes).

    Args:
        y_true (array): An array containing the true class for each prediction.
            For example: [0, 1, 1]
        y_prob (array): An array containing the predicted probability for each class
            and for each prediction. For example: [[0.9, 0.1], [0.6, 0.4], ...]
        class_names (dict): A dictionary containing the name to display for each class.
            For example: {0: "Class 0", 1: "Class 1", ...}).
        decision_threshold (float): The probablity above which the class is predicted
            (for binary classification models only).
        points (bool or str): A flag to display the individual predicted probabilities.

    Returns:
        go.Figure: The figure containing the classification predictions distribution.
    """
    range_max = np.max(y_true)
    range_min = np.min(y_true)
    plot_data = []
    plot_data.append(get_baseline_line(range_min, range_max))
    plot_data.extend(get_scatterplot_data(y_true, y_pred, show_density))
    fig = go.Figure(plot_data)
    return fig
    # if cls.trend:
    #     scatter_plots.append(
    #         go.Scatter(
    #             x=[0, range_max],
    #             y=[0, range_max],
    #             name="trend",
    #             mode="lines",
    #             line={"dash": "dash", "color": "black"},
    #             showlegend=False,
    #         )
    #     )
    # for i, column in enumerate(data):
    #     if column != "y":
    #         if cls.kde and not data.empty:
    #             x, y, Z = cls.kde_scipy(
    #                 data[column].values, data["y"].values, max=range_max * 1.2
    #             )
    #             scatter_plots.append(
    #                 go.Contour(
    #                     z=Z,
    #                     x=x,
    #                     y=y,
    #                     name=f"{column}_contour",
    #                     colorscale=cls.kde_gradients[i],
    #                     showscale=False,
    #                     opacity=0.6,
    #                     showlegend=False,
    #                     hoverinfo="none",
    #                     line_width=1.5,
    #                 ),
    #             )
    #         scatter_plots.append(
    #             go.Scatter(
    #                 x=data["y"],
    #                 y=data[column],
    #                 mode="markers",
    #                 hoverinfo="none",
    #                 name=f"{column}_scatter",
    #                 marker={
    #                     "color": DEFAULT_PLOTLY_COLORS[i],
    #                     "opacity": 0.5,
    #                     "size": 5,
    #                 },
    #             )
    #         )
    # return scatter_plots


def get_baseline_line(range_min, range_max):
    return go.Scatter(
        x=[range_min, range_max],
        y=[range_min, range_max],
        mode="lines",
        line={"dash": "dash", "color": "black"},
        showlegend=False,
    )


def get_scatterplot_data(y_true, y_pred, show_density=False):
    fig_data = []
    y_pred = {"Predictions": y_pred} if isinstance(y_pred, np.ndarray) else y_pred
    for i, (name, y) in enumerate(y_pred.items()):
        color = DEFAULT_PLOTLY_COLORS[i]
        fig_data.append(
            go.Scatter(
                x=y_true,
                y=y,
                mode="markers",
                name="Predictions",
                marker={"color": color, "size": 1},
                legendgroup=name,
                legendgrouptitle={"text": name},
            )
        )
        if show_density:
            fig_data.append(
                go.Histogram2dContour(
                    x=y_true,
                    y=y,
                    colorscale=get_colorscale(color),
                    line_color=color,
                    name="Density",
                    showscale=False,
                    legendgroup=name,
                    showlegend=True,
                )
            )
    return fig_data


def get_colorscale(color, N=10):
    color = color.replace("rgb(", "").replace(")", "").split(",")
    colorscale = [
        (x, f"rgba({color[0]}, {color[1]}, {color[2]}, {x/2})")
        for x in np.linspace(0, 1, N)
    ]
    return colorscale

    # classes = np.unique(y_true)
    # if not class_names:
    #     class_names = {c: str(c) for c in sorted(classes)}
    # if len(class_names) == 2:
    #     plots_data = binary_distribution(y_true, y_prob, class_names, points)
    # else:
    #     plots_data = multiclass_distribution(y_true, y_prob, class_names, points)
    # layout = create_classification_distribution_layout(class_names)
    # fig = go.Figure(data=plots_data, layout=layout)
    # if len(class_names) == 2:
    #     fig = add_decision_threshold(fig, decision_threshold)
    # return fig


def binary_distribution(y_true, y_pred, class_names, points):
    """Returns violin plots showing the predicted probability for the positive class
    considering the true label.

    Args:
        y_true (array): An array containing the true class for each prediction.
        y_pred (array): An array containing the predicted probability for each class
            and for each prediction.
        class_names (dict): A dictionary containing the name to display for each class.
            For example: {0: "Class 0", 1: "Class 1", ...}).
        points (bool or str): A flag to display the individual predicted probabilities.

    Returns:
        list: The violin plots data.
    """
    positive_class = max(class_names)
    plots_data = []
    for i, true_class in enumerate(class_names):
        y_class = [
            pc[positive_class] for tc, pc in zip(y_true, y_pred) if tc == true_class
        ]
        plots_data.append(
            go.Violin(
                y=y_class,
                points=points,
                pointpos=0,
                jitter=1,
                marker={"opacity": 0.2, "color": DEFAULT_PLOTLY_COLORS[i]},
                name=class_names[true_class],
            )
        )
    return plots_data


def multiclass_distribution(y_true, y_pred, class_names, points):
    """Returns violin plots showing the predicted probability for each class
    considering the true label.

    Args:
        y_true (array): An array containing the true class for each prediction.
        y_pred (array): An array containing the predicted probability for each class
            and for each prediction.
        class_names (dict): A dictionary containing the name to display for each class.
            For example: {0: "Class 0", 1: "Class 1", ...}).
        points (bool or str): A flag to display the individual predicted probabilities.

    Returns:
        list: The violin plots data.
    """
    plots_data = []
    for i, pred_class in enumerate(class_names):
        for j, true_class in enumerate(class_names):
            y_class = [pc[i] for tc, pc in zip(y_true, y_pred) if tc == true_class]
            plots_data.append(
                go.Violin(
                    y=y_class,
                    points=points,
                    pointpos=0,
                    jitter=1,
                    marker={"opacity": 0.2, "color": DEFAULT_PLOTLY_COLORS[j]},
                    yaxis=f"y{i+1}",
                    name=class_names[true_class],
                    showlegend=(i == 0),
                    legendgroup=j,
                )
            )
    return plots_data


def create_classification_distribution_layout(class_names):
    """Returns the layout for the classification predictions distribution plot.

    Args:
        class_names (dict): A dictionary containing the name to display for each class.

    Returns:
        go.Layout: The layout for the classification predictions distribution plot.
    """
    yaxes = {}
    if len(class_names) == 2:
        yaxes["yaxis"] = {
            "range": [0, 1],
            "title": f"P({class_names[max(class_names)]})",
        }
    else:
        for i, name in enumerate(class_names.values()):
            domain = [1 - (i + 1) / len(class_names), 1 - i / len(class_names) - 0.02]
            yaxes[f"yaxis{i+1}"] = {
                "domain": domain,
                "range": [0, 1],
                "title": f"P({name})",
            }
    layout = go.Layout(
        xaxis={"title": "Actual outcome", "anchor": "y"},
        width=800,
        height=250 * len(class_names),
        legend={"orientation": "h"},
        **yaxes,
    )
    return layout


def add_decision_threshold(fig, decision_threshold):
    """Adds the decision threshold to the figure (for binary classification only).

    Args:
        fig (go.Figure): The plotly figure to which to add the decision threshold.
        decision_threshold (float): The probablity above which the positive class is
            predicted.

    Returns:
        go.Figure: The plotly figure with the decision threshold.
    """
    if decision_threshold:
        fig.add_hline(
            decision_threshold,
            line_width=3,
            line_dash="dash",
            line_color="black",
            annotation_text=f"Threshold: {decision_threshold:.1%}",
            annotation_position="top left",
        )
    return fig
