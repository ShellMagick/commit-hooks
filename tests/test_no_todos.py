from __future__ import annotations

from hooks import no_todos


def test_no_todos(tmpdir):
    f = tmpdir.join('todo.txt')
    # noinspection SpellCheckingInspection
    f.write_text('ño wäy Jőßé!', encoding='utf-8')
    assert no_todos.main((str(f),)) == 0


def test_has_todo(tmpdir):
    f = tmpdir.join('todo.txt')
    # noinspection SpellCheckingInspection
    f.write_text('TODO: ¥eßűs, ∂éñ∂ þħïs!', encoding='utf-8')
    assert no_todos.main((str(f),)) == 1


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
    f = tmpdir.join('todo.txt')
    # noinspection SpellCheckingInspection
    f.write_text('TODO: ฿űþ ñ∅™ þħïs!', encoding='utf-8')
    assert no_todos.main(('-e', 'todo.txt', str(f))) == 0


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
