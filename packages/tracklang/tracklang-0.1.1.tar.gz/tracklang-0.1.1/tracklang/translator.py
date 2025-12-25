BLOCK_OPENERS = {
    "START_RACE": "def",
    "CHECKPOINT": "if",
    "ALT_ROUTE": "elif",
    "ELSE_ROUTE": "else",
    "LOOP_TRACK": "while",
    "LAP": "for",
}

SIMPLE_KEYWORDS = {
    "PB": "",
    "GO": "",
    "RESTART_MAP": "return",
    "DNF": "break",
    "RESET_RUN": "continue",
}

OPERATORS = {
    "FASTER_THAN": ">",
    "SLOWER_THAN": "<",
    "EQUALS": "==",
    "NOT_PB": "!=",
    "AT_LEAST": ">=",
    "AT_MOST": "<=",
}


def translate_line(line: str) -> str:
    line = line.strip()
    if not line or line.startswith("#"):
        return ""

    # Operators first
    for k, v in OPERATORS.items():
        line = line.replace(k, v)

    # fixing the thing :(
    if line.startswith("CHAT "):
        rest = line[len("CHAT "):].strip()
        # Wrap in parentheses if not already
        if not (rest.startswith("(") and rest.endswith(")")):
            rest = f"({rest})"
        return f"print{rest}"

    # INSTALLOPENPLANETPLUGIN -> import
    if line.startswith("INSTALLOPENPLANETPLUGIN "):
        parts = line.split()
        if "AS" in parts:
            module = parts[1]
            alias = parts[3]
            return f"import {module} as {alias}"
        else:
            module = parts[1]
            return f"import {module}"

    # DOWNLOADFROMNADEO -> from x import y
    if line.startswith("DOWNLOADFROMNADEO "):
        parts = line.split()
        module = parts[1]
        thing = parts[2]
        return f"from {module} import {thing}"

    # SIMPLE_KEYWORDS
    for k, v in SIMPLE_KEYWORDS.items():
        if line.startswith(k + " "):
            line = line.replace(k, v, 1)
            break

    return line


def translate(source: str) -> str:
    indent = 0
    output = []

    for raw_line in source.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line == "FINISH":
            indent -= 1
            if indent < 0:
                raise SyntaxError("FINISH without matching block")
            continue

        # Blocks
        opened = False
        for k, v in BLOCK_OPENERS.items():
            if line.startswith(k):
                rest = line[len(k):].strip()
                line_to_add = f"{v} {rest}:".rstrip()
                output.append("    " * indent + line_to_add)
                indent += 1
                opened = True
                break

        if not opened:
            translated = translate_line(line)
            if translated:
                output.append("    " * indent + translated)

    if indent != 0:
        raise SyntaxError("Unclosed block (missing FINISH)")

    return "\n".join(output)