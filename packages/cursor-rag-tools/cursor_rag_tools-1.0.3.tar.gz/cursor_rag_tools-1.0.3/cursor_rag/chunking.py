"""
Semantic chunking for code files.

This module prefers syntactic/semantic boundaries (functions/classes/methods) over raw text splitting.
Falls back to plain text chunking if parsing isn't available.
"""

from __future__ import annotations

import ast
import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Chunk:
    text: str
    start_line: int | None = None  # 1-based
    end_line: int | None = None  # 1-based, inclusive
    symbol_type: str | None = None
    symbol_name: str | None = None
    language: str | None = None


def _safe_import_tree_sitter() -> tuple[Any | None, Any | None]:
    """
    Returns (get_parser, get_language) from tree_sitter_languages if available; otherwise (None, None).
    """

    try:
        mod = importlib.import_module("tree_sitter_languages")
    except Exception:
        return None, None

    get_parser = getattr(mod, "get_parser", None)
    get_language = getattr(mod, "get_language", None)
    if not callable(get_parser) or not callable(get_language):
        return None, None
    return get_parser, get_language


def detect_language(file_path: Path) -> str | None:
    ext = file_path.suffix.lower()
    if ext == ".py":
        return "python"
    if ext in {".js", ".jsx"}:
        return "javascript"
    if ext in {".ts", ".tsx"}:
        return "typescript"
    return None


def text_chunks(text: str, *, max_chars: int, overlap: int) -> list[Chunk]:
    if not text:
        return []
    if max_chars <= 0:
        return [Chunk(text=text)]
    if overlap < 0:
        overlap = 0
    step = max(1, max_chars - overlap)
    chunks: list[Chunk] = []
    for i in range(0, len(text), step):
        chunks.append(Chunk(text=text[i : i + max_chars]))
    return chunks


def chunk_file(
    *,
    content: str,
    file_path: Path,
    max_chars: int,
    overlap: int,
    min_chars: int,
    enable_semantic: bool = True,
) -> list[Chunk]:
    """
    Chunk a single file. Uses semantic chunking for supported languages, otherwise falls back to text chunking.
    """

    if not content.strip():
        return []

    language = detect_language(file_path)
    if not enable_semantic or language is None:
        return text_chunks(content, max_chars=max_chars, overlap=overlap)

    # Always prefer Python AST-based chunking: works on any Python version and requires no extra deps.
    if language == "python":
        try:
            chunks = _python_ast_chunks(
                content=content,
                max_chars=max_chars,
                min_chars=min_chars,
            )
            if chunks:
                return chunks
        except Exception:
            # fall back to tree-sitter or plain text
            pass

    get_parser, _get_language = _safe_import_tree_sitter()
    if get_parser is None:
        return text_chunks(content, max_chars=max_chars, overlap=overlap)

    try:
        parser = get_parser(language)
    except Exception:
        return text_chunks(content, max_chars=max_chars, overlap=overlap)

    source_bytes = content.encode("utf-8", errors="ignore")
    tree = parser.parse(source_bytes)
    root = tree.root_node

    chunks = _semantic_chunks_from_tree(
        source_bytes=source_bytes,
        root=root,
        language=language,
        max_chars=max_chars,
        min_chars=min_chars,
    )
    if not chunks:
        return text_chunks(content, max_chars=max_chars, overlap=overlap)
    return chunks


