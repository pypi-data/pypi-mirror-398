"""Functions to display the distribution of features for machine learning models."""

import numpy as np
import pandas as pd
import scipy.stats as st
import seaborn as sns
from pandas.api.types import is_numeric_dtype
from plotly import graph_objs as go
from plotly.colors import DEFAULT_PLOTLY_COLORS
from tqdm.auto import tqdm

from ml_inspector.utils import remove_outliers


def plot_regression_features_distribution(df, features, target, max_cat=20, ci=0.95):
    """Displays the distribution of continuous and categorical features as a function
    of a continuous target variable for regression tasks.

    :param pandas.DataFrame df:
        The pandas.DataFrame containing the features to display.
    :param list features:
        The list of features (strings) to display.
    :param pandas.Series target:
        The pandas Series containing the target variable for the
        regression task.
    :param int max_cat:
        The maximum number of unique values for a numerical feature to be
        considered a categorical variable.
    :param str save_path:
        The path to export the .png figures to.
    :param bool display:
        A flag to display the feature distributions.
    """
    plot_data = []
    visibility_index = []
    features_types = []
    visible = True
    for feature in tqdm(features, desc="Generating feature distributions"):
        continuous = is_numeric_dtype(df[feature]) and df[feature].nunique() > 20
        if continuous:
            data = continuous_feature(df, feature, target, max_cat, ci, visible)
        else:
            data = discrete_feature(df, feature, target, max_cat, visible)
        plot_data.extend(data)
        visibility_index.extend([feature] * len(data))
        features_types.append("continuous" if continuous else "discrete")
        visible = False
    layout = feature_layout(features[0], target)
    fig = go.Figure(data=plot_data, layout=layout)
    fig = add_feature_selection_button(fig, features, visibility_index, features_types)
    return fig


def continuous_feature(df, column, target, bins, ci=0.95, visible=True):
    """Display the distribution and average target value for the selected continuous
    column for a regression problem.


    :param pandas.DataFrame df:
        The pandas DataFrame containing the column to display and the target.
    :param str column:
        The name of the continuous column for which to display the distribution.
    :param str target:
        The name of the target variable.
    :param int bins:
        The number of bins by which to group by the column values.
    :param float ci:
        The condifence interval for the average target value.

    :returns plotly.graph_objs.Figure:
        The figure containing the column distribution.
    """
    df = df.copy()
    df[column] = remove_outliers(df[column])
    data = [
        go.Histogram(
            x=df[column],
            xaxis="x1",
            yaxis="y1",
            marker={"color": DEFAULT_PLOTLY_COLORS[0]},
            name="Distribution",
            visible=visible,
        ),
        go.Scatter(
            x=df[column],
            y=df[target],
            mode="markers",
            xaxis="x2",
            yaxis="y2",
            marker={"color": DEFAULT_PLOTLY_COLORS[0]},
            name="Observations",
            visible=visible,
        ),
    ]
    data.extend(continuous_feature_average(df, column, target, bins, ci, visible))
    return data


def continuous_feature_average(df, column, target, bins, ci, visible):
    """Returns the plots for the average target value as a function of the selected
    column values, as well as the confidence interval on the average target value.

    :param pandas.DataFrame df:
        The pandas DataFrame containing the column to display and the target.
    :param str column:
        The name of the continuous column for which to display the distribution.
    :param str target:
        The name of the target variable.
    :param int bins:
        The number of bins by which to group by the column values.
    :param float ci:
        The condifence interval for the average target value.

    :returns list:
        A list of plots or the average target value and its condifence interval.
    """
    aggregates = df.groupby(
        pd.qcut(df[column], q=bins, duplicates="drop"), observed=True
    )[target].agg(["mean", "std", "count"])
    z = st.norm.ppf(ci)
    avg = pd.Series([val for val in aggregates["mean"] for _ in (0, 1)])
    error = pd.Series(
        [
            z * std / np.sqrt(count)
            for std, count in zip(aggregates["std"], aggregates["count"])
            for _ in (0, 1)
        ]
    )
    indices = []
    for i in aggregates.index:
        indices.extend([i.left, i.right])
    data = [
        go.Scatter(
            x=indices,
            y=avg,
            mode="lines",
            xaxis="x2",
            yaxis="y2",
            line={"color": DEFAULT_PLOTLY_COLORS[1]},
            name="Average target",
            legendgroup="average",
            visible=visible,
        ),
        go.Scatter(
            x=indices,
            y=avg - error,
            mode="lines",
            xaxis="x2",
            yaxis="y2",
            line={"color": DEFAULT_PLOTLY_COLORS[1], "dash": "dash"},
            name="Confidence interval",
            showlegend=False,
            legendgroup="average",
            visible=visible,
        ),
        go.Scatter(
            x=indices,
            y=avg + error,
            fill="tonexty",
            mode="lines",
            xaxis="x2",
            yaxis="y2",
            line={"color": DEFAULT_PLOTLY_COLORS[1], "dash": "dash"},
            name="Confidence interval",
            legendgroup="average",
            visible=visible,
        ),
    ]
    return data


