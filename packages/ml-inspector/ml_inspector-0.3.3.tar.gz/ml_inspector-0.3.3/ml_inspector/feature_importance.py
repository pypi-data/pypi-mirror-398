import logging

import numpy as np
import plotly.graph_objs as go
from sklearn.model_selection import cross_val_score
from tqdm.auto import tqdm

logger = logging.getLogger(__name__)


def plot_feature_importance(
    estimator, X, y=None, importance_type=None, scoring=None, cv=5, n_jobs=-1, max_nb=20
):
    """Displays the feature importance for the estimator, using the default feature
    importance for tree-based models or the removal importance (obtained by training
    the model after removing each feature calculated using cross-validation).

    Args:
        estimator (BaseEstimator): A fitted estimator that accepts the selected method.
        X (pd.DataFrame): The features for which to display the importance.
        y (pd.Series): The target variable (for removal importance)
        importance_type (str | None): The type of feature importance to display:
            * None: default feature importance for tree-based models
            * 'removal': removal importance
        scoring (str): The name of the  scoring function for which to estimate the
            importance of each feature.
        cv (int): The number of cross-validation folds to use.
        n_jobs (int): The number of parallel jobs to use to evaluate cross-validation
            scores.
        max_nb (int): The maximum number of features  importance to display.

    Returns:
        go.Figure: The feature importance plot.
    """
    importance = get_feature_importance(
        estimator,
        X,
        y,
        importance_type=importance_type,
        scoring=scoring,
        cv=cv,
        n_jobs=n_jobs,
    )
    data = feature_importance_plot_data(importance, max_nb)
    layout = feature_importance_layout(importance_type, scoring)
    return go.Figure(data, layout)


def get_feature_importance(estimator, X, y, importance_type, scoring, cv=5, n_jobs=1):
    """Returns the feature importance for the estimator, using the default feature
    importance for tree-based models or the removal importance (obtained by training
    the model after removing each feature calculated using cross-validation).

    Args:
        estimator (BaseEstimator): A fitted estimator that accepts the selected method.
        X (pd.DataFrame): The features for which to display the importance.
        y (pd.Series): The target variable (for removal importance)
        importance_type (str | None): The type of feature importance to display:
            * None: default feature importance for tree-based models
            * 'removal': removal importance
        scoring (str): The name of the  scoring function for which to estimate the
            importance of each feature.
        cv (int): The number of cross-validation folds to use.
        n_jobs (int): The number of parallel jobs to use to evaluate cross-validation
            scores.

    Returns:
        dict: The importance of each feature in descending order.
    """
    if importance_type is None:
        importance = tree_model_importance(estimator, X)
    elif importance_type == "removal":
        importance = removal_importance(estimator, X, y, scoring, cv, n_jobs)
    importance = dict(sorted(importance.items(), key=lambda t: t[1], reverse=True))
    return importance


def tree_model_importance(estimator, X):
    """Returns the default feature importance of a tree-based estimator. An
    exception is raised if the estimator does not have a 'feature_importances_'
    attribute.

    :type estimator: A fitted estimator that accepts the selected method.
    :param estimator:
        The fitted estimator for which to estimate the importance of each feature.
    :param pandas.DataFrame X:
        A pandas DataFrame containing the features for which to display the
        importance.

    :returns dict:
        A dictionary containing the default feature importance of a tree-based
        estimator.
    """
    if hasattr(estimator, "feature_importances_"):
        return {f: i for f, i in zip(X.columns, estimator.feature_importances_)}
    raise ValueError(
        "The estimator is not a tree-based model. "
        "Use 'removal' importance type instead."
    )


def removal_importance(
    estimator,
    X,
    y,
    scoring,
    cv=5,
    n_jobs=-1,
):
    """Returns the removal importance of each feature for the estimator using
    cross-validation. The removal importance corresponds to the decreases
    in the estimator score when the feature is removed.

    :type estimator: A fitted estimator that accepts the selected method.
    :param estimator:
        The fitted estimator for which to estimate the importance of each feature.
    :param pandas.DataFrame X:
        A pandas DataFrame containing the features for which to calculate the
        importance.
    :param pandas.Series y:
        A pandas Series containing the training target variable to calculate the
        estimator's removal importance.
    :type scorer: A function that takes y_true and y_pred as arguments.
    :param scorer:
        The scorer for which to estimate the importance of each feature. Extra
        arguments for the scorer can also be passed (e.g. multi_class='ovr')
    :param str method:
        The name of the estimator method used to make predictions ('predict' or
        'predict_proba').
    :param bool greater_is_better:
        A flag to indicate that a higher score is better. Must be set to false when
        the scorer used is an error or loss function (e.g. mean_absolute_error)
    :param int cv:
        The number of cross-validation folds to use.
    :param int n_jobs:
        The number of parallel jobs to use to evaluate the cross validation score.

    :returns dict:
        A dictionary containing the removal importance for each feature.
    """
    importance = {col: [] for col in X.columns}
    base_score = cross_val_score(
        estimator, X, y, scoring=scoring, cv=cv, n_jobs=n_jobs
    ).mean()
    X = X.copy()
    for col in tqdm(X.columns, desc="Calculating feature importance"):
        old_X_col = X[col].copy()
        X[col] = 0
        new_score = cross_val_score(
            estimator, X, y, scoring=scoring, cv=cv, n_jobs=n_jobs
        ).mean()
        X[col] = old_X_col.copy()
        importance[col] = base_score - new_score
    return importance


def feature_importance_plot_data(importance, max_nb):
    """Returns a bar plot of feature importance.

    :param collections.OrderedDict importance:
        A dictionary containing the importance of each feature in descending order.
    :param int max_nb:
        The maximum number of features for which to display the importance.

    :return go.Figure:
        A figure containing a bar plot of feature importance.
    """
    features = [f.replace("_", " ").capitalize() for f in importance][:max_nb]
    importance_vals = list(importance.values())[:max_nb]
    min_scale = np.min(importance_vals) - np.max(importance_vals)
    plot_data = go.Bar(
        x=importance_vals,
        y=features,
        orientation="h",
        text=features,
        textposition="auto",
        marker={"color": importance_vals, "colorscale": "Blues", "cmid": min_scale},
        textfont_size=12,
    )
    return plot_data


def feature_importance_layout(importance_type, scorer):
    x_label = "Feature importance"
    if importance_type == "removal":
        x_label += f" (impact on {scorer} score)"
    return go.Layout(
        yaxis={"autorange": "reversed", "tickvals": []},
        xaxis={"title": x_label},
        height=700,
        width=1000,
    )
