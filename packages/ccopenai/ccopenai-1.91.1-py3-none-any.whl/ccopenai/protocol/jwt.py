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

from typing import List

from pydantic import BaseModel


# Jwe represents the JSON Web Encryption as specified in RFC 7516
class Jwe(BaseModel):
    # JWE JOSE Header(Section 4 in RFC 7516)
    class JoseHeader(BaseModel):
        # the cryptographic algorithm(Section 4.1.1 in RFC 7515)
        #
        # such as "RSA-OAEP-256" or "SM2SM3"
        alg: str = "RSA-OAEP-256"
        # the content encryption algorithm used to perform authenticated encryption
        # on the plaintext to produce the ciphertext and the Authentication Tag.
        #
        # such as "A128GCM" or "SM4GCM"
        enc: str = "A128GCM"
        # if has_signature = True: the message structure is Jwe(Jws(plain_text)),
        # if has_signature = False: the message structure is Jwe(plain_text)
        has_signature: bool = False

    # RFC4648 BASE64_URL_UNPADDED(UTF8(JWE JOSE Header))
    protected: str = None

    # RFC4648 BASE64_URL_UNPADDED(JWE Encrypted Key)
    encrypted_key: str = None

    # RFC4648 BASE64_URL_UNPADDED(JWE Initialization Vector)
    iv: str = ""

    # RFC4648 BASE64_URL_UNPADDED(JWE Ciphertext)
    ciphertext: str = ""

    # RFC4648 BASE64_URL_UNPADDED(JWE Authentication Tag)
    tag: str = ""

    # RFC4648 BASE64_URL_UNPADDED(JWE AAD)
    aad: str = ""


class Jws(BaseModel):
    # JWS JOSE Header(Section 4 in RFC 7515)
    class JoseHeader(BaseModel):
        # the cryptographic algorithm(Section 4.1.1 in RFC 7515)
        #
        # such as "RS256"
        alg: str = ""

        # The "x5c" (X.509 certificate chain) Header Parameter contains the
        # X.509 public key certificate or certificate chain [RFC5280]
        # corresponding to the key used to digitally sign the JWS.
        x5c: List[str] = None

    # RFC4648 BASE64_URL_UNPADDED(UTF8(JWS JOSE Header))
    protected: str = None

    # RFC4648 BASE64_URL_UNPADDED(JWS Payload)
    payload: str = ""

    # RFC4648 BASE64_URL_UNPADDED(JWS Signature)
    signature: str = None
