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

from pydantic import BaseModel

from .common import RequestHeader
from .status import Status
from .ual import UnifiedAttestationReport

report_type = UnifiedAttestationReport


class GetRaCertRequest(BaseModel):
    header: RequestHeader = None
    # prevent replay attacks, the random number provided by the client
    nonce: str = None
    # whether to generate report by using nonce or just use cache
    # if True, generate report.
    # if False, use cache
    refresh_ra_report: bool = False


class GetRaCertResponse(BaseModel):
    status: Status = None
    # quote.report_data = SHA256( cert || '.' || nonce )
    attestation_report: report_type = None
    # certificate, X.509 PEM format
    cert: str = None
    nonce: str = None
