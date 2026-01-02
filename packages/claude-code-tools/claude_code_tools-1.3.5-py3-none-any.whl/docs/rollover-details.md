# How Rollover Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ROLLOVER: Continue work in fresh context while preserving full history    │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────┐
  │  aichat resume          │  ◄── User triggers rollover of session ghi789
  │  or aichat search       │
  └───────────┬─────────────┘
              │
              ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │  1. TRACE LINEAGE of ghi789                                          │
  │     Follow continue_metadata.parent_session_file pointers backwards  │
  │                                                                      │
  │     ghi789.jsonl ──► def456.jsonl ──► abc123.jsonl (original)        │
  └──────────────────────────────────────────────────────────────────────┘
              │
              ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │  2. BUILD PROMPT                                                     │
  │     • Chronological list of all ancestor session files               │
  │     • Instructions to extract context                                │
  │     • Optional: summary of work extracted by another agent           │
  └──────────────────────────────────────────────────────────────────────┘
              │
              ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │  3. CREATE NEW INTERACTIVE SESSION (jkl012)                          │
  │                                                                      │
  │     • Work summary already present in prompt, OR                     │
  │     • User can ask agent to recover specific parts of prior work     │
  │       (using session-search skill or session-searcher sub-agent)     │
  └──────────────────────────────────────────────────────────────────────┘
              │
              ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │  4. INJECT METADATA (first line of jkl012.jsonl)                     │
  │                                                                      │
  │     {                                                                │
  │       "continue_metadata": {                                         │
  │         "parent_session_file": "/path/to/ghi789.jsonl",              │
  │         "parent_session_id": "ghi789-...",                           │
  │         "continued_at": "2025-12-19T..."                             │
  │       }                                                              │
  │     }                                                                │
  └──────────────────────────────────────────────────────────────────────┘
              │
              ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │  5. RESUME INTERACTIVELY                                             │
  │     claude --resume jkl012  ◄── Fresh context, full history access   │
  └──────────────────────────────────────────────────────────────────────┘


  RESULT: Linked chain with on-demand context retrieval
  ═══════════════════════════════════════════════════════

    abc123.jsonl ◄─── def456.jsonl ◄─── ghi789.jsonl ◄─── jkl012.jsonl
    (original)        (trimmed)         (rollover)        (NEW SESSION)
         │                 │                 │                  │
         └─────────────────┴─────────────────┴──────────────────┘
         Agent can read any ancestor on demand
         (using session-search skill or session-searcher sub-agent)
```
