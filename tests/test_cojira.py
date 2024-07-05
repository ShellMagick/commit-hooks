from __future__ import annotations

import json
import subprocess
import unittest
from os import environ
from typing import Any
from unittest.mock import call
from urllib import request
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import Request

import pytest
from typing_extensions import Buffer

from hooks import cojira


@pytest.fixture(autouse=True)
def restore_urlopen():
    # before
    original_urlopener = cojira.request.urlopen

    # test
    yield

    # after
    cojira.request.urlopen = original_urlopener
    assert cojira.request.urlopen == request.urlopen


class CalledProcessError(RuntimeError):
    pass


def exec_cmd(*cmd: str, return_code: int | None = 0, **kwargs: Any) \
        -> str | Buffer:
    kwargs.setdefault('stdout', subprocess.PIPE)
    kwargs.setdefault('stderr', subprocess.PIPE)
    proc = subprocess.Popen(cmd, **kwargs)
    stdout, stderr = proc.communicate()
    if return_code is not None and proc.returncode != return_code:
        raise CalledProcessError(
            cmd,
            return_code,
            proc.returncode,
            stdout,
            stderr,
        )
    return stdout


@pytest.mark.parametrize(
    'params',
    [
        dict(commit_msg='banana', ticket=None),
        dict(commit_msg='batman', ticket=None),
        dict(commit_msg='XYZ-987', ticket=None),
        dict(commit_msg='XYZ-987: Banana', ticket='XYZ-987'),
    ],
)
def test_get_ticket_commit(tmpdir, params):
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text(params['commit_msg'], encoding='utf-8')
        assert \
            cojira.get_ticket('pseudo_commit_msg.txt') == params['ticket']


class MockedInfo:
    def __init__(self, charset):
        self.charset = charset

    def get_param(self, param_name):
        return self.charset if 'charset' == param_name else None


class MockedResponse:
    def __init__(self, payload, charset=None):
        if type(payload) is bytes:
            self.payload = payload
        else:
            self.payload = payload.encode('utf-8')
        self._info = MockedInfo(charset)

    def read(self):
        return self.payload

    def info(self):
        return self._info


def unauthorized(_):
    raise HTTPError(
        code=401, url='http://dummy', msg='test HTTP 401', hdrs=[],
        fp=None,
    )


@pytest.mark.parametrize(
    'params', [
        dict(
            mocked_response=lambda _:
            MockedResponse('{"j":"son"}'),
            expected=None,
        ),
        dict(
            mocked_response=lambda _:
            MockedResponse('{"fields": { "fixVersions": [] }}'),
            expected=None,
        ),
        dict(
            mocked_response=lambda _:
            MockedResponse('{"fields": { "fixVersions": [1] }}'),
            expected=None,
        ),
        dict(
            mocked_response=lambda _:
            MockedResponse('{"fields": { "fixVersions": [1, 2] }}'),
            expected=None,
        ),
        dict(
            mocked_response=lambda _:
            MockedResponse('{"fields": { "fixVersions": [{"notName": "notVersion"}] }}'),  # noqa: E501
            expected=None,
        ),
        dict(
            mocked_response=lambda _:
            MockedResponse('{"fields": { "fixVersions": [{"name": "version"}] }}'),  # noqa: E501
            expected='version',
        ),
    ],
)
def test_get_ticket_version(params):
    cojira.request.urlopen = params['mocked_response']
    if params['expected']:
        assert \
            cojira.get_ticket_version('na', 'http://bana', 'bu') == \
            params['expected']
    else:
        assert \
            cojira.get_ticket_version('na', 'http://bana', 'bu') is \
            params['expected']


@pytest.mark.parametrize(
    'params', [
        dict(
            mocked_response=None, ticket=None, uri=None, pat=None,
            expected=ValueError,
        ),
        dict(
            mocked_response=None, ticket=None, uri='', pat=None,
            expected=ValueError,
        ),
        dict(
            mocked_response=None, ticket=None, uri='non-uri', pat=None,
            expected=ValueError,
        ),
        dict(
            mocked_response=unauthorized, ticket=None, uri='http://uri',
            pat=None, expected=HTTPError,
        ),
        dict(
            mocked_response=lambda _: MockedResponse('{"j":"son"}'),
            ticket=None, uri='http://uri',
            pat=None,
            expected=json.loads('{"j":"son"}'),
        ),
    ],
)
def test_jira_pat_exceptions(params):
    if params['mocked_response']:
        cojira.request.urlopen = params['mocked_response']
    try:
        result = cojira.fetch_jira(
            params['ticket'], params['uri'], params['pat'],
        )
        if params['expected'] is not Exception:
            assert result == params['expected']
    except Exception as e:
        assert type(e) is params['expected']


