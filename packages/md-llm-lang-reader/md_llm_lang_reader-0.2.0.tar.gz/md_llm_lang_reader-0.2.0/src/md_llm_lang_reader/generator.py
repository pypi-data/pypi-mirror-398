import re
import html
import json
import os
import sys
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

import multiai


def extract_json_array(raw: str) -> str:
    """
    Extract the outermost JSON array if the model adds extra text.
    If it still fails, return the raw string (json.loads will fail).
    """
    s = raw.strip()

    if s.startswith("[") and s.endswith("]"):
        return s

    i = s.find("[")
    j = s.rfind("]")
    if i != -1 and j != -1 and j > i:
        return s[i: j + 1]

    m = re.search(r"(\[\s*\{.*\}\s*\])", s, flags=re.S)
    if m:
        return m.group(1)

    return s


def split_and_translate(paragraph: str, src: str, tgt: str, client: "multiai.Prompt") -> List[Dict[str, str]]:
    """
    Ask the model to split a paragraph into sentences and translate each.
    Retries up to 3 times if JSON parsing fails. Conversation history is kept.
    """
    first_prompt = f"""You are given a paragraph in {src}.

Task:
1) Split it into natural sentences.
   - Do NOT split on abbreviations (e.g., "Mr.", "Dr.", "etc.") or numbered list markers like "1." unless it is truly the end of a sentence.
2) For each sentence, provide a direct translation into {tgt}.

Output:
Return ONLY valid JSON (no markdown, no commentary).
The JSON must be an array of objects with exactly these keys:
- "src": the original sentence in {src}
- "tgt": its translation in {tgt}

Paragraph:
{paragraph}
"""

    raw_last = ""
    for attempt in range(1, 4):
        prompt = first_prompt if attempt == 1 else (
            "The JSON you returned could not be parsed by json.loads(). "
            "Please resend ONLY valid JSON (no markdown, no commentary), "
            'matching exactly the required schema: an array of objects with keys "src" and "tgt".'
        )

        raw = client.ask(prompt)
        raw_last = raw.strip()

        candidate = extract_json_array(raw_last)
        try:
            data = json.loads(candidate)
        except Exception:
            continue

        if not isinstance(data, list):
            continue

        out: List[Dict[str, str]] = []
        ok = True
        for item in data:
            if not isinstance(item, dict):
                ok = False
                break
            s = (item.get("src") or "").strip()
            t = (item.get("tgt") or "").strip()
            if not s or not t:
                ok = False
                break
            out.append({"src": s, "tgt": t})

        if ok and out:
            return out

    raise ValueError(
        "Could not parse valid JSON after 3 attempts. Raw output follows:\n\n" + raw_last
    )


