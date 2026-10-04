/**
 * AI Slop Detection Patterns
 * 
 * These patterns identify common AI-generated code characteristics that
 * don't match typical human coding style.
 */

export const SLOP_PATTERNS = [
  // Excessive comments
  {
    id: 'verbose-obvious-comment',
    name: 'Verbose obvious comment',
    description: 'Comments stating the obvious that humans rarely write',
    regex: /\/\/\s*(Initialize|Declare|Create|Set|Define|Call|Return|Check|Validate|Get|Fetch|Process|Handle|Update|Increment|Decrement)\s+(?:the\s+)?(?:a\s+)?\w+(?:\s+variable|\s+function|\s+method|\s+value|\s+result|\s+array|\s+object)?\s*$/gmi,
    severity: 'low',
    autofix: 'remove-line'
  },
  {
    id: 'section-divider-comment',
    name: 'Section divider comments',
    description: 'Excessive section dividers with decorations',
    regex: /\/\/\s*[-=*]{3,}\s*\w+.*[-=*]{3,}\s*$/gm,
    severity: 'low',
    autofix: 'remove-line'
  },
  {
    id: 'todo-placeholder',
    name: 'Generic TODO placeholder',
    description: 'Vague TODO comments without context',
    regex: /\/\/\s*TODO:\s*(Implement|Add|Handle|Fix)\s+(this|here|later|functionality|logic|error handling)\s*$/gmi,
    severity: 'medium',
    autofix: 'flag'
  },
  
  // Defensive programming overkill
  {
    id: 'triple-null-check',
    name: 'Triple null/undefined check',
    description: 'Excessive null checking patterns',
    regex: /if\s*\(\s*\w+\s*!==?\s*null\s*&&\s*\w+\s*!==?\s*undefined\s*&&\s*\w+\s*!==?\s*['"]?['"]?\s*\)/g,
    severity: 'medium',
    autofix: 'flag'
  },
  {
    id: 'empty-catch-log',
    name: 'Empty catch with console.error',
    description: 'Try-catch that only logs without handling',
    regex: /catch\s*\(\s*\w+\s*\)\s*\{\s*(console\.(error|log)\([^)]+\);?\s*|\/\/.*\s*)*\}/gs,
    severity: 'medium',
    autofix: 'flag'
  },
  {
    id: 'unnecessary-try-catch',
    name: 'Unnecessary try-catch wrapper',
    description: 'Try-catch around non-throwing synchronous code',
    regex: /try\s*\{\s*(const|let|var)\s+\w+\s*=\s*[^;]+;\s*\}\s*catch/g,
    severity: 'low',
    autofix: 'flag'
  },
  
  // Verbose variable naming
  {
    id: 'verbose-temp-variable',
    name: 'Verbose temporary variable',
    description: 'Unnecessarily descriptive temp variable names',
    regex: /(?:const|let|var)\s+(temporaryVariableFor|tempValueOf|resultOfThe|valueToBeReturned|dataToProcess)\w*/g,
    severity: 'low',
    autofix: 'flag'
  },
  {
    id: 'response-data-chain',
    name: 'Response data chain',
    description: 'Excessive response.data.data patterns',
    regex: /response\.data\.data\./g,
    severity: 'low',
    autofix: 'flag'
  },
  
  // Redundant patterns
  {
    id: 'console-log-debug',
    name: 'Debug console.log',
    description: 'Console logs left for debugging',
    regex: /console\.log\(['"](DEBUG|TEMP|TEST|TODO|FIXME|XXX|HACK):?/gi,
    severity: 'high',
    autofix: 'remove-line'
  },
  {
    id: 'commented-console-log',
    name: 'Commented out console.log',
    description: 'Commented debugging statements',
    regex: /\/\/\s*console\.(log|debug|info|warn|error)\(/g,
    severity: 'low',
    autofix: 'remove-line'
  },
  {
    id: 'redundant-return',
    name: 'Redundant return undefined',
    description: 'Explicit return undefined at function end',
    regex: /return\s+undefined\s*;\s*\}/g,
    severity: 'low',
    autofix: 'simplify'
  },
  {
    id: 'triple-equals-null',
    name: 'Triple equals null AND undefined',
    description: 'Checking both null and undefined separately',
    regex: /\w+\s*===?\s*null\s*\|\|\s*\w+\s*===?\s*undefined/g,
    severity: 'low',
    autofix: 'simplify'
  },
  
  // Over-logging
  {
    id: 'function-entry-log',
    name: 'Function entry logging',
    description: 'Logging at the start of every function',
    regex: /(?:function\s+\w+|(?:const|let|var)\s+\w+\s*=\s*(?:async\s*)?(?:\([^)]*\)|[^=]+)\s*=>)\s*\{[^}]*?console\.log\(['"`](?:Entering|Starting|Begin|Called|Invoking)/gs,
    severity: 'medium',
    autofix: 'flag'
  },
  {
    id: 'function-exit-log',
    name: 'Function exit logging',
    description: 'Logging at the end of every function',
    regex: /console\.log\(['"`](?:Exiting|Ending|Finished|Completed|Done|Returning)/gi,
    severity: 'medium',
    autofix: 'remove-line'
  },
  
  // Type coercion verbosity
  {
    id: 'string-coercion-verbose',
    name: 'Verbose string coercion',
    description: 'Using String() instead of template literal',
    regex: /String\(\w+\)\s*\+\s*String\(\w+\)/g,
    severity: 'low',
    autofix: 'flag'
  },
  {
    id: 'boolean-comparison',
    name: 'Explicit boolean comparison',
    description: 'Comparing to true/false explicitly',
    regex: /===?\s*true|===?\s*false|true\s*===?|false\s*===?/g,
    severity: 'low',
    autofix: 'simplify'
  },
  
  // Import patterns
  {
    id: 'wildcard-import-inline',
    name: 'Wildcard import with inline usage',
    description: 'Using * import and accessing with dot notation excessively',
    regex: /import\s+\*\s+as\s+(\w+)\s+from[^;]+;\s*(?:[^]*?\1\.){5,}/gs,
    severity: 'low',
    autofix: 'flag'
  },
  
  // Async patterns
  {
    id: 'await-promise-all-single',
    name: 'Promise.all with single promise',
    description: 'Using Promise.all for a single promise',
    regex: /await\s+Promise\.all\(\[\s*\w+\s*\]\)/g,
    severity: 'low',
    autofix: 'simplify'
  },
  {
    id: 'async-no-await',
    name: 'Async function without await',
    description: 'Async function that never awaits',
    regex: /async\s+(?:function\s+\w+|\([^)]*\)\s*=>|\w+\s*=>)\s*\{[^}]*\}/g,
    needsValidation: true, // Check if await exists within
    severity: 'medium',
    autofix: 'flag'
  }
];

/**
 * File extensions to analyze
 */
export const SUPPORTED_EXTENSIONS = [
  '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
  '.py',
  '.go',
  '.rs',
  '.java', '.kt', '.kts',
  '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp',
  '.cs',
  '.rb',
  '.php',
  '.swift',
  '.vue', '.svelte'
];

/**
 * Files/directories to skip
 */
export const IGNORE_PATTERNS = [
  'node_modules',
  '.git',
  'dist',
  'build',
  'coverage',
  '.next',
  '.nuxt',
  'vendor',
  '__pycache__',
  '.venv',
  'venv',
  'target',
  'bin',
  'obj'
];