def check_auth_header(request: Request):
    if request.type != 'http' and request.type != 'https':
        raise URLError('banana')

    if not request.has_header('Authorization'):
        raise HTTPError(
            code=401, url='http://dummy', msg='test HTTP 401',
            hdrs=[], fp=None,
        )
    auth_header = request.get_header('Authorization')
    if not auth_header.strip() == 'Bearer pat_on_the_back':
        raise HTTPError(
            code=401, url='http://dummy', msg='test HTTP 401',
            hdrs=[], fp=None,
        )
    return MockedResponse('{"fields": { "status": {"statusCategory": {"key": "done"}} }}')  # noqa: E501


@pytest.mark.parametrize(
    'params', [
        dict(token=None, expected=HTTPError),
        dict(token='', expected=HTTPError),
        dict(
            token='pat_on_the_back',
            expected=json.loads('{"fields": { "status": {"statusCategory": {"key": "done"}} }}'),  # noqa: E501
        ),
    ],
)
def test_jira_auth(params):
    cojira.request.urlopen = check_auth_header
    try:
        if type(params['expected']) is not HTTPError:
            assert cojira.fetch_jira('tick', 'http://et', params['token']) == \
                params['expected']
    except Exception as e:
        assert type(e) is params['expected']


@pytest.mark.parametrize(
    'params', [
        dict(
            mocked_response=lambda _: MockedResponse('{"j":"son"}'),
            expected=None,
        ),
        dict(
            mocked_response=lambda _: MockedResponse('{"fields": { "status": {} }}'),  # noqa: E501
            expected=None,
        ),
        dict(
            mocked_response=lambda _: MockedResponse('{"fields": { "status": {"notStatusCategory": {}} }}'),  # noqa: E501
            expected=None,
        ),
        dict(
            mocked_response=lambda _: MockedResponse('{"fields": { "status": {"statusCategory": {}} }}'),  # noqa: E501
            expected=None,
        ),
        dict(
            mocked_response=lambda _: MockedResponse('{"fields": { "status": {"statusCategory": {"notKey": ""}} }}'),  # noqa: E501
            expected=None,
        ),
        dict(
            mocked_response=lambda _: MockedResponse('{"fields": { "status": {"statusCategory": {"key": ""}} }}'),  # noqa: E501
            expected='',
        ),
        dict(
            mocked_response=lambda _: MockedResponse('{"fields": { "status": {"statusCategory": {"key": "done"}} }}'),  # noqa: E501
            expected='done',
        ),
    ],
)
def test_get_ticket_status_category(params):
    cojira.request.urlopen = params['mocked_response']
    if params['expected']:
        assert \
            cojira.get_ticket_status_category('na', 'http://bana', 'bu') == \
            params['expected']
    else:
        assert \
            cojira.get_ticket_status_category('na', 'http://bana', 'bu') is \
            params['expected']


def mocked_response(_):
    return MockedResponse('{"fields": { "fixVersions": [{"name": "version"}], "status": {"statusCategory": {"key": "indeterminate"}} }}')  # noqa: E501


def test_cojira_non_json_response(tmpdir):
    cojira.request.urlopen = lambda _: MockedResponse('<this><is not="a"/><json/></this>')  # noqa: E501
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('ABC-123: Banana', encoding='utf-8')
        assert cojira.main(('pseudo_commit_msg.txt', '-u=http://banana')) == 1


def test_cojira_ticket_is_done(tmpdir):
    cojira.request.urlopen = lambda _: MockedResponse('{"fields": { "status": {"statusCategory": {"key": "done"}} }}')  # noqa: E501
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('ABC-123: Banana', encoding='utf-8')
        assert cojira.main(('pseudo_commit_msg.txt', '-u=http://banana')) == 1


def test_cojira_ticket_without_version(tmpdir):
    cojira.request.urlopen = lambda _: MockedResponse('')
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('ABC-123: Banana', encoding='utf-8')
        assert cojira.main(
            (
                'pseudo_commit_msg.txt',
                '-v=not-this-version',
                '-u=http://banana',
            ),
        ) == 3


def test_cojira_without_uri(tmpdir):
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('ABC-123: Banana', encoding='utf-8')
        assert cojira.main(('pseudo_commit_msg.txt', '-l')) == 0
        try:
            cojira.main(('pseudo_commit_msg.txt',))
            assert False
        except ValueError as e:
            assert 'unknown url type' in str(e)


def test_cojira_with_non_utf8():
    cojira.request.urlopen = lambda _: MockedResponse(b'\xff\xfe{\x00"\x00j\x00"\x00:\x00"\x00s\x00\xf8\x00n\x00"\x00}\x00', 'utf_16')  # noqa: E501
    assert cojira.fetch_jira('tick', 'http://et', '') == \
        json.loads(b'\xff\xfe{\x00"\x00j\x00"\x00:\x00"\x00s\x00\xf8\x00n\x00"\x00}\x00'.decode('utf_16'))  # noqa: E501


