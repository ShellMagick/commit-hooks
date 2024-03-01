from __future__ import annotations

import pytest

from hooks import lint_commit_message


def test_empty(tmpdir):
    f = tmpdir.join('empty.txt')
    f.write_text('', encoding='utf-8')
    assert lint_commit_message.main((str(f),)) == 10


def test_no_empty_line_after_subject(tmpdir):
    f = tmpdir.join('pseudo_commit_msg.txt')
    f.write_text('Subject\nBody\nBody2', encoding='utf-8')
    assert lint_commit_message.main((str(f),)) == 1


def test_empty_line_after_subject(tmpdir):
    f = tmpdir.join('pseudo_commit_msg.txt')
    f.write_text('Subject\n\nBody\nBody2', encoding='utf-8')
    assert lint_commit_message.main((str(f),)) == 0


def test_subject_line_too_long(tmpdir):
    f = tmpdir.join('pseudo_commit_msg.txt')
    f.write_text(
        '12345678901234567890123456789012345678901234567890'
        '12345678901234567890123',
        encoding='utf-8',
    )
    assert lint_commit_message.main((str(f),)) == 2


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


@pytest.mark.parametrize('commit_msg', ['Hello!', 'Bye?', '!Ay¡'])
def test_subject_line_ends_with_punctuation(tmpdir, commit_msg):
    f = tmpdir.join('pseudo_commit_msg.txt')
    f.write_text(commit_msg, encoding='utf-8')
    assert lint_commit_message.main((str(f),)) == 4


def test_body_line_too_long(tmpdir):
    f = tmpdir.join('pseudo_commit_msg.txt')
    f.write_text(
        'A\n\n'
        '12345678901234567890123456789012345678901234567890'
        '12345678901234567890123456789012345678901234567890'
        '123456789012345678901',
        encoding='utf-8',
    )
    assert lint_commit_message.main((str(f),)) == 6


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
