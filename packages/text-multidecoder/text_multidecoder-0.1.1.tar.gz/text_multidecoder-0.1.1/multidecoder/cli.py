import sys
import click

from multidecoder.core import multidecode
from multidecoder.output import display_result


@click.command()
@click.option("-t", "--text", "text")
def main(text):
    if text is not None:
        # Assume utf-8
        text = text.encode()
    else:
        text = sys.stdin.buffer.read()
    assert isinstance(text, bytes)

    results = multidecode(text, max_depth=10)
    display_result(results)


if __name__ == '__main__':
    main()
