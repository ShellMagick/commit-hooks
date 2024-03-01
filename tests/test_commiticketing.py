from __future__ import annotations

import random
import subprocess
import unittest
from typing import Any
from unittest.mock import patch, call

import pytest

from hooks import commiticketing


class CalledProcessError(RuntimeError):
    pass


def exec_cmd(*cmd: str, retcode: int | None = 0, **kwargs: Any) -> str:
    kwargs.setdefault('stdout', subprocess.PIPE)
    kwargs.setdefault('stderr', subprocess.PIPE)
    proc = subprocess.Popen(cmd, **kwargs)
    stdout, stderr = proc.communicate()
    if retcode is not None and proc.returncode != retcode:
        raise CalledProcessError(cmd, retcode, proc.returncode, stdout, stderr)
    return stdout


def test_no_branch(tmpdir):
    with tmpdir.as_cwd():
        assert commiticketing.get_active_branch_name() is None


test_set_1 = ['main',
              'nonmain',
              'ABC-123',
              'ABC-123-abc',
              'non/main',
              'non/main-123',
              'non/ABC-123',
              'non/ABC-123-abc',
              'bak/u12/ABC-123',
              'bak/u12/ABC-123-abc'
              ]
test_set_2 = ['main',
              'nonmain',
              'ABC-123',
              'ABC-123-abc',
              'non/main',
              'non/main-123'
              ]


@pytest.mark.parametrize('branch_name', test_set_1)
def test_get_active_branch_name_simple(tmpdir, branch_name):
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        exec_cmd('git', 'checkout', '-b', branch_name)
        assert commiticketing.get_active_branch_name() == branch_name


@pytest.mark.parametrize('branch_name', test_set_1)
def test_get_active_branch_name_switcheroo(tmpdir, branch_name):
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        exec_cmd('git', 'checkout', '-b', branch_name)
        assert commiticketing.get_active_branch_name() == branch_name
        pseudo = branch_name + '-' + str(random.randint(0, 100))
        exec_cmd('git', 'checkout', '-b', pseudo)
        assert commiticketing.get_active_branch_name() == pseudo
        exec_cmd('git', 'checkout', '-b', branch_name)
        assert commiticketing.get_active_branch_name() == branch_name


@pytest.mark.parametrize('branch_name', test_set_2)
def test_get_prefix_no_match(tmpdir, branch_name):
    assert commiticketing.get_prefix(branch_name, []) is None


@pytest.mark.parametrize('params',
                         [dict(branch='DEF-159-def', prefix=None, leveled=[]),
                          dict(branch='non/ABC-123-abc', prefix='ABC-123', leveled=[]),
                          dict(branch='feature/XYZ-987', prefix='XYZ-987', leveled=[]),
                          dict(branch='feature/XYZ-987', prefix='XYZ-987', leveled=['bak']),
                          dict(branch='bugfix/XYZ-987', prefix='XYZ-987', leveled=[]),
                          dict(branch='bugfix/XYZ-987', prefix='XYZ-987', leveled=['bak']),
                          dict(branch='hotfix/XYZ-987', prefix='XYZ-987', leveled=[]),
                          dict(branch='hotfix/XYZ-987', prefix='XYZ-987', leveled=['bak']),
                          dict(branch='bak/u123/NM-555', prefix=None, leveled=[]),
                          dict(branch='bak/u123/NM-555', prefix='NM-555', leveled=['bak']),
                          dict(branch='bak/u123/NM-555-abc', prefix='NM-555', leveled=['bak']),
                          dict(branch='bak/u123/really/NM-555', prefix=None, leveled=['bak']),
                          ]
                         )
def test_get_prefix(tmpdir, params):
    assert commiticketing.get_prefix(params['branch'], params['leveled']) == params['prefix']


def test_not_reified(tmpdir):
    with tmpdir.as_cwd():
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('Abracadabra', encoding='utf-8')
        assert commiticketing.main((str(f),)) == 3


