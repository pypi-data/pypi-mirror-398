# Reddit Post: aichat resume

**Title:** Tool for continuing Claude Code sessions when context fills up

---

If you use Claude Code, you've hit this: context fills up mid-task, and your options are (a) lossy compaction that throws away information, or (b) start fresh and lose the conversation history.

I built `aichat resume` to handle this. When you're running low on context:

1. Type `>resume` in your session
2. Quit Claude Code
3. Run `aichat resume` (session ID is already in clipboard)
4. Pick a strategy: trim large tool outputs, smart-trim with AI analysis, or rollover to fresh session

The key thing: nothing gets lost. All strategies keep pointers to parent sessions, so the agent can look up prior work when needed. You get a chain of linked sessions instead of losing context.

Quick demo of the `>resume` trigger: [video in README]

Install:
```
uv tool install claude-code-tools
claude plugin marketplace add pchalasani/claude-code-tools
claude plugin install "aichat@cctools-plugins"
```

Repo: https://github.com/pchalasani/claude-code-tools

Works with Codex too. Feedback welcome.
