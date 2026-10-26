from __future__ import annotations

import json
import sys
from typing import Any


def print_explainer_json(payload: Any) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    stream = sys.stdout
    if hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    try:
        stream.write(text)
        stream.flush()
        return
    except UnicodeEncodeError:
        buffer = getattr(stream, "buffer", None)
        if buffer is None:
            raise
        buffer.write(text.encode("utf-8", errors="replace"))
        buffer.flush()
