#!/usr/bin/env python3
"""
Skill Compass - Audit Script
Scans skill directories for triggering issues and outputs a diagnostic report.
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# YAML frontmatter pattern
FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
NAME_RE = re.compile(r'^name:\s*(.+)$', re.MULTILINE)
DESC_RE = re.compile(r'^description:\s*(.+?)(?=\n[a-z_]+:|\n---|\Z)', re.MULTILINE | re.DOTALL)

# Trigger phrase indicators
TRIGGER_PHRASES = [
    "use when", "invoke when", "always invoke", "use for", "trigger",
    "activate when", "run when", "always use", "do not use for",
    "do not use when", "not for"
]

# Directive language indicators
DIRECTIVE_WORDS = [
    "always", "must", "never", "do not", "ensure", "require",
    "invoke", "activate", "trigger", "load this"
]

# Vague/non-triggering language
WEAK_PHRASES = [
    "helps with", "this skill provides", "this skill is for",
    "can be used", "supports", "enables", "allows you to"
]

# Common skill directories to check
DEFAULT_SKILL_DIRS = [
    os.path.expanduser("~/.openclaw/skills"),
    os.path.expanduser("~/.openclaw/workspace/skills"),
    os.path.expanduser("~/.agents/skills"),
    os.path.expanduser("~/.openclaw/.agents/skills"),
]

# Token budget threshold (chars)
TOKEN_BUDGET_WARN = 20000
TOKEN_BUDGET_CRITICAL = 30000

# Description length thresholds
DESC_MIN_CHARS = 30
DESC_MAX_CHARS = 350  # ideal is <150 for core trigger, but total can be longer


def parse_frontmatter(content: str) -> Tuple[Optional[Dict], str]:
    """Extract YAML frontmatter from SKILL.md content."""
    match = FRONTMATTER_RE.match(content)
    if not match:
        return None, content
    
    fm_text = match.group(1)
    body = content[match.end():]
    
    # Parse name
    name_match = NAME_RE.search(fm_text)
    name = name_match.group(1).strip().strip('"\'') if name_match else None
    
    # Parse description (may span multiple lines until next key or ---)
    desc_match = DESC_RE.search(fm_text)
    desc = desc_match.group(1).strip().strip('"\'') if desc_match else None
    
    # Check for unquoted colons in description
    colon_issue = False
    if desc:
        # Re-check raw line for unquoted colon issues
        for line in fm_text.split('\n'):
            if line.strip().startswith('description:'):
                val = line.split('description:', 1)[1].strip()
                if ':' in val and not (val.startswith('"') or val.startswith("'")):
                    colon_issue = True
                break
    
    return {
        'name': name,
        'description': desc,
        'colon_issue': colon_issue,
        'raw_frontmatter': fm_text,
    }, body


def score_description(desc: str, name: str) -> Dict:
    """Score a description for trigger quality. Returns score (0-100) and issues."""
    if not desc:
        return {
            'score': 0,
            'issues': ['CRITICAL: No description found'],
            'suggestions': ['Add a description with trigger conditions']
        }
    
    issues = []
    suggestions = []
    score = 100
    desc_lower = desc.lower()
    
    # Check length
    if len(desc) < DESC_MIN_CHARS:
        score -= 30
        issues.append(f'SHORT: Description is only {len(desc)} chars (min {DESC_MIN_CHARS})')
        suggestions.append('Expand to include specific trigger conditions and keywords')
    
    if len(desc) > DESC_MAX_CHARS:
        score -= 15
        issues.append(f'LONG: Description is {len(desc)} chars (max {DESC_MAX_CHARS})')
        suggestions.append('Move detail to SKILL.md body, keep frontmatter concise')
    
    # Check for trigger phrases
    has_trigger = any(p in desc_lower for p in TRIGGER_PHRASES)
    if not has_trigger:
        score -= 35
        issues.append('NO_TRIGGER: Missing trigger condition (no "Use when..." or similar)')
        suggestions.append('Add trigger phrases: "Use when...", "Invoke when...", "ALWAYS use for..."')
    
    # Check for weak language
    has_weak = any(p in desc_lower for p in WEAK_PHRASES)
    if has_weak:
        score -= 15
        issues.append('WEAK_LANG: Uses passive language instead of directive')
        suggestions.append('Replace "Helps with..." with "ALWAYS invoke when..."')
    
    # Check for directive language
    has_directive = any(w in desc_lower for w in DIRECTIVE_WORDS)
    if has_directive:
        score += 5  # bonus, capped at 100
    
    # Check for negative constraints
    has_negative = any(p in desc_lower for p in ['do not use', 'not for', 'do not invoke'])
    if not has_negative:
        score -= 5
        suggestions.append('Consider adding "Do NOT use for..." to prevent false triggers')
    
    # Check for keywords/trigger vocabulary
    word_count = len(desc.split())
    if word_count < 10:
        score -= 10
        issues.append('FEW_KEYWORDS: Description too short for good keyword matching')
    
    score = max(0, min(100, score))
    
    return {
        'score': score,
        'issues': issues,
        'suggestions': suggestions,
    }


def find_skill_dirs(search_paths: List[str]) -> List[Path]:
    """Find all skill directories containing SKILL.md files."""
    skill_files = []
    for base in search_paths:
        if not os.path.isdir(base):
            continue
        for root, dirs, files in os.walk(base):
            # Skip hidden directories and node_modules
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
            if 'SKILL.md' in files:
                skill_files.append(Path(root) / 'SKILL.md')
    return skill_files


def detect_conflicts(skills: List[Dict]) -> List[Dict]:
    """Detect description conflicts/overlaps between skills."""
    conflicts = []
    
    for i, s1 in enumerate(skills):
        for s2 in skills[i+1:]:
            if not s1.get('description') or not s2.get('description'):
                continue
            
            d1 = set(s1['description'].lower().split())
            d2 = set(s2['description'].lower().split())
            
            if not d1 or not d2:
                continue
            
            # Jaccard similarity
            overlap = len(d1 & d2) / len(d1 | d2)
            
            if overlap > 0.4:
                conflicts.append({
                    'skill_a': s1.get('name', 'unknown'),
                    'skill_b': s2.get('name', 'unknown'),
                    'overlap': f'{overlap:.0%}',
                    'shared_keywords': sorted(d1 & d2)[:10],
                    'severity': 'HIGH' if overlap > 0.6 else 'MEDIUM',
                    'suggestion': f'Add negative constraints to distinguish {s1.get("name")} from {s2.get("name")}',
                })
    
    return conflicts


def audit_skills(skills_dir: str, auto_fix: bool = False) -> Dict:
    """Audit all skills in a directory."""
    report = {
        'skills_dir': skills_dir,
        'total_skills': 0,
        'issues_found': 0,
        'skills': [],
        'conflicts': [],
        'token_budget': {'total_chars': 0, 'status': 'OK'},
        'summary': {},
    }
    
    # Find skill files
    if os.path.isdir(skills_dir):
        search_paths = [skills_dir]
    else:
        search_paths = DEFAULT_SKILL_DIRS
    
    skill_files = find_skill_dirs(search_paths)
    report['total_skills'] = len(skill_files)
    
    if not skill_files:
        report['error'] = f'No SKILL.md files found in {search_paths}'
        return report
    
    total_desc_chars = 0
    
    for sf in skill_files:
        try:
            content = sf.read_text(encoding='utf-8')
        except Exception as e:
            report['skills'].append({
                'path': str(sf),
                'error': f'Cannot read file: {e}',
                'score': 0,
            })
            report['issues_found'] += 1
            continue
        
        fm, body = parse_frontmatter(content)
        
        if fm is None:
            report['skills'].append({
                'path': str(sf),
                'error': 'No YAML frontmatter found',
                'score': 0,
                'issues': ['CRITICAL: Missing YAML frontmatter (--- ... ---)'],
                'suggestions': ['Add frontmatter with name: and description: fields'],
            })
            report['issues_found'] += 1
            continue
        
        skill_info = {
            'path': str(sf),
            'name': fm['name'] or 'MISSING',
            'description_length': len(fm['description'] or ''),
        }
        
        if fm['colon_issue']:
            skill_info['issues'] = ['YAML: Colon in description may break parsing']
            skill_info['auto_fix'] = 'Wrap description in quotes'
            report['issues_found'] += 1
            
            if auto_fix:
                fixed = auto_fix_colon(content)
                if fixed:
                    sf.write_text(fixed)
                    skill_info['fixed'] = True
        
        score_result = score_description(fm['description'] or '', fm['name'] or '')
        skill_info.update(score_result)
        
        if score_result['issues']:
            report['issues_found'] += len(score_result['issues'])
        
        if fm['description']:
            total_desc_chars += len(fm['description'])
        
        report['skills'].append(skill_info)
    
    # Token budget analysis
    report['token_budget']['total_chars'] = total_desc_chars
    if total_desc_chars > TOKEN_BUDGET_CRITICAL:
        report['token_budget']['status'] = 'CRITICAL'
        report['token_budget']['message'] = f'{total_desc_chars} chars exceeds critical threshold. Skills may be silently dropped.'
    elif total_desc_chars > TOKEN_BUDGET_WARN:
        report['token_budget']['status'] = 'WARNING'
        report['token_budget']['message'] = f'{total_desc_chars} chars approaching budget limit.'
    
    # Conflict detection
    report['conflicts'] = detect_conflicts(report['skills'])
    
    # Summary
    scores = [s.get('score', 0) for s in report['skills']]
    report['summary'] = {
        'avg_score': sum(scores) / len(scores) if scores else 0,
        'passing': sum(1 for s in scores if s >= 70),
        'failing': sum(1 for s in scores if s < 70),
        'critical': sum(1 for s in scores if s < 30),
    }
    
    return report


def auto_fix_colon(content: str) -> Optional[str]:
    """Fix unquoted colons in YAML description field."""
    lines = content.split('\n')
    fixed = False
    for i, line in enumerate(lines):
        if line.strip().startswith('description:'):
            val = line.split('description:', 1)[1].strip()
            if ':' in val and not val.startswith('"') and not val.startswith("'"):
                lines[i] = f'description: "{val}"'
                fixed = True
            break
    return '\n'.join(lines) if fixed else None


BACKUP_DIR = os.path.expanduser("~/.skill-compass-backups")


def create_backup(skills_dir: str) -> Optional[str]:
    """Backup all SKILL.md files before modifying. Returns backup path or None."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, timestamp)
    
    skill_files = find_skill_dirs([skills_dir])
    if not skill_files:
        return None
    
    os.makedirs(backup_path, exist_ok=True)
    count = 0
    for sf in skill_files:
        skill_dir = sf.parent
        rel_path = skill_dir.relative_to(skills_dir) if os.path.isdir(skills_dir) else Path(skill_dir.name)
        dest_dir = backup_path / rel_path
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / "SKILL.md"
        try:
            dest_file.write_text(sf.read_text(encoding='utf-8'), encoding='utf-8')
            count += 1
        except Exception:
            pass
    
    if count == 0:
        return None
    
    # Write metadata
    meta_file = os.path.join(backup_path, "_backup_info.txt")
    with open(meta_file, 'w') as f:
        f.write(f"timestamp: {timestamp}\n")
        f.write(f"skills_dir: {skills_dir}\n")
        f.write(f"files_backed_up: {count}\n")
    
    return backup_path


