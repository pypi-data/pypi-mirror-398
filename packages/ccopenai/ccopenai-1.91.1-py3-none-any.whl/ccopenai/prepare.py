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

import os

from .crypto import util as crypto_util
from .env import set_data_key, set_public_key
from .ra import util as ra_util


def prepare_crypto_env(base_url: str, api_key: str, timeout, default_headers):
    # set publick key
    public_key = ra_util.get_public_key(base_url, api_key, timeout, default_headers)
    set_public_key(public_key)

    # set data key
    if os.environ.get("DATA_KEY", None) is None:
        data_key = crypto_util.gen_key(16)
        set_data_key(data_key)


async def prepare_crypto_env_async(
    base_url: str, api_key: str, timeout, default_headers
):
    # set public key
    public_key = await ra_util.get_public_key_async(
        base_url, api_key, timeout, default_headers
    )
    set_public_key(public_key)

    # set data key
    if os.environ.get("DATA_KEY", None) is None:
        data_key = crypto_util.gen_key(16)
        set_data_key(data_key)
