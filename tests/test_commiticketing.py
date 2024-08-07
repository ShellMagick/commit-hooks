from __future__ import annotations

import random
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from typing_extensions import Buffer

from hooks import commiticketing


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


def test_no_branch(tmpdir):
    with tmpdir.as_cwd():
        assert commiticketing.get_active_branch_name() is None


test_set_1 = [
    'main',
    'non-main',
    'ABC-123',
    'ABC-123-abc',
    'non/main',
    'non/main-123',
    'non/ABC-123',
    'non/ABC-123-abc',
    'bak/u12/ABC-123',
    'bak/u12/ABC-123-abc',
]
test_set_2 = [
    'main',
    'non-main',
    'ABC-123',
    'ABC-123-abc',
    'non/main',
    'non/main-123',
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


def test_get_active_branch_name_during_rebase(tmpdir):
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        exec_cmd('git', 'checkout', '-b', 'base')
        exec_cmd('git', 'config', 'user.email', 'joe@banana.br')
        exec_cmd('git', 'config', 'user.name', 'Banana Joe')
        exec_cmd('git', 'commit', '--allow-empty', '-m', 'base commit')
        exec_cmd('git', 'checkout', '-b', 'to-rebase')
        f = tmpdir.join('conflicting.txt')
        f.write_text('Abracadabra', encoding='utf-8')
        exec_cmd('git', 'add', 'conflicting.txt')
        exec_cmd('git', 'commit', '-m', '1')
        exec_cmd('git', 'checkout', 'base')
        exec_cmd('git', 'checkout', '-b', 'rebase-onto')
        f = tmpdir.join('conflicting.txt')
        f.write_text('Bananas', encoding='utf-8')
        exec_cmd('git', 'add', 'conflicting.txt')
        exec_cmd('git', 'commit', '-m', '2')
        exec_cmd('git', 'checkout', 'to-rebase')
        exec_cmd('git', 'rebase', 'rebase-onto', return_code=1)
        assert commiticketing.get_active_branch_name() == 'to-rebase'


def test_get_active_branch_name_during_patch(tmpdir):
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        exec_cmd('git', 'config', 'user.email', 'joe@banana.br')
        exec_cmd('git', 'config', 'user.name', 'Banana Joe')
        exec_cmd('git', 'checkout', '-b', 'base')
        exec_cmd('git', 'commit', '--allow-empty', '-m', 'base commit')
        exec_cmd('git', 'checkout', '-b', 'to-rebase')
        f = tmpdir.join('conflicting.txt')
        f.write_text('Abra', encoding='utf-8')
        exec_cmd('git', 'add', 'conflicting.txt')
        exec_cmd('git', 'commit', '-m', '1')
        f.write_text('Abracadabra', encoding='utf-8')
        exec_cmd('git', 'add', 'conflicting.txt')
        exec_cmd('git', 'commit', '-m', '2')
        exec_cmd('git', 'checkout', 'base')
        exec_cmd('git', 'checkout', '-b', 'rebase-onto')
        f = tmpdir.join('conflicting.txt')
        f.write_text('Ba', encoding='utf-8')
        exec_cmd('git', 'add', 'conflicting.txt')
        exec_cmd('git', 'commit', '-m', '3')
        f.write_text('Bananas', encoding='utf-8')
        exec_cmd('git', 'add', 'conflicting.txt')
        exec_cmd('git', 'commit', '-m', '4')
        exec_cmd('git', 'checkout', 'to-rebase')
        p = Path(tmpdir.join('test.patch'))
        p.write_bytes(
            exec_cmd('git', 'format-patch', '-2', 'to-rebase', '--stdout'),
        )
        exec_cmd('git', 'am', p.as_posix(), return_code=128)
        assert commiticketing.get_active_branch_name() == 'to-rebase'


@pytest.mark.parametrize('branch_name', test_set_2)
def test_get_prefix_no_match(tmpdir, branch_name):
    assert commiticketing.get_prefix(branch_name, []) is None


@pytest.mark.parametrize(
    'params',
    [
        dict(branch='DEF-159-def', prefix=None, leveled=[]),
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
    ],
)
def test_get_prefix(tmpdir, params):
    assert commiticketing.get_prefix(params['branch'], params['leveled']) == \
           params['prefix']


def test_not_reified(tmpdir):
    with patch('builtins.print') as mocked_print:
        with tmpdir.as_cwd():
            f = tmpdir.join('pseudo_commit_msg.txt')
            f.write_text('Abracadabra', encoding='utf-8')
            assert commiticketing.main((str(f),)) == 3
        assert mocked_print.call_args_list[-1].args[0] \
            .endswith('Could not reify branch name.')


@pytest.mark.parametrize('branch_name', test_set_2)
def test_out_of_scope_branch_default(tmpdir, branch_name):
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        exec_cmd('git', 'checkout', '-b', branch_name)
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('Abracadabra', encoding='utf-8')
        assert commiticketing.main((str(f),)) == 1


@pytest.mark.parametrize(
    'params',
    [
        dict(branch='feature/XYZ-987', proc='feat', leveled='usr'),
        dict(branch='user/u123/NM-555', proc='feat', leveled='usr'),
    ],
)
def test_out_of_scope_branch_non_default(tmpdir, params):
    with patch('builtins.print') as mocked_print:
        with tmpdir.as_cwd():
            exec_cmd('git', 'init')
            exec_cmd('git', 'checkout', '-b', params['branch'])
            f = tmpdir.join('pseudo_commit_msg.txt')
            f.write_text('Abracadabra', encoding='utf-8')
            assert commiticketing.main(
                ('-b', params['proc'], '-t', params['leveled'], str(f)),
            ) == 1
        assert mocked_print.call_args_list[-1].args[0] \
            .endswith(
            f"You wanted to commit to a branch [{params['branch']}], "
            'which does not correspond to the commiticketing setup.',
            )


@pytest.mark.parametrize(
    'branch_name',
    (
            'feature/XYZ/987',
            'user/u123/NM/555',
    ),
)
def test_in_scope_mismatched_default(tmpdir, branch_name):
    with patch('builtins.print') as mocked_print:
        with tmpdir.as_cwd():
            exec_cmd('git', 'init')
            exec_cmd('git', 'checkout', '-b', branch_name)
            f = tmpdir.join('pseudo_commit_msg.txt')
            f.write_text('Abracadabra', encoding='utf-8')
            assert commiticketing.main((str(f),)) == 2
        assert mocked_print.call_args_list[-1].args[0] \
            .endswith(
                f'[{branch_name}] does not correspond to branch naming '
                'rules, consult guidelines.',
            )


@pytest.mark.parametrize(
    'params',
    [
        dict(branch='feat/XYZ/987', proc='feat', leveled='usr'),
        dict(branch='usr/u123/NM/555', proc='feat', leveled='usr'),
    ],
)
def test_in_scope_mismatched_non_default(tmpdir, params):
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        exec_cmd('git', 'checkout', '-b', params['branch'])
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('Abracadabra', encoding='utf-8')
        assert commiticketing.main(
            ('-b', params['proc'], '-t', params['leveled'], str(f)),
        ) == 2


@pytest.mark.parametrize(
    'branch_name',
    (
            'feature/XYZ-987',
            'bugfix/NM-555',
            'hotfix/ABC-123',
            'user/u123/QWE-456',
            'backup/b321/RTY-654',
            'feature/XYZ-987-abc',
            'bugfix/NM-555-abc',
            'hotfix/ABC-123-abc',
            'user/u123/QWE-456-abc',
            'backup/b321/RTY-654-abc',
    ),
)
def test_prefix_if_not_there(tmpdir, branch_name):
    prefix = commiticketing.get_prefix(branch_name, ['user', 'backup'])
    with (
        tmpdir.as_cwd(),
        patch('builtins.print') as mocked_print,
    ):
        exec_cmd('git', 'init')
        exec_cmd('git', 'checkout', '-b', branch_name)
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('abracadabra', encoding='utf-8')
        assert commiticketing.main((str(f),)) == 0
        assert not mocked_print.call_args_list[-1].args[0] \
            .endswith('Commiticketing did not change your subject line.')
        assert mocked_print.call_args_list[-1].args[0] \
            .endswith(
                'Commiticketing prefixed your subject line '
                f'with [{prefix}: ] and made it sentence case'
                ' after.',
            )
        with open(f) as msg:
            assert msg.readline() == f'{prefix}: Abracadabra'


@pytest.mark.parametrize(
    'params',
    [
        dict(branch='feature/XYZ-987', msg='abracadabra'),
        dict(branch='bugfix/NM-555', msg='abracadabra'),
        dict(branch='hotfix/ABC-123', msg='abracadabra'),
        dict(branch='user/u123/QWE-753', msg='abracadabra'),
        dict(branch='backup/bak/RTY-654', msg='abracadabra'),
        dict(branch='feature/XYZ-987', msg='Abracadabra'),
        dict(branch='bugfix/NM-555', msg='Abracadabra'),
        dict(branch='hotfix/ABC-123', msg='Abracadabra'),
        dict(branch='user/u123/QWE-753', msg='Abracadabra'),
        dict(branch='backup/bak/RTY-654', msg='Abracadabra'),
    ],
)
def test_prefix_not_doubling(tmpdir, params):
    prefix = commiticketing.get_prefix(params['branch'], ['user', 'backup'])
    with (
        tmpdir.as_cwd(),
        patch('builtins.print') as mocked_print,
    ):
        exec_cmd('git', 'init')
        exec_cmd('git', 'checkout', '-b', params['branch'])
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text(
            f"{prefix}: {params['msg']}",
            encoding='utf-8',
        )
        assert commiticketing.main((str(f),)) == 0
        with open(f) as msg:
            assert msg.readline() == f'{prefix}: Abracadabra'
    if params['msg'] == 'Abracadabra':
        assert mocked_print.call_args_list[-1].args[0] \
            .endswith('Commiticketing did not change your subject line.')
    elif params['msg'] == 'abracadabra':
        assert not mocked_print.call_args_list[-1].args[0] \
            .endswith('Commiticketing did not change your subject line.')


@pytest.mark.parametrize(
    'params',
    [
        dict(branch='feature/XYZ-987', infix=''),
        dict(branch='bugfix/NM-555', infix='(bugfix) '),
        dict(branch='hotfix/ABC-123', infix='(hotfix) '),
        dict(branch='user/u123/QWE-753', infix=''),
        dict(branch='backup/bak/RTY-654', infix=''),
        dict(branch='feature/XYZ-987', infix=''),
        dict(branch='bugfix/NM-555', infix='(bugfix) '),
        dict(branch='hotfix/ABC-123', infix='(hotfix) '),
        dict(branch='user/u123/QWE-753', infix=''),
        dict(branch='backup/bak/RTY-654', infix=''),
    ],
)
def test_prefix_long_default(tmpdir, params):
    prefix = commiticketing.get_prefix(params['branch'], ['user', 'backup'])
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        exec_cmd('git', 'checkout', '-b', params['branch'])
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text('Abracadabra', encoding='utf-8')
        assert commiticketing.main(('-l', str(f))) == 0
        with open(f) as msg:
            assert msg.readline() == f"{prefix}: {params['infix']}Abracadabra"


@pytest.mark.parametrize(
    'params',
    [
        dict(
            branch='feat/XYZ-987',
            infix='(feat) ', proc='feat', leveled='usr', long=True, exclude=[],
        ),
        dict(
            branch='usr/u123/NM-555',
            infix='(usr) ', proc='feat', leveled='usr', long=True, exclude=[],
        ),
    ],
)
def test_prefix_long_non_default(tmpdir, params):
    prefix = commiticketing.get_prefix(params['branch'], [params['leveled']])
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        exec_cmd('git', 'checkout', '-b', params['branch'])
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text(
            f"{prefix}: {params['infix']}Abracadabra",
            encoding='utf-8',
        )
        assert commiticketing.main(
            ('-b', params['proc'], '-t', params['leveled'], '-l', str(f)),
        ) == 0
        with open(f) as msg:
            assert msg.readline() == f"{prefix}: {params['infix']}Abracadabra"


@pytest.mark.parametrize(
    'params',
    [
        dict(
            branch='feat/XYZ-987',
            infix='(feat) ', proc='feat', leveled='usr', long=True,
            exclude='usr',
        ),
        dict(
            branch='usr/u123/NM-555',
            infix='', proc='feat', leveled='usr', long=True, exclude='usr',
        ),
    ],
)
def test_prefix_long_with_excluded(tmpdir, params):
    prefix = commiticketing.get_prefix(params['branch'], [params['leveled']])
    with tmpdir.as_cwd():
        exec_cmd('git', 'init')
        exec_cmd('git', 'checkout', '-b', params['branch'])
        f = tmpdir.join('pseudo_commit_msg.txt')
        f.write_text(
            f"{prefix}: {params['infix']}Abracadabra",
            encoding='utf-8',
        )
        assert \
            commiticketing.main(
                (
                    '-b', params['proc'], '-t', params['leveled'], '-l', '-e',
                    params['exclude'], str(f),
                ),
            ) == 0
        with open(f) as msg:
            assert msg.readline() == f"{prefix}: {params['infix']}Abracadabra"
