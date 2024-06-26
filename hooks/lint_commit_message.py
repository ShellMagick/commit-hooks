from __future__ import annotations

import argparse
from collections.abc import Sequence
from re import match


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='Commit message to check')
    parser.add_argument(
        '-sl',
        '--subject-line-length',
        default='72',
        help='Maximum length of subject line (default: 72)',
    )
    parser.add_argument(
        '-bl',
        '--body-line-length',
        default='120',
        help='Maximum length of lines in the body (default: 120)',
    )
    parser.add_argument(
        '-e',
        '--ending',
        default='[.,;?!\\-]',
        help='Regex, defining forbidden characters for ending the subject line'
             ' (default: [.,;?!\\-])',
    )
    args = parser.parse_args(argv)

    with open(args.filename, encoding='utf-8') as msg:
        lines = msg.readlines()

        # Rule 0: There must be a commit message
        if not lines:
            print('The commit message must not be empty.')
            return 10

        # Rule 1: Separate the subject line and the body with an empty line
        if len(lines) != 1 and match(r'^.+$', lines[1].rstrip()):
            print(
                'The subject line and body '
                'must be separated by an empty line.',
            )
            return 1

        # Rule 2: Subject line is limited to 50 characters
        # -> we by default relax this rule to 72
        #    (modern world, auto-prefixing, etc.)
        # -> can be relaxed via argument
        if len(lines[0]) > int(args.subject_line_length):
            print(
                'The subject line must not be longer '
                f'than {args.subject_line_length}, '
                f'currently it is {len(lines[0])}.',
            )
            return 2

        # Rule 3: Capitalize the subject line
        # -> Should be done automatically via the prepare-commit-msg hook

        # Rule 4: Do not end the subject line with a period
        # -> We restrict this more,
        #    it should not end with any non-word character
        if match(r'^.*%s$' % args.ending, lines[0].rstrip()):
            print('The subject line must not end with punctuation.')
            return 4

        # Rule 5: Use imperative mood in the subject line
        # -> NOT CHECKED, would need NLP

        # Rule 6: Wrap the lines of the body at 72 characters
        # -> we by default relax this rule to 120 (modern world)
        # -> can be relaxed via argument
        for index, line in enumerate(lines[2:]):
            if len(line) > int(args.body_line_length):
                print(
                    'Wrap lines of the message body '
                    f'after {args.body_line_length} characters, '
                    f'currently line {index+1} is {len(line)} long. '
                    f'The line is: "{line}".',
                )
                return 6

        # Rule 7: Use the body to explain what and why vs. how
        # -> NOT CHECKED, would need advanced NLP

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
