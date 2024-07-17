from __future__ import annotations

import re
import unittest
from pathlib import Path
from unittest.mock import call

from hooks import no_boms


def test_utf32_bom_le(tmpdir):
    with unittest.mock.patch('builtins.print') as mocked_print:
        f = Path(tmpdir.join('bom32le.txt'))
        f.write_bytes(
            b'\xff\xfe\x00\x00'
            b'\x42\x65\x66\xc3\xb6\x72\xc4\x99\x20\xc5\xa7\x68'
            b'\x69\x73\x20\x74\x65\x78\x74\x20\xc3\xbe\x65\x72'
            b'\x65\x20\x69\xc3\x9f\x20\x61\x6e\x20\x55\x54\x46\x2d'
            b'\x33\x32\x20\x28\x4c\x45\x29'
            b'\x20\xe2\x98\x85\xe2\x98\x85\xce\x92\x4f\x4d\xe3'
            b'\x86\x98\xe3\x86\x92\xe3\x86\x9d',
        )
        assert no_boms.main((str(f),)) == 13
        assert re.match(r'^.*[\\/]bom32le\.txt: has a UTF-32 BOM \(LE\)$',
                        mocked_print.call_args.args[0]) is not None


def test_utf32_bom_be(tmpdir):
    with unittest.mock.patch('builtins.print') as mocked_print:
        f = Path(tmpdir.join('bom32be.txt'))
        f.write_bytes(
            b'\x00\x00\xfe\xff'
            b'\x42\x65\x66\xc3\xb6\x72\xc4\x99\x20\xc5\xa7\x68'
            b'\x69\x73\x20\x74\x65\x78\x74\x20\xc3\xbe\x65\x72'
            b'\x65\x20\x69\xc3\x9f\x20\x61\x6e\x20\x55\x54\x46\x2d'
            b'\x33\x32\x20\x28\x42\x45\x29'
            b'\x20\xe2\x98\x85\xe2\x98\x85\xce\x92\x4f\x4d\xe3'
            b'\x86\x98\xe3\x86\x92\xe3\x86\x9d',
        )
        assert no_boms.main((str(f),)) == 11
        assert re.match(r'^.*[\\/]bom32be\.txt: has a UTF-32 BOM \(BE\)$',
                        mocked_print.call_args.args[0]) is not None


def test_utf16_bom_le(tmpdir):
    with unittest.mock.patch('builtins.print') as mocked_print:
        f = Path(tmpdir.join('bom16le.txt'))
        f.write_bytes(
            b'\xff\xfe'
            b'\x42\x65\x66\xc3\xb6\x72\xc4\x99\x20\xc5\xa7\x68'
            b'\x69\x73\x20\x74\x65\x78\x74\x20\xc3\xbe\x65\x72'
            b'\x65\x20\x69\xc3\x9f\x20\x61\x6e\x20\x55\x54\x46\x2d'
            b'\x31\x36\x20\x28\x4c\x45\x29'
            b'\x20\xe2\x98\x85\xe2\x98\x85\xce\x92\x4f\x4d\xe3'
            b'\x86\x98\xe3\x86\x92\xe3\x86\x9d',
        )
        assert no_boms.main((str(f),)) == 7
        assert re.match(r'^.*[\\/]bom16le\.txt: has a UTF-16 BOM \(LE\)$',
                        mocked_print.call_args.args[0]) is not None


def test_utf16_bom_be(tmpdir):
    with unittest.mock.patch('builtins.print') as mocked_print:
        f = Path(tmpdir.join('bom16be.txt'))
        f.write_bytes(
            b'\xfe\xff'
            b'\x42\x65\x66\xc3\xb6\x72\xc4\x99\x20\xc5\xa7\x68'
            b'\x69\x73\x20\x74\x65\x78\x74\x20\xc3\xbe\x65\x72'
            b'\x65\x20\x69\xc3\x9f\x20\x61\x6e\x20\x55\x54\x46\x2d'
            b'\x31\x36\x20\x28\x42\x45\x29'
            b'\x20\xe2\x98\x85\xe2\x98\x85\xce\x92\x4f\x4d\xe3'
            b'\x86\x98\xe3\x86\x92\xe3\x86\x9d',
        )
        assert no_boms.main((str(f),)) == 5
        assert re.match(r'^.*[\\/]bom16be\.txt: has a UTF-16 BOM \(BE\)$',
                        mocked_print.call_args.args[0]) is not None


