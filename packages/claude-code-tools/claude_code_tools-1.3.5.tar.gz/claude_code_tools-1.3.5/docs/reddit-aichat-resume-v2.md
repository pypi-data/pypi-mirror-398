# Reddit Post: aichat resume (v2)

**Title:** I don't compact my Claude Code sessions. I chain them.

---

Compaction throws away context. I'd rather keep everything and let the 
agent retrieve it when needed.

**Core principles:**

- **Lossless** — compaction summarizes and discards; I want nothing lost
- **Searchable** — sessions must be full-text searchable, fast (Claude Code's 
  built-in search only matches titles)
- **Fast** — 50+ sessions in a lineage, thousands of lines each — grep doesn't 
  scale, so I built a Tantivy-indexed Rust CLI that returns results in ms
- **Portable** — hand off between agents: start in Claude Code, continue in 
  Codex CLI, or vice versa

**The problem with compaction:**

When you hit context limits, Claude Code's default is to compact — 
summarize and discard. But summaries lose nuance. That debugging session 
where you finally figured out the race condition? Gone. The architectural 
decision you made three hours ago? Flattened into a sentence.

**My approach: session chaining**

Instead of compacting, I chain sessions together:

1. When context fills up, type `>resume`
2. Pick a strategy (trim, smart-trim, or rollover)
3. Start fresh — but with full lineage back to every ancestor session

Nothing gets deleted. The agent traces back and pulls context on demand.

**Three resume strategies:**

| Strategy | What it does | When to use |
|----------|--------------|-------------|
| **Trim** | Truncates bloated tool outputs and early messages | Quick fix, frees 30-50% |
| **Smart trim** | AI decides what's safe to cut | When you want surgical precision |
| **Rollover** | Fresh session with lineage pointers | Clean slate, full history preserved |

**Why Rust + Tantivy?**

Session chains get long. You might have 50+ sessions in a lineage, each with 
thousands of lines of conversation. Grepping through JSON files doesn't scale. 
So I built `aichat-search` — a Rust CLI using Tantivy (the engine behind 
Quickwit and other search tools). It indexes sessions on first run, then 
returns results in milliseconds. The agent can search your entire history 
without you waiting.

**What you get:**

- Fast full-text search across all sessions (Tantivy-indexed, not grep)
- `/recover-context` command — agent pulls context from parent sessions
- Session-searcher sub-agent — searches history without polluting your context
- Cross-agent handoff — start in Claude Code, continue in Codex CLI, or vice versa

**Quick demo:** [video in README]

**Install:**

```bash
# Install the CLI tools
uv tool install claude-code-tools
brew install pchalasani/tap/aichat-search  # or: cargo install aichat-search

# Add the plugin
claude plugin marketplace add pchalasani/claude-code-tools
claude plugin install "aichat@cctools-plugins"
```

Repo: https://github.com/pchalasani/claude-code-tools

---

Curious how others handle context limits. Do you compact and hope for the 
best, or have you built something similar?
