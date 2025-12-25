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

import base64
import datetime
import secrets
from typing import List

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from . import constants


def sha256(*args: bytes) -> bytes:
    """
    calcute hash value from bytes using sha256 algorithm

    Returns:
        hash value
    """
    h = hashes.Hash(hashes.SHA256())
    assert (
        len(args) >= 1
    ), "At least one piece of data is involved in the calculation of hash."
    h.update(args[0])
    for arg in args[1:]:
        h.update(constants.SEPARATOR)
        h.update(arg)
    return h.finalize()


def gen_key(nbytes: int = 32) -> bytes:
    """
    generating cryptographically secure random numbers

    Args:
        nbytes: the bit len

    Returns:
        secure random numbers
    """
    return secrets.token_bytes(nbytes)


def generate_rsa_keypair() -> (bytes, List[bytes]):
    """
    generate RSA private key and x509 certification chain in pem format

    Returns:
        pair of (private_key, cert_chain) in pem format
    """
    # generate private key and public key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=3072,
    )
    public_key = private_key.public_key()

    # build x509 certification
    builder = x509.CertificateBuilder()
    builder = builder.subject_name(
        x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, "model-service"),
            ]
        )
    )
    builder = builder.issuer_name(
        x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, "model-service"),
            ]
        )
    )
    one_day = datetime.timedelta(1, 0, 0)
    builder = builder.not_valid_before(datetime.datetime.today() - one_day)
    builder = builder.not_valid_after(datetime.datetime.today() + (one_day * 30))
    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.public_key(public_key)
    certificate = builder.sign(
        private_key=private_key,
        algorithm=hashes.SHA256(),
    )

    # return in pem format
    return (
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ),
        [certificate.public_bytes(encoding=serialization.Encoding.PEM)],
    )


def convert_pem_to_der(cert_pem: bytes) -> bytes:
    """
    convert x509 certfication from pem format to der format

    Args:
        cert_pem: the certification in pem format

    Returns:
        the certification in der format
    """
    cert = x509.load_pem_x509_certificate(cert_pem)
    return cert.public_bytes(encoding=serialization.Encoding.DER)


def get_public_key_from_cert(cert_pem: bytes) -> bytes:
    """
    get the public key in pem format from x509 certification

    Args:
        cert_pem: the x509 certification in pem format

    Returns:
        the public key in pem format
    """
    cert = x509.load_pem_x509_certificate(cert_pem)
    return cert.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def generate_party_id(pk: rsa.RSAPublicKey) -> str:
    """
    generate party id from public key

    Args:
        pk: the publick key

    Returns:
        the party id
    """
    party_id = base64.b32encode(
        sha256(
            pk.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    )
    return party_id.decode("ascii").rstrip("=")


def generate_party_id_from_cert(cert: bytes, format: str = "PEM") -> str:
    """
    generate party id from certification

    Args:
        cert: the certification
        format: the certification format, only choices in ["PEM", "DER"]

    Returns:
        the party id
    """
    if format == "PEM":
        public_key = x509.load_pem_x509_certificate(cert).public_key()
    elif format == "DER":
        public_key = x509.load_der_x509_certificate(cert).public_key()
    else:
        raise RuntimeError(f"format {format} is not supported")
    return generate_party_id(public_key)