def _semantic_chunks_from_tree(
    *,
    source_bytes: bytes,
    root: Any,
    language: str,
    max_chars: int,
    min_chars: int,
) -> list[Chunk]:
    """
    Extract semantic nodes (functions/classes/methods) and normalize sizes by splitting big chunks and merging small ones.
    """

    symbol_nodes = _collect_symbol_nodes(root=root, language=language)
    symbol_nodes.sort(key=lambda n: (n.start_byte, n.end_byte))

    # Preamble chunk: module header/imports/comments up to first symbol.
    chunks: list[Chunk] = []
    if symbol_nodes:
        first = symbol_nodes[0]
        preamble_text = _decode_span(source_bytes, 0, first.start_byte).strip()
        if preamble_text:
            chunks.append(
                Chunk(
                    text=preamble_text,
                    start_line=1,
                    end_line=_to_1based_line(first.start_point[0]),
                    symbol_type="preamble",
                    symbol_name=None,
                    language=language,
                )
            )
    else:
        # No symbols found; let caller fallback.
        return []

    for node in symbol_nodes:
        node_text = _decode_span(source_bytes, node.start_byte, node.end_byte).strip()
        if not node_text:
            continue

        start_line = _to_1based_line(node.start_point[0])
        end_line = _to_1based_line(node.end_point[0])
        symbol_type, symbol_name = _symbol_info(node=node, language=language, source_bytes=source_bytes)

        base_chunk = Chunk(
            text=node_text,
            start_line=start_line,
            end_line=end_line,
            symbol_type=symbol_type,
            symbol_name=symbol_name,
            language=language,
        )

        # Split oversized chunks by syntactic children (statement blocks / class bodies).
        if max_chars > 0 and len(base_chunk.text) > max_chars:
            chunks.extend(
                _split_large_chunk(
                    node=node,
                    source_bytes=source_bytes,
                    language=language,
                    max_chars=max_chars,
                    symbol_type=symbol_type,
                    symbol_name=symbol_name,
                )
            )
        else:
            chunks.append(base_chunk)

    # Merge very small adjacent chunks (same file) to reduce fragmentation.
    return _merge_small_chunks(chunks, max_chars=max_chars, min_chars=min_chars)


