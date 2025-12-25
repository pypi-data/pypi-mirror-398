# Copyright 2024 Ant Group Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"),
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

from typing import List, Literal

from pydantic import BaseModel


class UnifiedAttestationAttributes(BaseModel):
    # The TEE platform, in case some verifier needs to verify this.
    str_tee_platform: str = ""
    # The TEE platform hardware-related identity or version
    hex_platform_hw_version: str = ""
    # The TEE platform TCB software-related version
    hex_platform_sw_version: str = ""
    # The TEE platform security-related attributes or flags
    hex_secure_flags: str = ""
    # The measurement of TEE implement internal stuff
    hex_platform_measurement: str = ""
    # The measurement of TEE instance boot time stuff
    hex_boot_measurement: str = ""
    # The name of this tee instance
    str_tee_name: str = ""
    # The TEE instance or trust application identity when generating the report
    str_tee_identity: str = ""
    # The static measurement of trust application when loading the code
    hex_ta_measurement: str = ""
    # The dynamical measurement of trust application code,
    # for example, the real-time measurement of code in secure memory
    # after the trust application is already run.
    hex_ta_dyn_measurement: str = ""
    # The measurement or other identity of the trust application signer
    hex_signer: str = ""
    # The product ID of the TEE instance or trust application
    hex_prod_id: str = ""
    # The minimal ISV SVN of the TEE instance or trust application
    str_min_isvsvn: str = ""
    # The bool string "0" for debuggable, "1" for not debuggable
    bool_debug_disabled: str = "1"
    # The user data for generating the attestation report
    hex_user_data: str = ""
    # hex string hash or original pem public key
    hex_hash_or_pem_pubkey: str = ""
    # The independent freshness value besides what is in user data
    hex_hash_or_pem_pubkey: str = ""
    # The independent freshness value besides what is in user data
    hex_nonce: str = ""
    # The service provider id, e.g. use in sgx1, 64 bytes hex string
    hex_spid: str = ""
    # The report verified time set by verifier if there is trust time
    str_verified_time: str = ""


# Match rules for nested report verification
class UnifiedAttestationNestedPolicy(BaseModel):
    sub_attributes: List[UnifiedAttestationAttributes] = None


class UnifiedAttestationNestedPolicies(BaseModel):
    # The group name and id are used for group attestation
    str_group_name: str = ""
    str_group_id: str = ""
    policies: List[UnifiedAttestationNestedPolicy] = None


# UnifiedAttestationPolicy is used when verifying the attestation report.
# Both main or nested submodule attester support multi-version of instances.
class UnifiedAttestationPolicy(BaseModel):
    # Assume one public key is bound to one report, specify it here.
    # We can also specify the public key or its hash in the main or submodule
    # UnifiedAttestationAttributes. Public key verification will happen
    # in both two places.
    # NOTE: if there is a submodule attester, we must specify the public key
    # here to verify the signature of the submodel attestation result.
    pem_public_key: str = ""
    # For the main attester
    main_attributes: List[UnifiedAttestationAttributes] = None
    # For submodule attesters
    nested_policies: UnifiedAttestationNestedPolicies = None


# Special Parameters for different TEE platforms
class UnifiedAttestationReportParams(BaseModel):
    # The identity string for the report instance which is cached inside TEE.
    # It's optional and usually used in Asynchronous processes.
    str_report_identity: str = ""
    # The user data in some TEE platforms, Max to 64 Bytes of HEX string.
    # Users need to convert binary value data to HEX string themselves.
    hex_user_data: str = ""
    # The JSON serialized string of UnifiedAttestationNestedReports
    json_nested_reports: str = ""
    # User specified public key instead of UAK to be put into report_data
    pem_public_key: str = ""
    # Service Provider ID for SGX1 only
    hex_spid: str = ""


class UnifiedAttestationGenerationParams(BaseModel):
    # For which TEE instance to generate the unified attestation report
    tee_identity: str = ""
    # which type of unified attestation report to be generated
    report_type: str = ""
    # Provide freshness if necessary.
    report_hex_nonce: str = ""
    report_params: UnifiedAttestationReportParams = None


# Unified Attestation Report
class UnifiedAttestationReport(BaseModel):
    # For compatibility and update later, the current version is "1.0"
    str_report_version: str = ""
    # Valid type string: "BackgroundCheck"|"Passport"|"Uas"
    str_report_type: Literal["BackgroundCheck", "Passport", "Uas"] = "Passport"
    # The TEE platform name
    str_tee_platform: str = ""
    # Different JSON serialized string for each TEE platform
    # The TEE platforms are in charge of parsing it in their own way.
    json_report: str = ""
    # The JSON serialized string of UnifiedAttestationNestedReports
    json_nested_reports: str = ""


# Unified attestation report with public key authentication
class UnifiedAttestationAuthReport(BaseModel):
    report: UnifiedAttestationReport = None
    pem_public_key: str = ""


# UnifiedAttestationReport::json_report for SGX2 DCAP
# Store the quote and PCCS verification collateral for SGX2 DCAP attestation
class DcapReport(BaseModel):
    # For BackgroundCheck type report: Only quote in the report
    b64_quote: str = ""
    # For Passport type report: Quote and collateral in report
    # The serialized JSON string of the SgxQlQveCollateral
    json_collateral: str = ""


# SGX DCAP quote verification collateral
# Get this after generating the quote and adding it to the report
# In this way, the challenger will don't need to connect PCCS anymore.
class SgxQlQveCollateral(BaseModel):
    # uint32_t, version = 1. PCK Cert chain is in the Quote.
    version: int = 1
    pck_crl_issuer_chain: str = ""
    root_ca_crl: str = ""
    pck_crl: str = ""
    tcb_info_issuer_chain: str = ""
    tcb_info: str = ""
    qe_identity_issuer_chain: str = ""
    qe_identity: str = ""
    # <  0x00000000: SGX or 0x00000081: TDX
    tee_type: int = 0


# UnifiedAttestationReport::json_report for HyperEnclave
# Only a quote is required for HyperEnclave attestation
class HyperEnclaveReport(BaseModel):
    b64_quote: str = ""


# UnifiedAttestationReport::json_report for Huawei Kunpeng
class KunpengReport(BaseModel):
    b64_quote: str = ""
    int_version: int = 0


# UnifiedAttestationReport::json_report for Hygon CSV
class HygonCsvReport(BaseModel):
    # For BackgroundCheck type report: Only quote in the report
    b64_quote: str = ""
    # For Passport type report: Quote and collateral in report
    # The serialized JSON string of the HygonCsvCertChain
    json_cert_chain: str = ""
    # Save chip id to avoid to parse it from b64_quote when verify report
    str_chip_id: str = ""


# UnifiedAttestationReport::json_report for Intel TDX
class IntelTdxReport(BaseModel):
    b64_quote: str = ""
    # For Passport type report: Quote and collateral in report
    # The serialized JSON string of the SgxQlQveCollateral
    json_collateral: str = ""


# Hygon CSV report verification collateral about certificates
# Get this after generating the quote and adding it to the report
# In this way, the challenger will don't need to connect PCCS anymore.
class HygonCsvCertChain(BaseModel):
    # The Base64 string of hygon_root_cert_t
    b64_hsk_cert: str = ""
    # The Base64 string of csv_cert_t
    b64_cek_cert: str = ""
