# errlog-smartgit - Python Edition

**Version**: 1.0.0  
**Status**: ✅ Production Ready

errlog-smartgit is the error handler companion to SmartGit. It provides detailed error feedback, step-by-step process view, and colored output for debugging.

## Installation

```bash
pip install errlog-smartgit
```

This automatically installs SmartGit as a dependency.

## Quick Start

```bash
# Complete workflow with detailed feedback
smartgit-err all

# Create repository with details
smartgit-err repo my-project

# Get help
smartgit-err help
```

## Features

✅ Step-by-step process view  
✅ Detailed error messages  
✅ Colored output  
✅ Timing information  
✅ Progress tracking  

## Commands

```bash
smartgit-err all [-no-version] [-no-deploy]
smartgit-err repo <name>
smartgit-err ignore <files>
smartgit-err include <files>
smartgit-err version <project> <version> [files]
smartgit-err addfile <project> <version> <files>
smartgit-err lab [project]
smartgit-err shortcut <name> <command>
smartgit-err help
```

## Usage Examples

### Deploy with Detailed Feedback

```bash
cd my-project
smartgit-err all
```

**Output**:
```
▶ smartgit all
Total steps: 10
[1/10] Executing step 1/10
[2/10] Executing step 2/10
...
✓ Success
Completed in 2345ms
```

### When to Use

- **smartgit**: Production, automation, CI/CD
- **smartgit-err**: Development, debugging, learning

## License

MIT

---

**errlog-smartgit: Making debugging simple.**
