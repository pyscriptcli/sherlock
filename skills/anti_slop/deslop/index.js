export { 
  analyzeChanges, 
  analyzeFile, 
  generateFixes,
  calculateSlopScore,
  getDiff,
  getFileDiff,
  parseAddedLines
} from './lib/analyzer.js';

export { 
  SLOP_PATTERNS, 
  SUPPORTED_EXTENSIONS, 
  IGNORE_PATTERNS 
} from './lib/patterns.js';
