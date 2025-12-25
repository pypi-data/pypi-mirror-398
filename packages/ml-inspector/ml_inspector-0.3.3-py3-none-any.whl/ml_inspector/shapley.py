"""Shapley values for machine learning predictions."""

import logging

import numpy as np
import plotly.graph_objs as go
import shap
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)


def plot_waterfall(model, X, class_index=None, max_display=10, x_title=None):
    explainer = ShapleyExplainer(model)
    return explainer.plot_waterfall(
        X, class_index=class_index, max_display=max_display, x_title=x_title
    )


class ShapleyExplainer:

    def __init__(self, model):
        self.model = model
        self.explainer = self.get_explainer(model)

    def get_explainer(self, model, X=None):
        """Returns a SHAP explainer object for the model and training data.

        :param model:
            The model for which to generate the shap values.
        :param pandas.DataFrame X:
            A pandas DataFrame containing the model features.
        :param string model_output:
            The type of model output ("raw", "probability", "margin", ...)

        :returns shap.Explainer:
            A SHAP explainer for the model.
        """
        model, _ = self.preprocess_pipeline(model)
        explainer = shap.Explainer(model)
        return explainer

    def preprocess_pipeline(self, model, X=None):
        """Tranforms the input data and returns the final estimator if the model is a
        pipeline.

        :type model: A fitted sklearn machine learning model, or function to make
            predictions.
        :param model:
            The model for which to generate the shap values.
        :param pandas.DataFrame X:
            A pandas DataFrame containing the model features.

        :returns tuple:
            A tuple containing the transformed model and data if the model is a
            pipeline.
        """
        if isinstance(model, Pipeline):
            if X is not None:
                X = model[:-1].transform(X)
            model = model[-1]
        return model, X

    def calculate_shap_values(self, X, class_index=None):
        """Calculates the Shapley values given a shap explainer.

        Args:
            X (array): The model input features.
            class_index (int | None): The index of the class for which to compute the

        Returns:
            array: The shap values for the input features.
        """
        _, X = self.preprocess_pipeline(self.model, X)
        shap_values = self.explainer(X)
        if shap_values.values.ndim == 3:
            if class_index is None:
                if shap_values.values.shape[-1] > 2:
                    raise ValueError(
                        "For multi-class models, the "
                        "class_index parameter must be provided"
                    )
                elif shap_values.values.shape[-1] == 2:
                    logger.info(
                        "By default, the class_index parameter for a binary model is 1"
                    )
                    class_index = 1
            shap_values.values = shap_values.values[:, :, class_index]
            shap_values.base_values = shap_values.base_values[:, class_index]
            # shap_values.expected_value = shap_values.expected_value[class_index]
        return shap_values

    def calculate_single_shap_value(self, X, class_index):
        """Uses a sklearn.Pipeline to transform the input DataFrame. Then applies this to
        the given shap.Explainer and returns the shap values.

        :param shap.Explainer explainer:
            The previously trained explainer.
        :param sklearn.Pipeline pipeline:
            The Pipeline where the last index is an estimator.
        :param pd.DataFrame X:
            The input DataFrame to be transformed into shap values.

        :return shap._explanation.Explanation:
            The explanation object of shap values.
        """
        shap_value = self.calculate_shap_values(X, class_index)
        shap_value = self._reshape_shap_values(shap_value)
        return shap_value

    def plot_waterfall(self, X, class_index=None, max_display=10, x_title=None):
        shap_value = self.calculate_shap_values(X, class_index)
        shap_value = self._reshape_shap_values(shap_value)
        shap_value.feature_names = self._rename_features(shap_value, X)
        fig = self._create_plotly_waterfall_plot(shap_value, max_display, x_title)
        return fig

    def _rename_features(self, shap_value, X):
        """Creates a list of feature/value pairs for more information.

        :param shap._explanation.Explanation shap_value:
            The shap explanation object.

        :return list:
            A list of strings with the feature name and value combined.
        """
        feature_name_value = []
        for feature, value in zip(shap_value.feature_names, shap_value.data.tolist()):
            new_feature_name = feature
            if feature in X and X[feature].values[0] != value:
                new_feature_name = f"{feature} ({X[feature].values[0]})"
            if isinstance(value, float):
                feature_name_value.append(f"{new_feature_name} : {value:.2f}")
            else:
                feature_name_value.append(f"{new_feature_name} : {value}")
        return feature_name_value

    def _create_plotly_waterfall_plot(self, shap_value, max_display, x_title):
        """Creates the plotly figure for the given shap values and the number of features
        to display.

        :param shap._explanation.Explanation shap_value:
            The shap explanation object.
        :param dict offset: (optional)
            A dict of additional data points to add to the waterfall plot.
        :param max_display int: (optional)
            The number of features to display on the waterfall plot. If None, all are.
        :param str title: (optional)
            The title of the plot.
        :param str x_axis_title: (optional)
            The label for the x-axis, should be the target.
        :param str texttemplate:
            The formatting for float inputs into strings accross the plot.

        :return plotly.Figure:
            The plotly Figure object.
        """
        if min(shap_value.values) >= -1 and max(shap_value.values) <= 1:
            texttemplate = ".1%"
        else:
            texttemplate = ".2f"
        shap_dict = self._process_shap_value_plotly(shap_value, max_display)
        data = self._create_plotly_waterfall_data(shap_dict, texttemplate)
        layout = self._create_plotly_waterfall_layout(x_title, shap_dict)
        fig = go.Figure(data=data, layout=layout)
        fig = self._add_vlines(fig, shap_dict, texttemplate)
        return fig

    def _add_vlines(self, fig, shap_dict, texttemplate):
        """Adds vertical lines with annotations for base and total.

            :param plotly.Figure fig:
                The plotly Figure object containing a Waterfall plot.
            :param dict shap_dict:
                The dictionary of processed shap values and features.
            :param str texttemplate:
                The formatting for float inputs into strings accross the plot.

        :return plotly.Figure:
            The plotly Figure object.
        """
        base = shap_dict["base_values"]
        total = shap_dict["total"]
        if base > total:
            base_pos = "top right"
            total_pos = "top left"
        else:
            base_pos = "top left"
            total_pos = "top right"
        fig.add_vline(
            x=base,
            line_dash="dash",
            annotation_text=f"Base: {base:{texttemplate}}",
            annotation_position=base_pos,
            line_color="rgba(50,50,50,0.2)",
        )
        fig.add_vline(
            x=total,
            line_dash="dash",
            annotation_text=f"Predicted: {total:{texttemplate}}",
            annotation_position=total_pos,
            line_color="rgba(50,50,50,0.2)",
        )
        return fig

    def _create_plotly_waterfall_data(self, shap_dict, texttemplate):
        """Creates the data object for a plotly waterfall plot using the input dictionary.

        :param dict shap_dict:
            The dictionary of processed shap values and features.
        :param str texttemplate:
            The formatting for float inputs into strings accross the plot.
        :return list:
            The data list used by plotly for creating the figure.
        """
        data = [
            go.Waterfall(
                name="Waterfall",
                orientation="h",
                base=shap_dict["base_values"],
                y=shap_dict["feature_names"],
                x=shap_dict["values"],
                text=shap_dict["values"],
                textposition="auto",
                texttemplate=f"%{{text:{texttemplate}}}",
                decreasing={"marker": {"color": "rgba(0,139,252,255)"}},
                increasing={"marker": {"color": "rgba(255,0,81,255)"}},
                connector={"visible": True},
                hovertemplate=f"%{{text:{texttemplate}}}",
            )
        ]
        return data

    def _process_shap_value_plotly(self, shap_value, max_display):
        """Change feature names to include their value. Order both by the magnitue of the
        value. Restrict the number of entries if max_display.

        :param shap._explanation.Explanation shap_value:
            The shap explanation object.
        :param max_display int: (optional)
            The number of features to display on the waterfall plot. If None, all are.

        :return dict:
            A dictionary containing: processed values and features, base value and
            total.
        """
        shap_dict = self._generate_shap_dict(shap_value)
        if max_display is not None:
            shap_dict = self._restrict_max_items(shap_dict, max_display)
        return shap_dict

    def _restrict_max_items(self, shap_dict, max_display):
        n_not_displayed = len(shap_dict["values"]) - max_display
        if n_not_displayed > 1:
            remaining_values = sum(shap_dict["values"][:n_not_displayed])
            shap_dict["values"] = shap_dict["values"][n_not_displayed:]
            shap_dict["feature_names"] = shap_dict["feature_names"][n_not_displayed:]
            # Waterfall plots are displayed in reverse order
            shap_dict["values"].insert(0, remaining_values)
            shap_dict["feature_names"].insert(
                0, f"{n_not_displayed} additional features"
            )
        return shap_dict

    def _generate_shap_dict(self, shap_value):
        """Generates a dictionary containing the required components contained within the
        Explanation object. Values are sorted based on the magnitude of their effect.

        :param shap._explanation.Explanation shap_value:
            The shap explanation object.

        :return dict:
            A dictionary with keys: value, feature_names, base_values, total.
        """
        shap_dict = {}
        argsort = np.abs(shap_value.values).argsort()
        shap_dict["values"] = [shap_value.values[i] for i in argsort]
        shap_dict["feature_names"] = [shap_value.feature_names[i] for i in argsort]
        shap_dict["base_values"] = shap_value.base_values
        shap_dict["total"] = shap_dict["base_values"] + sum(shap_dict["values"])
        return shap_dict

    def _reshape_shap_values(self, shap_value):
        """Reshapes the shap_value in order for internal data processing. The number of
        dimensions in a shap_value depend on classification or regression.

        :param shap._explanation.Explanation shap_value:
            The shap explanation object.

        :return shap._explanation.Explanation:
            The input shap_value reshaped to a single dimension.
        """
        if shap_value.values.ndim == 3:
            shap_value = shap_value[0, :, 1]
        elif shap_value.values.ndim == 2:
            shap_value = shap_value[0, :]
        shap_value.values = shap_value.values.ravel()
        if isinstance(shap_value.base_values, np.ndarray):
            shap_value.base_values = shap_value.base_values.ravel()[0]
        return shap_value

    def _create_plotly_waterfall_layout(self, x_axis_title, shap_dict):
        """Creates the layout for the plotly waterfall plot.

        :param str title: (optional)
            The title of the plot.
        :param str x_axis_title: (optional)
            The label for the x-axis, should be the target.
        :param dict shap_dict:
            The dictionary of processed shap values and features.

        :return go.Layout:
            The layout used by plotly when creating a Figure.
        """

        layout = go.Layout(
            {
                "xaxis": {"title": x_axis_title, "gridcolor": "rgb(240,240,240)"},
                "yaxis": {
                    "title": "Features",
                    "range": (-0.65, len(shap_dict["values"]) + 0.5),
                    "tickmode": "linear",
                    "gridcolor": "rgb(240,240,240)",
                },
                "hovermode": "y",
                "autosize": False,
                "width": 1000,
                "height": 500,
                "plot_bgcolor": "rgba(0,0,0,0)",
                "margin_pad": 10,
            }
        )
        return layout