@pytest.mark.parametrize('branch_name', test_set_2)
def test_out_of_scope_branch_default(tmpdir, branch_name):
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        exec_cmd('git', 'checkout', '-b', branch_name)
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('Abracadabra', encoding='utf-8')
        assert commiticketing.main((str(f),)) == 1


@pytest.mark.parametrize('params',
                         [dict(branch='feature/XYZ-987', proc='feat', leveled='usr'),
                          dict(branch='user/u123/NM-555', proc='feat', leveled='usr'),
                          ]
                         )
def test_out_of_scope_branch_non_default(tmpdir, params):
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        exec_cmd('git', 'checkout', '-b', params['branch'])
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('Abracadabra', encoding='utf-8')
        assert commiticketing.main(('-b', params['proc'], '-t', params['leveled'], str(f),)) == 1


@pytest.mark.parametrize('branch_name',
                         ('feature/XYZ/987',
                          'user/u123/NM/555',
                          )
                         )
def test_in_scope_mismatched_default(tmpdir, branch_name):
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        exec_cmd('git', 'checkout', '-b', branch_name)
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('Abracadabra', encoding='utf-8')
        assert commiticketing.main((str(f),)) == 2


@pytest.mark.parametrize('params',
                         [dict(branch='feat/XYZ/987', proc='feat', leveled='usr'),
                          dict(branch='usr/u123/NM/555', proc='feat', leveled='usr'),
                          ]
                         )
def test_in_scope_mismatched_non_default(tmpdir, params):
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        exec_cmd('git', 'checkout', '-b', params['branch'])
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('Abracadabra', encoding='utf-8')
        assert commiticketing.main(('-b', params['proc'], '-t', params['leveled'], str(f),)) == 2


@pytest.mark.parametrize('branch_name',
                         ('feature/XYZ-987',
                          'bugfix/NM-555',
                          'hotfix/ABC-123',
                          'user/u123/QWE-456',
                          'backup/b321/RTY-654',
                          'feature/XYZ-987-abc',
                          'bugfix/NM-555-abc',
                          'hotfix/ABC-123-abc',
                          'user/u123/QWE-456-abc',
                          'backup/b321/RTY-654-abc'
                          )
                         )
def test_prefix_if_not_there(tmpdir, branch_name):
    with tmpdir.as_cwd():
        with unittest.mock.patch('builtins.print') as mocked_print:
            exec_cmd('git', 'init')
            exec_cmd('git', 'checkout', '-b', branch_name)
            f = tmpdir.join('pseudo_commit_msg.txt')
            f.write_text('abracadabra', encoding='utf-8')
            assert commiticketing.main((str(f),)) == 0
            assert call('Commiticketing did not change your subject line') not in mocked_print.mock_calls
            with open(f, 'r') as msg:
                assert msg.readline() == f"{commiticketing.get_prefix(branch_name, ['user', 'backup'])}: Abracadabra"


@pytest.mark.parametrize('params',
                         [dict(branch='feature/XYZ-987', msg='abracadabra'),
                          dict(branch='bugfix/NM-555', msg='abracadabra'),
                          dict(branch='hotfix/ABC-123', msg='abracadabra'),
                          dict(branch='user/u123/QWE-753', msg='abracadabra'),
                          dict(branch='backup/bak/RTY-654', msg='abracadabra'),
                          dict(branch='feature/XYZ-987', msg='Abracadabra'),
                          dict(branch='bugfix/NM-555', msg='Abracadabra'),
                          dict(branch='hotfix/ABC-123', msg='Abracadabra'),
                          dict(branch='user/u123/QWE-753', msg='Abracadabra'),
                          dict(branch='backup/bak/RTY-654', msg='Abracadabra'),
                          ])
