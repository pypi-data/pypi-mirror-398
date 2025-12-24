from __future__ import annotations

import functools
from typing import Callable, Iterable, NamedTuple


class DecoderResult(NamedTuple):
    value: str | bytes
    args: tuple[str, ...] | None


DecoderFunction = Callable[[bytes | str], DecoderResult]
DecoderImplFunction = Callable[[str | bytes], str | bytes | tuple[str, str | bytes]]
DECODERS: dict[str, DecoderFunction] = {}


def add_decoder(name: str):
    def decorator(fn):
        wrapped = wrap_decoder_function(fn)
        DECODERS[name] = wrapped
        return wrapped

    return decorator


def iter_decoders() -> Iterable[tuple[str, DecoderFunction]]:
    return DECODERS.items()


def wrap_decoder_function(fn: DecoderImplFunction) -> DecoderFunction:
    @functools.wraps(fn)
    def decorated(*args, **kwargs) -> DecoderResult:
        result = fn(*args, **kwargs)
        if isinstance(result, DecoderResult):
            return result
        if isinstance(result, (str, bytes)):
            return DecoderResult(value=result, args=None)
        if isinstance(result, tuple):
            [value, args] = result
            if not isinstance(value, (str, bytes)):
                raise TypeError(f"Invalid decoded value type: {type(value)}")
            if isinstance(args, str):
                args = (args,)
            if not (isinstance(args, tuple) and all(isinstance(x, str) for x in args)):
                raise TypeError("Malformed args returned by decoder")
            return DecoderResult(value=value, args=args)
        raise TypeError(f"Invalid decoder return value: {type(result)}")

    return decorated
