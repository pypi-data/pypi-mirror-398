"""Functions to display the distribution of features for a classification model."""

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from plotly import graph_objs as go
from plotly.colors import DEFAULT_PLOTLY_COLORS
from tqdm.auto import tqdm

from ml_inspector.utils import remove_outliers


def plot_classification_features_distribution(
    df, features, target, class_names=None, max_cat=20, max_bins=50
):
    """Displays the distribution of continuous and categorical features as a function
    of a categorical target variable for classification tasks.

    Args:
        df (pd.DataFrame): The DataFrame containing the features to display.
        features (list): The list of features names to display.
        target (str): The target variable to display.
        class_names (dict): A dictionary containing the name to display for each
            class (e.g. {1: "Class 1", 2: "Class 2", ...}).
        max_cat (int): The maximum number of unique values for a numerical
            feature to be considered a categorical variable.
        max_bins (int): The maximum number of bins to display numerical features.

    Returns:
        go.Figure: The figure containing the feature distributions.
    """
    plot_data = []
    visible = True
    for feature in tqdm(features, desc="Generating feature distributions"):
        if is_numeric_dtype(df[feature]) and df[feature].nunique() > max_cat:
            data = continuous_feature(
                df, feature, target, class_names, max_bins, visible
            )
        else:
            data = discrete_feature(df, feature, target, class_names, max_cat, visible)
        plot_data.extend(data)
        visible = False
    layout = feature_layout(features[0])
    fig = go.Figure(data=plot_data, layout=layout)
    fig = add_feature_selection_button(
        fig, df[features], offset=2 * df[target].nunique()
    )
    return fig


def continuous_feature(df, column, target, class_names=None, max_bins=50, visible=True):
    """Display the selected column's distribution and probability for each class
    for a continuous column.

    Args:
        df (pd.DataFrame): The DataFrame containing the column and the target.
        column (str): The continuous column for which to display the distributions
            and probabilities.
        target (str): The target variable.
        class_names (dict): A dictionary containing the name to display for each
            class (e.g. {1: "Class 1", 2: "Class 2", ...}).
        max_bins (int): The maximum number of bins to display numerical features.

    Returns:
        go.Figure: The column distribution and probability for each class.
    """
    df = df.copy()
    df[column] = remove_outliers(df[column])
    classes = sorted(df[target].unique())
    if not class_names:
        class_names = {c: str(c) for c in classes}
    n_bins = int(np.min([df[column].nunique(), max_bins]))
    data = []
    base = np.zeros_like(n_bins)
    for i, cl in enumerate(classes):
        if data:
            base = base + data[-1]["y"]
        cl_name = class_names[cl]
        color = DEFAULT_PLOTLY_COLORS[i]
        data.append(
            continuous_class_distribution(
                df, column, target, cl, cl_name, color, n_bins, visible
            )
        )
        data.append(
            continuous_class_probability(
                df, column, target, cl, cl_name, color, n_bins, base, visible
            )
        )
    return data


def continuous_class_distribution(
    df, column, target, cl, class_name, color, n_bins, visible
):
    """Returns a violinplot of the column distribution for the subset of the data
    corresponding to the selected class.

    Args:
        df (pd.DataFrame): The DataFrame containing the column and the target.
        column (str): The continuous column for which to display the distributions.
        target (str): The target variable.
        cl (int): The class for which to generate the column distribution.
        class_name (str): The name of the class.
        color (str): The color to use for the violinplot.
        n_bins (int): The number of bins by which to group the variable.

    Returns:
        go.Bar: The column distribution for the selected class.
    """
    x_bins = np.linspace(df[column].min(), df[column].max(), n_bins + 1)
    data_bins = pd.cut(df[column], bins=x_bins, include_lowest=True)
    df_class = df[df[target] == cl]
    dist = df_class.groupby(data_bins, observed=False)[target].count() / len(df_class)
    round_int = int(np.log10(n_bins / (1 + x_bins[-1] - x_bins[0]))) + 1
    return go.Bar(
        x=x_bins.round(round_int),
        y=dist.values,
        marker={"color": color},
        opacity=0.4,
        legendgroup=class_name,
        name=f"Distribution of {class_name}",
        yaxis="y1",
        offsetgroup=0,
        visible=visible,
    )


def continuous_class_probability(
    df, column, target, cl, class_name, color, n_bins, base, visible
):
    """Returns a bar plot for the selected class probability as a function of the
    column value.

    Args:
        df (pd.DataFrame): The DataFrame containing the column and the target.
        column (str): The continuous column for which to display the probabilities.
        target (str): The target variable.
        cl (int): The class for which to generate the column distribution.
        class_name (str): The name of the class.
        color (str): The color to use for the violinplot.
        n_bins (int): The number of bins by which to group the variable.
        base (array): The base of the stacked bar plot.

    Returns:
        go.Bar: The selected class probability as a function of column value.
    """
    x_bins = np.linspace(df[column].min(), df[column].max(), n_bins + 1)
    data_bins = pd.cut(df[column], bins=x_bins, include_lowest=True)
    avg_prob = df.groupby(data_bins, observed=False)[target].apply(
        lambda x: np.mean(x == cl)
    )
    round_int = int(np.log10(n_bins / (1 + x_bins[-1] - x_bins[0]))) + 1
    return go.Bar(
        x=x_bins.round(round_int),
        y=avg_prob.values,
        base=base,
        marker={"color": color},
        opacity=0.4,
        legendgroup=class_name,
        name=f"Probability of {class_name}",
        xaxis="x2",
        yaxis="y2",
        offsetgroup=0,
        visible=visible,
    )


