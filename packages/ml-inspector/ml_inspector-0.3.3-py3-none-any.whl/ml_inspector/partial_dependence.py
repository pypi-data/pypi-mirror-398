"""Functions to display partial depencence plots."""

import numpy as np
import pandas as pd
from plotly import graph_objs as go
from plotly.colors import DEFAULT_PLOTLY_COLORS
from tqdm.auto import tqdm

from ml_inspector.utils import remove_outliers


def select_feature_values(X, feature, max_nb_points):
    """Returns a list of values for the selected feature. If the feature is numerical
    then its quantiles are used as the feature values. If the feature is a string
    (categorical feature), the most frequent values are returned.

    :param pandas.DataFrame X:
        A pandas DataFrame containing the training data.
    :param str feature:
        The feature for which to return the values.
    :param int max_nb_points:
        The maximum number of values returned for the feature.

    :returns list:
        The list of values for the selected feature.
    """
    if X[feature].dtype == "object":
        feature_values = list(X[feature].value_counts().index)[:max_nb_points]
    else:
        X = X.copy()
        X[feature] = remove_outliers(X[feature], sigma_factor=0)
        feature_values = [
            X[feature].quantile(i / (max_nb_points - 1), interpolation="nearest")
            for i in range(max_nb_points)
        ]
        feature_values = sorted(set(feature_values))
    return feature_values


def ceteris_paribus(estimator, row, feature, feature_values, **kwargs):
    """Returns the estimator probability predictions as a function of the values
    for a selected feature for a single row of data (all other features remaining
    equal).

    :type estimator: A fitted sklearn estimator.
    :param estimator:
        The estimator with which to make predictions.
    :param pandas.Series row:
        A pandas Series containing the features for the selected row.
    :param str feature:
        The feature for which to estimate the ceteris paribus dependence.
    :param list feature_values:
        The list of values for the feature with which to make predictions with.

    :returns numpy.array:
        The list of ceteris paribus predictions for the row of data for each
        of the values for the selected feature.
    """
    X_ceteris_paribus = pd.DataFrame([row] * len(feature_values))
    X_ceteris_paribus[feature] = feature_values
    if estimator._estimator_type == "classifier":
        predictions = estimator.predict_proba(X_ceteris_paribus)
        if len(estimator.classes_) == 2:
            predictions = predictions[:, 1]
        else:
            predictions = np.array(
                [predictions[:, i] for i in range(len(estimator.classes_))]
            )
    else:
        predictions = estimator.predict(X_ceteris_paribus, **kwargs)
    return predictions


def partial_dependence(
    estimator, X, feature, max_nb_points=20, max_sample=50, **kwargs
):
    """Returns all the estimator predictions for a sample of rows drawn from
    the training dataset by only varying the selected feature over the
    range of values.

    :type estimator: A fitted sklearn estimator.
    :param estimator:
        The estimator for which to assess the partial dependence on a feature.
    :param pandas.DataFrame X:
        A pandas DataFrame containing the training data.
    :param str feature:
        The feature for which to assess the partial dependence of the estimator.
    :param int max_nb_points:
        The maximum number feature values.
    :param int max_sample:
        The number of samples from the training data on which to estimate the
        partial dependence of the model on the feature.

    :returns tuple:
        A tuple containing the values that the selected feature may take as well
        as the ceteris paribus predictions for these feature values, and the
        impact of each predictions relative to the average predictions.
    """
    all_predictions, all_impacts = [], []
    if len(X) < max_sample:
        max_sample = len(X)
    X_sample = X.sample(max_sample)
    feature_values = select_feature_values(X, feature, max_nb_points)
    for index, row in X_sample.iterrows():
        predictions = ceteris_paribus(estimator, row, feature, feature_values, **kwargs)
        all_predictions.append(predictions)
        if predictions.ndim == 1:
            impacts = predictions - np.mean(predictions)
        elif predictions.ndim == 2:
            impacts = np.subtract(predictions.T, np.mean(predictions, axis=1)).T
        all_impacts.append(impacts)
    return feature_values, np.array(all_predictions), np.array(all_impacts)


def plot_partial_dependence(
    estimator,
    X,
    features=None,
    max_nb_points=20,
    max_sample=100,
    class_names=None,
    **kwargs,
):
    """Plots the partial dependence of an estimator on a selected feature as well
    as the confidence interval for the dependence based on a sample of rows
    drawn from the training data.

    :type estimator: A fitted sklearn estimator.
    :param estimator:
        The estimator for which to assess the partial dependence on a feature.
    :param pandas.DataFrame X:
        A pandas DataFrame containing the training data.
    :param list features:
        A list of features for which to assess the partial dependence of the model.
    :param int max_nb_points:
        The maximum number feature values.
    :param int max_sample:
        The number of samples from the training data on which to estimate the
        partial dependence of the model on the feature.
    :param dict class_names:
        A dictionary containing the name to display for each class
        (e.g. {1: "Class 1", 2: "Class 2", ...}).
    :param str save_path:
        The path to export the figure to.
    :param bool display:
        A flag to display the partial dependence plot.
    """
    plot_data = []
    visible = True
    if features is None:
        features = X.columns
    for feature in tqdm(features, desc="Calculating partial dependence"):
        feature_values, all_predictions, all_impacts = partial_dependence(
            estimator,
            X,
            feature,
            max_nb_points=max_nb_points,
            max_sample=max_sample,
            **kwargs,
        )
        if all_predictions[0].ndim == 2:
            if not class_names:
                class_names = {c: f"Class {c}" for c in estimator.classes_}
            class_names = {i: class_names[i] for i in estimator.classes_}
        plot_data.extend(
            partial_dependence_plot_data(
                feature_values, all_impacts, class_names, visible=visible
            )
        )
        visible = False
    layout = partial_dependence_plot_layout(X.columns[0])
    fig = go.Figure(data=plot_data, layout=layout)
    fig = add_feature_selection_button(fig, X, max_sample)
    return fig


