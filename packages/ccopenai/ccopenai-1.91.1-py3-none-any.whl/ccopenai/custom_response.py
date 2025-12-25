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

import logging
import typing

import httpx

ENCRYPT_API_LIST = [
    "/chat/completions",
]


def decrypt(encrypted_content: bytes):
    from .crypto import jwt
    from .env import get_data_key
    from .protocol import jwt as jwt_pb

    plaintext_content = jwt.parse_jwe(
        jwt_pb.Jwe.model_validate_json(encrypted_content), None, get_data_key()
    )
    return plaintext_content


def is_encrypted(url_path: str):
    for key in ENCRYPT_API_LIST:
        if url_path.endswith(key):
            return True
    return False


def is_sse_response(response: httpx.Response):
    content_type = response.headers.get("Content-Type", "").lower()
    return "text/event-stream" in content_type


def split_sse(data: str):
    events = data.split("\n\n")
    return events[0:-1], bytearray(events[-1].encode())


def decrypt_sse(event: str):
    # judge whether the event is the mark of end
    if event == "data: [DONE]":
        return event.encode()
    # if not the mark, then decrypt the jwe
    jwe = event.split("data:", 1)[1].strip()
    plaintext = decrypt(jwe.encode())

    return b"data: " + plaintext


def compose_sse(events: list):
    decrypted_sse = bytearray()
    for event in events:
        decrypted_sse.extend(decrypt_sse(event))
        decrypted_sse.extend(b"\n\n")
    return bytes(decrypted_sse)


def custom_iter_bytes(
    self: httpx.Response, chunk_size: int | None = None
) -> typing.Iterator[bytes]:
    """
    A byte-iterator over the decoded response content.
    This allows us to handle gzip, deflate, brotli, and zstd encoded responses.
    """
    from httpx._decoders import ByteChunker
    from httpx._exceptions import request_context

    if hasattr(self, "_content"):
        chunk_size = len(self._content) if chunk_size is None else chunk_size
        for i in range(0, len(self._content), max(chunk_size, 1)):
            yield self._content[i : i + chunk_size]
    else:
        decoder = self._get_content_decoder()
        chunker = ByteChunker(chunk_size=chunk_size)
        # encrypt info
        encrypted = is_encrypted(self.url.path)
        expect_len = int(
            self.headers.get("content-length", 0)
            or self.headers.get("Content-Length", 0)
        )
        complete_encrypt_data = bytearray()
        is_sse = is_sse_response(self)

        with request_context(request=self._request):
            for raw_bytes in self.iter_raw():
                decoded = decoder.decode(raw_bytes)

                # decrypt after decode
                if encrypted:
                    if is_sse:
                        complete_encrypt_data.extend(decoded)
                        # judge whether SSE exists
                        if b"\n\n" in complete_encrypt_data:
                            events, complete_encrypt_data = split_sse(
                                complete_encrypt_data.decode()
                            )
                            decoded = compose_sse(events)
                        else:
                            continue
                    elif expect_len:
                        complete_encrypt_data.extend(decoded)
                        if len(complete_encrypt_data) < expect_len:
                            continue
                        decoded = decrypt(bytes(complete_encrypt_data))
                        complete_encrypt_data.clear()
                    else:
                        decoded = decrypt(decoded)

                # chunk after decrypt
                for chunk in chunker.decode(decoded):
                    yield chunk

            if encrypted and len(complete_encrypt_data) > 0:
                if is_sse:
                    decoded = decrypt_sse(complete_encrypt_data.decode())
                else:
                    # crypt data completely
                    decoded = decrypt(bytes(complete_encrypt_data))
                complete_encrypt_data.clear()

                # chunk after decrypt
                for chunk in chunker.decode(decoded):
                    yield chunk

            decoded = decoder.flush()
            for chunk in chunker.decode(decoded):
                yield chunk  # pragma: no cover
            for chunk in chunker.flush():
                yield chunk


async def custom_aiter_bytes(
    self: httpx.Response, chunk_size: int | None = None
) -> typing.AsyncIterator[bytes]:
    """
    A byte-iterator over the decoded response content.
    This allows us to handle gzip, deflate, brotli, and zstd encoded responses.
    """
    from httpx._decoders import ByteChunker
    from httpx._exceptions import request_context

    if hasattr(self, "_content"):
        chunk_size = len(self._content) if chunk_size is None else chunk_size
        for i in range(0, len(self._content), max(chunk_size, 1)):
            yield self._content[i : i + chunk_size]
    else:
        decoder = self._get_content_decoder()
        chunker = ByteChunker(chunk_size=chunk_size)
        # encrypt info
        encrypted = is_encrypted(self.url.path)
        expect_len = int(
            self.headers.get("content-length", 0)
            or self.headers.get("Content-Length", 0)
        )
        complete_encrypt_data = bytearray()
        is_sse = is_sse_response(self)

        with request_context(request=self._request):
            async for raw_bytes in self.aiter_raw():
                decoded = decoder.decode(raw_bytes)

                # decrypt after decode
                if encrypted:
                    if is_sse:
                        complete_encrypt_data.extend(decoded)
                        # judge whether SSE exists
                        if b"\n\n" in complete_encrypt_data:
                            events, complete_encrypt_data = split_sse(
                                complete_encrypt_data.decode()
                            )
                            decoded = compose_sse(events)
                        else:
                            continue
                    elif expect_len:
                        complete_encrypt_data.extend(decoded)
                        if len(complete_encrypt_data) < expect_len:
                            continue
                        decoded = decrypt(bytes(complete_encrypt_data))
                        complete_encrypt_data.clear()
                    else:
                        decoded = decrypt(decoded)

                # chunk after decrypt
                for chunk in chunker.decode(decoded):
                    yield chunk

            if encrypted and len(complete_encrypt_data) > 0:
                if is_sse:
                    decoded = decrypt_sse(complete_encrypt_data.decode())
                else:
                    # crypt data completely
                    decoded = decrypt(bytes(complete_encrypt_data))
                complete_encrypt_data.clear()

                # chunk after decrypt
                for chunk in chunker.decode(decoded):
                    yield chunk

            decoded = decoder.flush()
            for chunk in chunker.decode(decoded):
                yield chunk  # pragma: no cover
            for chunk in chunker.flush():
                yield chunk


httpx.Response.iter_bytes = custom_iter_bytes
httpx.Response.aiter_bytes = custom_aiter_bytes

logging.warning("Replace httpx response method!")
