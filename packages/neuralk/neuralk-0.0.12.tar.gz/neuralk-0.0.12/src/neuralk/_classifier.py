import contextlib
import secrets
import tempfile
import logging
from pathlib import Path

from neuralk.model import analysis
import numpy as np
import polars as pl
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.validation import check_array, check_X_y

from .utils import logger
from .neuralk import get_client
from ._pricing import compute_credits_to_use_nicl

_MAX_FEATURES = 500
_MAX_CLASSES = 100
_MAX_ROWS_TOTAL = 1e6
_MAX_ROWS_PREDICT = 1e5


def _random_string():
    return secrets.token_hex()[:8]


@contextlib.contextmanager
def tmp_dataset(client, project, df):
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        file = tmp_dir / f"df_{_random_string()}.parquet"
        df.write_parquet(file)
        dataset = client.datasets.create(
            project, f"train_data_{_random_string()}", str(file)
        )
        try:
            logger.debug(f"Uploading dataset ....")
            dataset = client.datasets.wait_until_complete(dataset, verbose=False)
            yield dataset
        finally:
            try:
                pass
                #client.datasets.delete(dataset)
            except Exception:
                pass


@contextlib.contextmanager
def tmp_analysis(client, analysis, kind, verbose: bool = False):
    try:
        logger.debug(f"Running {kind} analysis")
        analysis = client.analysis.wait_until_complete(analysis, refresh_time=10, verbose=verbose)
        if analysis.error is not None:
            raise RuntimeError(str(analysis.error))

        yield analysis
    finally:
        try:
            client.analysis.delete(analysis)
        except Exception:
            pass


def validate_usage_fast_nicl_fit(
    nb_features: int,
    nb_classes: int,
    max_features: int = _MAX_FEATURES,
    max_classes: int = _MAX_CLASSES,
) -> bool:
    """
    When using the fit method with fast NICL, we have to control:
    - The number of features
    - The number of classes

    If these constraints are not met, we will raise an error.
    """
    ## Check nb_features <= 500
    if nb_features > max_features:
        raise ValueError(
            f"The number of features ({nb_features}) is greater than the maximum number of features ({max_features})."
        )
    if nb_classes > max_classes:
        raise ValueError(
            f"The number of classes ({nb_classes}) is greater than the maximum number of classes ({max_classes})."
        )


def validate_usage_fast_nicl_predict(
    nb_rows_train: int,
    nb_rows_predict: int,
    max_rows_total: int = _MAX_ROWS_TOTAL,
    max_rows_predict: int = _MAX_ROWS_PREDICT,
) -> bool:
    """
    When using the predict method with fast NICL, we have to control:
    - The total number of rows (train + predict)
    - The number of rows in the predict set
    - The credits to use for the prediction

    If these constraints are not met, we will raise an error.
    """
    ## Check nb_rows (train + test) <= 1M
    nb_rows_total = nb_rows_train + nb_rows_predict
    if nb_rows_total > max_rows_total:
        raise ValueError(
            f"The number of total rows ({nb_rows_total}) is greater than the maximum number of rows ({max_rows_total})."
        )

    ## Check nb_rows (test) <= 100K
    if nb_rows_predict > max_rows_predict:
        raise ValueError(
            f"The number of predict rows ({nb_rows_predict}) is greater than the maximum number of rows ({max_rows_predict})."
        )


def check_has_enough_credits(
    df_predict: pl.DataFrame,
    credits_available: float,
):
    number_credits_predictions = compute_credits_to_use_nicl(df_predict)
    if number_credits_predictions > credits_available:
        raise RuntimeError(
            f"Insufficient credits."
            f"Credits available: {credits_available}, "
            f"Credits needed: {number_credits_predictions}"
        )


class Classifier(ClassifierMixin, BaseEstimator):
    """
    Classifier that relies on the Neuralk API.

    To use this classifier, the environment variables
    ``NEURALK_USERNAME`` and ``NEURALK_PASSWORD`` must be
    defined.
    """

    def fit(self, X, y):
        """Fit the classifier.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data
        y : array-like of shape (n_samples,)
            Target values

        Returns
        -------
        self : Classifier
            The fitted estimator.
        """

        self.label_encoder_ = LabelEncoder()
        encoded_y = self.label_encoder_.fit_transform(y)
        self.classes_ = self.label_encoder_.classes_
        validate_usage_fast_nicl_fit(X.shape[1], len(self.classes_))

        X, encoded_y = check_X_y(X, encoded_y, dtype="float32")
        X = pl.DataFrame(X, schema=[f"X_{i}" for i in range(X.shape[1])])
        self.X_cols_ = X.columns
        self.target_column_ = "y"
        self.train_data_ = X.with_columns(y=encoded_y)
        self.project_name_ = "neuralk_classifier_scratch"
        return self

    def predict(self, X):
        return self._predict(X)['predict']

    def predict_proba(self, X):
        proba = self._predict(X)['predict_proba']
        if proba is None:
            raise ValueError("This analysis was fitted before predict_proba became available")
        return proba

    def _predict(self, X: pl.DataFrame):
        """Predict class labels

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            The feature matrix.

        Returns
        -------
        ndarray of shape (n_samples,)
            The predicted class labels.
        """
        X_test = pl.DataFrame(check_array(X, dtype="float32"), schema=self.X_cols_)
        validate_usage_fast_nicl_predict(self.train_data_.shape[0], X_test.shape[0])
        with contextlib.ExitStack() as stack:
            client = get_client()

            credits_available = client.organization.get_credits_available()
            check_has_enough_credits(X_test, credits_available)

            project = client.projects.create(self.project_name_, exist_ok=True)
            train_dataset = stack.enter_context(
                tmp_dataset(client, project, self.train_data_)
            )

            fit_analysis = stack.enter_context(
                tmp_analysis(
                    client,
                    client.analysis.create_classifier_fit(
                        dataset=train_dataset,
                        name=f"neuralk_classifier_fit_{_random_string()}",
                        target_column=(self.target_column_,),
                        fast_nicl_mode=True,
                    ),
                    "fit",
                    verbose=False,
                )
            )
            test_dataset = stack.enter_context(tmp_dataset(client, project, X_test))
            predict_analysis = stack.enter_context(
                tmp_analysis(
                    client,
                    client.analysis.create_classifier_predict(
                        dataset=test_dataset,
                        name=f"neuralk_classifier_predict_{_random_string()}",
                        classifier_fit_analysis=fit_analysis.id,
                        fast_nicl_mode=True,
                    ),
                    "predict",
                    verbose=True,
                )
            )
            tmp_dir = stack.enter_context(tempfile.TemporaryDirectory())
            tmp_dir = Path(tmp_dir)
            client.analysis.download_results(
                predict_analysis.id, folder_path=str(tmp_dir)
            )
            predictions_file = next(tmp_dir.glob("transformed_data_file_*.parquet"))
            predictions = pl.read_parquet(predictions_file)
            if len(predictions.columns) == 1:
                predictions = predictions.to_series().to_numpy()
            else:
                predictions = predictions.to_numpy()
            predictions = self.label_encoder_.inverse_transform(predictions)
            try:
                proba_file = next(tmp_dir.glob("predicted_proba_file_*.parquet"))
                proba = pl.read_parquet(proba_file).to_numpy()
            except StopIteration:
                proba = None
            return {'predict_proba': proba, 'predict': predictions}