def list_backups() -> list:
    """List available backups, newest first."""
    if not os.path.isdir(BACKUP_DIR):
        return []
    backups = []
    for name in sorted(os.listdir(BACKUP_DIR), reverse=True):
        meta = os.path.join(BACKUP_DIR, name, "_backup_info.txt")
        info = {}
        if os.path.isfile(meta):
            for line in open(meta):
                if ':' in line:
                    k, v = line.strip().split(':', 1)
                    info[k.strip()] = v.strip()
        backups.append({
            'id': name,
            'path': os.path.join(BACKUP_DIR, name),
            'files': info.get('files_backed_up', '?'),
            'skills_dir': info.get('skills_dir', '?'),
        })
    return backups


def rollback(skills_dir: str, backup_id: Optional[str] = None) -> bool:
    """Restore SKILL.md files from a backup. Uses latest if backup_id is None."""
    backups = list_backups()
    if not backups:
        return False
    
    if backup_id:
        target = next((b for b in backups if b['id'] == backup_id), None)
        if not target:
            return False
    else:
        target = backups[0]
    
    backup_path = target['path']
    restored = 0
    for root, dirs, files in os.walk(backup_path):
        if 'SKILL.md' in files:
            rel = os.path.relpath(root, backup_path)
            dest_dir = os.path.join(skills_dir, rel) if rel != '.' else skills_dir
            dest_file = os.path.join(dest_dir, 'SKILL.md')
            src_file = os.path.join(root, 'SKILL.md')
            try:
                os.makedirs(dest_dir, exist_ok=True)
                with open(src_file, 'r') as f:
                    content = f.read()
                with open(dest_file, 'w') as f:
                    f.write(content)
                restored += 1
            except Exception:
                pass
    
    target['restored'] = restored
    return restored > 0


