from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LoadedTranscript:
    transcript_text: str = ""
    transcript_srt: str | None = None
    source: str = "none"
    warning: str = ""


def load_transcript_input(
    *,
    transcript_text: str = "",
    transcript_path: str | None = None,
    transcript_srt_path: str | None = None,
) -> LoadedTranscript:
    explicit_text = transcript_text.strip()
    explicit_path = transcript_path or transcript_srt_path
    if explicit_text:
        warning = ""
        if explicit_path:
            warning = f"Transcript file ignored because pasted transcript text was provided: {explicit_path}"
        return LoadedTranscript(transcript_text=explicit_text, source="provided_plain_transcript", warning=warning)
    if not explicit_path:
        return LoadedTranscript()
    path = Path(explicit_path)
    if not path.exists():
        raise FileNotFoundError(f"Transcript file not found: {path}")
    return load_transcript_file(path)


def load_transcript_file(path: Path) -> LoadedTranscript:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return LoadedTranscript(transcript_text=_read_text_file(path), source=f"provided_{suffix[1:]}")
    if suffix == ".srt":
        return LoadedTranscript(transcript_srt=_read_text_file(path), source="provided_srt")
    if suffix == ".vtt":
        return LoadedTranscript(transcript_srt=vtt_to_srt(_read_text_file(path)), source="provided_vtt")
    if suffix == ".json":
        return load_json_transcript(path)
    if suffix == ".docx":
        return LoadedTranscript(transcript_text=read_docx_text(path), source="provided_docx")
    if suffix == ".pdf":
        return LoadedTranscript(transcript_text=read_pdf_text(path), source="provided_pdf")
    raise ValueError(
        f"Unsupported transcript file type '{suffix or '(none)'}'. "
        "Supported transcript files: .txt, .md, .srt, .vtt, .json, .docx, .pdf."
    )


def load_json_transcript(path: Path) -> LoadedTranscript:
    payload = json.loads(_read_text_file(path))
    if isinstance(payload, dict) and str(payload.get("text") or "").strip():
        return LoadedTranscript(transcript_text=str(payload["text"]).strip(), source="provided_json_text")
    segments = payload if isinstance(payload, list) else payload.get("segments", []) if isinstance(payload, dict) else []
    if isinstance(segments, list) and segments:
        return LoadedTranscript(transcript_srt=segments_to_srt(segments), source="provided_json_segments")
    raise ValueError("Transcript JSON must contain either a non-empty 'text' field or a non-empty 'segments' list.")


def vtt_to_srt(vtt_text: str) -> str:
    cues: list[dict[str, Any]] = []
    lines = vtt_text.replace("\ufeff", "").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.upper().startswith("WEBVTT") or line.startswith(("NOTE", "STYLE", "REGION")):
            i += 1
            continue
        if "-->" not in line and i + 1 < len(lines) and "-->" in lines[i + 1]:
            i += 1
            line = lines[i].strip()
        if "-->" not in line:
            i += 1
            continue
        start_raw, end_raw = _split_vtt_timing(line)
        i += 1
        text_lines: list[str] = []
        while i < len(lines) and lines[i].strip():
            text_lines.append(lines[i].strip())
            i += 1
        cues.append({"start": _normalize_timestamp(start_raw), "end": _normalize_timestamp(end_raw), "text": " ".join(text_lines)})
    return segments_to_srt(cues)


def segments_to_srt(segments: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for index, segment in enumerate(segments, start=1):
        text = str(segment.get("text") or "").strip()
        if not text:
            continue
        start = _segment_time_to_srt(segment.get("start", segment.get("start_sec", 0.0)))
        end = _segment_time_to_srt(segment.get("end", segment.get("end_sec", segment.get("start_sec", 0.0))))
        blocks.append(f"{index}\n{start} --> {end}\n{text}")
    if not blocks:
        raise ValueError("Timestamped transcript did not contain any text segments.")
    return "\n\n".join(blocks) + "\n"


def read_docx_text(path: Path) -> str:
    try:
        from docx import Document  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("DOCX transcript support requires python-docx. Install it or provide .txt/.srt/.vtt/.json.") from exc
    document = Document(str(path))
    text = "\n".join(paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()).strip()
    if not text:
        raise ValueError(f"DOCX transcript did not contain readable text: {path}")
    return text


def read_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("PDF transcript support requires pypdf. Install it or provide .txt/.srt/.vtt/.json.") from exc
    reader = PdfReader(str(path))
    text = "\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()
    if not text:
        raise ValueError(f"PDF transcript did not contain readable text: {path}")
    return text


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig").strip()


def _split_vtt_timing(line: str) -> tuple[str, str]:
    start_raw, rest = line.split("-->", 1)
    end_raw = rest.strip().split()[0]
    return start_raw.strip(), end_raw.strip()


def _normalize_timestamp(value: str) -> str:
    value = value.replace(".", ",")
    if re.match(r"^\d{2}:\d{2},\d{3}$", value):
        return f"00:{value}"
    return value


def _segment_time_to_srt(value: Any) -> str:
    if isinstance(value, str):
        return _normalize_timestamp(value)
    seconds = max(0.0, float(value or 0.0))
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    whole_seconds = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis == 1000:
        whole_seconds += 1
        millis = 0
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{millis:03d}"