def _python_ast_chunks(*, content: str, max_chars: int, min_chars: int) -> list[Chunk]:
    """
    Semantic chunking for Python using stdlib ast.

    Strategy:
    - Create chunks for top-level functions/classes.
    - Also include class methods as separate chunks.
    - Add a "preamble" chunk (imports/module docstring/etc) before the first symbol.
    - Split oversized symbols by grouping statements in their body (not raw text splitting).
    - Merge very small chunks.
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    lines = content.splitlines()

    symbols: list[tuple[ast.AST, str | None, str | None]] = []

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.class_stack: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> Any:
            symbols.append((node, "class", node.name))
            self.class_stack.append(node.name)
            for stmt in node.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append((stmt, "method", stmt.name))
            self.generic_visit(node)
            self.class_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
            # Only top-level functions (methods are added in ClassDef above)
            if not self.class_stack:
                symbols.append((node, "function", node.name))
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
            if not self.class_stack:
                symbols.append((node, "function", node.name))
            self.generic_visit(node)

    Visitor().visit(tree)

    def start_line(n: ast.AST) -> int | None:
        return getattr(n, "lineno", None)

    def end_line(n: ast.AST) -> int | None:
        return getattr(n, "end_lineno", None)

    symbols = [(n, t, name) for (n, t, name) in symbols if start_line(n) and end_line(n)]
    symbols.sort(key=lambda x: (start_line(x[0]) or 10**9, end_line(x[0]) or 10**9))

    if not symbols:
        return []

    chunks: list[Chunk] = []

    first_start = start_line(symbols[0][0]) or 1
    if first_start > 1:
        preamble_text = "\n".join(lines[: first_start - 1]).strip()
        if preamble_text:
            chunks.append(
                Chunk(
                    text=preamble_text,
                    start_line=1,
                    end_line=first_start - 1,
                    symbol_type="preamble",
                    symbol_name=None,
                    language="python",
                )
            )

    for node, sym_type, sym_name in symbols:
        s = start_line(node)
        e = end_line(node)
        if not s or not e:
            continue
        text = "\n".join(lines[s - 1 : e]).strip()
        if not text:
            continue

        base = Chunk(
            text=text,
            start_line=s,
            end_line=e,
            symbol_type=sym_type,
            symbol_name=sym_name,
            language="python",
        )

        if max_chars > 0 and len(base.text) > max_chars:
            chunks.extend(
                _python_split_large_symbol(
                    node=node,
                    lines=lines,
                    max_chars=max_chars,
                    symbol_type=sym_type,
                    symbol_name=sym_name,
                )
            )
        else:
            chunks.append(base)

    return _merge_small_chunks(chunks, max_chars=max_chars, min_chars=min_chars)


def _python_split_large_symbol(
    *,
    node: ast.AST,
    lines: list[str],
    max_chars: int,
    symbol_type: str | None,
    symbol_name: str | None,
) -> list[Chunk]:
    """
    Split a large Python function/class by grouping its top-level body statements.
    This is structure-based, not raw text splitting.
    """
    s = getattr(node, "lineno", None)
    e = getattr(node, "end_lineno", None)
    body = getattr(node, "body", None)
    if not s or not e or not isinstance(body, list) or not body:
        return [
            Chunk(
                text="\n".join(lines[s - 1 : e]).strip() if s and e else "",
                start_line=s,
                end_line=e,
                symbol_type=symbol_type,
                symbol_name=symbol_name,
                language="python",
            )
        ]

    # Header = from symbol start to just before first body statement.
    first_stmt = body[0]
    first_stmt_line = getattr(first_stmt, "lineno", None) or (s + 1)
    header_end = max(s, first_stmt_line - 1)
    header_text = "\n".join(lines[s - 1 : header_end]).rstrip()

    parts: list[Chunk] = []

    group_start = None
    group_end = None

    def flush() -> None:
        nonlocal group_start, group_end
        if group_start is None or group_end is None:
            return
        body_text = "\n".join(lines[group_start - 1 : group_end]).strip()
        if not body_text:
            group_start = None
            group_end = None
            return
        text = (header_text + "\n" + body_text).strip() if header_text else body_text
        parts.append(
            Chunk(
                text=text,
                start_line=s,
                end_line=group_end,
                symbol_type=symbol_type,
                symbol_name=symbol_name,
                language="python",
            )
        )
        group_start = None
        group_end = None

    current_len = len(header_text)
    for stmt in body:
        stmt_s = getattr(stmt, "lineno", None)
        stmt_e = getattr(stmt, "end_lineno", None)
        if not stmt_s or not stmt_e:
            continue

        if group_start is None:
            group_start, group_end = stmt_s, stmt_e
            current_len = len(header_text) + len("\n".join(lines[group_start - 1 : group_end]))
            continue

        prospective_end = stmt_e
        prospective_len = len(header_text) + len("\n".join(lines[group_start - 1 : prospective_end]))
        if prospective_len > max_chars and current_len > 0:
            flush()
            group_start, group_end = stmt_s, stmt_e
            current_len = len(header_text) + len("\n".join(lines[group_start - 1 : group_end]))
        else:
            group_end = stmt_e
            current_len = prospective_len

    flush()
    return parts


def _collect_symbol_nodes(*, root: Any, language: str) -> list[Any]:
    """
    Collect top-level semantic nodes; includes class methods as separate nodes.
    """

    nodes: list[Any] = []

    def visit(node: Any, *, parent: Any | None = None) -> None:
        t = getattr(node, "type", "")

        # Unwrap export statements (JS/TS).
        if language in {"javascript", "typescript"} and t in {"export_statement", "export_default_declaration"}:
            for child in getattr(node, "named_children", []) or []:
                visit(child, parent=node)
            return

        if language == "python":
            if t in {"function_definition", "class_definition", "decorated_definition"}:
                if t == "decorated_definition":
                    # decorated_definition wraps a class_definition/function_definition
                    for child in getattr(node, "named_children", []) or []:
                        if getattr(child, "type", "") in {"function_definition", "class_definition"}:
                            nodes.append(child)
                            # Also walk inside class to get methods.
                            if getattr(child, "type", "") == "class_definition":
                                _collect_python_class_methods(child, out=nodes)
                    return

                nodes.append(node)
                if t == "class_definition":
                    _collect_python_class_methods(node, out=nodes)
                return

        if language in {"javascript", "typescript"}:
            if t in {"function_declaration", "class_declaration"}:
                nodes.append(node)
                if t == "class_declaration":
                    _collect_js_class_methods(node, out=nodes)
                return

            # const foo = () => {} / function() {}
            if t == "lexical_declaration":
                for child in getattr(node, "named_children", []) or []:
                    if getattr(child, "type", "") == "variable_declarator":
                        init = _first_named_child_of_type(child, {"arrow_function", "function"})
                        if init is not None:
                            nodes.append(child)
                return

        # Traverse
        for child in getattr(node, "named_children", []) or []:
            visit(child, parent=node)

    visit(root)

    # Prefer unique byte ranges to avoid duplicates (e.g., decorated wrappers)
    uniq: dict[tuple[int, int], Any] = {}
    for n in nodes:
        key = (n.start_byte, n.end_byte)
        uniq.setdefault(key, n)
    return list(uniq.values())


def _collect_python_class_methods(class_node: Any, *, out: list[Any]) -> None:
    block = _first_named_child_of_type(class_node, {"block"})
    if block is None:
        return
    for child in getattr(block, "named_children", []) or []:
        if getattr(child, "type", "") in {"function_definition", "decorated_definition"}:
            if getattr(child, "type", "") == "decorated_definition":
                inner = _first_named_child_of_type(child, {"function_definition"})
                if inner is not None:
                    out.append(inner)
            else:
                out.append(child)


def _collect_js_class_methods(class_node: Any, *, out: list[Any]) -> None:
    body = _first_named_child_of_type(class_node, {"class_body"})
    if body is None:
        return
    for child in getattr(body, "named_children", []) or []:
        if getattr(child, "type", "") == "method_definition":
            out.append(child)


def _first_named_child_of_type(node: Any, types: set[str]) -> Any | None:
    for ch in getattr(node, "named_children", []) or []:
        if getattr(ch, "type", "") in types:
            return ch
    return None


def _symbol_info(*, node: Any, language: str, source_bytes: bytes) -> tuple[str | None, str | None]:
    t = getattr(node, "type", "")

    if language == "python":
        if t == "class_definition":
            return "class", _extract_identifier(node, source_bytes=source_bytes)
        if t == "function_definition":
            return "function", _extract_identifier(node, source_bytes=source_bytes)
        return "symbol", _extract_identifier(node, source_bytes=source_bytes)

    if language in {"javascript", "typescript"}:
        if t == "class_declaration":
            return "class", _extract_identifier(node, source_bytes=source_bytes)
        if t == "function_declaration":
            return "function", _extract_identifier(node, source_bytes=source_bytes)
        if t == "method_definition":
            return "method", _extract_identifier(node, source_bytes=source_bytes)
        if t == "variable_declarator":
            return "function", _extract_identifier(node, source_bytes=source_bytes)
        return "symbol", _extract_identifier(node, source_bytes=source_bytes)

    return None, None


def _extract_identifier(node: Any, *, source_bytes: bytes) -> str | None:
    # Common approach: find first named child of type identifier/property_identifier.
    for ch in getattr(node, "named_children", []) or []:
        if getattr(ch, "type", "") in {"identifier", "property_identifier", "type_identifier"}:
            return _decode_span(source_bytes, ch.start_byte, ch.end_byte)
    return None


def _split_large_chunk(
    *,
    node: Any,
    source_bytes: bytes,
    language: str,
    max_chars: int,
    symbol_type: str | None,
    symbol_name: str | None,
) -> list[Chunk]:
    """
    Split a large node into smaller semantic parts using its body children.
    """

    body = None
    if language == "python":
        body = _first_named_child_of_type(node, {"block"})
    elif language in {"javascript", "typescript"}:
        # Functions have statement_block, classes have class_body, methods have statement_block.
        body = _first_named_child_of_type(node, {"statement_block", "class_body"})

    if body is None or not getattr(body, "named_children", None):
        # As a last resort, keep whole node (caller will accept oversize).
        start_line = _to_1based_line(node.start_point[0])
        end_line = _to_1based_line(node.end_point[0])
        return [
            Chunk(
                text=_decode_span(source_bytes, node.start_byte, node.end_byte).strip(),
                start_line=start_line,
                end_line=end_line,
                symbol_type=symbol_type,
                symbol_name=symbol_name,
                language=language,
            )
        ]

    header_text = _decode_span(source_bytes, node.start_byte, body.start_byte).rstrip()
    header_text = header_text if header_text else ""

    parts: list[Chunk] = []
    group_start = None
    group_end = None
    group_end_line = None
    last_child = None

    def flush_group() -> None:
        nonlocal group_start, group_end, group_end_line, last_child
        if group_start is None or group_end is None:
            return
        body_text = _decode_span(source_bytes, group_start, group_end).strip()
        if not body_text:
            group_start = None
            group_end = None
            group_end_line = None
            last_child = None
            return

        text = (header_text + "\n" + body_text).strip() if header_text else body_text
        start_line = _to_1based_line(node.start_point[0])
        end_line = group_end_line or _to_1based_line(node.end_point[0])
        parts.append(
            Chunk(
                text=text,
                start_line=start_line,
                end_line=end_line,
                symbol_type=symbol_type,
                symbol_name=symbol_name,
                language=language,
            )
        )
        group_start = None
        group_end = None
        group_end_line = None
        last_child = None

    current_len = len(header_text)
    for child in getattr(body, "named_children", []) or []:
        c_start, c_end = child.start_byte, child.end_byte
        if c_end <= c_start:
            continue
        _ = c_end - c_start

        if group_start is None:
            group_start, group_end = c_start, c_end
            last_child = child
            group_end_line = _to_1based_line(child.end_point[0])
            current_len = len(header_text) + (group_end - group_start)
            continue

        prospective = len(header_text) + (c_end - group_start)
        if prospective > max_chars and current_len > 0:
            flush_group()
            group_start, group_end = c_start, c_end
            last_child = child
            group_end_line = _to_1based_line(child.end_point[0])
            current_len = len(header_text) + (group_end - group_start)
        else:
            group_end = c_end
            last_child = child
            group_end_line = _to_1based_line(child.end_point[0])
            current_len = prospective

    flush_group()
    return parts


def _merge_small_chunks(chunks: list[Chunk], *, max_chars: int, min_chars: int) -> list[Chunk]:
    if not chunks:
        return []
    if max_chars <= 0:
        return chunks

    merged: list[Chunk] = []
    buf = chunks[0]
    for nxt in chunks[1:]:
        if len(buf.text) >= min_chars:
            merged.append(buf)
            buf = nxt
            continue

        combined_len = len(buf.text) + 2 + len(nxt.text)
        if combined_len <= max_chars:
            buf = Chunk(
                text=(buf.text.rstrip() + "\n\n" + nxt.text.lstrip()).strip(),
                start_line=buf.start_line,
                end_line=nxt.end_line or buf.end_line,
                symbol_type=buf.symbol_type or nxt.symbol_type,
                symbol_name=buf.symbol_name or nxt.symbol_name,
                language=buf.language or nxt.language,
            )
        else:
            merged.append(buf)
            buf = nxt

    merged.append(buf)
    return merged


def _to_1based_line(row0: int) -> int:
    return int(row0) + 1


def _decode_span(source_bytes: bytes, start_byte: int, end_byte: int) -> str:
    if end_byte <= start_byte:
        return ""
    try:
        return source_bytes[start_byte:end_byte].decode("utf-8", errors="ignore")
    except Exception:
        return ""