@pytest.mark.parametrize(
    'params', [
        dict(v1='version', v2='version2', expected=0),
        dict(v1='version3', v2='version', expected=0),
        dict(v1='version2', v2='version3', expected=2),
        dict(v1='version,version2', v2='', expected=0),
        dict(v1='version3,version', v2='', expected=0),
        dict(v1='version2,version3', v2='', expected=2),
    ],
)
def test_multiple_allowed_fix_versions(tmpdir, params):
    cojira.request.urlopen = mocked_response
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('ABC-123: Banana', encoding='utf-8')
        assert cojira.main(
            (
                'pseudo_commit_msg.txt',
                f'-v={params["v1"]}', f'-v={params["v2"]}',
                '-u=http://banana',
            ),
        ) == params['expected']


@pytest.mark.parametrize(
    'params', [
        dict(
            v1='$VERSION', v2='version2',
            u='$YYYJIRA_URI', p='$YYYJIRA_PAT',
            expected=0,
        ),
        dict(
            v1='$VERSION', v2='$VERSION2',
            u='$YYYJIRA_URI', p='$YYYJIRA_PAT',
            expected=0,
        ),
        dict(
            v1='version3', v2='$VERSION',
            u='$YYYJIRA_URI', p='$YYYJIRA_PAT',
            expected=0,
        ),
        dict(
            v1='$VERSION2', v2='version3',
            u='$YYYJIRA_URI', p='$YYYJIRA_PAT',
            expected=2,
        ),
        dict(
            v1='$VERSION', v2='version2',
            u='http://banana', p='$YYYJIRA_PAT',
            expected=0,
        ),
        dict(
            v1='$VERSION', v2='$VERSION2',
            u='http://banana', p='$YYYJIRA_PAT',
            expected=0,
        ),
        dict(
            v1='version3', v2='$VERSION',
            u='http://banana', p='$YYYJIRA_PAT',
            expected=0,
        ),
        dict(
            v1='$VERSION2', v2='version3',
            u='http://banana', p='$YYYJIRA_PAT',
            expected=2,
        ),
        dict(
            v1='$VERSION', v2='version2',
            u='$YYYJIRA_URI', p='pat_on_the_back',
            expected=0,
        ),
        dict(
            v1='$VERSION', v2='$VERSION2',
            u='$YYYJIRA_URI', p='pat_on_the_back',
            expected=0,
        ),
        dict(
            v1='version3', v2='$VERSION',
            u='$YYYJIRA_URI', p='pat_on_the_back',
            expected=0,
        ),
        dict(
            v1='$VERSION2', v2='version3',
            u='$YYYJIRA_URI', p='pat_on_the_back',
            expected=2,
        ),
        dict(
            v1='$VERSION', v2='version2',
            u='http://banana', p='pat_on_the_back',
            expected=0,
        ),
        dict(
            v1='$VERSION', v2='$VERSION2',
            u='http://banana', p='pat_on_the_back',
            expected=0,
        ),
        dict(
            v1='version3', v2='$VERSION',
            u='http://banana', p='pat_on_the_back',
            expected=0,
        ),
        dict(
            v1='$VERSION2', v2='version3',
            u='http://banana', p='pat_on_the_back',
            expected=2,
        ),
    ],
)
def test_env_var_resolution(tmpdir, params):
    cojira.request.urlopen = mocked_response
    environ['YYYJIRA_URI'] = 'http://banana'
    environ['YYYJIRA_PAT'] = 'pat_on_the_back'
    environ['VERSION'] = 'version'
    environ['VERSION2'] = 'version2'
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('ABC-123: Banana', encoding='utf-8')
        assert cojira.main(
            (
                'pseudo_commit_msg.txt',
                f'-v={params["v1"]}', f'-v={params["v2"]}',
                f'-u={params["u"]}', f'-p={params["p"]}',
            ),
        ) == params['expected']


def test_jira_pat_as_env_var(tmpdir):
    cojira.request.urlopen = check_auth_header
    environ['YYYJIRA_PAT'] = 'pat_on_the_back'
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('ABC-123: Banana', encoding='utf-8')
        assert cojira.main(
            (
                'pseudo_commit_msg.txt', '-e=none',
                '-u=http://banana', '-p=$YYYJIRA_PAT',
            )
        ) == 0


def test_version_empty_via_env_var(tmpdir):
    cojira.request.urlopen = mocked_response
    environ['EMPTY_VERSION'] = ''
    with (
        tmpdir.as_cwd(),
        unittest.mock.patch('builtins.print') as mocked_print,
    ):
        exec_cmd('git', 'init')
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('ABC-123: Banana', encoding='utf-8')
        assert cojira.main(
            (
                'pseudo_commit_msg.txt',
                f'-v=$EMPTY_VERSION',
                '-u=http://banana', '-p=pat_on_the_back',
            ),
        ) == 0
        assert call('Ticket fix version not checked') \
            in mocked_print.mock_calls


