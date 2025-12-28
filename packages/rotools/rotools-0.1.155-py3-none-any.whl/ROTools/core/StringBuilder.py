class StringBuilder:
    def __init__(self, col_format=None):
        self.lines = []
        self.col_format = col_format

    def set_col_format(self, width):
        self.col_format = width

    def add_table_row(self, *args):
        if len(args) != len(self.col_format):
            raise ValueError("Invalid number of columns")
        values = [f"{a:{w}}" for a, w in zip(args, self.col_format)]

        self.add_line("".join(values))

    def add_line(self, text):
        self.lines.append(text)

    def add_segment_line(self, head, value, skip_none=False, separate_line=False):
        if skip_none and value is None:
            return
        head = f"{head:{self.col_format[0]}}"
        if separate_line:
            value = f"\n{value}\n"
        self.add_line(f"{head}: {value}")

    def build(self, parent_tag=None):
        text = "\n".join(self.lines)
        if parent_tag:
            text = f"<{parent_tag}>{text}</{parent_tag}>"
        return text
