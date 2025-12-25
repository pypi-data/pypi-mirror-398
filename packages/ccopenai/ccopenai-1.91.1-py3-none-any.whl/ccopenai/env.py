#
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
import base64


def ra_verify() -> bool:
    value = os.environ.get("RA_VERIFY", "true")

    return value.strip().lower() not in ["false", "0", "no", "n", "off"]


def skip_data_verify() -> bool:
    value = os.environ.get("SKIP_DATA_VERIFY", "true")

    return value.strip().lower() not in ["false", "0", "no", "n", "off"]


def set_public_key(public_key: bytes):

    os.environ["PUBLIC_KEY"] = base64.b64encode(public_key).decode()


def get_public_key() -> bytes:
    public_key_b64 = os.environ.get("PUBLIC_KEY", None)

    assert public_key_b64, "public key is empty"

    return base64.b64decode(public_key_b64)


def set_data_key(data_key: bytes):

    os.environ["DATA_KEY"] = base64.b64encode(data_key).decode()


def get_data_key() -> bytes:
    data_key_b64 = os.environ.get("DATA_KEY", None)

    assert data_key_b64, "data key is empty"

    return base64.b64decode(data_key_b64)