def is_fence_line(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith("```") or stripped.startswith("~~~")


def fence_delim(line: str) -> str:
    stripped = line.lstrip()
    if stripped.startswith("```"):
        return "```"
    if stripped.startswith("~~~"):
        return "~~~"
    return ""


def paragraph_preview(paragraph: str, words: int = 5) -> str:
    toks = paragraph.split()
    if len(toks) <= words:
        return " ".join(toks)
    return " ".join(toks[:words]) + " ..."


def parse_frontmatter(lines: List[str]) -> Tuple[Dict[str, str], List[str]]:
    """
    Parse YAML-like frontmatter from the beginning of the lines.
    Returns a dictionary of metadata and the remaining lines.
    """
    if not lines or not lines[0].strip() == "---":
        return {}, lines

    metadata = {}
    content_start_idx = 0
    
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            content_start_idx = i + 1
            break
        
        parts = line.split(":", 1)
        if len(parts) == 2:
            key = parts[0].strip()
            value = parts[1].strip()
            metadata[key] = value
    
    if content_start_idx == 0:
        return {}, lines

    return metadata, lines[content_start_idx:]


def render_markdown_links(text: str) -> str:
    """
    Simple converter for Markdown links [text](url) to HTML <a> tags.
    """
    escaped = html.escape(text)
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    return re.sub(pattern, r'<a href="\2">\1</a>', escaped)


def extract_last_processed_line(path: str) -> int:
    """
    Reads the existing HTML file and finds the last processed line number
    stored in the comments <!-- processed_line: N -->.
    Returns -1 if not found or file does not exist.
    """
    if not os.path.exists(path):
        return -1
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        matches = re.findall(r'<!-- processed_line: (\d+) -->', content)
        if matches:
            return int(matches[-1])
    except Exception:
        pass
        
    return -1


@dataclass
class Options:
    input_path: str
    output_path: str
    src: str
    tgt: str
    provider: str
    model: str
    verbose: int = 1
    js_url: str = ""
    css_url: str = ""
    resume: bool = False


def generate_file(opts: Options) -> None:
    """
    Generate the HTML and write it to opts.output_path incrementally.
    """
    
    # 1. Setup Input
    with open(opts.input_path, encoding="utf-8") as f:
        all_lines = f.readlines()

    metadata, lines = parse_frontmatter(all_lines)
    description = metadata.get("description", "")
    
    # 2. Setup State for Resume
    start_line_index = 0
    initial_content = ""
    
    if opts.resume and os.path.exists(opts.output_path):
        last_processed = extract_last_processed_line(opts.output_path)
        
        if last_processed == -1:
            # Check if the file is already completed (markers were removed)
            try:
                with open(opts.output_path, "r", encoding="utf-8") as f:
                    content_check = f.read()
                if "</html>" in content_check:
                    print("Nothing to continue.")
                    return
            except Exception:
                pass
            # If not completed and no markers, start from beginning (or it's a new file)
        
        if last_processed >= 0:
            if opts.verbose >= 1:
                print(f"Resuming from line {last_processed + 1}...")
            start_line_index = last_processed + 1
            
            with open(opts.output_path, "r", encoding="utf-8") as f:
                initial_content = f.read()
            
            # Remove closing tags and potential footer if resuming
            initial_content = initial_content.replace("</body></html>", "")
            footer_marker = '<div class="footer">'
            if footer_marker in initial_content:
                idx = initial_content.rfind(footer_marker)
                if idx != -1:
                    initial_content = initial_content[:idx]

    # 3. Setup LLM Client
    client = multiai.Prompt()
    client.set_model(opts.provider, opts.model)

    # 4. Logging Helpers
    def log_heading(line: str):
        if opts.verbose >= 1:
            print(line)

    def log_paragraph(paragraph: str):
        if opts.verbose == 2:
            print(paragraph_preview(paragraph))
        elif opts.verbose == 3:
            print(paragraph)

    # 5. Open Output File for Writing
    f_out = open(opts.output_path, "w", encoding="utf-8")
    
    try:
        if start_line_index == 0:
            # Write Header
            f_out.write(f"""<!DOCTYPE html>
<html lang="{html.escape(opts.src)}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(opts.output_path)}</title>
<link rel="stylesheet" href="{opts.css_url}">
<script src="{opts.js_url}"></script>
</head>
<body>
""")
            if description:
                desc_html = render_markdown_links(description)
                f_out.write(f'<div class="description">{desc_html}</div>\n')
        else:
            # Write existing content
            f_out.write(initial_content)

        buffer: List[str] = []
        in_code_block = False
        fence = ""
        code_lines: List[str] = []
        
        def write_chunk(chunk: str, line_idx: int):
            """Write a chunk of HTML and flush to disk."""
            f_out.write(chunk)
            f_out.write(f"\n<!-- processed_line: {line_idx} -->\n")
            f_out.flush()
            os.fsync(f_out.fileno())

        def flush_code_block(line_idx: int):
            if not code_lines:
                return
            code_text = "\n".join(code_lines)
            code_lines.clear()
            chunk = "<pre><code>" + html.escape(code_text) + "</code></pre>"
            write_chunk(chunk, line_idx)

        def flush_paragraph(line_idx: int):
            if not buffer:
                return
            paragraph = " ".join(buffer).strip()
            buffer.clear()
            if not paragraph:
                return

            log_paragraph(paragraph)
            
            try:
                pairs = split_and_translate(paragraph, opts.src, opts.tgt, client)
            except Exception as e:
                raise e

            chunk_parts = []
            for p in pairs:
                src_sent = p["src"]
                tgt_sent = p["tgt"]

                esc_src = html.escape(src_sent)
                esc_tgt = html.escape(tgt_sent)

                data_speak = html.escape(src_sent, quote=True)
                data_lang = html.escape(opts.src, quote=True)

                chunk_parts.append('<div class="src">')
                chunk_parts.append(
                    f'{esc_src} <button class="speak-btn" type="button" data-speak="{data_speak}" data-lang="{data_lang}">🔊</button>'
                )
                chunk_parts.append("</div>")
                chunk_parts.append(f'<div class="tgt">{esc_tgt}</div>')
            
            write_chunk("\n".join(chunk_parts), line_idx)

        # Iterate over the content lines
        for i, raw_line in enumerate(lines):
            if i < start_line_index:
                continue

            line = raw_line.rstrip("\n")

            if is_fence_line(line):
                if not in_code_block:
                    flush_paragraph(i - 1)
                    in_code_block = True
                    fence = fence_delim(line)
                    continue
                else:
                    if fence and line.lstrip().startswith(fence):
                        in_code_block = False
                        fence = ""
                        flush_code_block(i)
                        continue
                    code_lines.append(line)
                    continue

            if in_code_block:
                code_lines.append(line)
                continue

            stripped = line.rstrip()

            if stripped.startswith("# "):
                flush_paragraph(i - 1)
                chunk = f"<h1>{html.escape(stripped[2:])}</h1>"
                write_chunk(chunk, i)
                log_heading(stripped)
            elif stripped.startswith("## "):
                flush_paragraph(i - 1)
                chunk = f"<h2>{html.escape(stripped[3:])}</h2>"
                write_chunk(chunk, i)
                log_heading(stripped)
            elif stripped.startswith("### "):
                flush_paragraph(i - 1)
                chunk = f"<h3>{html.escape(stripped[4:])}</h3>"
                write_chunk(chunk, i)
                log_heading(stripped)
            elif stripped.startswith("#### "):
                flush_paragraph(i - 1)
                chunk = f"<h4>{html.escape(stripped[5:])}</h4>"
                write_chunk(chunk, i)
                log_heading(stripped)
            elif stripped.strip() == "":
                flush_paragraph(i)
            else:
                buffer.append(stripped.strip())

        # End of loop
        last_idx = len(lines) - 1
        if in_code_block:
            in_code_block = False
            flush_code_block(last_idx)

        flush_paragraph(last_idx)

        f_out.write('\n<div class="footer">Translated with LLM and HTML created by <a href="https://sekika.github.io/langreader/">langreader</a>.</div>')
        f_out.write("\n</body></html>")

    finally:
        f_out.close()

    # 6. Cleanup Markers (only if successfully finished)
    # If the process crashed, we haven't reached here, so markers remain for resume.
    if opts.verbose >= 1:
        print("Cleaning up intermediate markers...")

    with open(opts.output_path, "r", encoding="utf-8") as f:
        final_content = f.read()

    # Remove the processing markers using regex
    # Matches "\n<!-- processed_line: 123 -->" and replaces with empty string (or simple newline adjustment)
    # To keep the spacing clean, we replace the marker line (including the newline before it) with nothing
    # or handle the newline logic carefully.
    # write_chunk adds: \n<!-- ... -->\n
    # So we remove `\n<!-- processed_line: \d+ -->` to leave the trailing \n for separation.
    final_content = re.sub(r'\n<!-- processed_line: \d+ -->', '', final_content)

    with open(opts.output_path, "w", encoding="utf-8") as f:
        f.write(final_content)
