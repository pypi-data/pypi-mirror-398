---
name: warn-claude-subprocess
enabled: true
event: bash
pattern: \bclaude\s+
action: warn
---

**Claude CLI Subprocess Warning**

Running the `claude` CLI command from a Bash subprocess will fail due to sandboxing restrictions. The Claude Agent SDK is designed to work inside the Claude Code runtime, not from external processes.

**Why this fails:**
- Subprocess lacks authentication context from parent session
- Sandbox isolation prevents LLM invocations
- Missing environment variables and tokens

**Alternatives:**
- Use the **Task tool** with appropriate `subagent_type` to spawn subagents
- Use the Anthropic API directly with `ANTHROPIC_API_KEY`
- Act as the LLM directly for developmental testing (manual workflow execution)

See: https://github.com/anthropics/claude-code/issues/5892
