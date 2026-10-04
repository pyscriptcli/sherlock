#!/usr/bin/env node

import { analyzeChanges, generateFixes, calculateSlopScore } from '../lib/analyzer.js';
import { SLOP_PATTERNS } from '../lib/patterns.js';

const COLORS = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  gray: '\x1b[90m'
};

function c(color, text) {
  return `${COLORS[color]}${text}${COLORS.reset}`;
}

function printUsage() {
  console.log(`
${c('bold', 'deslop')} - Detect and remove AI-generated code patterns (slop)

${c('bold', 'USAGE')}
  deslop [options] [command]

${c('bold', 'COMMANDS')}
  scan              Scan changed files for slop patterns (default)
  patterns          List all detection patterns
  score             Show slop score only

${c('bold', 'OPTIONS')}
  -b, --base <branch>   Base branch to compare against (default: main)
  -a, --all             Scan all lines, not just diff additions
  -j, --json            Output as JSON
  -v, --verbose         Show all matches including low severity
  -q, --quiet           Only show summary
  -h, --help            Show this help

${c('bold', 'EXAMPLES')}
  deslop                      # Scan current branch vs main
  deslop -b develop           # Scan against develop branch
  deslop --all                # Scan entire files, not just changes
  deslop patterns             # List detection patterns
  deslop score                # Quick slop score
`);
}

function printPatterns() {
  console.log(c('bold', '\nSlop Detection Patterns\n'));
  
  const bySeverity = { high: [], medium: [], low: [] };
  for (const p of SLOP_PATTERNS) {
    bySeverity[p.severity].push(p);
  }
  
  for (const severity of ['high', 'medium', 'low']) {
    const color = severity === 'high' ? 'red' : severity === 'medium' ? 'yellow' : 'gray';
    console.log(c(color, `${severity.toUpperCase()} SEVERITY`));
    
    for (const p of bySeverity[severity]) {
      console.log(`  ${c('cyan', p.id)}`);
      console.log(`    ${p.description}`);
    }
    console.log();
  }
}

function printResults(results, options = {}) {
  const { verbose, quiet } = options;
  const score = calculateSlopScore(results);
  
  // Header
  console.log();
  if (score === 0) {
    console.log(c('green', '  No slop detected! Your code is clean.'));
  } else if (score < 20) {
    console.log(c('green', `  Slop Score: ${score}/100 (Clean)`));
  } else if (score < 50) {
    console.log(c('yellow', `  Slop Score: ${score}/100 (Some cleanup needed)`));
  } else {
    console.log(c('red', `  Slop Score: ${score}/100 (Significant slop detected)`));
  }
  console.log();
  
  // Summary
  console.log(c('dim', `  Analyzed: ${results.analyzedFiles} files | Skipped: ${results.skippedFiles} files`));
  console.log(c('dim', `  Base branch: ${results.baseBranch}`));
  console.log();
  
  if (quiet) return;
  
  // Matches by severity
  if (results.totalMatches > 0) {
    const { high, medium, low } = results.bySeverity;
    
    if (high > 0) console.log(c('red', `  ${high} high severity issues`));
    if (medium > 0) console.log(c('yellow', `  ${medium} medium severity issues`));
    if (low > 0 && verbose) console.log(c('gray', `  ${low} low severity issues`));
    console.log();
    
    // File-by-file breakdown
    for (const file of results.files) {
      const relevantMatches = verbose 
        ? file.matches 
        : file.matches.filter(m => m.severity !== 'low');
      
      if (relevantMatches.length === 0) continue;
      
      console.log(c('cyan', `  ${file.filePath}`));
      
      for (const match of relevantMatches) {
        const severityColor = match.severity === 'high' ? 'red' : match.severity === 'medium' ? 'yellow' : 'gray';
        console.log(`    ${c('dim', `L${match.lineNumber}:`)} ${c(severityColor, match.name)}`);
        console.log(`    ${c('dim', match.lineContent.slice(0, 80))}`);
      }
      console.log();
    }
    
    // Top patterns
    const sortedPatterns = Object.entries(results.byPattern)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
    
    if (sortedPatterns.length > 0) {
      console.log(c('bold', '  Top patterns found:'));
      for (const [pattern, count] of sortedPatterns) {
        console.log(`    ${c('dim', `${count}x`)} ${pattern}`);
      }
      console.log();
    }
    
    // Suggestions
    const fixes = generateFixes(results);
    const removable = fixes.filter(f => f.action === 'delete');
    
    if (removable.length > 0) {
      console.log(c('green', `  ${removable.length} lines can be auto-removed`));
      console.log(c('dim', '  (Run with --fix to apply - coming soon)\n'));
    }
  }
}

function printJson(results) {
  const score = calculateSlopScore(results);
  console.log(JSON.stringify({ ...results, score }, null, 2));
}

function printScore(results) {
  const score = calculateSlopScore(results);
  const emoji = score === 0 ? '✨' : score < 20 ? '✅' : score < 50 ? '⚠️' : '🚨';
  console.log(`${emoji} Slop Score: ${score}/100`);
}

// Parse arguments
const args = process.argv.slice(2);
const options = {
  baseBranch: 'main',
  diffOnly: true,
  json: false,
  verbose: false,
  quiet: false
};

let command = 'scan';

for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  
  if (arg === '-h' || arg === '--help') {
    printUsage();
    process.exit(0);
  } else if (arg === '-b' || arg === '--base') {
    options.baseBranch = args[++i];
  } else if (arg === '-a' || arg === '--all') {
    options.diffOnly = false;
  } else if (arg === '-j' || arg === '--json') {
    options.json = true;
  } else if (arg === '-v' || arg === '--verbose') {
    options.verbose = true;
  } else if (arg === '-q' || arg === '--quiet') {
    options.quiet = true;
  } else if (!arg.startsWith('-')) {
    command = arg;
  }
}

// Execute
try {
  if (command === 'patterns') {
    printPatterns();
  } else if (command === 'score' || command === 'scan') {
    const results = analyzeChanges(options);
    
    if (options.json) {
      printJson(results);
    } else if (command === 'score') {
      printScore(results);
    } else {
      printResults(results, options);
    }
    
    // Exit with error if high severity issues found
    if (results.bySeverity.high > 0) {
      process.exit(1);
    }
  } else {
    console.error(`Unknown command: ${command}`);
    printUsage();
    process.exit(1);
  }
} catch (error) {
  console.error(c('red', `Error: ${error.message}`));
  process.exit(1);
}
