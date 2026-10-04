# deslop

Detect and remove AI-generated code patterns (slop) from your branches.

AI coding assistants often introduce patterns that experienced developers recognize immediately: obvious comments, excessive try-catch blocks, verbose variable names, and defensive programming overkill. This tool scans your git diffs and flags these patterns before they accumulate into technical debt.

## Installation

```bash
npm install -g deslop
```

Or use directly with npx:

```bash
npx deslop
```

## Quick Start

```bash
# Scan current branch against main
deslop

# Scan against a different base branch
deslop -b develop

# Get just the slop score
deslop score

# See all patterns including low severity
deslop -v

# Output as JSON for CI integration
deslop -j
```

## What It Detects

### High Severity
- Debug console.log statements left in code
- Function entry/exit logging patterns

### Medium Severity
- Generic TODO placeholders without context
- Triple null/undefined checks
- Empty catch blocks that only log errors
- Excessive function entry/exit logging

### Low Severity
- Verbose obvious comments ("Initialize the variable")
- Section divider comments
- Redundant return undefined
- Explicit boolean comparisons (=== true)
- Unnecessary try-catch wrappers
- Promise.all with single promise

Run `deslop patterns` to see all detection rules.

## Commands

| Command | Description |
|---------|-------------|
| `deslop` or `deslop scan` | Scan changed files for slop patterns |
| `deslop patterns` | List all detection patterns |
| `deslop score` | Show slop score only (0-100) |

## Options

| Option | Description |
|--------|-------------|
| `-b, --base <branch>` | Base branch to compare against (default: main) |
| `-a, --all` | Scan all lines, not just diff additions |
| `-j, --json` | Output as JSON |
| `-v, --verbose` | Show all matches including low severity |
| `-q, --quiet` | Only show summary |

## Slop Score

The slop score ranges from 0 to 100:

- **0-19**: Clean code
- **20-49**: Some cleanup needed
- **50+**: Significant slop detected

The score weights issues by severity:
- High severity: 10 points
- Medium severity: 5 points
- Low severity: 1 point

Normalized per analyzed file to prevent larger PRs from scoring worse.

## CI Integration

Add to your CI pipeline to catch slop before merge:

```yaml
# GitHub Actions example
- name: Check for AI slop
  run: npx deslop --json > slop-report.json

- name: Fail if high severity
  run: |
    if [ $(cat slop-report.json | jq '.bySeverity.high') -gt 0 ]; then
      echo "High severity slop detected"
      exit 1
    fi
```

The CLI exits with code 1 if high severity issues are found.

## Programmatic Usage

```javascript
import { analyzeChanges, calculateSlopScore } from 'deslop';

const results = analyzeChanges({
  baseBranch: 'main',
  diffOnly: true
});

console.log(`Slop score: ${calculateSlopScore(results)}`);
console.log(`High severity: ${results.bySeverity.high}`);

for (const file of results.files) {
  for (const match of file.matches) {
    console.log(`${file.filePath}:${match.lineNumber} - ${match.name}`);
  }
}
```

## Patterns Reference

### Verbose Obvious Comments

AI often adds comments that state the obvious:

```javascript
// Bad (AI slop)
// Initialize the result variable
const result = [];

// Good (human style)
const result = [];
```

### Triple Null Checks

AI tends to be overly defensive:

```javascript
// Bad (AI slop)
if (value !== null && value !== undefined && value !== '') {
  // ...
}

// Good (human style)
if (value) {
  // ...
}
```

### Debug Logging

AI frequently leaves debug statements:

```javascript
// Bad (AI slop)
console.log('DEBUG: entering function');
console.log('TEMP: value is', value);

// Good (human style)
// No debug logs in production code
```

### Empty Catch Blocks

AI wraps everything in try-catch:

```javascript
// Bad (AI slop)
try {
  const data = JSON.parse(str);
} catch (error) {
  console.error('Error parsing JSON:', error);
}

// Good (human style - if you need try-catch)
try {
  const data = JSON.parse(str);
} catch (error) {
  throw new ParseError(`Invalid JSON: ${error.message}`);
}
```

## Why "Slop"?

The term "slop" emerged in developer communities to describe AI-generated code that technically works but has telltale signs of non-human origin: over-engineered, overly defensive, excessively commented, and stylistically inconsistent with human-written code.

Slop isn't necessarily buggy - it's just... sloppy. It clutters codebases, obscures intent, and creates maintenance burden. This tool helps you catch it early.

## Contributing

Found a slop pattern that should be detected? Open an issue or PR with:

1. Example of the slop pattern
2. Why it's typically AI-generated
3. Suggested regex or detection logic

## License

MIT