def print_report(report: Dict, json_output: bool = False):
    """Print the audit report."""
    if json_output:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return
    
    print("=" * 70)
    print("🛡️  SKILL SENTINEL — AUDIT REPORT")
    print("=" * 70)
    print(f"\n📂 Directory: {report['skills_dir']}")
    print(f"📊 Total skills: {report['total_skills']}")
    print(f"⚠️  Issues found: {report['issues_found']}")
    
    if report.get('error'):
        print(f"\n❌ {report['error']}")
        return
    
    # Summary
    s = report['summary']
    print(f"\n📈 Score Summary:")
    print(f"   Average score: {s.get('avg_score', 0):.0f}/100")
    print(f"   ✅ Passing (≥70): {s.get('passing', 0)}")
    print(f"   ⚠️  Needs work (<70): {s.get('failing', 0)}")
    print(f"   🔴 Critical (<30): {s.get('critical', 0)}")
    
    # Token budget
    tb = report['token_budget']
    status_emoji = {'OK': '✅', 'WARNING': '⚠️ ', 'CRITICAL': '🔴'}.get(tb['status'], '❓')
    print(f"\n🪙  Token Budget: {status_emoji} {tb['total_chars']} chars ({tb['status']})")
    if tb.get('message'):
        print(f"   {tb['message']}")
    
    # Per-skill details
    print(f"\n{'─'*70}")
    print("SKILL DETAILS:")
    print(f"{'─'*70}")
    
    for skill in sorted(report['skills'], key=lambda x: x.get('score', 0)):
        score = skill.get('score', 0)
        name = skill.get('name', 'unknown')
        emoji = '✅' if score >= 70 else '⚠️ ' if score >= 30 else '🔴'
        
        print(f"\n{emoji} {name} — Score: {score}/100")
        print(f"   Path: {skill['path']}")
        
        if skill.get('error'):
            print(f"   ❌ Error: {skill['error']}")
        
        for issue in skill.get('issues', []):
            print(f"   • {issue}")
        
        for sug in skill.get('suggestions', []):
            print(f"   💡 {sug}")
        
        if skill.get('fixed'):
            print(f"   🔧 Auto-fixed!")
    
    # Conflicts
    if report['conflicts']:
        print(f"\n{'─'*70}")
        print(f"⚡ CONFLICTS DETECTED: {len(report['conflicts'])}")
        print(f"{'─'*70}")
        for c in report['conflicts']:
            emoji = '🔴' if c['severity'] == 'HIGH' else '⚠️ '
            print(f"\n{emoji} {c['skill_a']} ↔ {c['skill_b']} ({c['overlap']} overlap)")
            print(f"   Shared: {', '.join(c['shared_keywords'][:5])}")
            print(f"   💡 {c['suggestion']}")
    
    print(f"\n{'='*70}")
    print("Audit complete. Fix issues above to improve skill trigger reliability.")
    print(f"{'='*70}\n")


