
## FMOD TCP Response Format

FMOD Studio's TCP command interface returns responses in a wrapped format that includes both log output and structured JSON:

```
log(): <log messages>
\0out(): {"ok": true, "result": ...}

\0
```

Key characteristics:
- `log():` lines contain human-readable log messages
- `out():` lines contain the actual JSON response payload
- Response is terminated by null bytes (`\0`)
- May contain multiple newlines between sections

Parsing strategy:
1. Use regex `out\(\):\s*(\{.*\})` with `re.DOTALL` flag to extract JSON after `out(): `
2. If regex fails, fall back to parsing the entire stripped response
3. Handle JSON decode errors by returning `{"ok": false, "error": "..."}`

This format requires specialized parsing rather than direct `json.loads()` on the raw response.
