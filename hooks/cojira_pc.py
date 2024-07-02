from __future__ import annotations

from collections.abc import Sequence

from hooks import cojira


def main(argv: Sequence[str] | None = None) -> int:
    return cojira.main([]) if len(argv) <= 3 else cojira.main(argv[3:])


if __name__ == '__main__':
    raise SystemExit(main())
