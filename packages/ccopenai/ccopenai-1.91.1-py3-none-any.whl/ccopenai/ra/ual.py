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

import logging
from dataclasses import dataclass

from ..crypto import util
from ..protocol import (
    GetRaCertResponse,
    UnifiedAttestationPolicy,
    UnifiedAttestationAttributes,
)

# tee plat types
TEE_PLAT_SGX = "sgx"
TEE_PLAT_TDX = "tdx"
TEE_PLAT_CSV = "csv"
TEE_PLAT_HYPER_POD = "hyperpod"

# tee plat types in UAL Protobuf
UAL_TEE_PLAT_SGX = "SGX_DCAP"
UAL_TEE_PLAT_TDX = "TDX"
UAL_TEE_PLAT_CSV = "CSV"
UAL_TEE_PLAT_HYPERPOD = "HyperPod"


@dataclass
class TeeConstraints:
    """
    tee constraints
    """

    mr_plat: str = ""
    mr_boot: str = ""
    mr_ta: str = ""
    mr_signer: str = ""


def verify_ra_report(
    ra_response: GetRaCertResponse,
    tee_plat: str = TEE_PLAT_TDX,
    tee_constraints: TeeConstraints = TeeConstraints(),
):
    """
    verify remote attestation report
    """
    from trustflow.attestation.verification import verifier

    policy = UnifiedAttestationPolicy()
    rule = UnifiedAttestationAttributes()

    from ..env import skip_data_verify

    if skip_data_verify():
        rule.hex_user_data = ""
    else:
        user_data = util.sha256(
            ra_response.cert.encode("utf-8"), ra_response.nonce.encode("utf-8")
        )
        rule.hex_user_data = user_data.hex().upper()

    if tee_plat == TEE_PLAT_SGX:
        rule.bool_debug_disabled = "true"
        rule.str_tee_platform = UAL_TEE_PLAT_SGX
        rule.hex_ta_measurement = tee_constraints.mr_ta
        rule.hex_signer = tee_constraints.mr_signer
    elif tee_plat == TEE_PLAT_TDX:
        rule.bool_debug_disabled = "true"
        rule.str_tee_platform = UAL_TEE_PLAT_TDX
        rule.hex_platform_measurement = tee_constraints.mr_plat
        rule.hex_boot_measurement = tee_constraints.mr_boot
        rule.hex_ta_measurement = tee_constraints.mr_ta
    elif tee_plat == TEE_PLAT_CSV:
        rule.str_tee_platform = UAL_TEE_PLAT_CSV
        rule.hex_boot_measurement = tee_constraints.mr_boot
    elif tee_plat == TEE_PLAT_HYPER_POD:
        rule.str_tee_platform = UAL_TEE_PLAT_HYPERPOD
    else:
        raise ValueError(f"Invalid TEE platform: {tee_plat}")

    if policy.main_attributes is None:
        policy.main_attributes = [rule]
    else:
        policy.main_attributes.append(rule)

    report_json = ra_response.attestation_report.model_dump_json(exclude_none=True)
    policy_json = policy.model_dump_json(exclude_none=True)

    verify_status = verifier.attestation_report_verify(report_json, policy_json)
    if verify_status.code != 0:
        raise RuntimeError(
            f"attestation_report_verify failed. Code:{verify_status.code}, Message:{verify_status.message}."
        )
    logging.warning("Verify attestation report success.")
