from __future__ import annotations

import unittest
from unittest.mock import call

import pytest

from hooks import lint_commit_message


def test_empty(tmpdir):
    with unittest.mock.patch('builtins.print') as mocked_print:
        f = tmpdir.join('empty.txt')
        f.write_text('', encoding='utf-8')
        assert lint_commit_message.main((str(f),)) == 10
        assert call('The commit message must not be empty.') \
               in mocked_print.mock_calls


def test_no_empty_line_after_subject(tmpdir):
    with unittest.mock.patch('builtins.print') as mocked_print:
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('Subject\nBody\nBody2', encoding='utf-8')
        assert lint_commit_message.main((str(f),)) == 1
        assert call(
            'The subject line and body must be separated by an empty '
            'line.',
        ) in mocked_print.mock_calls


def test_empty_line_after_subject(tmpdir):
    f = tmpdir.join('pseudo_commit_msg.txt')
    f.write_text('Subject\n\nBody\nBody2', encoding='utf-8')
    assert lint_commit_message.main((str(f),)) == 0


def test_subject_line_too_long(tmpdir):
    with unittest.mock.patch('builtins.print') as mocked_print:
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text(
            '12345678901234567890123456789012345678901234567890'
            '12345678901234567890123',
            encoding='utf-8',
        )
        assert lint_commit_message.main((str(f),)) == 2
        assert call(
            'The subject line must not be longer than 72, currently '
            'it is 73.',
        ) in mocked_print.mock_calls


def test_subject_line_relaxed_not_too_long(tmpdir):
    f = tmpdir.join('pseudo_commit_msg.txt')
    f.write_text(
        '12345678901234567890123456789012345678901234567890'
        '12345678901234567890123',
        encoding='utf-8',
    )
    assert lint_commit_message.main(('-sl', '73', str(f))) == 0


def test_subject_line_relaxed_too_long(tmpdir):
    f = tmpdir.join('pseudo_commit_msg.txt')
    f.write_text(
        '12345678901234567890123456789012345678901234567890'
        '123456789012345678901234',
        encoding='utf-8',
    )
    assert lint_commit_message.main(('-sl', '73', str(f))) == 2


@pytest.mark.parametrize(
    'commit_msg',
    ['Hello!', 'Bye?', 'Oy.', 'Some (thing)', 'Hey /ho/'],
)
def test_subject_line_ends_with_punctuation_and_regex(tmpdir, commit_msg):
    with unittest.mock.patch('builtins.print') as mocked_print:
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text(commit_msg, encoding='utf-8')
        assert lint_commit_message.main(('-e', '\\W', str(f))) == 4
        assert call('The subject line must not end with punctuation.') \
               in mocked_print.mock_calls


@pytest.mark.parametrize(
    'commit_msg',
    ['Hello!', 'Bye?', 'Oy.'],
)
def test_subject_line_ends_forbidden_default(tmpdir, commit_msg):
    with unittest.mock.patch('builtins.print') as mocked_print:
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text(commit_msg, encoding='utf-8')
        assert lint_commit_message.main((str(f),)) == 4
        assert call('The subject line must not end with punctuation.') \
               in mocked_print.mock_calls


@pytest.mark.parametrize(
    'commit_msg',
    ['Some (thing)', 'Hey /ho/'],
)
def test_subject_line_ends_enabled_default(tmpdir, commit_msg):
    f = tmpdir.join('pseudo_commit_msg.txt')
    f.write_text(commit_msg, encoding='utf-8')
    assert lint_commit_message.main((str(f),)) == 0


def test_body_line_too_long(tmpdir):
    with unittest.mock.patch('builtins.print') as mocked_print:
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text(
            'A\n\n'
            '12345678901234567890123456789012345678901234567890'
            '12345678901234567890123456789012345678901234567890'
            '123456789012345678901',
            encoding='utf-8',
        )
        assert lint_commit_message.main((str(f),)) == 6
        assert call(
            'Wrap lines of the message body after 120 characters, '
            'currently line 1 is 121 long. The line is: '
            '"12345678901234567890123456789012345678901234567890'
            '12345678901234567890123456789012345678901234567890'
            '123456789012345678901".',
        ) in mocked_print.mock_calls


def test_body_line_relaxed_not_too_long(tmpdir):
    f = tmpdir.join('pseudo_commit_msg.txt')
    f.write_text(
        'A\n\n'
        '12345678901234567890123456789012345678901234567890'
        '12345678901234567890123456789012345678901234567890'
        '123456789012345678901',
        encoding='utf-8',
    )
    assert lint_commit_message.main(('-bl', '121', str(f))) == 0


def test_body_line_relaxed_too_long(tmpdir):
    f = tmpdir.join('pseudo_commit_msg.txt')
    f.write_text(
        'A\n\n'
        '12345678901234567890123456789012345678901234567890'
        '12345678901234567890123456789012345678901234567890'
        '1234567890123456789012',
        encoding='utf-8',
    )
    assert lint_commit_message.main(('-bl', '121', str(f))) == 6
