# Copyright 2024 Ant Group Co., Ltd.
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

from typing import Mapping

from pydantic import BaseModel


# RequestHeader carries the user custom headers.
class RequestHeader(BaseModel):
    # Custom headers used to record custom information.
    # Possible fields that could be included:
    # - trace_id
    # - party_id
    # - app_name
    # - ...
    custom_headers: Mapping[str, str] = None


class PublicKey(BaseModel):
    # `RSA`, `SM2`
    scheme: str = "RSA"
    # The format of the public key is given in the `SubjectPublicKeyInfo` structure in RFC5280
    # pem format
    public_key: str = None
