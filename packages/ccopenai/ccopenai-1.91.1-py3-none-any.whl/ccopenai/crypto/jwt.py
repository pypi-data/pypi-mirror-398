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

import base64
from typing import List, Union

from cryptography.hazmat.primitives.asymmetric import rsa

from ..crypto import asymm, symm, util
from ..protocol import Jwe, Jws

RSA_SHA256 = "RS256"
SEPARATOR = b"."


def encode_base64(input_bytes: bytes, urlsafe: bool = True) -> str:
    """
    Encode bytes as an unpadded base64 string.

    Args:
        input_bytes: the data will be encode
        urlsafe: whether to encode data in urlsafe method

    Returns:
        the base64 encode string
    """

    if urlsafe:
        encode = base64.urlsafe_b64encode
    else:
        encode = base64.b64encode

    output_bytes = encode(input_bytes)
    output_string = output_bytes.decode("ascii")
    return output_string.rstrip("=")


def decode_base64(input_string: str) -> bytes:
    """Decode an unpadded standard or urlsafe base64 string to bytes."""

    input_bytes = input_string.encode("ascii")
    input_len = len(input_bytes)
    padding = b"=" * (3 - ((input_len + 3) % 4))

    # Passing altchars here allows decoding both standard and urlsafe base64
    output_bytes = base64.b64decode(input_bytes + padding, altchars=b"-_")
    return output_bytes


def pack_jws(
    content: str,
    private_key_pem: bytes,
    cert_pems: List[bytes] = None,
) -> Jws:
    """
    construct the data struct Jws

    Args:
        content: the data will be signed
        private_key_pem: the private key in pem format is used to sign Jws
        cert_pems: the certification chain in pem format is used to verify the signature in Jws

    Returns:
        the Jws instance
    """
    jws = Jws()
    jws_JoseHeader = jws.JoseHeader()
    jws_JoseHeader.alg = RSA_SHA256
    # fill jws_JoseHeader.x5c
    jws_JoseHeader.x5c.extend(
        [
            # has padding
            base64.standard_b64encode(util.convert_pem_to_der(cert_pem)).decode("utf-8")
            for cert_pem in cert_pems
        ]
    )
    jws.protected = encode_base64(
        jws_JoseHeader.model_dump_json(exclude_none=True).encode("utf-8")
    )
    jws.payload = encode_base64(content.encode("utf-8"))
    jws.signature = encode_base64(
        asymm.RsaSigner(private_key_pem)
        .update(jws.protected.encode("utf-8"))
        .update(SEPARATOR)
        .update(jws.payload.encode("utf-8"))
        .sign()
    )
    return jws


def pack_jwe(
    content: str,
    public_key_pem: bytes = None,
    data_key: bytes = None,
    public_key_scheme: str = "RSA-OAEP-256",
    data_key_scheme: str = "A128GCM",
    jwe_sig: bool = False,
    private_key_pem: bytes = None,
    cert_pems: List[bytes] = None,
) -> Jwe:
    """
    construct the data struct Jwe

    Args:
        content: the data will be encrypted
        public_key_pem: the public key in pem format is used to encrypt data_key.
                If None, data_key will be not encrypted
        data_key: the key is used to encrypt data
        public_key_scheme: the scheme of public key
        data_key_scheme: the scheme of data_key
        jwe_sig: whether to use Jws to sign the data
        private_key_pem: the private key in pem format is used to sign Jws, only takes effect when jwe_sig = True
        cert_pems: the certification chain in pem format is used to verify the signature in Jws,
                    only takes effect when jwe_sig = True

    Returns:
        the Jwe instance
    """
    # pack jws
    if jwe_sig:
        jws = pack_jws(content, private_key_pem, cert_pems)
        content = jws.model_dump_json(exclude_none=True)
    # pack jwe
    if data_key is None:
        data_key = util.gen_key(16)
    iv = util.gen_key(12)
    aad = b""

    jwe = Jwe()
    jwe_header = jwe.JoseHeader()
    # TODO: support more encrypt algorithm
    jwe_header.alg = public_key_scheme
    jwe_header.enc = data_key_scheme
    jwe_header.has_signature = jwe_sig

    (ciphertext, tag) = symm.AesGcmEncryptor(data_key, jwe_header.enc).encrypt(
        content.encode("utf-8"), iv, aad
    )
    if public_key_pem:
        encrypted_data_key = asymm.RsaEncryptor(public_key_pem, jwe_header.alg).encrypt(
            data_key
        )
    else:
        encrypted_data_key = b""
    jwe.protected = encode_base64(
        jwe_header.model_dump_json(exclude_none=True).encode("utf-8")
    )
    jwe.encrypted_key = encode_base64(encrypted_data_key)
    jwe.iv = encode_base64(iv)
    jwe.aad = ""
    jwe.ciphertext = encode_base64(ciphertext)
    jwe.tag = encode_base64(tag)

    return jwe


def parse_jwe(
    jwe: Jwe,
    private_key: Union[bytes, str, rsa.RSAPrivateKey] = None,
    data_key: bytes = None,
) -> bytes:
    """
    get data from Jwe instance

    Args:
        jwe: the Jwe instance
        private_key: if not None, it will be used to decrypt data_key from the Jwe instance
        data_key: the key is used to decrypt data, only takes effect when private_key is None

    Returns: string or the serialization of class
    """
    # parse jwe struct
    jwe_header = jwe.JoseHeader.model_validate_json(decode_base64(jwe.protected))

    iv = decode_base64(jwe.iv)
    ciphertext = decode_base64(jwe.ciphertext)
    tag = decode_base64(jwe.tag)
    aad = decode_base64(jwe.aad)
    # get data key
    if private_key:
        data_key = asymm.RsaDecryptor(private_key, jwe_header.alg).decrypt(
            decode_base64(jwe.encrypted_key)
        )
    # decrypt data
    plain_text = symm.AesGcmDecryptor(data_key, jwe_header.enc).decrypt(
        ciphertext, iv, aad, tag
    )

    # if jwe_header.has_signature, the data exists in the Jws instance
    if jwe_header.has_signature:
        # TODO: verify signature
        jws = Jws.model_validate_json(plain_text)

        # if msg is none, it means it is string or binary

        return decode_base64(jws.payload)

    else:
        return plain_text