def test_utf8_bom_directly(tmpdir):
    with unittest.mock.patch('builtins.print') as mocked_print:
        f = Path(tmpdir.join('bom8.txt'))
        f.write_bytes(
            b'\xef\xbb\xbf'
            b'\x42\x65\x66\xc3\xb6\x72\xc4\x99\x20\xc5\xa7\x68'
            b'\x69\x73\x20\x74\x65\x78\x74\x20\xc3\xbe\x65\x72'
            b'\x65\x20\x69\xc3\x9f\x20\x61\x6e\x20\x55\x54\x46\x2d'
            b'\x38'
            b'\x20\xe2\x98\x85\xe2\x98\x85\xce\x92\x4f\x4d\xe3'
            b'\x86\x98\xe3\x86\x92\xe3\x86\x9d',
        )
        assert no_boms.main((str(f),)) == 3
        assert re.match(r'^.*[\\/]bom8\.txt: has a UTF-8 BOM$',
                        mocked_print.call_args.args[0]) is not None


def test_utf8_bom_via_encoding(tmpdir):
    f = tmpdir.join('bom8.txt')
    # noinspection SpellCheckingInspection
    f.write_text(
        'Beförę ŧhis text þere iß an UTF-8 ★★ΒOM㆘㆒㆝',
        encoding='utf-8-sig',
    )
    assert no_boms.main((str(f),)) == 3


def test_utf8_wo_bom_via_encoding(tmpdir):
    f = tmpdir.join('no_bom.txt')
    # noinspection SpellCheckingInspection
    f.write_text(
        'Beförę ŧhis text þere iß no UTF-8 ★★ΒOM㆘㆒㆝',
        encoding='utf-8',
    )
    assert no_boms.main((str(f),)) == 0


def test_non_utf8(tmpdir):
    f = tmpdir.join('latin1.txt')
    f.write_text('ño wäy Jößé!', encoding='latin_1')
    assert no_boms.main((str(f),)) == 0


def test_combination_violation(tmpdir):
    fu32le = Path(tmpdir.join('bom32le.txt'))
    fu32le.write_bytes(
        b'\xff\xfe\x00\x00'
        b'\x42\x65\x66\xc3\xb6\x72\xc4\x99\x20\xc5\xa7\x68'
        b'\x69\x73\x20\x74',
    )
    fu32be = Path(tmpdir.join('bom32be.txt'))
    fu32be.write_bytes(
        b'\x00\x00\xfe\xff'
        b'\x42\x65\x66\xc3\xb6\x72\xc4\x99\x20\xc5\xa7\x68'
        b'\x69\x73\x20\x74',
    )
    fu16le = Path(tmpdir.join('bom16le.txt'))
    fu16le.write_bytes(
        b'\xfe\xff'
        b'\x42\x65\x66\xc3\xb6\x72\xc4\x99\x20\xc5\xa7\x68'
        b'\x69\x73\x20\x74',
    )
    fu16be = Path(tmpdir.join('bom16be.txt'))
    fu16be.write_bytes(
        b'\xff\xfe'
        b'\x42\x65\x66\xc3\xb6\x72\xc4\x99\x20\xc5\xa7\x68'
        b'\x69\x73\x20\x74',
    )
    fu8 = Path(tmpdir.join('bom8.txt'))
    fu8.write_bytes(
        b'\xef\xbb\xbf'
        b'\x42\x65\x66\xc3\xb6\x72\xc4\x99\x20\xc5\xa7\x68'
        b'\x69\x73\x20\x74',
    )
    fu32le2 = Path(tmpdir.join('bom32le_2.txt'))
    fu32le2.write_bytes(
        b'\xff\xfe\x00\x00'
        b'\x42\x65\x66\xc3\xb6\x72\xc4\x99\x20\xc5\xa7\x68'
        b'\x69\x73\x20\x74',
    )
    assert no_boms.main([
        str(fu32le),
        str(fu32be),
        str(fu16le),
        str(fu16be),
        str(fu8),
        str(fu32le2),
    ]) == 123