def print_init_guide(report: Dict):
    """Print a step-by-step onboarding guide for first-time users."""
    s = report['summary']
    failing = [sk for sk in report['skills'] if sk.get('score', 100) < 70 and not sk.get('error')]
    
    print("=" * 70)
    print("🧭  SKILL COMPASS — SETUP GUIDE")
    print("=" * 70)
    print()
    print(f"📊 Scanned {report['total_skills']} skills in: {report['skills_dir']}")
    print(f"   ✅ {s.get('passing', 0)} passing  |  ⚠️  {s.get('failing', 0)} need work  |  🔴 {s.get('critical', 0)} critical")
    print(f"   Average score: {s.get('avg_score', 0):.0f}/100")
    print()
    
    if not failing:
        print("🎉 All your skills are healthy! Nothing to do.")
        print()
        print("Next steps:")
        print("  • Re-run anytime with: python3 audit_skills.py")
        print("  • Add to CI: python3 audit_skills.py --json")
        return
    
    print("─" * 70)
    print("3 STEPS TO FIX YOUR SKILLS")
    print("─" * 70)
    print()
    print("Step 1/3: Auto-fix YAML syntax issues")
    print("  $ python3 scripts/audit_skills.py --fix")
    print()
    print("Step 2/3: Generate an AI prompt to rewrite bad descriptions")
    print("  $ python3 scripts/audit_skills.py --suggest")
    print()
    print("Step 3/3: Paste the output to your AI agent (Claude, GPT, etc.)")
    print("  The agent will rewrite each description and apply the fixes.")
    print("  Then re-run the audit to verify your scores improved:")
    print("  $ python3 scripts/audit_skills.py")
    print()
    
    print("─" * 70)
    print(f"SKILLS THAT NEED ATTENTION ({len(failing)})")
    print("─" * 70)
    for sk in sorted(failing, key=lambda x: x.get('score', 0)):
        score = sk.get('score', 0)
        name = sk.get('name', 'unknown')
        issues = sk.get('issues', [])
        issue_str = '; '.join(issues) if issues else 'see suggestions'
        print(f"  ⚠️  {name} ({score}/100) — {issue_str}")
    print()
    print("=" * 70)
    print()
    
    # Auto-run step 1
    print("▶  Running Step 1 (auto-fix YAML)...\n")
    # Create backup before fixing
    backup_path = create_backup(report['skills_dir'])
    if backup_path:
        print(f'   💾 Backup saved: {backup_path}')
    # Re-run with fix
    fixed_report = audit_skills(report['skills_dir'], auto_fix=True)
    yaml_fixed = sum(1 for sk in fixed_report['skills'] if sk.get('fixed'))
    if yaml_fixed:
        print(f"   🔧 Fixed {yaml_fixed} YAML issue(s) automatically.\n")
    else:
        print("   ✅ No YAML issues found — nothing to auto-fix.\n")
    
    # Show step 2 preview
    print("▶  Step 2 preview — here's your AI prompt:\n")
    print("─" * 70)
    print(generate_suggestion_prompt(fixed_report))
    print("─" * 70)
    print()
    print("📋 Copy the prompt above and paste it to your AI agent.")
    print("   The agent will rewrite the descriptions and save the files.")
    print("   Then run `python3 scripts/audit_skills.py` to verify.")
    print()
    backup_id = os.path.basename(backup_path) if backup_path else '<id>'
    print("⏮️  If something goes wrong, rollback with:")
    print(f"   python3 scripts/audit_skills.py --rollback                    # restore latest backup")
    print(f"   python3 scripts/audit_skills.py --rollback --backup-id {backup_id}  # this specific one")
    print(f"   python3 scripts/audit_skills.py --list-backups               # see all backups")
    print()


