from http import HTTPStatus

import requests

from ..exceptions import NeuralkException

from ._configuration import NEURALK_REFRESH_TOKEN_RETRY, Configuration
from ._errors import ERROR_FIELD, EXPIRED_TOKEN_ERROR
from ._request_type import RequestType


class RequestHandler:
    def __init__(
        self,
        user_id: str,
        password: str,
        timeout: int,
        refresh_token_retry: int = NEURALK_REFRESH_TOKEN_RETRY,
    ):
        self.user_id = user_id
        self.password = password
        self.timeout = timeout
        self.refresh_token_retry = refresh_token_retry

        self.access_token = None
        self.refresh_token = None

    def get(
        self, url: str, params=None, data=None, json=None, files=None, stream=False
    ):
        return self._sendRequest(
            url, RequestType.GET, params, data, json, files, stream
        )

    def post(
        self, url: str, params=None, data=None, json=None, files=None, stream=False
    ):
        return self._sendRequest(
            url, RequestType.POST, params, data, json, files, stream
        )

    def put(
        self, url: str, params=None, data=None, json=None, files=None, stream=False
    ):
        return self._sendRequest(
            url, RequestType.PUT, params, data, json, files, stream
        )

    def delete(
        self, url: str, params=None, data=None, json=None, files=None, stream=False
    ):
        return self._sendRequest(
            url, RequestType.DELETE, params, data, json, files, stream
        )

    def _sendRequest(
        self,
        url: str,
        request_type: RequestType,
        params=None,
        data=None,
        json=None,
        files=None,
        stream=False,
    ):
        return self._send_request_with_try_count(
            url, request_type, 1, params, data, json, files, stream
        )

    def _refresh_token(self) -> bool:
        resp = self._execute_request(
            "auth/refresh",
            RequestType.POST,
            data={
                "refresh_token": self.refresh_token,
            },
        )
        if resp.status_code == HTTPStatus.OK:
            self.access_token = resp.json()["access_token"]
            self.refresh_token = resp.json()["refresh_token"]
            return True
        return False

    def _execute_request(
        self,
        url: str,
        request_type: RequestType,
        headers=None,
        params=None,
        data=None,
        json=None,
        files=None,
        stream=False,
    ):
        final_url = f"{Configuration.neuralk_endpoint}/{url}"
        match (request_type):
            case RequestType.GET:
                return requests.get(
                    final_url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json,
                    files=files,
                    timeout=self.timeout,
                    stream=stream,
                )
            case RequestType.POST:
                return requests.post(
                    final_url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json,
                    files=files,
                    timeout=self.timeout,
                    stream=stream,
                )
            case RequestType.PUT:
                return requests.put(
                    final_url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json,
                    files=files,
                    timeout=self.timeout,
                    stream=stream,
                )
            case RequestType.DELETE:
                return requests.delete(
                    final_url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json,
                    files=files,
                    timeout=self.timeout,
                    stream=stream,
                )
        return None

    def _send_request_with_try_count(
        self,
        url: str,
        request_type: RequestType,
        try_count: int,
        params=None,
        data=None,
        json=None,
        files=None,
        stream=False,
    ):
        headers = {}
        headers["Authorization"] = f"Bearer {self.access_token}"

        resp: requests.Response = self._execute_request(
            url, request_type, headers, params, data, json, files, stream
        )
        if resp.status_code != HTTPStatus.OK:
            # Handle specific errors
            if (
                resp.status_code == HTTPStatus.UNAUTHORIZED
                and resp.content != ""
                and ERROR_FIELD in resp.json()
                and resp.json()[ERROR_FIELD] == EXPIRED_TOKEN_ERROR
            ):
                if (
                    not self._refresh_token()
                    and try_count > NEURALK_REFRESH_TOKEN_RETRY
                ):
                    raise NeuralkException.from_resp(
                        "Access token is expired and cannot be refreshed", resp
                    )
                return self._send_request_with_try_count(
                    url, request_type, try_count + 1, params, data, json, files, stream
                )
            return resp
        else:
            return resp
