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

from ..crypto import util
from ..env import ra_verify
from .ra_cert_pems import AsyncRaCertPems, RaCertPems


def get_public_key(base_url: str, api_key: str, timeout, default_headers):

    response = RaCertPems(base_url, ra_verify(), api_key, default_headers).get(
        timeout=timeout
    )

    return util.get_public_key_from_cert(response.cert.encode("utf-8"))


async def get_public_key_async(base_url: str, api_key: str, timeout, default_headers):

    response = await AsyncRaCertPems(
        base_url, ra_verify(), api_key, default_headers
    ).get(timeout=timeout)

    return util.get_public_key_from_cert(response.cert.encode("utf-8"))
