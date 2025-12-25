# Copyright 2025 Ant Group Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from http import HTTPStatus
from typing import Any, Mapping

import httpx

from ..crypto import util
from ..protocol import GetRaCertRequest, GetRaCertResponse


class RaCertPems:

    def __init__(
        self,
        base_url: str,
        verify: bool = True,
        api_key: str = None,
        headers: Mapping[str, Any] = {},
        **kwargs,
    ):
        self.verify = verify
        self.base_url = base_url
        self.api_key = api_key
        self.headers = (
            (headers if headers else {})
            | self.default_headers
            | (self.auth_headers if self.api_key else {})
        )

    @property
    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"API_KEY {self.api_key}"}

    @property
    def default_headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    def get(self, nonce: str = None, timeout: float = None) -> GetRaCertResponse:
        """
        Get the ra report and cert of server

        Args:
            nonce: random value, preventing replay attacks
            timeout: in seconds

        Returns:
            the ra report and cert of server

        Raises:
            the request failed or the nonce verification failed
        """
        from ..env import skip_data_verify

        nonce = nonce or util.gen_key().hex().upper()
        request = GetRaCertRequest(nonce=nonce)
        request.refresh_ra_report = not skip_data_verify()

        data = request.model_dump_json(exclude_unset=True, exclude_none=True)

        # send
        with httpx.Client(verify=False) as client:
            response = client.post(
                f"{self.base_url}/api/v1/ra_report/get",
                content=data,
                timeout=timeout,
                headers=self.headers,
            )
            assert (
                response.status_code == HTTPStatus.OK
            ), f"response status error, status code {response.status_code} content {response.content}"
            ra_response = GetRaCertResponse.model_validate_json(response.content)
            assert ra_response.status.code == 0, f"status error {ra_response}"

            ra_response.nonce = nonce
            # need ra verify
            if self.verify:
                from .ual import verify_ra_report

                verify_ra_report(ra_response)
            return ra_response


class AsyncRaCertPems:

    def __init__(
        self,
        base_url: str,
        verify: bool = True,
        api_key: str = None,
        headers: Mapping[str, Any] = {},
        **kwargs,
    ):
        self.base_url = base_url
        self.verify = verify
        self.api_key = api_key
        self.headers = (
            (headers if headers else {})
            | self.default_headers
            | (self.auth_headers if self.api_key else {})
        )

    @property
    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"API_KEY {self.api_key}"}

    @property
    def default_headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    async def get(self, nonce: str = None, timeout: float = None) -> GetRaCertResponse:
        """
        Get the ra report and cert of server

        Args:
            nonce: random value, preventing replay attacks
            timeout: in seconds

        Returns:
            the ra report and cert of server

        Raises:
            the request failed or the nonce verification failed
        """
        from ..env import skip_data_verify

        nonce = nonce or util.gen_key().hex().upper()
        request = GetRaCertRequest(nonce=nonce)
        request.refresh_ra_report = not skip_data_verify()

        data = request.model_dump_json(exclude_unset=True, exclude_none=True)

        # send
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/ra_report/get",
                content=data,
                timeout=timeout,
                headers=self.headers,
            )
            assert (
                response.status_code == HTTPStatus.OK
            ), f"response status error, status code {response.status_code} content {await response.aread()}"
            ra_response = GetRaCertResponse.model_validate_json(response.content)
            assert ra_response.status.code == 0, f"status error {ra_response}"

            ra_response.nonce = nonce
            # need ra verify
            if self.verify:
                from .ual import verify_ra_report

                verify_ra_report(ra_response)
            return ra_response
