def pre_mutation(context):
    line = context.current_source_line.strip()
    if line.startswith('print('):
        context.skip = True
    if line.startswith('parser.'):
        context.skip = True
    if line == "if __name__ == '__main__':":
        context.skip = True
