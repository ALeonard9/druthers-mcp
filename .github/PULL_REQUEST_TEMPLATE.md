## Summary

<!--
Bullets. Lead with the cause, then the fix — not a changelog of files touched.
Say what does NOT change if that's load-bearing.
-->

-

## Test plan

<!--
Checked boxes with real evidence: actual pass counts, the specific cases added,
and what you exercised through the MCP Inspector against the local API.
-->

- [ ] `task test` — N passed, including <the new cases>
- [ ] `task lint` clean
- [ ] Exercised via MCP Inspector (`task dev`) against the local API: <tool called, result>

## Checklist

- [ ] Branch named `feat/…`, `fix/…`, or `chore/…`
- [ ] New tool has a test in `tests/server_test.py`, patterned on its nearest sibling (see AGENTS.md → Testing)
- [ ] Per-domain change checked against the other three domains (movies/TV/books/games)
- [ ] CI green (lint + tests)
- [ ] No secrets committed
- [ ] README tool table updated if the tool surface changed

<!--
Closing issues: repeat the keyword for EVERY issue. The comma form
("Closes #a, #b") silently closes only the first one.
Closes #a. Closes #b.
-->