def generate_suggestion_prompt(report: Dict) -> str:
    """Generate a ready-to-use prompt for an AI agent to rewrite bad descriptions."""
    failing = [s for s in report['skills'] if s.get('score', 100) < 70
               and not s.get('error')]

    if not failing:
        return "✅ All skills pass — no description rewrites needed!"

    lines = [
        "You are a skill description optimizer. Your job is to rewrite SKILL.md",
        "frontmatter descriptions so they trigger reliably in AI agents.",
        "",
        "## Rules",
        "1. Start with \"Use when...\" or \"ALWAYS invoke when...\"",
        "2. Include specific trigger keywords the user might say",
        "3. Add \"Do NOT use for...\" to prevent false triggers when relevant",
        "4. Keep the description under 350 characters",
        "5. Do NOT change the skill name — only the description",
        "",
        "## Skills to Fix",
        "",
    ]

    for i, skill in enumerate(failing, 1):
        name = skill.get('name', 'unknown')
        path = skill.get('path', '')
        score = skill.get('score', 0)
        issues = skill.get('issues', [])
        suggestions = skill.get('suggestions', [])

        # Try to read current description from file
        current_desc = ""
        try:
            content = Path(path).read_text(encoding='utf-8')
            fm, _ = parse_frontmatter(content)
            if fm and fm.get('description'):
                current_desc = fm['description']
        except Exception:
            pass

        lines.append(f"### {i}. {name} (Score: {score}/100)")
        lines.append(f"**File:** `{path}`")
        if current_desc:
            lines.append(f"**Current description:** {current_desc}")
        if issues:
            lines.append(f"**Issues:** {'; '.join(issues)}")
        if suggestions:
            lines.append(f"**Hints:** {'; '.join(suggestions)}")
        lines.append("")

    lines.extend([
        "## Output Format",
        "",
        "For each skill, output the new `description:` line in YAML format.",
        "Example:",
        "",
        "```yaml",
        "# multi-search-engine",
        "description: \"Use when the user asks to search the web, look something up, or find information online. Supports 16 search engines including Google, Bing, DuckDuckGo. Do NOT use for simple factual lookups the model already knows.\"",
        "```",
        "",
        "After generating all rewrites, apply them to the respective SKILL.md files.",
    ])

    return "\n".join(lines)


