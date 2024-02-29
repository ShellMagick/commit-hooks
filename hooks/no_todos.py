from __future__ import annotations

import argparse
from os.path import basename
from typing import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='Filenames to check')
    parser.add_argument(
        '-t', '--todo-tag', action='append',
        help='TODO tag to disallow as file content, may be specified multiple times (by default: TODO, FIXME, XXX)',
    )
    parser.add_argument(
        '-e', '--except-in', action='append', default=[],
        help='Except in these files (i.e., a file with this name is allowed to contain the tags), '
             'may be specified multiple times'
    )
    args = parser.parse_args(argv)

    disallowed = frozenset(args.todo_tag or ('TODO', 'FIXME', 'XXX'))

    retv = 0

    for filename in args.filenames:
        with open(filename, encoding='utf-8') as f:
            lines = f.readlines()

        for tag in disallowed:
            for line in lines:
                if tag in line:
                    if basename(filename) in args.except_in:
                        print(f'{filename}: contains {tag}, but is on the exception list')
                        break  # pragma: no mutate
                    retv += 1
                    print(f'{filename}: contains {tag}')

    return retv


if __name__ == '__main__':
    raise SystemExit(main())