def test_prefix_not_doubling(tmpdir, params):
    with tmpdir.as_cwd():
        with unittest.mock.patch('builtins.print') as mocked_print:
            exec_cmd('git', 'init')
            exec_cmd('git', 'checkout', '-b', params['branch'])
            f = tmpdir.join('pseudo_commit_msg.txt')
            f.write_text(f"{commiticketing.get_prefix(params['branch'], ['user', 'backup'])}: {params['msg']}",
                         encoding='utf-8')
            assert commiticketing.main((str(f),)) == 0
            with open(f, 'r') as msg:
                assert msg.readline() == (f"{commiticketing.get_prefix(params['branch'], ['user', 'backup'])}: "
                                          f"Abracadabra")
                if params['msg'] == "Abracadabra":
                    assert call('Commiticketing did not change your subject line') in mocked_print.mock_calls
                elif params['msg'] == "abracadabra":
                    assert call('Commiticketing did not change your subject line') not in mocked_print.mock_calls


@pytest.mark.parametrize('params',
                         [dict(branch='feature/XYZ-987', infix=''),
                          dict(branch='bugfix/NM-555', infix='(bugfix) '),
                          dict(branch='hotfix/ABC-123', infix='(hotfix) '),
                          dict(branch='user/u123/QWE-753', infix=''),
                          dict(branch='backup/bak/RTY-654', infix=''),
                          dict(branch='feature/XYZ-987', infix=''),
                          dict(branch='bugfix/NM-555', infix='(bugfix) '),
                          dict(branch='hotfix/ABC-123', infix='(hotfix) '),
                          dict(branch='user/u123/QWE-753', infix=''),
                          dict(branch='backup/bak/RTY-654', infix=''),
                          ]
                         )
def test_prefix_long_default(tmpdir, params):
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        exec_cmd('git', 'checkout', '-b', params['branch'])
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('Abracadabra', encoding='utf-8')
        assert commiticketing.main(('-l', str(f))) == 0
        with open(f, 'r') as msg:
            assert msg.readline() == \
                   f"{commiticketing.get_prefix(params['branch'], ['user', 'backup'])}: {params['infix']}Abracadabra"


@pytest.mark.parametrize('params',
                         [dict(branch='feat/XYZ-987',
                               infix='(feat) ', proc='feat', leveled='usr', long=True, exclude=[]),
                          dict(branch='usr/u123/NM-555',
                               infix='(usr) ', proc='feat', leveled='usr', long=True, exclude=[]),
                          ]
                         )
def test_prefix_long_non_default(tmpdir, params):
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        exec_cmd('git', 'checkout', '-b', params['branch'])
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text(
            f"{commiticketing.get_prefix(params['branch'], [params['leveled']])}: {params['infix']}Abracadabra",
            encoding='utf-8')
        assert commiticketing.main(('-b', params['proc'], '-t', params['leveled'], '-l', str(f))) == 0
        with open(f, 'r') as msg:
            assert msg.readline() == \
                   f"{commiticketing.get_prefix(params['branch'], [params['leveled']])}: {params['infix']}Abracadabra"


@pytest.mark.parametrize('params',
                         [dict(branch='feat/XYZ-987',
                               infix='(feat) ', proc='feat', leveled='usr', long=True, exclude='usr'),
                          dict(branch='usr/u123/NM-555',
                               infix='', proc='feat', leveled='usr', long=True, exclude='usr'),
                          ]
                         )
def test_prefix_long_with_excluded(tmpdir, params):
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        exec_cmd('git', 'checkout', '-b', params['branch'])
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text(
            f"{commiticketing.get_prefix(params['branch'], [params['leveled']])}: {params['infix']}Abracadabra",
            encoding='utf-8')
        assert \
            commiticketing.main(
                ('-b', params['proc'], '-t', params['leveled'], '-l', '-e', params['exclude'], str(f))
            ) == 0
        with open(f, 'r') as msg:
            assert msg.readline() == \
                   f"{commiticketing.get_prefix(params['branch'], [params['leveled']])}: {params['infix']}Abracadabra"