def print_suggestion_prompt(report: Dict):
    """Print the AI-ready suggestion prompt."""
    prompt = generate_suggestion_prompt(report)
    print(prompt)


# GitHub URL extraction pattern
GITHUB_URL_RE = re.compile(r'https?://github\.com/([\w.-]+/[\w.-]+)', re.IGNORECASE)


def extract_repo(skill_path: str) -> Optional[str]:
    """Try to find a GitHub repo URL from SKILL.md content."""
    try:
        content = Path(skill_path).read_text(encoding='utf-8')
        matches = GITHUB_URL_RE.findall(content)
        # Filter out common false positives
        for m in matches:
            lower = m.lower()
            if any(skip in lower for skip in ['github.com/trending', 'github.com/search',
                                              'github.com/explore', 'github.com/about']):
                continue
            return m.rstrip('.')  # owner/repo
        return None
    except Exception:
        return None

def generate_feedback_issues(skills_dir: str) -> str:
    """Generate GitHub issue drafts for skills whose descriptions were improved.
    Compares current (fixed) descriptions against backup to find what changed."""
    backups = list_backups()
    before_descs = {}
    if backups:
        backup_path = backups[0]['path']
        for root, dirs, files in os.walk(backup_path):
            if 'SKILL.md' in files:
                try:
                    content = open(os.path.join(root, 'SKILL.md')).read()
                    fm, _ = parse_frontmatter(content)
                    if fm and fm.get('name') and fm.get('description'):
                        before_descs[fm['name']] = fm['description']
                except Exception:
                    pass

    skill_files = find_skill_dirs([skills_dir])
    improvements = []

    for sf in skill_files:
        try:
            content = sf.read_text(encoding='utf-8')
            fm, _ = parse_frontmatter(content)
            if not fm or not fm.get('name'):
                continue
            name = fm['name']
            new_desc = fm.get('description', '')
            old_desc = before_descs.get(name, '')
            if old_desc and new_desc and old_desc != new_desc:
                desc_lower = new_desc.lower()
                if any(p in desc_lower for p in TRIGGER_PHRASES):
                    repo = extract_repo(str(sf))
                    improvements.append({
                        'name': name, 'path': str(sf), 'repo': repo,
                        'old_desc': old_desc, 'new_desc': new_desc,
                    })
        except Exception:
            pass

    if not improvements:
        return "\u2705 No description improvements detected. Run --backup before fixing, then --feedback after."

    lines_out = [
        "=" * 70,
        "\U0001F4E7  SKILL COMPASS \u2014 UPSTREAM FEEDBACK",
        "=" * 70,
        "",
        "Found {} improved description(s). Review and submit the ones you want to share.".format(len(improvements)),
        "",
    ]

    for i, imp in enumerate(improvements, 1):
        name = imp['name']
        repo = imp['repo']
        old = imp['old_desc']
        new = imp['new_desc']

        lines_out.append("\u2500" * 70)
        lines_out.append("{}. {}".format(i, name))
        lines_out.append("\u2500" * 70)
        lines_out.append("")

        # Build issue content (shared between preview and gh command)
        issue_title = "Improve `{}` description for better agent trigger reliability".format(name)

        issue_body_parts = [
            "### Context",
            "",
            "Agent skills rely on their `description` field to tell the AI *when* to fire. "
            "Research across 650 skills shows that descriptions without a trigger condition "
            '(\"Use when...\") only activate ~37% of the time, while directive ones hit ~100%.',
            "",
            "### Current",
            "```yaml",
            "description: {}".format(old),
            "```",
            "",
            "### Suggested",
            "```yaml",
            "description: {}".format(new),
            "```",
            "",
            "### How this was found",
            "",
            "Ran [Skill Compass](https://github.com/Thomaszhou22/skill-compass) "
            "\u2014 a community tool that audits skill descriptions for trigger reliability. "
            "You can scan your own skills with:",
            "```bash",
            "clawhub install skill-compass-guardian",
            "python3 scripts/audit_skills.py --init",
            "```",
        ]
        issue_body = "\n".join(issue_body_parts)

        if repo:
            lines_out.append("Repo: https://github.com/{}".format(repo))
            lines_out.append("")
            lines_out.append("Submit with one command:")
            lines_out.append("")
            lines_out.append('  gh issue create -R {} \\'.format(repo))
            lines_out.append('    --title "{}" \\'.format(issue_title))
            lines_out.append('    --body "{}"'.format(issue_body.replace('"', '\\"')))
        else:
            lines_out.append("File: {}".format(imp['path']))
            lines_out.append("\u26a0\ufe0f  No GitHub repo URL found in SKILL.md.")
            lines_out.append("   Add your repo URL to the SKILL.md body to enable upstream feedback.")
        lines_out.append("")
        lines_out.append("Issue preview:")
        lines_out.append("")
        lines_out.append("---")
        lines_out.append("**Title:** {}".format(issue_title))
        lines_out.append("")
        for part in issue_body_parts:
            lines_out.append(part)
        lines_out.append("---")
        lines_out.append("")

    lines_out.append("=" * 70)
    lines_out.append("\U0001F4A1 Tip: --backup before fixing, --feedback after. That's how we get the before/after diff.")
    lines_out.append("=" * 70)

    return "\n".join(lines_out)


