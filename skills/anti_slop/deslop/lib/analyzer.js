import { execSync } from 'child_process';
import { readFileSync, existsSync } from 'fs';
import { join, extname, basename, dirname } from 'path';
import { SLOP_PATTERNS, SUPPORTED_EXTENSIONS, IGNORE_PATTERNS } from './patterns.js';

/**
 * Get the diff between current branch and base
 */
export function getDiff(baseBranch = 'main', targetBranch = 'HEAD') {
  try {
    // Try main first, then master
    const branches = [baseBranch, 'master', 'develop'];
    let diff = null;
    
    for (const branch of branches) {
      try {
        diff = execSync(`git diff ${branch}...${targetBranch} --name-only`, {
          encoding: 'utf-8',
          stdio: ['pipe', 'pipe', 'pipe']
        });
        break;
      } catch (e) {
        continue;
      }
    }
    
    if (!diff) {
      // Fallback: diff against initial commit or staged changes
      try {
        diff = execSync('git diff --cached --name-only', { encoding: 'utf-8' });
      } catch (e) {
        diff = execSync('git diff --name-only', { encoding: 'utf-8' });
      }
    }
    
    return diff.trim().split('\n').filter(Boolean);
  } catch (error) {
    throw new Error(`Failed to get git diff: ${error.message}`);
  }
}

/**
 * Get file content with diff hunks highlighted
 */
export function getFileDiff(filePath, baseBranch = 'main') {
  try {
    const branches = [baseBranch, 'master', 'develop'];
    
    for (const branch of branches) {
      try {
        return execSync(`git diff ${branch}...HEAD -- "${filePath}"`, {
          encoding: 'utf-8',
          stdio: ['pipe', 'pipe', 'pipe']
        });
      } catch (e) {
        continue;
      }
    }
    
    // Fallback to staged or working diff
    try {
      return execSync(`git diff --cached -- "${filePath}"`, { encoding: 'utf-8' });
    } catch (e) {
      return execSync(`git diff -- "${filePath}"`, { encoding: 'utf-8' });
    }
  } catch (error) {
    return null;
  }
}

/**
 * Parse diff to get added lines with line numbers
 */
export function parseAddedLines(diffContent) {
  const lines = diffContent.split('\n');
  const addedLines = [];
  let currentLine = 0;
  
  for (const line of lines) {
    // Parse hunk header: @@ -start,count +start,count @@
    const hunkMatch = line.match(/^@@\s+-\d+(?:,\d+)?\s+\+(\d+)(?:,\d+)?\s+@@/);
    if (hunkMatch) {
      currentLine = parseInt(hunkMatch[1], 10);
      continue;
    }
    
    if (line.startsWith('+') && !line.startsWith('+++')) {
      addedLines.push({
        lineNumber: currentLine,
        content: line.slice(1), // Remove the + prefix
        raw: line
      });
      currentLine++;
    } else if (line.startsWith('-') && !line.startsWith('---')) {
      // Removed line, don't increment
      continue;
    } else if (!line.startsWith('\\')) {
      // Context line
      currentLine++;
    }
  }
  
  return addedLines;
}

/**
 * Analyze a single file for slop patterns
 */
