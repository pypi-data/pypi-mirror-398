# Made a tool that lets Claude Code control terminal apps - thought some of you might find it useful

Hey everyone! I've been using Claude Code a lot lately and kept running into the same frustration - it couldn't interact with CLI applications that need user input. So I built something to fix that.

## What it does

It's basically like Playwright/Puppeteer but for the terminal. Claude Code can now:
- Run interactive scripts and respond to prompts
- Use debuggers like pdb to step through code
- Launch and control other CLI apps
- Even spin up another Claude Code instance to have it work as a sub-agent -- 
  and unlike the built-in sub-agents, you can clearly see what's going on.

[GIF PLACEHOLDER - Shows tmux-cli in action]

## How it works

The magic happens through tmux (terminal multiplexer). I created a tool called `tmux-cli` that gives Claude Code the ability to:
- Launch apps in separate tmux panes
- Send keystrokes to them
- Capture their output
- Wait for them to idle

You don't need to know tmux commands - Claude Code handles everything. Just tell it what you want and it figures out the tmux stuff.

## Real use cases I've found helpful

- **Debugging**: Claude can now use pdb to step through Python code, examine variables, and help me understand program flow
- **Testing interactive scripts**: No more manually entering test inputs - Claude handles it
- **Spawn other Claudes**: I can have Claude launch another Claude instance to work on
  a task and interact with it. And unlike the built-in sub-agents, it's fully visible.

## Getting it

If you want to try it:

```bash
# Install from PyPI
uv tool install claude-code-tools

# Or get latest from GitHub
uv tool install git+https://github.com/pchalasani/claude-code-tools
```

Then add a snippet to your `~/.claude/CLAUDE.md` to let Claude Code know about tmux-cli.

The repo also includes some other tools like encrypted .env backup and a Claude session finder, but tmux-cli is the main thing I wanted to share.

## Not trying to oversell

This isn't revolutionary or anything - it's just a practical tool that solved a real problem I kept hitting. If you work with Claude Code and interactive CLIs, you might find it useful too.

Happy to answer questions or hear if anyone has similar tools they've built!

Repo: https://github.com/pchalasani/claude-code-tools