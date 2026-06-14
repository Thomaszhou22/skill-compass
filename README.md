# 🧭 Skill Compass

Audit and fix agent skill descriptions so they trigger reliably. Works with OpenClaw, Claude Code, and any agentskills.io-compatible platform.

## Install

```bash
# ClawHub
clawhub install skill-compass-guardian

# Or from source
git clone https://github.com/Thomaszhou22/skill-compass.git
cp -r skill-compass ~/.openclaw/skills/
```

## Quick Start

```bash
# Scan all skills in default directories
python3 scripts/audit_skills.py

# Scan a specific directory
python3 scripts/audit_skills.py --skills-dir ~/.claude/skills

# Auto-fix common issues (YAML colons, missing triggers)
python3 scripts/audit_skills.py --fix

# Generate an AI-ready prompt to rewrite bad descriptions
python3 scripts/audit_skills.py --suggest

# JSON output for CI/CD
python3 scripts/audit_skills.py --json
```

### What the audit tells you

```
🧭  SKILL COMPASS — AUDIT REPORT

📂 Directory: ~/.openclaw/skills
📊 Total skills: 18
⚠️  Issues found: 11

📈 Score Summary:
   Average score: 81/100
   ✅ Passing (≥70): 12
   ⚠️  Needs work (<70): 6
   🔴 Critical (<30): 0

⚠️  multi-search-engine — Score: 50/100
   • NO_TRIGGER: Missing trigger condition
   • WEAK_LANG: Uses passive language instead of directive
   💡 Add trigger phrases: "Use when...", "Invoke when..."

✅ powerpoint-pptx — Score: 100/100
```

Each skill gets a score 0–100 based on:
- **Trigger condition** — does the description say *when* to use it?
- **YAML validity** — does frontmatter parse correctly?
- **Token budget** — is total description length within limits?
- **Conflict detection** — do descriptions overlap with other skills?

## How It Works

Most skill triggering failures come down to one thing: **the description doesn't tell the agent when to fire.**

The workflow is two steps:

**Step 1 — Audit.** Run the script, get a report telling you which skills have problems and what kind.

**Step 2 — Fix.** Some fixes are automatic (`--fix` flag), others need human judgment:

| Fix type | Who does it | Example |
|----------|-------------|--------|
| YAML syntax errors | Script auto-fixes | Missing quotes around colons |
| Description too long | Script auto-fixes | Truncates to token budget |
| Missing trigger condition | `--suggest` generates a prompt | `"Helps with weather"` → `"Use when user asks about weather, temperature, or forecasts"` |
| Weak/passive language | `--suggest` generates a prompt | `"Can assist with..."` → `"ALWAYS invoke when..."` |

The key insight: description quality is the #1 factor in trigger reliability. Directive descriptions ("Use when...") achieve ~100% activation, while passive ones ("Helps with...") only ~37%.

For the full diagnostic workflow, see [`SKILL.md`](SKILL.md). For documented failure patterns with real cases, see [`references/failure-patterns.md`](references/failure-patterns.md).

## Files

```
skill-compass/
├── SKILL.md                        # Diagnostic workflow + fix guide
├── scripts/
│   └── audit_skills.py             # Automated scanner (Python 3, no deps)
├── references/
│   └── failure-patterns.md         # 6 failure patterns with fixes
└── README.md
```

## Compatibility

- ✅ OpenClaw
- ✅ Claude Code
- ✅ Cursor, Codex CLI, Gemini CLI (anything using SKILL.md)
- ✅ Any platform following the [agentskills.io](https://agentskills.io) standard

## License

MIT-0 — Free to use, modify, and distribute. No attribution required.
