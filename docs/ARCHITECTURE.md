# Architecture Overview

This document describes the public, high-level architecture of the project. Implementation details that are specific to the client engagement are intentionally omitted.

## System boundaries

The complete system is organized around five boundaries:

1. **Request and interaction layer** — accepts CLI requests and Slack messages, normalizes their context, and routes interactive approvals.
2. **Agentic workflow layer** — coordinates discovery, scripting, review, avatar selection, rendering, recovery, and delivery as explicit stages.
3. **Content and timing layer** — extracts website evidence, loads transcripts, calculates narration budgets, and aligns spoken content to a video timeline.
4. **Media layer** — drives browser capture and avatar generation, then uses FFmpeg/ffprobe for normalization, composition, and validation.
5. **Persistence and delivery layer** — stores resumable job artifacts, records stage events, prevents duplicate work, and posts progress and results to Slack.

## URL explainer path

```text
Request
  -> URL discovery
  -> page evidence and browser capture
  -> reviewer page approval
  -> narration generation and quality checks
  -> reviewer script approval
  -> avatar and voice selection
  -> avatar render + B-roll capture
  -> video composition
  -> Slack delivery
```

The design separates evidence collection from narration generation. That boundary makes it possible to review what the system found before an LLM turns it into a script, reducing hallucination and improving screen-to-narration alignment.

## Screen-recording path

```text
Source recording
  -> acquisition and normalization
  -> transcript ingestion or audio transcription
  -> timestamp alignment
  -> overlay-window segmentation
  -> introduction review
  -> avatar segment rendering
  -> timeline composition
  -> Slack delivery
```

Transcript timing is treated as the source of truth when available. The pipeline retains intermediate timing and render artifacts so a failed stage can be resumed without repeating every external API call.

## Reliability patterns

- Explicit job and stage status rather than implicit filesystem assumptions
- Persisted intermediate artifacts for recovery and auditability
- Idempotency and duplicate-request protection for Slack-triggered work
- Bounded API polling and retry behavior
- Structured JSON output for machine-driven CLI calls
- Graceful mock or placeholder behavior during local development
- Human approval before costly avatar-rendering operations

## Technology profile

- Python 3.11+
- JavaScript / Node.js
- OpenClaw skills and plugin hooks
- Slack Web API and interactive workflows
- OpenAI-compatible language and transcription APIs
- HeyGen avatar-video APIs
- Playwright browser automation
- FFmpeg and ffprobe media processing
- yt-dlp source acquisition

## Public-repository scope

The public branch contains a few generic utilities that illustrate input normalization, web-content extraction, narration budgeting, and structured output. Orchestration code, client-specific logic, integration internals, tests, deployment configuration, and production artifacts are excluded.
