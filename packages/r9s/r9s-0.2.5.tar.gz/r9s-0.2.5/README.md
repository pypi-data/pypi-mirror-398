# r9s

The official Python library for the r9s API

## Quick start

Install:

```bash
pip install r9s
```

Or directly execute the CLI:

```bash
uvx r9s
```

### Configure Claude Code with r9s

1. Get an r9s API key and (optionally) set:

   ```bash
   export r9s_API_KEY="your_api_key"
   export r9s_BASE_URL="https://api.r9s.ai"
   ```

2. Run the setup command and follow the prompts:

   ```bash
   r9s set claude-code
   ```

   This updates `~/.claude/settings.json` and keeps a backup under `~/.r9s/backup/claude-code/`.

3. To restore the previous config:

   ```bash
   r9s reset claude-code
   ```

For advanced usage and development details, see `docs/cli-dev-guide.md`.
