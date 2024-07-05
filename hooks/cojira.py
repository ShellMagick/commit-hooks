from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from collections.abc import Set
from os import environ
from re import search
from typing import SupportsIndex
from urllib import request


def get_ticket(commit_msg_filename: str) -> str | None:
    with open(commit_msg_filename, encoding='utf-8') as msg:
        lines = msg.readlines()
        ticketing = search(r'^([A-Z]{2,}-[1-9][0-9]*): .*', lines[0])
        return None if not ticketing else ticketing.group(1)


def fetch_jira(
    ticket: str,
    jira_uri: str,
    jira_pat: str,
) -> SupportsIndex | slice | None:
    try:
        req = request.Request(f'{jira_uri}/rest/api/latest/issue/{ticket}')
        req.add_header('Authorization', f'Bearer {jira_pat}')
        resp = request.urlopen(req)
        return json.loads(
            resp.read().decode(resp.info().get_param('charset') or 'utf-8'),
        )
    except json.decoder.JSONDecodeError:  # unexpected response
        return None


def get_ticket_version(
    ticket: str,
    jira_uri: str,
    jira_pat: str,
) -> str | None:
    body = fetch_jira(ticket, jira_uri, jira_pat)
    if not body:
        return None
    try:
        fixVersions = body['fields']['fixVersions']  # type: ignore[index]
        return fixVersions[0]['name'] if len(fixVersions) == 1 else None
    except (KeyError, TypeError):  # no .fields.fixVersions[0].name
        return None


def get_ticket_status_category(
    ticket: str,
    jira_uri: str,
    jira_pat: str,
) -> str | None:
    body = fetch_jira(ticket, jira_uri, jira_pat)
    try:
        if body:
            return body['fields']['status']['statusCategory']['key']  # type: ignore[index]  # noqa: E501
        else:
            return None
    except (KeyError, TypeError):  # no .fields.status.statusCategory.key
        return None


def check_ticket_status_category(
    ticket_status_category: str | None,
    allowed: Set[str],
    disallowed: Set[str],
) -> bool:
    if not ticket_status_category:
        return False
    if ticket_status_category in allowed \
       or ticket_status_category not in disallowed:
        return True
    return False


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('commit_msg', help='Filename of commit message')
    parser.add_argument(
        '-l', '--lenient', action='store_true',
        help='If set, and no JIRA URI is present,'
             ' this hook defaults to a NOOP',
    )
    parser.add_argument(
        '-u', '--jira-uri',
        help='URI of JIRA instance, may be an environment variable'
             ' (starting with "$")',
    )
    parser.add_argument(
        '-p', '--jira-pat',
        help='Personal access token (PAT) to use for JIRA authentication,'
             ' may be an environment variable (starting with "$")',
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
        help='Ticket status category to be disallowed,'
             ' may be specified multiple times'
             ' (default: "done")',
    )
    parser.add_argument(
        '-v', '--allowed-fix-version', action='append',
        help='Fix version to be allowed;'
             ' not checked if none specified;'
             ' may be specified multiple times,'
             ' may any of them be an environment variable (starting with "$")'
             ' (default: none)',
    )
    args = parser.parse_args(argv)
    default_value = ''  # pragma: no mutate
    if args.jira_uri and args.jira_uri.startswith('$'):  # pragma: no mutate
        args.jira_uri = environ.get(args.jira_uri[1:], default_value)
    if args.lenient and not (args.jira_uri and args.jira_uri.strip()):
        print('Lenient early exit, because no JIRA URI given')
        return 0

    if args.jira_pat and args.jira_pat.startswith('$'):  # pragma: no mutate
        args.jira_pat = environ.get(args.jira_pat[1:], default_value)
    if args.allowed_fix_version:
        resolved = []
        for e in args.allowed_fix_version:
            if e.startswith('$'):  # pragma: no mutate
                resolved.extend(environ.get(e[1:], default_value).split(','))
            else:
                resolved.extend(e.split(','))
        args.allowed_fix_version = filter(None, resolved)

    allowed = frozenset(args.allow_status_category or ())
    disallowed = frozenset(args.disallow_status_category or ('done',))
    version = frozenset(args.allowed_fix_version or ())

    ticket = get_ticket(args.commit_msg)
    if not ticket:
        print('Could not reify ticket from commit message')
        return 4
    print(f'Checking ticket "{ticket}"')

    if len(version) > 0:
        ticket_version = \
            get_ticket_version(ticket, args.jira_uri, args.jira_pat)
        if not ticket_version:
            print('Ticket has no fix version, but it is expected')
            print(
                '\t(allowed versions are:'
                f' {str(version).replace("frozenset","")})',
            )
            return 3
        if ticket_version not in version:
            print(f'Fix version of ticket ("{ticket_version}") is not allowed')
            print(
                '\t(allowed versions are:'
                f' {str(version).replace("frozenset","")})',
            )
            return 2
        print(f'Ticket fix version ("{ticket_version}") is allowed')
        print(
            '\t(allowed versions are:'
            f' {str(version).replace("frozenset","")})',
        )
    else:
        print('Ticket fix version not checked')

    category = get_ticket_status_category(
        ticket, args.jira_uri, args.jira_pat,
    )
    if check_ticket_status_category(category, allowed, disallowed):
        print('Ticket is OK according to COJIRA rules')
        return 0
    print(f'Ticket status category ("{category}") is not allowed')
    print(
        f'\t(allowed categories are: {str(allowed).replace("frozenset","")},',
    )
    print(
        '\t disallowed categories are:'
        f' {str(disallowed).replace("frozenset","")})',
    )
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
