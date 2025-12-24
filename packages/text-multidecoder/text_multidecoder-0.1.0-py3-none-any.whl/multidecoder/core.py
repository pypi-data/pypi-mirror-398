from __future__ import annotations

from typing import Iterable, NamedTuple

from .decoders import iter_decoders


class Result(NamedTuple):
    decoder_id: str
    value: str | bytes
    args: tuple[str, ...] | None
    sub_results: Iterable["Result"]

    # Have we encountered this result before?
    is_new_path: bool


def multidecode(text: str | bytes, max_depth=100, dedupe_set: set | None = None) -> Iterable[Result]:
    if max_depth <= 0:
        return  # Max depth reached

    if dedupe_set is None:
        dedupe_set = set()

    assert isinstance(text, (str, bytes))
    for name, decoder in iter_decoders():
        try:
            result = decoder(text)

        except Exception:
            continue  # Nothing was decoded

        if text == result.value:
            continue  # Nothing changed

        yield Result(
            decoder_id=name,
            value=result.value,
            args=result.args,
            sub_results=multidecode(result.value, max_depth=max_depth - 1, dedupe_set=dedupe_set),
            is_new_path=result.value not in dedupe_set,
        )
        dedupe_set.add(result.value)
