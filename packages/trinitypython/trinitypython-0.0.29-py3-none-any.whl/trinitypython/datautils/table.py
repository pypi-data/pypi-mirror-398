def parse_markdown_table(markdown: str) -> list:
    lines = markdown.strip().split('\n')
    table = []

    # Skip the separator line (usually second line with ---)
    for i, line in enumerate(lines):
        # Skip separator line
        if i == 1 and set(line.replace('|', '').strip()) <= {'-', ' '}:
            continue
        # Split by '|' and strip whitespace
        row = [cell.strip() for cell in line.strip('|').split('|')]
        table.append(row)

    return table

def parse_fixed_width_table(text: str) -> list:
    lines = text.strip().split('\n')

    # Skip the separator line (usually second line)
    content_lines = [line for i, line in enumerate(lines) if i != 1]

    # Determine column boundaries from the separator line
    separator_line = lines[1]
    col_starts = []
    in_col = False

    for i, ch in enumerate(separator_line):
        if ch != ' ' and not in_col:
            col_starts.append(i)
            in_col = True
        elif ch == ' ' and in_col:
            in_col = False
    col_starts.append(len(separator_line))  # Add end boundary

    # Parse each line using column boundaries
    table = []
    for line in content_lines:
        row = []
        for start, end in zip(col_starts, col_starts[1:]):
            cell = line[start:end].strip()
            row.append(cell)
        table.append(row)

    return table
