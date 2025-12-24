# Multidecoder

Automatically attempt to (recursively) decode text using common
encodings.


## Supported encodings

- base64 (and its urlsafe variant)
- hexadecimal
- html escape characters
- url encoding


## Supported unicode encodings

Via [chardet](https://pypi.org/project/chardet/):

- ASCII, UTF-8, UTF-16 (2 variants), UTF-32 (4 variants)
- Big5, GB2312, EUC-TW, HZ-GB-2312, ISO-2022-CN (Traditional and Simplified Chinese)
- EUC-JP, SHIFT_JIS, CP932, ISO-2022-JP (Japanese)
- EUC-KR, ISO-2022-KR, Johab (Korean)
- KOI8-R, MacCyrillic, IBM855, IBM866, ISO-8859-5, windows-1251 (Cyrillic)
- ISO-8859-5, windows-1251 (Bulgarian)
- ISO-8859-1, windows-1252, MacRoman (Western European languages)
- ISO-8859-7, windows-1253 (Greek)
- ISO-8859-8, windows-1255 (Visual and Logical Hebrew)
- TIS-620 (Thai)


## Install

TODO: install via pipx (as a tool) or pip/uv (as a library)

The recommended way to install this is via [pipx](https://pipx.pypa.io/stable/installation/):

    pipx install text-multidecoder

Or from git:

    pipx install git+https://github.com/rshk/multidecoder.git@main

Or run from a source code checkout:

    git clone https://github.com/rshk/multidecoder.git
    cd ./multidecoder
    uv sync
    uv run multidecoder


## Command-line usage

    multidecoder -t "string to decode"
    multidecoder < decodeme.txt


## Library usage

    from multidecoder import multidecode, display_result

    results = multidecode(text, max_depth=10)
    display_result(results, sys.stdout)


## Contributing

Just open an issue or pull request on gituhb.

If your're contributing a decoder, place short ones (max 10 lines or
so) inside the `basic` module. Longer ones should be placed in their
own module.

Decoders carrying extra dependencies should probably be made optional,
and possibly installed as "extras". Support for optional decoders is
not implemented yet, but please do reach out if this is something you
might need.