def discrete_feature(df, column, target, class_names=None, max_cat=12, visible=True):
    """Display the selected column's distribution and probability for each class
    for a categorical or discrete column.

    Args:
        df (pd.DataFrame): The DataFrame containing the column and the target.
        column (str): The discrete column for which to display the distributions
            and probabilities.
        target (str): The target variable.
        class_names (dict): A dictionary containing the name to display for each
            class (e.g. {1: "Class 1", 2: "Class 2", ...}).
        max_cat (int): The maximum number of categories or discrete values to display.

    Returns:
        go.Figure: The column distribution and probability for each class.
    """
    df = df.copy()
    classes = sorted(df[target].unique())
    if not class_names:
        class_names = {c: str(c) for c in classes}
    data = []
    if df[column].dtype == pd.Int64Dtype():
        df[column] = df[column].astype("int64")
    if df[column].dtype == pd.Float64Dtype():
        df[column] = df[column].astype("float64")
    df[column] = df[column].fillna("Missing")
    order = df[column].value_counts().index[:max_cat]
    for i, cl in enumerate(classes):
        cl_name = class_names[cl]
        color = DEFAULT_PLOTLY_COLORS[i]
        data.append(
            discrete_class_distribution(
                df, column, target, cl, cl_name, order, color, visible
            )
        )
        data.append(
            discrete_class_probability(
                df, column, target, cl, cl_name, order, color, visible
            )
        )
    return data


def discrete_class_distribution(
    df, column, target, cl, class_name, order, color, visible
):
    """Returns a barplot for the column distribution for the subset of the data
    corresponding to the selected class.

    :param pandas.DataFrame df:
        The pandas DataFrame containing the column to display and the target.
    :param str column:
        The name of the discrete column for which to display the distribution.
    :param str target:
        The name of the target variable.
    :param int cl:
        The class for which to generate the column distribution.
    :param str class_name:
        The name of the class.
    :param list order:
        The list of discrete values ordered by how they should be displayed.
    :param str color:
        The color to use for the histogram.

    :returns plotly.graph_objs.Bar:
        The column distribution for the selected class.
    """
    count = (
        df[df[target] == cl].groupby(column)[target].count().reindex(order).fillna(0)
    )
    return go.Bar(
        x=count.index,
        y=count.values,
        marker={"color": color},
        name=f"Distribution of {class_name}",
        legendgroup=class_name,
        yaxis="y1",
        opacity=0.8,
        visible=visible,
    )


def discrete_class_probability(
    df, column, target, cl, class_name, order, color, visible
):
    """Returns a line plot for the selected class probability as a function of the
    column value.

    :param pandas.DataFrame df:
        The pandas DataFrame containing the column to display and the target.
    :param str column:
        The name of the discrete column.
    :param str target:
        The name of the target variable.
    :param int cl:
        The class for which to generate the column distribution.
    :param str class_name:
        The name of the class.
    :param list order:
        The list of discrete values ordered by how they should be displayed.
    :param str color:
        The color to use for the histogram.

    :returns plotly.graph_objs.Scatter:
        The selected class probability as a function of column value.
    """
    avg = df.groupby(column)[target].apply(lambda x: np.mean(x == cl)).reindex(order)
    return go.Scatter(
        x=avg.index,
        y=avg.values,
        marker={"color": color},
        name=f"Probability of {class_name}",
        legendgroup=class_name,
        xaxis="x2",
        yaxis="y2",
        stackgroup="one",
        visible=visible,
    )


def feature_layout(column):
    """Generates the plotly layout for the classification feature distribution plot.

    :param pandas.DataFrame df:
        The pandas DataFrame containing the column to display.
    :param str column:
        The name of the column for which to plot the distribution.
    :param str barmode:
        A string to indicate how to display bars relative to each other ('group',
        'overlay', 'stack')
    :param str type:
        A string to indicate the type of feature to display ('continuous' or
        'discrete')

    :returns plotly.graph_objs.Layout:
        The layout for the plot.
    """
    columns_name = column.replace("_", " ")
    return go.Layout(
        legend={"orientation": "h"},
        width=1000,
        height=1000,
        template="plotly_white",
        bargap=0,
        xaxis={"title": columns_name},
        yaxis={"title": "Distribution", "domain": [0.55, 1.0]},
        xaxis2={"title": columns_name, "anchor": "y2"},
        yaxis2={"title": "Probability", "domain": [0, 0.45]},
    )


def add_feature_selection_button(fig, X, offset):
    buttons = []
    for col in X.columns:
        xaxis_type = "linear"
        if not is_numeric_dtype(X[col]):
            xaxis_type = "category"
        buttons.append(
            {
                "args": [
                    {"visible": [c == col for c in X.columns for _ in range(offset)]},
                    {
                        "xaxis.title.text": col,
                        "xaxis.type": xaxis_type,
                        "xaxis2.title.text": col,
                        "xaxis2.type": xaxis_type,
                    },
                ],
                "label": col,
                "method": "update",
            }
        )
    fig.update_layout(
        updatemenus=[
            dict(
                buttons=buttons,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0,
                xanchor="left",
                y=1.3,
                yanchor="top",
            ),
        ]
    )
    scale_menu = dict(
        buttons=[
            {
                "label": "Linear x-axis",
                "method": "relayout",
                "args": [{"xaxis.type": "linear", "xaxis2.type": "linear"}],
            },
            {
                "label": "Log x-axis",
                "method": "relayout",
                "args": [{"xaxis.type": "log", "xaxis2.type": "log"}],
            },
        ],
        type="buttons",
        direction="right",
        pad={"r": 10, "t": 10},
        showactive=True,
        active=0,
        x=0.25,
        xanchor="left",
        y=1.3,
        yanchor="top",
    )
    existing_menus = list(fig.layout.updatemenus) if fig.layout.updatemenus else []
    fig.update_layout(updatemenus=existing_menus + [scale_menu])
    return fig