export function analyzeFile(filePath, options = {}) {
  const ext = extname(filePath);
  
  // Skip unsupported files
  if (!SUPPORTED_EXTENSIONS.includes(ext)) {
    return { filePath, matches: [], skipped: true, reason: 'unsupported-extension' };
  }
  
  // Skip ignored paths
  for (const pattern of IGNORE_PATTERNS) {
    if (filePath.includes(pattern)) {
      return { filePath, matches: [], skipped: true, reason: 'ignored-path' };
    }
  }
  
  // Get file content
  let content;
  try {
    if (existsSync(filePath)) {
      content = readFileSync(filePath, 'utf-8');
    } else {
      return { filePath, matches: [], skipped: true, reason: 'file-not-found' };
    }
  } catch (error) {
    return { filePath, matches: [], skipped: true, reason: 'read-error' };
  }
  
  const matches = [];
  const lines = content.split('\n');
  
  // If we're only checking diff, get added lines
  let addedLineNumbers = null;
  if (options.diffOnly) {
    const diff = getFileDiff(filePath, options.baseBranch);
    if (diff) {
      const addedLines = parseAddedLines(diff);
      addedLineNumbers = new Set(addedLines.map(l => l.lineNumber));
    }
  }
  
  for (const pattern of SLOP_PATTERNS) {
    // Skip patterns that need validation (complex analysis)
    if (pattern.needsValidation) continue;
    
    const regex = new RegExp(pattern.regex.source, pattern.regex.flags);
    let match;
    
    while ((match = regex.exec(content)) !== null) {
      // Find line number
      const beforeMatch = content.slice(0, match.index);
      const lineNumber = beforeMatch.split('\n').length;
      
      // If checking diff only, skip non-added lines
      if (addedLineNumbers && !addedLineNumbers.has(lineNumber)) {
        continue;
      }
      
      const lineContent = lines[lineNumber - 1] || '';
      
      matches.push({
        pattern: pattern.id,
        name: pattern.name,
        description: pattern.description,
        severity: pattern.severity,
        lineNumber,
        lineContent: lineContent.trim(),
        match: match[0].slice(0, 100), // Truncate long matches
        autofix: pattern.autofix
      });
    }
  }
  
  return { filePath, matches, skipped: false };
}

/**
 * Analyze all changed files
 */
export function analyzeChanges(options = {}) {
  const baseBranch = options.baseBranch || 'main';
  const changedFiles = getDiff(baseBranch);
  
  const results = {
    baseBranch,
    totalFiles: changedFiles.length,
    analyzedFiles: 0,
    skippedFiles: 0,
    totalMatches: 0,
    bySeverity: { high: 0, medium: 0, low: 0 },
    byPattern: {},
    files: []
  };
  
  for (const filePath of changedFiles) {
    const fileResult = analyzeFile(filePath, { 
      diffOnly: options.diffOnly !== false,
      baseBranch 
    });
    
    if (fileResult.skipped) {
      results.skippedFiles++;
      continue;
    }
    
    results.analyzedFiles++;
    
    if (fileResult.matches.length > 0) {
      results.files.push(fileResult);
      results.totalMatches += fileResult.matches.length;
      
      for (const match of fileResult.matches) {
        results.bySeverity[match.severity]++;
        results.byPattern[match.pattern] = (results.byPattern[match.pattern] || 0) + 1;
      }
    }
  }
  
  return results;
}

/**
 * Generate fix suggestions
 */
export function generateFixes(results) {
  const fixes = [];
  
  for (const file of results.files) {
    for (const match of file.matches) {
      if (match.autofix === 'remove-line') {
        fixes.push({
          file: file.filePath,
          line: match.lineNumber,
          action: 'delete',
          reason: match.name
        });
      } else if (match.autofix === 'simplify') {
        fixes.push({
          file: file.filePath,
          line: match.lineNumber,
          action: 'review',
          suggestion: `Consider simplifying: ${match.name}`,
          reason: match.description
        });
      }
    }
  }
  
  return fixes;
}

/**
 * Calculate slop score (0-100, lower is better)
 */
export function calculateSlopScore(results) {
  if (results.analyzedFiles === 0) return 0;
  
  const weights = { high: 10, medium: 5, low: 1 };
  const totalWeight = 
    results.bySeverity.high * weights.high +
    results.bySeverity.medium * weights.medium +
    results.bySeverity.low * weights.low;
  
  // Normalize to 0-100 (100 matches = 100 score at medium severity)
  const rawScore = (totalWeight / results.analyzedFiles) * 10;
  return Math.min(100, Math.round(rawScore));
}
