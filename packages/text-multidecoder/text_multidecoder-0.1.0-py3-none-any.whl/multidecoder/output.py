from __future__ import annotations

import itertools
import sys
from contextlib import contextmanager
from typing import Any, Iterable, TextIO

from .core import Result


def display_result(
    results: Iterable[Result],
    output: TextIO | None = None,
):
    """
    Format the output of multidecode()

    Args:
        results: as returned by multidecode()
        output: output stream to write to, defaults to stdout
    """

    if output is None:
        output = sys.stdout
    assert output is not None

    oc = OutputColorizer(output, palette=PALETTE_TRUECOLOR)

    return _display_result(results, oc=oc)


def _display_result(
    results: Iterable[Result],
    oc: OutputColorizer,
    depth: int = 0,
):
    """
    Format the output of multidecode()

    Args:
        results: as returned by multidecode()
        depth: used internally for indentation
        oc: used internally for colorization
    """

    # Keep track of results we already encountered so we don't go down
    # the same path twice.
    encountered = {}

    indent = " " * (4 * depth)
    for result in results:
        # Text representation of the arguments
        text_args = ""
        if result.args:
            args_string = ",".join(result.args)
            text_args = f"({args_string})"

        if not result.is_new_path:
            oc.write(indent)

            with oc.color("muted"):
                oc.write("\x1b[]")
                oc.write(result.decoder_id)
                oc.write(text_args)
                oc.write(" -> ")

                if result.value in encountered:
                    oc.write(f"same as {encountered[result.value]}\n")
                else:
                    oc.write("(seen before) ")
                    oc.write(format_value(result.value))
                    oc.write("\n")

        else:
            encountered[result.value] = result.decoder_id

            # We need the counter to decide if this is a "leaf node"
            sub_results = list(result.sub_results)

            is_leaf_node = len(sub_results) == 0

            oc.write(indent)

            with oc.color("decname"):
                oc.write(result.decoder_id)
            with oc.color("decargs"):
                oc.write(text_args)
            with oc.color("arrow"):
                oc.write(" -> ")
            with oc.color("leafvalue" if is_leaf_node else "value"):
                oc.write(format_value(result.value))
            oc.write("\n")

            # Recursive display
            _display_result(sub_results, depth=depth + 1, oc=oc)


CSI = "\x1b["


def hex_to_truecolor(color: str):
    color = color.lstrip("#")
    if len(color) == 3:
        rs, gs, bs = color
        color = rs * 2 + gs * 2 + bs * 2
    if len(color) != 6:
        raise ValueError(f"Invalid hex color: {color}")
    color_from_hex = int.from_bytes(bytes.fromhex(color))
    red = color_from_hex // 256**2
    green = color_from_hex // 256 % 256
    blue = color_from_hex % 256
    return f"8;2;{red};{green};{blue}"


tc = hex_to_truecolor


PALETTE_NOCOLOR = {
    "muted": ("", ""),
    "value": ("", ""),
    "leafvalue": ("", ""),
    "decname": ("", ""),
    "decargs": ("", ""),
    "arrow": ("", ""),
}

PALETTE_TRUECOLOR = {
    "muted": (f"{CSI}3{tc('#78909C')}m", f"{CSI}39m"),
    "value": (f"{CSI}3{tc('#8BC34A')}m", f"{CSI}39m"),
    "leafvalue": (f"{CSI}3{tc('#FFEB3B')}m", f"{CSI}39m"),
    "decname": (f"{CSI}3{tc('#42A5F5')}m", f"{CSI}39m"),
    "decargs": (f"{CSI}3{tc('#1976D2')}m", f"{CSI}39m"),
    "arrow": (f"{CSI}3{tc('#4CAF50')}m", f"{CSI}39m"),
}


class OutputColorizer:
    def __init__(self, stream, palette):
        self.stream = stream
        self.palette = palette

    @contextmanager
    def color(self, name: str):
        [prefix, suffix] = self.palette.get(name, ("", ""))
        self.stream.write(prefix)
        try:
            yield
        finally:
            self.stream.write(suffix)

    def write(self, text):
        self.stream.write(text)

    def writeln(self, text):
        self.stream.write(text)
        self.stream.write("\n")


def format_value(value: str | bytes | Any):
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        hexval = " ".join(
            y for y in ("".join(x) for x in itertools.batched(value.hex(), 2))
        )
        reprval = str(value)
        if len(hexval) < len(reprval):
            return f"hex[ {hexval} ]"
        return reprval
    raise TypeError("Invalid type")
