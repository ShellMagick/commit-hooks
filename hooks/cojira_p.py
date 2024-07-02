from __future__ import annotations

from collections.abc import Sequence

from hooks import cojira


def main(argv: Sequence[str] | None = None) -> int:
    return cojira.main(argv[5]) if len(argv) <= 6 else cojira.main(argv[5] + argv[6:])


if __name__ == '__main__':
    raise SystemExit(main())
