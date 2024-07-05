from __future__ import annotations


def pre_mutation(context):
    line = context.current_source_line.strip()
    if line.startswith('parser.'):
        context.skip = True
    elif line == "if __name__ == '__main__':":
        context.skip = True
    elif line.strip().startswith("help='"):
        context.skip = True
