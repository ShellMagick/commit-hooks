from __future__ import annotations

from unittest.mock import patch

from hooks import no_todos


def test_no_todos(tmpdir):
    f = tmpdir.join('todo.txt')
    # noinspection SpellCheckingInspection
    f.write_text('ño wäy Jőßé!', encoding='utf-8')
    assert no_todos.main((str(f),)) == 0


def test_has_todo(tmpdir):
    with patch('builtins.print') as mocked_print:
        f = tmpdir.join('todo.txt')
        # noinspection SpellCheckingInspection
        f.write_text('TODO: ¥eßűs, ∂éñ∂ þħïs!', encoding='utf-8')
        assert no_todos.main((str(f),)) == 1
        assert mocked_print.call_args_list[-1].args[0] \
            .endswith('todo.txt: contains TODO')


def test_has_fixme(tmpdir):
    f = tmpdir.join('todo.txt')
    # noinspection SpellCheckingInspection
    f.write_text('FIXME: ¥eßűs, ∂éñ∂ þħïs!', encoding='utf-8')
    assert no_todos.main((str(f),)) == 1


def test_has_xxx(tmpdir):
    f = tmpdir.join('todo.txt')
    # noinspection SpellCheckingInspection
    f.write_text('XXX: ¥eßűs, ∂éñ∂ þħïs!', encoding='utf-8')
    assert no_todos.main((str(f),)) == 1


def test_has_todo_but_excepted(tmpdir):
    with patch('builtins.print') as mocked_print:
        f = tmpdir.join('todo.txt')
        # noinspection SpellCheckingInspection
        f.write_text('TODO: ฿űþ ñ∅™ þħïs!', encoding='utf-8')
        assert no_todos.main(('-e', 'todo.txt', str(f))) == 0
        assert mocked_print.call_args_list[-1].args[0] \
            .endswith('todo.txt: contains TODO, but is on the exception list')


def test_has_machs(tmpdir):
    f = tmpdir.join('todo.txt')
    # noinspection SpellCheckingInspection
    f.write_text('MACHS: ¥eßűs, ∂éñ∂ þħïs!', encoding='utf-8')
    assert no_todos.main(('-t', 'MACHS', str(f))) == 1


def test_complex_case(tmpdir):
    f1 = tmpdir.join('todo_1.txt')
    # noinspection SpellCheckingInspection
    f1.write_text('TODO: ¥eßűs, ∂éñ∂ þħïs!-1', encoding='utf-8')
    f2 = tmpdir.join('todo_2.txt')
    # noinspection SpellCheckingInspection
    f2.write_text('TODO: ¥eßűs, ∂éñ∂ þħïs!-2', encoding='utf-8')
    f3 = tmpdir.join('todo_3.txt')
    # noinspection SpellCheckingInspection
    f3.write_text('TODO: ¥eßűs, ∂éñ∂ þħïs!-3', encoding='utf-8')
    assert no_todos.main(('-e', 'todo_2.txt', str(f1), str(f2), str(f3))) == 2


def test_non_utf_8(tmpdir):
    with patch('builtins.print') as mocked_print:
        f1 = tmpdir.join('todo_utf8_bom.txt')
        # noinspection SpellCheckingInspection
        f1.write_text('TODO: ¥eßűs, ∂éñ∂ þħïs!-1', encoding='utf-8-sig')
        assert no_todos.main((str(f1),)) == 1
        for a in mocked_print.call_args_list:
            assert not a.args[0].endswith(
                'todo_utf8_bom.txt: cannot be read as UTF-8, trying UTF-16',
            )
        f2 = tmpdir.join('todo_utf16.txt')
        # noinspection SpellCheckingInspection
        f2.write_text('TODO: ¥eßűs, ∂éñ∂ þħïs!-1', encoding='utf-16')
        assert no_todos.main((str(f1), str(f2))) == 2
        assert mocked_print.call_args_list[-2].args[0] \
            .endswith('todo_utf16.txt: cannot be read as UTF-8, trying UTF-16')
        f3 = tmpdir.join('todo_greek.txt')
        # noinspection SpellCheckingInspection
        f3.write_text('TODO: Υeσΰς, δέηδ ΤΞΪΣ!-1', encoding='ISO-8859-7')
        assert no_todos.main((str(f1), str(f3), str(f2))) == 2
        assert mocked_print.call_args_list[-3].args[0] \
            .endswith('todo_greek.txt: cannot be read as UTF-16, skipping it')
