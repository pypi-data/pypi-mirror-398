import re

from .config import Config

LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
INLINE_MATH_PATTERN = re.compile(r"\$\$[^\$]+\$\$")
LIST_PATTERN = re.compile(r"^(\s*)([-*+]|\d+\.)\s")
HEADING_PATTERN = re.compile(r"^#{1,6}\s")
CODE_FENCE_PATTERN = re.compile(r"^```")
MATH_BLOCK_PATTERN = re.compile(r"^\$\$")
CALLOUT_PATTERN = re.compile(r"^(>+)\s?")
ADMONITION_PATTERN = re.compile(r"^(>+)\s*\[!(\w+)\]")


def format_markdown(text: str, config: Config | None = None) -> str:
    if config is None:
        config = Config()

    lines = text.split("\n")
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if CODE_FENCE_PATTERN.match(line):
            result.append(line)
            i += 1
            while i < len(lines) and not CODE_FENCE_PATTERN.match(lines[i]):
                result.append(lines[i])
                i += 1
            if i < len(lines):
                result.append(lines[i])
                i += 1
            continue

        if MATH_BLOCK_PATTERN.match(line.strip()):
            result.append(line)
            i += 1
            while i < len(lines) and not MATH_BLOCK_PATTERN.match(lines[i].strip()):
                result.append(lines[i])
                i += 1
            if i < len(lines):
                result.append(lines[i])
                i += 1
            continue

        if HEADING_PATTERN.match(line) or line.strip() == "":
            result.append(line)
            i += 1
            continue

        list_match = LIST_PATTERN.match(line)
        if list_match:
            list_prefix = list_match.group(0)
            indent = " " * len(list_prefix)
            content = line[list_match.end() :]
            effective_length = config.line_length - len(indent)
            wrapped = _wrap_paragraph(content, effective_length)
            wrapped_lines = wrapped.split("\n")
            result.append(list_prefix + wrapped_lines[0])
            for wrapped_line in wrapped_lines[1:]:
                result.append(indent + wrapped_line)
            i += 1
            continue

        admonition_match = ADMONITION_PATTERN.match(line)
        if admonition_match:
            result.append(line)
            i += 1
            continue

        callout_match = CALLOUT_PATTERN.match(line)
        callout_prefix = ""
        if callout_match:
            callout_prefix = callout_match.group(1) + " "
            line = line[callout_match.end() :]

        para_lines = [line]
        i += 1
        while i < len(lines):
            next_line = lines[i]
            if (
                next_line.strip() == ""
                or HEADING_PATTERN.match(next_line)
                or LIST_PATTERN.match(next_line)
                or CODE_FENCE_PATTERN.match(next_line)
                or MATH_BLOCK_PATTERN.match(next_line.strip())
            ):
                break
            if callout_prefix and CALLOUT_PATTERN.match(next_line):
                next_callout = CALLOUT_PATTERN.match(next_line)
                next_line = next_line[next_callout.end() :]
            para_lines.append(next_line)
            i += 1

        paragraph = " ".join(para_lines)
        effective_length = config.line_length - len(callout_prefix)
        wrapped = _wrap_paragraph(paragraph, effective_length)
        if callout_prefix:
            wrapped = "\n".join(
                callout_prefix + wrapped_line for wrapped_line in wrapped.split("\n")
            )
        result.append(wrapped)

    return "\n".join(result)


def _wrap_paragraph(paragraph: str, line_length: int) -> str:
    tokens = _tokenize_with_links(paragraph)

    if not tokens:
        return ""

    wrapped_lines = []
    current_line = []
    current_length = 0

    for token in tokens:
        token_length = len(token)

        if current_length == 0:
            current_line.append(token)
            current_length = token_length
        elif current_length + 1 + token_length <= line_length:
            current_line.append(token)
            current_length += 1 + token_length
        else:
            wrapped_lines.append(" ".join(current_line))
            current_line = [token]
            current_length = token_length

    if current_line:
        wrapped_lines.append(" ".join(current_line))

    return "\n".join(wrapped_lines)


def _tokenize_with_links(text: str) -> list[str]:
    tokens = []
    last_end = 0

    # Find all special patterns (links and inline math)
    patterns = []
    for match in LINK_PATTERN.finditer(text):
        patterns.append((match.start(), match.end(), match.group(0)))
    for match in INLINE_MATH_PATTERN.finditer(text):
        patterns.append((match.start(), match.end(), match.group(0)))

    # Sort by start position
    patterns.sort(key=lambda x: x[0])

    for start, end, matched_text in patterns:
        before = text[last_end:start]
        if before:
            tokens.extend(before.split())
        tokens.append(matched_text)
        last_end = end

    after = text[last_end:]
    if after:
        tokens.extend(after.split())

    return tokens
