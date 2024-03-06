from __future__ import annotations

import argparse
from collections.abc import Iterable
from collections.abc import Sequence
from pathlib import Path
from re import escape
from re import match


def get_active_branch_name() -> str | None:
    """
    Source: https://stackoverflow.com/a/62724213/5471574
        and https://stackoverflow.com/a/59115583/5471574

    This works for us, because the current working directory (i.e., current
    working directory) _IS_ the git repository.

    By default, and when in a conflicting rebase-apply, HEAD is found.

    During conflicting rebase-merge, we go via head-name.

    :return: The name of the currently checked out branch
    """
    head = None
    try:
        with (Path('.') / '.git' / 'HEAD').open('r') as f:
            content = f.read().splitlines()

        for line in content:
            if line[:4] == 'ref:':
                head = line.removeprefix('ref: refs/heads/')
        if head:
            return head

        with (
            Path('.') / '.git' / 'rebase-merge' / 'head-name'
        ).open('r') as f:
            content = f.read().splitlines()

        for line in content:
            head = line.removeprefix('refs/heads/')
        if head:
            return head

    except FileNotFoundError:
        pass

    return head


def get_prefix(branch: str, two_level_branches: Iterable[str]) -> str | None:
    for tlb in two_level_branches:
        if (
            branch.startswith(tlb)
            and match(
                r'^' + escape(tlb) + '/[^/]+/[A-Z]{2,}-[1-9][0-9]*(-.+)?$',
                branch,
            )
        ):
            return '-'.join(branch.split('/')[2].split('-')[:2])
    if match(r'^[^/]+/[A-Z]{2,}-[1-9][0-9]*(-.+)?$', branch):
        return '-'.join(branch.split('/')[1].split('-')[:2])
    else:
        return None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='Commit message to check')
    parser.add_argument(
        '-l', '--long-prefix', action='store_true',
        help='Add long prefix for branches (by default: no)',
    )
    parser.add_argument(
        '-e', '--exclude-long-prefix', action='append',
        help='Do not add long prefix for these branches'
             '(by default: feature, user, backup), '
             'may be specified multiple times',
    )
    parser.add_argument(
        '-t', '--two-level', action='append',
        help='Get prefix from second level,'
             'if branch starts with this (by default: user, backup), '
             'may be specified multiple times',
    )
    parser.add_argument(
        '-b', '--branch', action='append',
        help='Branch to process with this hook '
             '(by default: feature, bugfix, hotfix), '
             'may be specified multiple times',
    )
    args = parser.parse_args(argv)

    two_level_branches = frozenset(args.two_level or ('user', 'backup'))
    processed_branches = frozenset(
        args.branch or ('feature', 'bugfix', 'hotfix'),
    )
    short_branches = frozenset(
        args.exclude_long_prefix or ('feature', 'user', 'backup'),
    )
    branch = get_active_branch_name()

    if not branch:
        print('Could not reify branch name.')
        return 3

    with open(args.filename, encoding='utf-8') as msg:
        lines = msg.readlines()

    for candidate in frozenset.union(processed_branches, two_level_branches):
        if match(r'^' + escape(candidate) + '/.*$', branch):
            prefix = get_prefix(branch, two_level_branches)
            if not prefix:
                print(
                    f'[{branch}] does not correspond to branch naming rules, '
                    'consult guidelines.',
                )
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
                    print(
                        'Commiticketing prefixed your subject line with '
                        f'[{prefix}] and made it sentence case after.',
                    )
                    msg.writelines(lines)
            else:
                print('Commiticketing did not change your subject line.')

            return 0

    print(
        f'You wanted to commit to a branch [{branch}], '
        'which does not correspond to the commiticketing setup.',
    )
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