def discrete_feature(df, column, target, max_bins, visible=True):
    """Display the distribution of a categorical or discrete column for a regression
    problem.

    :param pandas.DataFrame df:
        The pandas DataFrame containing the column to display and the target.
    :param str column:
        The name of the discrete column for which to display the distributions
        and probabilities.
    :param str target:
        The name of the target variable.
    :param int max_bins:
        The maximum number of categories or discrete values to display. (if
        the number of discrete values is lower, then this number is used instead).

    :returns plotly.graph_objs.Figure:
        The figure containing the column distribution.
    """
    df = df.copy()
    df[column].fillna("Missing", inplace=True)
    ordered_categories = df[column].value_counts().index[:max_bins]
    if len(ordered_categories) > len(DEFAULT_PLOTLY_COLORS):
        pal = sns.color_palette(
            "Blues_r", n_colors=len(ordered_categories) + 1
        ).as_hex()
    else:
        pal = DEFAULT_PLOTLY_COLORS
    data = [
        go.Bar(
            x=ordered_categories,
            y=df[column].value_counts().values[:max_bins],
            marker={"color": pal},
            xaxis="x1",
            yaxis="y1",
            name="Distribution",
            showlegend=False,
            visible=visible,
        )
    ]
    for i, cat in enumerate(ordered_categories):
        data.append(
            go.Violin(
                x=df[df[column] == cat][column],
                y=df[df[column] == cat][target],
                meanline={"visible": True},
                points="all",
                pointpos=0,
                jitter=1,
                marker={"opacity": 0.2, "color": pal[i]},
                xaxis="x2",
                yaxis="y2",
                name=cat,
                showlegend=False,
                visible=visible,
            )
        )
    return data


def feature_layout(column, target):
    """Generates the plotly layout for the regression feature distribution plot.

    :param pandas.DataFrame df:
        The pandas DataFrame containing the column to display.
    :param str column:
        The name of the column for which to plot the distribution.
    :param str target:
        The name of the target variable.
    :param str type:
        A string to indicate the type of feature to display ('continuous' or
        'discrete')

    :returns plotly.graph_objs.Layout:
        The layout for the plot.
    """
    target_name = target.replace("_", " ")
    columns_name = column.replace("_", " ")
    return go.Layout(
        violinmode="overlay",
        legend={"orientation": "h"},
        width=1000,
        height=1000,
        title=f"Distribution of {columns_name}",
        template="plotly_white",
        xaxis={"title": columns_name},
        yaxis={"title": "Distribution", "domain": [0.55, 1.0], "showticklabels": True},
        xaxis2={"title": columns_name, "anchor": "y2"},
        yaxis2={"title": target_name, "domain": [0, 0.45]},
    )


def add_feature_selection_button(fig, features, visibility_index, features_types):
    buttons = []
    for col, col_type in zip(features, features_types):
        xaxis_type = "linear" if col_type == "continuous" else "category"
        args = [
            {"visible": [c == col for c in visibility_index]},
            {
                "xaxis.title.text": col,
                "xaxis.type": xaxis_type,
                "xaxis2.title.text": col,
                "xaxis2.type": xaxis_type,
            },
        ]
        buttons.append({"args": args, "label": col, "method": "update"})
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
        direction="down",
        pad={"r": 10, "t": 10},
        showactive=True,
        x=0.25,
        xanchor="left",
        y=1.3,
        yanchor="top",
    )
    existing_menus = list(fig.layout.updatemenus) if fig.layout.updatemenus else []
    fig.update_layout(updatemenus=existing_menus + [scale_menu])
    return fig