def test_version_multiple_via_env_var(tmpdir):
    cojira.request.urlopen = mocked_response
    environ['EMPTY_VERSION'] = 'a,b,version'
    with (
        tmpdir.as_cwd(),
        unittest.mock.patch('builtins.print') as mocked_print,
    ):
        exec_cmd('git', 'init')
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('ABC-123: Banana', encoding='utf-8')
        assert cojira.main(
            (
                'pseudo_commit_msg.txt',
                f'-v=$EMPTY_VERSION',
                '-u=http://banana', '-p=pat_on_the_back',
            ),
        ) == 0
        assert call('Ticket fix version ("version") is allowed') \
            in mocked_print.mock_calls
        assert (
            call('\t(allowed versions are: ({\'a\', \'b\', \'version\'}))') \
                in mocked_print.mock_calls or
            call('\t(allowed versions are: ({\'a\', \'version\', \'b\'}))') \
                in mocked_print.mock_calls or
            call('\t(allowed versions are: ({\'version\', \'a\', \'b\'}))') \
                in mocked_print.mock_calls or
            call('\t(allowed versions are: ({\'b\', \'a\', \'version\'}))') \
                in mocked_print.mock_calls or
            call('\t(allowed versions are: ({\'b\', \'version\', \'a\'}))') \
                in mocked_print.mock_calls or
            call('\t(allowed versions are: ({\'version\', \'b\', \'a\'}))') \
                in mocked_print.mock_calls
        )


@pytest.mark.parametrize(
    'params', [
        dict(
            e=0,
            msg='ABC-123: Banana',
            u=None,
            args=('pseudo_commit_msg.txt', '-l'),
            texts=[
                'Lenient early exit, because no JIRA URI given',
            ],
            alts=[],
        ),
        dict(
            e=4,
            msg='Banana',
            u=None,
            args=('pseudo_commit_msg.txt', '-u=http://banana'),
            texts=[
                'Could not reify ticket from commit message',
            ],
            alts=[],
        ),
        dict(
            e=3,
            msg='ABC-123: Banana',
            u=lambda _: MockedResponse(''),
            args=(
                'pseudo_commit_msg.txt', '-v=not-this-version',
                '-u=http://banana',
            ),
            texts=[
                'Ticket has no fix version, but it is expected',
                '\t(allowed versions are: ({\'not-this-version\'}))',
            ],
            alts=[],
        ),
        dict(
            e=1,
            msg='ABC-123: Banana',
            u=lambda _: MockedResponse('<this><is not="a"/><json/></this>'),
            args=('pseudo_commit_msg.txt', '-u=http://banana'),
            texts=[
                'Ticket fix version not checked',
                'Ticket status category ("None") is not allowed',
                '\t(allowed categories are: (),',
                '\t disallowed categories are: ({\'done\'}))',
            ],
            alts=[],
        ),
        dict(
            e=2,
            msg='ABC-123: Banana',
            u=mocked_response,
            args=(
                'pseudo_commit_msg.txt', '-v=version2', '-v=version3',
                '-u=http://banana',
            ),
            texts=[
                'Fix version of ticket ("version") is not allowed',
            ],
            alts=[
                [
                    '\t(allowed versions are: ({\'version2\', \'version3\'}))',
                    '\t(allowed versions are: ({\'version3\', \'version2\'}))',
                ],
            ],
        ),
        dict(
            e=0,
            msg='ABC-123: Banana',
            u=mocked_response,
            args=(
                'pseudo_commit_msg.txt', '-v=version', '-v=version2',
                '-u=http://banana',
            ),
            texts=[
                'Checking ticket "ABC-123"',
                'Ticket fix version ("version") is allowed',
                'Ticket is OK according to COJIRA rules',
            ],
            alts=[
                [
                    '\t(allowed versions are: ({\'version2\', \'version\'}))',
                    '\t(allowed versions are: ({\'version\', \'version2\'}))',
                ],
            ],
        ),
    ],
)
def test_cojira_outputs(tmpdir, params):
    with (
        tmpdir.as_cwd(),
        unittest.mock.patch('builtins.print') as mocked_print,
    ):
        if params['u'] is not None:
            cojira.request.urlopen = params['u']
        exec_cmd('git', 'init')
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text(params['msg'], encoding='utf-8')
        assert cojira.main(params['args']) == params['e']
        for t in params['texts']:
            assert call(t) in mocked_print.mock_calls
        for p in params['alts']:
            assert (
                call(p[0]) in mocked_print.mock_calls or
                call(p[1]) in mocked_print.mock_calls
            )
