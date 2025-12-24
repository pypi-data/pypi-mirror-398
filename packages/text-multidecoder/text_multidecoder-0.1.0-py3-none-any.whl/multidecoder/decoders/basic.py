from __future__ import annotations

import base64
import html
import urllib.parse
from typing import AnyStr

import chardet

from .registry import add_decoder


@add_decoder("base64")
def decode_base64(text: str | bytes) -> bytes:
    if isinstance(text, str):
        text = text.encode()
    return base64.decodebytes(text)


@add_decoder("base64_urlsafe")
def decode_base64_urlsafe(text: str | bytes) -> bytes:
    if isinstance(text, str):
        text = text.encode()
    return base64.urlsafe_b64decode(text)


@add_decoder("hex")
def decode_hex(text: str | bytes) -> bytes:
    if isinstance(text, bytes):
        text = text.decode()
    return bytes.fromhex(text)


@add_decoder("html")
def decode_html(text: AnyStr) -> AnyStr:
    return html.unescape(text)


@add_decoder("url")
def decode_url(text: AnyStr) -> AnyStr:
    if isinstance(text, bytes):
        return urllib.parse.unquote(text.decode()).encode()
    return urllib.parse.unquote(text)


@add_decoder("unicode-utf8")
def decode_unicode_utf8(text: bytes) -> str:
    return text.decode("utf-8")


@add_decoder("unicode-chardet")
def decode_unicode_chardet(text: bytes) -> tuple[str, str]:
    res = chardet.detect(text)
    encoding = res["encoding"]
    if encoding is None:
        raise ValueError("Falied to detect encoding")
    THRESHOLD = 0  # todo: do we need this?
    if res["confidence"] < THRESHOLD:
        raise ValueError("Chardet confidence too low")
    return text.decode(encoding), encoding