def main():
    parser = argparse.ArgumentParser(description='Skill Compass - Audit skill triggering issues')
    parser.add_argument('--skills-dir', default=None,
                        help='Path to skills directory (auto-detected if omitted)')
    parser.add_argument('--json', action='store_true',
                        help='Output JSON report')
    parser.add_argument('--fix', action='store_true',
                        help='Auto-fix common issues (YAML colons, etc.)')
    parser.add_argument('--suggest', action='store_true',
                        help='Generate an AI-ready prompt to rewrite bad descriptions')
    parser.add_argument('--init', action='store_true',
                        help='First-time setup: audit + auto-fix + suggest in one pass')
    parser.add_argument('--backup', action='store_true',
                        help='Backup all SKILL.md files before making changes')
    parser.add_argument('--rollback', action='store_true',
                        help='Restore SKILL.md files from the latest backup')
    parser.add_argument('--backup-id', default=None,
                        help='Specify a backup ID to rollback to (use --list-backups to see IDs)')
    parser.add_argument('--list-backups', action='store_true',
                        help='List all available backups')
    parser.add_argument('--feedback', action='store_true',
                        help='Generate GitHub issue drafts to share improved descriptions with upstream authors')
    
    args = parser.parse_args()
    
    # Determine skills directory
    if args.skills_dir:
        skills_dir = args.skills_dir
    else:
        # Auto-detect: use first existing default dir
        skills_dir = next((d for d in DEFAULT_SKILL_DIRS if os.path.isdir(d)), DEFAULT_SKILL_DIRS[0])
    
    # Handle backup management commands first
    if args.list_backups:
        backups = list_backups()
        if not backups:
            print("No backups found. Run --backup or --init to create one.")
        else:
            print("📦 Available Backups (newest first):\n")
            for b in backups:
                print(f"  ID: {b['id']}  |  Files: {b['files']}  |  Dir: {b['skills_dir']}")
            print(f"\nRestore with: python3 audit_skills.py --rollback [--backup-id <ID>]")
        return
    
    if args.rollback:
        print("⏮️  Rolling back...\n")
        success = rollback(skills_dir, args.backup_id)
        if success:
            print("✅ Restore complete! Re-run audit to verify:")
            print(f"   python3 audit_skills.py --skills-dir {skills_dir}")
        else:
            print("❌ No backup found to restore. Run --list-backups to see available backups.")
        return
    
    if args.backup:
        path = create_backup(skills_dir)
        if path:
            print(f"💾 Backup created: {path}")
            print(f"   Restore with: python3 audit_skills.py --rollback")
        else:
            print("❌ No SKILL.md files found to backup.")
        return
    
    if args.feedback:
        print(generate_feedback_issues(skills_dir))
        return
    
    # Create backup before --fix modifies files
    if args.fix:
        backup_path = create_backup(skills_dir)
        if backup_path:
            print(f"💾 Backup saved: {backup_path}")
            print(f"   Rollback with: python3 audit_skills.py --rollback\n")
    
    if args.init:
        report = audit_skills(skills_dir, auto_fix=False)
        print_init_guide(report)
    elif args.suggest:
        report = audit_skills(skills_dir, auto_fix=False)
        print_suggestion_prompt(report)
    else:
        report = audit_skills(skills_dir, auto_fix=args.fix)
        print_report(report, json_output=args.json)


if __name__ == '__main__':
    main()
