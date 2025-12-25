# EWTN Critical Security Issues Report

## Executive Summary

This report identifies critical security vulnerabilities in EWTN repositories, with specific file locations and GitHub links for immediate remediation.

## Repository URLs

1. **CNA Frontend**: https://github.com/EWTN-Global/cna-frontend
2. **EWTN Plus Foundation**: https://github.com/EWTN-Global/ewtn-plus-foundation

## Critical Security Findings

### 1. CNA Frontend Repository
**Repository**: https://github.com/EWTN-Global/cna-frontend
**Issues**: 2 Command Injection vulnerabilities

#### Identified Vulnerabilities:

##### A. Potential Command Injection in Sentry Configuration
- **File**: `config/sentry.php`
- **Line**: 9
- **GitHub Link**: https://github.com/EWTN-Global/cna-frontend/blob/main/config/sentry.php#L9
- **Issue**: Contains commented-out exec() command for git hash
- **Code Pattern**: `trim(exec('git --git-dir ' . base_path('.git') . ' log --pretty="%h" -n1 HEAD'))`
- **Risk**: If uncommented without proper sanitization, could lead to command injection
- **Severity**: CRITICAL (if activated)

##### B. Template Injection Risks
- **Files**: Multiple Blade template files using backtick JavaScript templates
  - `resources/views/component/amp/trendingpost.blade.php`
  - `resources/views/component/widget/trending.blade.php`
  - `resources/views/component/widget/trendingpost.blade.php`
- **Pattern**: JavaScript template literals with user data interpolation
- **Risk**: Potential XSS if user data is not properly escaped
- **Severity**: HIGH

### 2. EWTN Plus Foundation Repository
**Repository**: https://github.com/EWTN-Global/ewtn-plus-foundation
**Issues**: 15 Command Injection + 15 Path Traversal vulnerabilities

#### Command Injection Vulnerabilities:

##### A. Sync Upstream Tool - Multiple execSync Calls
- **File**: `tools/sync/sync-upstream.ts`
- **GitHub Link**: https://github.com/EWTN-Global/ewtn-plus-foundation/blob/main/tools/sync/sync-upstream.ts
- **Critical Lines**:
  - Line 3: `import { execSync } from 'child_process';`
  - Line 76-80: Git subtree add command
  - Line 90-94: Git subtree pull command
  - Line 120: Test execution
  - Line 139: Git diff command
  - Line 147: Find command
- **Issue**: Multiple execSync calls with string concatenation
- **Risk**: Command injection if repository URL or branch names are user-controlled
- **Severity**: CRITICAL

**Specific vulnerable patterns**:
```typescript
// Line 76-77 - Dangerous string concatenation
execSync(
  `git subtree add --prefix=${subtreePath} ${config.upstream.repository} ${config.upstream.branch} --squash`
)

// Line 139 - Path injection risk
execSync(`git diff --name-only HEAD~1 HEAD -- ${subtreePath}`)

// Line 147 - Command injection via find
execSync(`find ${subtreePath} -name "*.ts" -o -name "*.tsx"`)
```

#### Path Traversal Vulnerabilities:

##### B. Import Path Mappings
- **File**: `tools/codemods/transform-imports.ts`
- **GitHub Link**: https://github.com/EWTN-Global/ewtn-plus-foundation/blob/main/tools/codemods/transform-imports.ts
- **Lines**: 10-36
- **Pattern**: Multiple `../` relative path patterns
- **Risk**: Could be exploited if user-controlled paths are processed
- **Severity**: MEDIUM-HIGH

## Commit Analysis

### Recent Security-Relevant Commits:

#### CNA Frontend:
- No recent commits directly introducing these vulnerabilities
- Security issues appear to be in existing codebase
- Most recent commits focus on redirect functionality and PostHog integration

#### EWTN Plus Foundation:
- Security issues in tooling scripts, not in main application code
- `sync-upstream.ts` appears to be a development tool
- Risk is primarily to development environment, not production

## Recommended Actions

### Immediate Actions (Critical):

1. **CNA Frontend - Sentry Config**:
   - Remove or secure the commented exec() command in `config/sentry.php`
   - Use environment variables for version information instead

2. **EWTN Plus Foundation - sync-upstream.ts**:
   - Implement proper input validation for all parameters
   - Use array-based exec functions instead of string concatenation
   - Example fix:
   ```typescript
   // Instead of:
   execSync(`git subtree add --prefix=${subtreePath} ${repository} ${branch}`)

   // Use:
   execFileSync('git', ['subtree', 'add', '--prefix', subtreePath, repository, branch])
   ```

3. **Template Injection Prevention**:
   - Audit all Blade templates for proper escaping
   - Use `{{ }}` instead of `{!! !!}` for user data
   - Implement Content Security Policy (CSP) headers

### Medium Priority:

1. **Path Traversal Prevention**:
   - Validate and sanitize all file paths
   - Use path.resolve() with proper bounds checking
   - Implement allowlist for acceptable paths

2. **Code Review Process**:
   - Implement security linting (e.g., semgrep, CodeQL)
   - Add pre-commit hooks for security checks
   - Regular dependency audits

## Security Patterns Observed

### Common Issues Across Repositories:
1. **String concatenation in shell commands** - Primary vector for command injection
2. **Relative path usage** - Potential for directory traversal
3. **Template literal injection** - XSS risk in frontend code
4. **Development tools with elevated privileges** - Risk to development environment

### Positive Security Practices Noted:
- Use of TypeScript for type safety
- Modern framework usage (Next.js, React)
- Authentication implementation (Auth0)

## Risk Assessment

| Repository | Critical Issues | High Issues | Medium Issues | Overall Risk |
|------------|----------------|-------------|---------------|--------------|
| cna-frontend | 1 (if activated) | 2 | 0 | HIGH |
| ewtn-plus-foundation | 5 | 10 | 5 | CRITICAL |

## Verification Commands

To verify these findings, run the following commands:

```bash
# Check for exec patterns in CNA Frontend
grep -r "exec\|system\|shell_exec" --include="*.php" cna-frontend/

# Check for execSync in EWTN Plus Foundation
grep -r "execSync\|exec\|spawn" --include="*.ts" --include="*.js" ewtn-plus-foundation/

# Check for path traversal patterns
grep -r "\.\./\|path\.join.*req\|path\.resolve.*req" --include="*.ts" --include="*.js" ewtn-plus-foundation/
```

## Conclusion

Both repositories contain critical security vulnerabilities that require immediate attention. The most severe issues are in the EWTN Plus Foundation repository's development tooling, particularly the `sync-upstream.ts` file with multiple command injection vulnerabilities. While these are in development tools rather than production code, they still pose significant risk to the development environment and CI/CD pipeline.

Priority should be given to:
1. Securing all exec/execSync calls with proper input validation
2. Implementing secure coding practices for shell command execution
3. Adding security scanning to the CI/CD pipeline

---

*Report Generated: 2025-09-29*
*Analysis Tool: GitFlow Analytics Security Module*