def partial_dependence_plot_data(
    feature_values, all_impacts, class_names=None, ci=95, visible=True
):
    """Returns the data for the partial dependence plot and its confidence interval
    as well as the individual ceteris paribus plots.

    :param list feature_values:
        The list of feature values for the partial dependence plot.
    :param list all_predictions:
        A list of arrays containing the predictions for each feature value and
        for each row.
    :param list all_impacts:
        A list of arrays containing the impact of the feature relative to the
        average prediction for each feature value and for each row.
    :param dict class_names:
        A dictionary containing the name to display for each class
        (e.g. {1: "Class 1", 2: "Class 2", ...}).
    :param float ci:
        The confidence interval to display for the partial dependence plot (in
        percents).
    :param bool visible:
        A flag to display the individual ceteris paribus plots.

    :returns list:
        A list of plotly traces containing the partial dependence plot data.
    """
    data = []
    data.extend(add_individual_impact_plots(feature_values, all_impacts, visible))
    data.extend(
        add_average_impact_plots(feature_values, all_impacts, class_names, ci, visible)
    )
    return data


def add_individual_impact_plots(feature_values, all_impacts, visible):
    """Generates the individual sample partial dependence plots.

    :param list feature_values:
        The list of feature values for the partial dependence plot.
    :param list all_impacts:
        A list of arrays containing the impact of the feature relative to the
        average prediction for each feature value and for each row.

    :returns list:
        A list of plotly traces containing the partial dependence plot data.
    """
    data = []
    if all_impacts[0].ndim == 1:
        for i, impact in enumerate(all_impacts):
            data.append(
                go.Scatter(
                    x=feature_values,
                    y=impact,
                    mode="lines+markers",
                    marker={"color": "grey", "size": 1},
                    name="Individual predictions",
                    showlegend=(i == 0),
                    legendgroup="ceteris_paribus",
                    opacity=0.5,
                    hoverinfo="skip",
                    visible=visible,
                )
            )
    return data


def add_average_impact_plots(feature_values, all_impacts, class_names, ci, visible):
    """Add the average partial dependence and confidence interval plots. If there is
    more than two classes, one plot per class is created.

    :param list feature_values:
        The list of feature values for the partial dependence plot.
    :param list all_predictions:
        A list of arrays containing the predictions for each feature value and
        for each row.
    :param dict class_names:
        A dictionary containing the name to display for each class
        (e.g. {1: "Class 1", 2: "Class 2", ...}).
    :param float ci:
        The confidence interval to display for the partial dependence plot (in
        percents).

    :returns list:
        A list of plotly traces containing the partial dependence plot data.
    """
    data = []
    if all_impacts[0].ndim == 1:
        all_impacts = np.array([[x] for x in all_impacts])
    nb_plots = len(all_impacts[0])
    for i in range(nb_plots):
        mean_values = np.mean(all_impacts[:, i], axis=0)
        pos_std = np.percentile(all_impacts[:, i], q=100 - (100 - ci) / 2, axis=0)
        neg_std = np.percentile(all_impacts[:, i], q=(100 - ci) / 2, axis=0)
        color = DEFAULT_PLOTLY_COLORS[i]
        name = f" ({list(class_names.values())[i]})" if class_names else ""
        data.extend(
            [
                go.Scatter(
                    x=feature_values,
                    y=pos_std,
                    mode="lines+markers",
                    marker={"color": color, "size": 1},
                    name=f"{ci}% Confidence Interval" + f"{name}",
                    line={"width": 2, "dash": "dash"},
                    opacity=0.5,
                    legendgroup=i,
                    showlegend=False,
                    visible=visible,
                ),
                go.Scatter(
                    x=feature_values,
                    y=neg_std,
                    mode="lines+markers",
                    marker={"color": color, "size": 1},
                    name=f"{ci}% Confidence Interval" + f"{name}",
                    line={"width": 2, "dash": "dash"},
                    fill="tonexty",
                    opacity=0.5,
                    legendgroup=i,
                    visible=visible,
                ),
                go.Scatter(
                    x=feature_values,
                    y=mean_values,
                    mode="lines+markers",
                    marker={"color": color, "size": 6},
                    line={"width": 5},
                    name="Average partial dependence" + f"{name}",
                    legendgroup=i,
                    visible=visible,
                ),
            ]
        )
    return data


def partial_dependence_plot_layout(feature):
    """Returns the layout for the partial dependence plot.

    :param str feature:
        The feature for which to create the partial dependence plot.

    :returns go.Layout:
        The layout for the partial dependence plot.
    """
    layout = go.Layout(
        template="none",
        xaxis={"title": f"Value of {feature}"},
        yaxis={"title": "Impact on model prediction", "tickformat": ".2%"},
        height=600,
        width=1000,
        legend={"orientation": "h", "y": 1.1},
    )
    return layout


def add_feature_selection_button(fig, X, max_sample):
    repeat = max_sample + 3
    buttons = [
        {
            "args": [
                {"visible": [c == col for c in X.columns for _ in range(repeat)]},
                {"title": col, "xaxis": {"title": f"Value of {col}"}},
            ],
            "label": col,
            "method": "update",
        }
        for col in X.columns
    ]
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
    return fig
