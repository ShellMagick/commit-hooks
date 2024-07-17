from __future__ import annotations

import argparse
from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='Filenames to check')
    args = parser.parse_args(argv)

    result = 1

    for filename in args.filenames:
        with open(filename, 'rb') as f:
            candidate = f.read(4)

        # Note: we check in "reverse" order,
        #       because the UTF-16 BOM (LE) is a prefix of the UTF-32 BOM (LE)
        # Cf. https://www.unicode.org/faq/utf_bom.html#BOM
        if candidate == b'\xff\xfe\x00\x00':
            result *= 13
            print(f'{filename}: has a UTF-32 BOM (LE)')
        elif candidate == b'\x00\x00\xfe\xff':
            result *= 11
            print(f'{filename}: has a UTF-32 BOM (BE)')
        elif candidate[:2] == b'\xff\xfe':
            result *= 7
            print(f'{filename}: has a UTF-16 BOM (LE)')
        elif candidate[:2] == b'\xfe\xff':
            result *= 5
            print(f'{filename}: has a UTF-16 BOM (BE)')
        elif candidate[:3] == b'\xef\xbb\xbf':
            result *= 3
            print(f'{filename}: has a UTF-8 BOM')

    return result % 256 if result != 1 else 0


if __name__ == '__main__':
    raise SystemExit(main())
