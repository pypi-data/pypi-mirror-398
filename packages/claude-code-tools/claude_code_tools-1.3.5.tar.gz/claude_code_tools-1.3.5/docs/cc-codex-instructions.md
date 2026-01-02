# Codex MCP Tool Usage in Claude Code

## Required Parameters

When using the `mcp__gpt-codex__codex` tool in Claude Code, always include these parameters to ensure proper functionality:

```json
{
  "prompt": "your prompt here",
  "sandbox": "workspace-write",
  "approval-policy": "never",
  "include-plan-tool": false
}
```

## Parameter Explanation

- **`sandbox`**: Set to `"workspace-write"` to allow file modifications in the project
- **`approval-policy`**: Set to `"never"` to avoid approval prompts that block execution
- **`include-plan-tool`**: Set to `false` for Claude Code compatibility (prevents response format issues)

## Example Usage

```python
mcp__gpt-codex__codex(
    prompt="Analyze this codebase and suggest optimizations",
    sandbox="workspace-write",
    approval-policy="never",
    include-plan-tool=false
)
```

## Notes

- These overrides are necessary when `include_plan_tool = true` in the global config
- Without `include-plan-tool: false`, responses may not display properly in Claude Code
- The `approval-policy: "never"` prevents the tool from waiting for user approval