from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

LINE_RE = re.compile(r"""
    ^(?P<lead>\s*)
    (?:(?P<export>export)\s+)?        # optional 'export '
    (?P<key>[A-Za-z_][A-Za-z0-9_]*?)  # KEY
    (?P<eq>\s*=\s*)                   # equals with any spaces around
    (?P<val>.*)                       # value (raw, keep as-is)
    $
""", re.VERBOSE)

COMMENT_KEY_RE = re.compile(r"^(\s*#\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*=\s*.*)$")


def uppercase_env_keys(
        *, path: str | Path,
        output: Optional[str | Path] = None,
        backup: bool = False
) -> Path:
    """
    Преобразует имена переменных в .env и в комментариях в верхний регистр.

    :param path: путь к исходному .env
    :param output: путь к файлу вывода. Если None — правит на месте.
    :param backup: делать .bak при in-place
    :return: путь к записанному файлу
    """
    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(src)

    text = src.read_text(encoding="utf-8-sig").splitlines(keepends=True)

    out_lines = []

    for line in text:
        stripped = line.strip()

        # пустые строки — оставляем как есть
        if not stripped:
            out_lines.append(line)
            continue

        # комментарий с "ключом" вида # KEY=
        m_comment = COMMENT_KEY_RE.match(line.rstrip("\n"))
        if m_comment:
            prefix, key, rest = m_comment.groups()
            key_up = key.upper()
            # сохраняем оригинальный символ конца строки, если он был
            newline = "\n" if line.endswith("\n") else ""
            out_lines.append(f"{prefix}{key_up}{rest}{newline}")
            continue

        # стандартная строка с KEY=VAL
        m = LINE_RE.match(line.rstrip("\n"))
        if not m:
            out_lines.append(line)
            continue

        lead = m.group("lead") or ""
        export_kw = m.group("export") or ""
        key = m.group("key")
        eq = m.group("eq")
        val = m.group("val")

        key_up = key.upper()
        newline = "\n" if line.endswith("\n") else ""
        new_line = f"{lead}{(export_kw + ' ') if export_kw else ''}{key_up}{eq}{val}{newline}"
        out_lines.append(new_line)

    # запись
    if output is None:
        if backup:
            bak = src.with_suffix(src.suffix + ".bak")
            bak.write_text("".join(text), encoding="utf-8")
        dst = src
    else:
        dst = Path(output)

    dst.write_text("".join(out_lines), encoding="utf-8")
    return dst
