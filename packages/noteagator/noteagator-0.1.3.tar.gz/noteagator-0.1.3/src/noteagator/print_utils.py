import re
from typing import Any

import pyperclip

NOTE_COLORS = {
    "<red>": "\033[91m",
    "<blue>": "\033[94m",
    "<green>": "\033[92m",
    "<end>": "\033[0m",
}


def add_colors(text: str) -> str:
    for key, value in NOTE_COLORS.items():
        text = text.replace(key, str(value))
    return text


def replace_placeholders(
    body: str, replace_placeholders_dict: dict[str, Any], meta_data: dict[str, Any]
) -> str:
    for key, value in replace_placeholders_dict.items():
        if value is not None and meta_data.get("placeholders") is not None:
            if meta_data.get("placeholders").get(key) is not None:
                body = body.replace(str(meta_data["placeholders"][key]), str(value))
    return body


def get_code_by_number_markdown(text: str, copy_number: str) -> str:
    pattern = r"--copy (\d+)\n```(.*?)\n(.*?)\n```"

    matches = re.findall(pattern, text, re.DOTALL)
    for match in matches:
        if int(match[0]) == int(copy_number):
            return match[2]

    return None


def add_copy_markers_markdown(input_string: str) -> str:
    pattern = r"```(.*?)\n(.*?)\n```"

    def replace(match):
        language = match.group(1).strip()
        block_content = match.group(2)
        replace.counter += 1
        return f"--copy {replace.counter}\n```{language}\n{block_content}\n```"

    replace.counter = 0
    modified_string = re.sub(pattern, replace, input_string, flags=re.DOTALL)

    return modified_string


def print_note_markdown(markdown: str, copy: str) -> None:
    from rich.console import Console
    from rich.markdown import Markdown

    markdown = add_copy_markers_markdown(markdown)
    console = Console()
    md = Markdown(markdown)
    console.print(md)
    if copy:
        pyperclip.copy(get_code_by_number_markdown(markdown, copy))


def add_copy_markers_slim(markdown_content: str) -> str:
    lines = markdown_content.splitlines()
    out = []
    in_code = False
    first_in_block = False
    block_idx = 1

    def indent_for(i: int) -> str:
        return " " * len(f"--copy {i} ")

    for line in lines:
        if line.startswith("```"):
            if not in_code:
                in_code = True
                first_in_block = True
            else:
                in_code = False
                block_idx += 1
            continue

        if in_code:
            if first_in_block:
                out.append(f"--copy {block_idx} $ {line}")
                first_in_block = False
            else:
                out.append(f"{indent_for(block_idx)}$ {line}")
        else:
            out.append(line)

    return "\n".join(out)


def extract_copy_block(slim_text: str, copy_id: int) -> str:
    start_prefix = f"--copy {copy_id} $ "
    cont_prefix = " " * len(f"--copy {copy_id} ") + "$ "

    collecting = False
    buf = []

    for line in slim_text.splitlines():
        if not collecting:
            if line.startswith(start_prefix):
                collecting = True
                buf.append(line[len(start_prefix) :])
        else:
            if line.startswith(cont_prefix):
                buf.append(line[len(cont_prefix) :])
            elif line.startswith("--copy "):
                break
            else:
                break

    return "\n".join(buf)


def print_note_slim(body: str, copy: int | None) -> None:
    slim = add_copy_markers_slim(body)
    print(slim)

    if copy is not None:
        try:
            chunk = extract_copy_block(slim, int(copy))
            if not chunk:
                raise ValueError(f"No --copy {copy} block found.")
            pyperclip.copy(chunk)
        except Exception as e:
            print(e)


def format_note_body(
    body: str, meta_data: dict[str, Any], i: str, j: str, k: str, u: str, d: str, p: str
) -> str:
    replace_placeholders_dict = {"i": i, "j": j, "k": k, "u": u, "d": d, "p": p}
    body = add_colors(body)
    body = replace_placeholders(body, replace_placeholders_dict, meta_data)
    return body


def get_fmt(cli_fmt, config_fmt, note_fmt):
    if cli_fmt:
        return cli_fmt
    elif note_fmt == "markdown" or note_fmt == "slim":
        return note_fmt
    elif config_fmt:
        return config_fmt
    else:
        return "markdown"
