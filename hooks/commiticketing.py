from __future__ import annotations

import argparse
from re import match
from re import escape
from typing import Sequence, Optional, Set, Iterable
from pathlib import Path


def get_active_branch_name() -> Optional[str]:
    """
    Source: https://stackoverflow.com/a/62724213/5471574

    This works for us, because the current working directory (i.e., os.getcwd()) _IS_ the git repository.
    :return: The name of the currently checked out branch
    """
    head_dir = Path('.') / '.git' / 'HEAD'
    try:
        with head_dir.open('r') as f:
            content = f.read().splitlines()

        for line in content:
            if line[:4] == 'ref:':
                return line.partition('refs/heads/')[2]
    except FileNotFoundError:
        pass

    return None


def get_prefix(branch: str, two_level_branches: Iterable[str]) -> Optional[str]:
    for tlb in two_level_branches:
        if branch.startswith(tlb):
            if match(r'^' + escape(tlb) + '/[^/]+/[A-Z]{2,}-[1-9][0-9]*(-.+)?$', branch):
                return '-'.join(branch.split('/')[2].split('-')[:2])
    if match(r'^[^/]+/[A-Z]{2,}-[1-9][0-9]*(-.+)?$', branch):
        return '-'.join(branch.split('/')[1].split('-')[:2])
    else:
        return None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='Commit message to check')
    parser.add_argument('-l', '--long-prefix', action='store_true',
                        help='Add long prefix for branches (by default: no)')
    parser.add_argument('-e', '--exclude-long-prefix', action='append',
                        help='Do not add long prefix for these branches (by default: feature, user, backup), '
                             'may be specified multiple times')  # pragma: no mutate
    parser.add_argument('-t', '--two-level', action='append',
                        help='Get prefix from second level, if branch starts with this (by default: user, backup), '
                             'may be specified multiple times')  # pragma: no mutate
    parser.add_argument('-b', '--branch', action='append',
                        help='Branch to process with this hook '
                             '(by default: feature, bugfix, hotfix), '  # pragma: no mutate
                             'may be specified multiple times')  # pragma: no mutate
    args = parser.parse_args(argv)

    two_level_branches = frozenset(args.two_level or ('user', 'backup'))
    processed_branches = frozenset(args.branch or ('feature', 'bugfix', 'hotfix'))
    short_branches = frozenset(args.exclude_long_prefix or ('feature', 'user', 'backup'))
    branch = get_active_branch_name()

    if not branch:
        print(f'Could not reify branch name')
        return 3

    with open(args.filename, 'r', encoding='utf-8') as msg:
        lines = msg.readlines()

    for candidate in frozenset.union(processed_branches, two_level_branches):
        if match(r'^' + escape(candidate) + '/.*$', branch):
            prefix = get_prefix(branch, two_level_branches)
            if not prefix:
                print(f'[{branch}] does not correspond to branch naming rules, consult guidelines')
                return 2

            prefix += ': '
            if args.long_prefix and candidate not in short_branches:
                prefix += f'({candidate}) '

            subject_line = lines[0]

            lines[0] = lines[0].removeprefix(prefix)
            lines[0] = lines[0][0].upper() + lines[0][1:]
            lines[0] = prefix + lines[0]

            if lines[0] != subject_line:
                with open(args.filename, 'w', encoding='utf-8') as msg:
                    print(f'Commiticketing prefixed your subject line with [{prefix}] and made it sentence case after')
                    msg.writelines(lines)
            else:
                print('Commiticketing did not change your subject line')

            return 0

    print(f'You wanted to commit to a branch [{branch}], which does not correspond to the commiticketing setup')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
