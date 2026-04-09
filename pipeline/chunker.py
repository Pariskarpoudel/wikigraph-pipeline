# pipeline/chunker.py
import re
import logging
from typing import List, Dict
import config

logger = logging.getLogger(__name__)


def _token_count(text: str) -> int:
    return len(text.split())


def _clean(text: str) -> str:
    text = text.replace(" @-@ ", "-")
    text = text.replace(" @,@ ", ",")
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _parse_heading(line: str):
    """
    Parse WikiText-103 spaced heading format.
    '= Title ='           → level 1, 'Title'
    '= = Section = ='     → level 2, 'Section'
    '= = = Sub = = ='     → level 3, 'Sub'
    Returns (level, name) or (None, None) if not a heading.
    """
    tokens = line.strip().split()
    if not tokens or tokens[0] != '=':
        return None, None

    level = 0
    for t in tokens:
        if t == '=':
            level += 1
        else:
            break

    trailing = 0
    for t in reversed(tokens):
        if t == '=':
            trailing += 1
        else:
            break

    if level != trailing or level == 0:
        return None, None

    name_tokens = tokens[level: len(tokens) - trailing]
    if not name_tokens:
        return None, None

    return level, " ".join(name_tokens)


def _flush(buffer, title, section_path, chunk_index, chunks, min_tokens):
    if not buffer:
        return chunk_index
    text = _clean(" ".join(buffer))
    if _token_count(text) >= min_tokens:
        chunks.append({
            "article_title": title,
            "section_path":  section_path,
            "chunk_text":    text,
            "chunk_index":   chunk_index,
            "token_approx":  _token_count(text),
        })
        return chunk_index + 1
    return chunk_index


def _chunk_raw_text(
    raw: str,
    max_tokens: int,
    min_tokens: int,
    target_tokens: int,
) -> (List[Dict], str):
    """
    Core chunking logic — paragraph-based, shared by both WikiGraphs and essays.

    For WikiGraphs: headings are parsed and tracked as metadata (section_path)
                    but are NOT used as flush triggers anymore.
    For Essays:     no headings present, section_path stays as 'Body' throughout.

    Flush happens only when accumulated tokens exceed max_tokens.
    """
    lines         = raw.splitlines()
    title         = ""
    header_stack  = []
    chunks        = []
    buffer        = []
    buffer_tokens = 0
    chunk_index   = 0

    def get_path():
        return " / ".join(name for _, name in header_stack) or "Introduction"

    for line in lines:
        line = line.strip()
        if not line:
            continue

        level, name = _parse_heading(line)

        if level is not None:
            # ── Headings: update metadata only, do NOT flush ──────────────
            if level == 1:
                title = name
                header_stack = []
            else:
                while header_stack and header_stack[-1][0] >= level:
                    header_stack.pop()
                header_stack.append((level, name))
            continue

        para_tokens = _token_count(line)

        # Flush if adding this paragraph would exceed max_tokens
        if buffer_tokens + para_tokens > max_tokens:
            chunk_index = _flush(buffer, title, get_path(), chunk_index, chunks, min_tokens)
            buffer, buffer_tokens = [], 0

        # Paragraph itself exceeds max_tokens — split by sentence
        if para_tokens > max_tokens:
            sentences = re.split(r'(?<=[.!?])\s+', line)
            sub_buffer, sub_tokens = [], 0
            for sent in sentences:
                st = _token_count(sent)
                if sub_tokens + st > max_tokens:
                    chunk_index = _flush(sub_buffer, title, get_path(), chunk_index, chunks, min_tokens)
                    sub_buffer, sub_tokens = [], 0
                sub_buffer.append(sent)
                sub_tokens += st
            chunk_index = _flush(sub_buffer, title, get_path(), chunk_index, chunks, min_tokens)
            continue

        buffer.append(line)
        buffer_tokens += para_tokens

    _flush(buffer, title, get_path(), chunk_index, chunks, min_tokens)
    return chunks, title


def chunk_article(filepath: str) -> List[Dict]:
    """
    WikiGraphs entry point — reads from .txt file.
    Uses WIKI chunk config.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    chunks, title = _chunk_raw_text(
        raw,
        max_tokens=config.WIKI_CHUNK_MAX_TOKENS,
        min_tokens=config.WIKI_CHUNK_MIN_TOKENS,
        target_tokens=config.WIKI_CHUNK_TARGET_TOKENS,
    )
    logger.info(f"[wiki] '{title}' → {len(chunks)} chunks")
    return chunks


def chunk_article_from_text(text: str, fallback_title: str = "") -> List[Dict]:
    """
    WikiGraphs entry point — accepts raw text string directly.
    Uses WIKI chunk config.
    """
    chunks, parsed_title = _chunk_raw_text(
        text,
        max_tokens=config.WIKI_CHUNK_MAX_TOKENS,
        min_tokens=config.WIKI_CHUNK_MIN_TOKENS,
        target_tokens=config.WIKI_CHUNK_TARGET_TOKENS,
    )

    if not parsed_title and fallback_title:
        for chunk in chunks:
            chunk["article_title"] = fallback_title
        parsed_title = fallback_title

    logger.info(f"[wiki] '{parsed_title}' → {len(chunks)} chunks")
    return chunks


def chunk_essay_from_text(text: str, fallback_title: str = "") -> List[Dict]:
    """
    Essay (mine1) entry point — accepts raw text string directly.
    Uses ESSAY chunk config.

    Strips backtick wrappers that essays in the dataset sometimes have.
    section_path will be 'Body' throughout since essays have no headings.
    """
    # Strip backtick wrappers e.g. ```essay content```
    text = re.sub(r'^`{3,}|`{3,}$', '', text.strip()).strip()

    chunks, parsed_title = _chunk_raw_text(
        text,
        max_tokens=config.ESSAY_CHUNK_MAX_TOKENS,
        min_tokens=config.ESSAY_CHUNK_MIN_TOKENS,
        target_tokens=config.ESSAY_CHUNK_TARGET_TOKENS,
    )

    # Essays have no level-1 heading so always use fallback_title
    if fallback_title:
        for chunk in chunks:
            chunk["article_title"] = fallback_title

    parsed_title = fallback_title or parsed_title
    logger.info(f"[essay] '{parsed_title}' → {len(chunks)} chunks")
    return chunks