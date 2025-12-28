import hashlib
import io
import logging
import os
import platform
import time
from http import HTTPStatus
from importlib import metadata as importlib_metadata
from typing import Any, Dict, Optional

import httpx
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.validation import check_array, check_is_fitted, check_X_y

from neuralk.exceptions import NeuralkException
from neuralk.utils._remote_utils import create_tar, extract_tar


class OnPremiseClassifier(ClassifierMixin, BaseEstimator):
    """
    Sklearn-style estimator proxying fit/predict calls to an on-premise NICL server.

    This classifier connects to a local or self-hosted NICL (Neural In-Context Learning)
    server and provides a scikit-learn compatible interface for classification tasks.
    It's designed for users who have deployed NICL on their own infrastructure.

    Parameters
    ----------
    host : str
        Base URL of the NICL server (e.g., "http://localhost:8000").
        This is a required parameter.
    dataset_name : str, default="dataset"
        Name identifier for the dataset used in API requests.
    model : str, default="nicl-small"
        Model identifier/path to use for inference (e.g., "nicl-small", "nicl-large").
    timeout_s : int, default=900
        Request timeout in seconds for API calls.
    metadata : dict, optional
        Optional metadata dictionary to include with requests.
    user : str, optional
        Optional user identifier for request tracking.
    api_version : str, optional
        Optional API version string to send as 'Nicl-Version' header.
    default_headers : dict, optional
        Optional default headers to include with every request (e.g., authentication).

    Attributes
    ----------
    classes_ : ndarray of shape (n_classes,)
        The unique class labels found during fit.
    X_train_ : ndarray of shape (n_samples, n_features)
        Training data stored during fit.
    y_train_ : ndarray of shape (n_samples,)
        Training labels stored during fit.
    last_response_ : dict, optional
        The last response received from the remote server (set after predict/predict_proba).

    Examples
    --------
    >>> from neuralk import OnPremiseClassifier
    >>> import numpy as np
    >>> 
    >>> # Initialize the classifier with your NICL server URL
    >>> clf = OnPremiseClassifier(
    ...     host="http://localhost:8000",
    ...     model="nicl-small",
    ...     timeout_s=300
    ... )
    >>> 
    >>> # Generate some training data
    >>> X_train = np.random.randn(100, 10).astype(np.float32)
    >>> y_train = np.random.randint(0, 2, 100).astype(np.int64)
    >>> 
    >>> # Fit the classifier (stores training data)
    >>> clf.fit(X_train, y_train)
    >>> 
    >>> # Make predictions
    >>> X_test = np.random.randn(10, 10).astype(np.float32)
    >>> predictions = clf.predict(X_test)
    >>> probabilities = clf.predict_proba(X_test)

    Notes
    -----
    - The classifier requires numeric input data (numpy arrays with float32 dtype).
    - Training labels must be integers (int64 dtype).
    - The fit method only stores the training data; actual model training happens
      on the remote server during predict/predict_proba calls.
    - For advanced use cases, consider using the low-level helpers in
      ``neuralk.model.classify`` directly.
    """

    def __init__(
        self,
        *,
        host: str,
        dataset_name: str = "dataset",
        model: str = "nicl-small",
        timeout_s: int = 900,
        metadata: Optional[Dict[str, Any]] = None,
        user: Optional[str] = None,
        api_version: Optional[str] = None,
        default_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.host = host
        self.dataset_name = dataset_name
        self.model = model
        self.timeout_s = timeout_s
        self.metadata = metadata
        self.user = user
        self.api_version = api_version
        self.default_headers = default_headers

    def fit(self, X, y) -> "OnPremiseClassifier":
        """Fit the classifier by storing training data.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target values. Can be numeric or string labels.

        Returns
        -------
        self : OnPremiseClassifier
            Returns the instance itself.
        """
        # Validate input data
        X, y = check_X_y(X, y, dtype=None, ensure_2d=True)

        # Handle label encoding for non-numeric labels
        if not np.issubdtype(y.dtype, np.integer):
            self.label_encoder_ = LabelEncoder()
            y_encoded = self.label_encoder_.fit_transform(y)
            self.classes_ = self.label_encoder_.classes_
        else:
            y_encoded = y
            self.classes_ = np.unique(y_encoded)
            self.label_encoder_ = None

        # Convert to required dtypes
        self.X_train_ = check_array(X, dtype=np.float32, order='C')
        self.y_train_ = check_array(y_encoded, dtype=np.int64, ensure_2d=False, order='C')

        return self

    def predict(self, X) -> np.ndarray:
        """Predict class labels for samples in X.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples to predict.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted class labels per sample.
        """
        check_is_fitted(self, ("X_train_", "y_train_"))
        X = check_array(X, dtype=np.float32, order='C')
        result = self._fit_predict_remote(X_test=X)
        predictions = result["predict"]

        # Decode labels if we used a label encoder
        if self.label_encoder_ is not None:
            predictions = self.label_encoder_.inverse_transform(predictions)

        return predictions

    def predict_proba(self, X) -> np.ndarray:
        """Predict class probabilities for samples in X.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples to predict.

        Returns
        -------
        y_proba : ndarray of shape (n_samples, n_classes)
            Class probabilities for each sample. The columns correspond to
            the classes in sorted order, as they appear in the attribute
            ``classes_``.
        """
        check_is_fitted(self, ("X_train_", "y_train_"))
        X = check_array(X, dtype=np.float32, order='C')
        result = self._fit_predict_remote(X_test=X)
        return result["predict_proba"]

    def _fit_predict_remote(self, X_test) -> Dict[str, Any]:
        X_test = check_array(X_test, dtype=np.float32, order='C')
        return self._call_remote(
            X_train=self.X_train_,
            X_test=X_test,
            y_train=self.y_train_,
        )

    def _call_remote(
        self,
        *,
        X_train,
        X_test,
        y_train,
        dataset_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user: Optional[str] = None,
        timeout_s: Optional[int] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Execute the remote fit_predict call."""
        # Prepare request data
        dataset_name = dataset_name or self.dataset_name
        metadata = metadata or self.metadata
        user = user or self.user
        timeout = timeout_s or self.timeout_s

        # Build tar archive and headers
        tar_bytes, req_headers, n_train, n_test, num_features = self._build_tar_and_headers(
            dataset_name=dataset_name,
            X_train=X_train,
            X_test=X_test,
            y_train=y_train,
            model_path=self.model,
            metadata=metadata,
            user=user,
            extra_headers=extra_headers,
        )

        # Make HTTP request
        result = self._make_request(tar_bytes, req_headers, timeout)
        self.last_response_ = result
        return result

    def _build_tar_and_headers(
        self,
        *,
        dataset_name: str,
        X_train,
        X_test,
        y_train,
        model_path: str,
        metadata: Optional[Dict[str, Any]],
        user: Optional[str],
        extra_headers: Optional[Dict[str, str]],
    ):
        """Build tar archive and HTTP headers for the request."""
        X_train = check_array(X_train, dtype=np.float32, order='C')
        X_test = check_array(X_test, dtype=np.float32, order='C')
        y_train = check_array(y_train, dtype=np.int64, ensure_2d=False, order='C')

        archive = create_tar(
            {
                "method": "fit_predict",
                "model_path": model_path,
                "dataset": dataset_name,
                "metadata": metadata or {},
                "user": user or "",
            },
            {"X_train": X_train, "X_test": X_test, "y_train": y_train},
        )
        tar_bytes = archive.getvalue()

        base_headers = {**(self.default_headers or {})}
        base_headers.setdefault("Content-Type", "application/x-tar+zstd")
        base_headers.setdefault("User-Agent", self._get_user_agent())
        if self.api_version:
            base_headers.setdefault("Nicl-Version", self.api_version)
        if extra_headers:
            base_headers.update(extra_headers)
        base_headers["X-Content-SHA256"] = hashlib.sha256(tar_bytes).hexdigest()

        try:
            n_train, num_features = X_train.shape
            n_test = X_test.shape[0]
        except Exception:
            n_train, n_test, num_features = len(X_train), len(X_test), None

        return tar_bytes, base_headers, n_train, n_test, num_features

    def _get_user_agent(self) -> str:
        """Get the User-Agent string for requests."""
        try:
            pkg_version = importlib_metadata.version("neuralk_inference")
        except Exception:
            pkg_version = "0"
        return (
            f"neuralk-inference-client/{pkg_version} httpx/{httpx.__version__} "
            f"python/{platform.python_version()}"
        )

    def _make_request(self, tar_bytes: bytes, headers: Dict[str, str], timeout: int) -> Dict[str, Any]:
        """Make the HTTP request to the remote server."""
        host = self.host
        attempts = 0
        retry_statuses = {500, 502, 503, 504}

        while attempts < 3:
            attempts += 1
            start = time.perf_counter()

            try:
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(f"{host}", content=tar_bytes, headers=headers)

                    if response.status_code == 200:
                        elapsed_ms = int((time.perf_counter() - start) * 1000)
                        logging.getLogger("neuralk_nicl_client").info("POST /fit_predict 200 in %dms", elapsed_ms)
                        return self._decode_response(response)
                    elif response.status_code in retry_statuses and attempts < 3:
                        logging.getLogger("neuralk_nicl_client").warning(
                            "POST /fit_predict %s; retrying %d/3",
                            response.status_code,
                            attempts + 1,
                        )
                        time.sleep(0.5 * attempts)
                        continue
                    else:
                        self._raise_for_status(response)

            except httpx.TimeoutException as e:
                raise NeuralkException(
                    f"Timeout after {timeout}s",
                    HTTPStatus.REQUEST_TIMEOUT,
                    str(e),
                ) from e
            except httpx.HTTPError as e:
                raise NeuralkException(
                    "Network error while calling NICL service",
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    str(e),
                ) from e

        raise NeuralkException(
            "Unexpected response from NICL service",
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "No successful response after retries.",
        )

    def _decode_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Decode the response from the server."""
        response_bytes = response.content
        payload = extract_tar(io.BytesIO(response_bytes), load_cloudpickle=False)
        result: Dict[str, Any] = {
            "predict": payload["predict"],
            "predict_proba": payload["predict_proba"],
        }
        request_id = response.headers.get("x-request-id")
        if request_id:
            result["request_id"] = request_id
        return result

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Raise an appropriate exception for HTTP error responses."""
        try:
            data = response.json()
            err = data.get("error") if isinstance(data, dict) else None
        except Exception:
            err = None
        message = response.text
        if err:
            rid = err.get("request_id")
            message = f"{err.get('code')}: {err.get('message')}"
            if rid:
                message += f" (request_id={rid})"

        status = response.status_code
        if status in (401, 403):
            raise NeuralkException(message, HTTPStatus(status), response.text)
        elif 400 <= status < 500:
            raise NeuralkException(message, HTTPStatus(status), response.text)
        else:
            raise NeuralkException(message, HTTPStatus(status), response.text)
