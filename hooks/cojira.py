from __future__ import annotations

import argparse
import urllib
from collections.abc import Sequence
from re import search

from hooks import commiticketing


def get_ticket(file_or_branch: str) -> str:
    if not file_or_branch:  # post-checkout hook
        return commiticketing.get_prefix(commiticketing.get_active_branch_name(),
                                         ['user', 'backup'])

    try:
        with open(file_or_branch, encoding='utf-8') as msg:  # commit hook
            lines = msg.readlines()
            ticketing = search(r'^([A-Z]{2,}-[1-9][0-9]*): .*', lines[0])
            return commiticketing.get_prefix(commiticketing.get_active_branch_name(),
                                             ['user', 'backup']) \
                if not ticketing \
                else ticketing.group(1)
    except OSError:  # push hook
        return commiticketing.get_prefix(file_or_branch,
                                         ['user', 'backup'])


def get_ticket_version(ticket: str, jira_uri: str, jira_pat: str) -> str:
    urllib.request.HTTPCookieProcessor().
#    request = Request
    return ''


def get_ticket_status_category(ticket: str, jira_uri: str, jira_pat: str) -> str:
    return ''


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filename-or-branchname', help='To cross-check')
    parser.add_argument(
        '-u', '--jira-uri', action='store_true',
        help='URI of JIRA instance, may be an environment variable',
    )
    parser.add_argument(
        '-t', '--jira-pat', action='store_true',
        help='Personal access token (PAT) to authenticate against JIRA instance,'
             ' may be an environment variable',
    )
    parser.add_argument(
        '-i', '--allow-status-category', action='append',
        help='Ticket status category to be allowed,'
             ' may be specified multiple times;'
             ' has priority over disallowed status categories'
             ' (default: none)',
    )
    parser.add_argument(
        '-e', '--disallow-status-category', action='append',
        help=('Ticket status category to be disallowed, '
              ' may be specified multiple times'
              ' (default: "done")'),
    )
    parser.add_argument(
        '-v', '--allowed-fix-version', action='append',
        help=('Fix version to be allowed; '
              ' not checked if none specified;'
              ' may be specified multiple times,'
              ' may be an environment variable'
              ' (default: none)'),
    )
    args = parser.parse_args(argv)

    allowed = frozenset(args.allow_status_category)
    disallowed = frozenset(args.disallow_status_category or 'done')
    version = frozenset(args.allowed_fix_version)

    ticket = get_ticket(args.filename_or_branchname)

    if len(version) > 0:
        ticket_version = get_ticket_version(ticket, args.jira_uri, args.jira_pat)
        if ticket_version not in version:
            return 1

    ticket_status_category = get_ticket_status_category(ticket, args.jira_uri, args.jira_pat)
    if ticket_status_category in allowed or ticket_status_category not in disallowed:
        return 0
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
