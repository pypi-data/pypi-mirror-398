# Git Commit Message Standards

## Basic Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

## Commit Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat: add user login functionality` |
| `fix` | Bug fix | `fix: resolve login page crash issue` |
| `docs` | Documentation updates | `docs: update API documentation` |
| `style` | Code formatting (no functional changes) | `style: fix code indentation` |
| `refactor` | Code refactoring | `refactor: restructure user service module` |
| `test` | Testing related | `test: add user login unit tests` |
| `chore` | Build tools, auxiliary tools changes | `chore: update dependency versions` |
| `perf` | Performance optimization | `perf: optimize database query performance` |
| `ci` | CI/CD related | `ci: update GitHub Actions configuration` |
| `build` | Build system related | `build: update webpack configuration` |
| `revert` | Revert commit | `revert: revert commit abc1234` |

## Scope (Optional)

Indicates the area of the codebase affected by the commit:
- Module name: `auth`, `user`, `api`, `ui`
- File name: `utils`, `config`, `middleware`
- Feature area: `login`, `dashboard`, `settings`

## Subject

- Use consistent language (English or Chinese)
- Keep it concise, under 50 characters
- Use imperative mood, present tense
- Start with lowercase
- No period at the end

## Body (Optional)

- Explain **why** you made this change in detail
- Leave a blank line after the subject
- Wrap lines at 72 characters
- Can span multiple lines

## Footer (Optional)

- **Breaking Changes**: Incompatible changes
- **Issues**: Related issue references

## Examples

### Simple Commit
```
feat: add user avatar upload functionality
```

### With Scope
```
feat(auth): add two-factor authentication
```

### Complete Format
```
feat(user): add user avatar upload functionality

- Support PNG and JPG formats
- Limit file size to 2MB maximum
- Auto-generate thumbnails
- Add upload progress bar

Closes #123
```

### Bug Fix
```
fix(login): resolve remember password feature failure

Fixed issue where login state was lost after page refresh
when user checked "remember password".

Modified localStorage storage logic.

Fixes #456
```

### Breaking Change
```
feat(api): update user API response format

BREAKING CHANGE: 
User API response format has been updated:
- Removed `user_name` field
- Added `username` and `display_name` fields
- Update client code to adapt to new format

Closes #789
```

## Special Cases

### MCP Tool Related
```
feat(mcp): add load_figure tool
fix(mcp): fix error handling in get_data tool
docs(mcp): update tool usage documentation
```

### Multiple Changes
```
feat: optimize user management module

- feat(user): add batch delete functionality
- fix(user): resolve user list pagination issue
- style(user): standardize user form styles
```

## Rules Summary

1. **Must use type prefix**
2. **Subject line under 50 characters**
3. **Body lines under 72 characters**
4. **Use imperative mood**
5. **Blank line between subject and body**
6. **Use bullet points for multiple changes**
7. **Reference issues with Closes/Fixes**

## Recommended Tools

- **Commitizen**: Interactive commit tool
- **Husky**: Git hooks manager
- **Commitlint**: Commit message linting

```bash
# Install commitizen
npm install -g commitizen cz-conventional-changelog

# Usage
git cz
```

## Configuration Examples

### .gitmessage Template
```
# <type>(<scope>): <subject>
# 
# <body>
# 
# <footer>
```

### commitlint.config.js
```javascript
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'subject-max-length': [2, 'always', 50],
    'type-enum': [2, 'always', [
      'feat', 'fix', 'docs', 'style', 'refactor',
      'test', 'chore', 'perf', 'ci', 'build', 'revert'
    ]]
  }
}
```

## Quick Reference

### Common Patterns
```bash
# New feature
git commit -m "feat: add user authentication"
git commit -m "feat(auth): implement OAuth login"

# Bug fix
git commit -m "fix: resolve memory leak in data processing"
git commit -m "fix(api): handle null response from external service"

# Documentation
git commit -m "docs: add installation guide"
git commit -m "docs(readme): update setup instructions"

# Refactoring
git commit -m "refactor: extract utility functions to separate module"
git commit -m "refactor(components): simplify form validation logic"

# Testing
git commit -m "test: add integration tests for payment flow"
git commit -m "test(utils): increase coverage for helper functions"
```

### MCP Development Specific
```bash
# Adding new MCP tools
git commit -m "feat(mcp): add load_figure tool for image processing"
git commit -m "feat(mcp): implement database_query tool"

# MCP tool fixes
git commit -m "fix(mcp): resolve file path validation in load_figure"
git commit -m "fix(mcp): handle connection timeout in api_call tool"

# MCP documentation
git commit -m "docs(mcp): add tool usage examples"
git commit -m "docs(mcp): update tool configuration guide"
```