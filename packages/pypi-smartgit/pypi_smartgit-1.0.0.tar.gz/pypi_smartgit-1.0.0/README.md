# SmartGit - Python Edition

**Version**: 1.0.0  
**Status**: ✅ Production Ready

SmartGit is an intelligent Git automation tool that simplifies complex Git workflows into minimal, intuitive commands.

## Installation

```bash
pip install smartgit
```

## Quick Start

```bash
# Complete workflow
smartgit all

# Create repository
smartgit repo my-project

# Ignore files
smartgit ignore *.log *.tmp

# Create version
smartgit version my-project v1.0.0

# Get help
smartgit help
```

## Features

✅ One-command deployment (`smartgit all`)  
✅ Auto-detects project name  
✅ Auto-versions from .env/.json  
✅ Deploys to GitHub Pages  
✅ GitLab ready  
✅ Minimal output  

## Commands

```bash
smartgit all [-no-version] [-no-deploy]
smartgit repo <name>
smartgit ignore <files>
smartgit include <files>
smartgit version <project> <version> [files]
smartgit addfile <project> <version> <files>
smartgit lab [project]
smartgit shortcut <name> <command>
smartgit help
```

## Usage Examples

### Deploy Everything

```bash
cd my-project
smartgit all
```

### Deploy Without Versioning

```bash
smartgit all -no-version
```

### Deploy Without Deployment

```bash
smartgit all -no-deploy
```

## Documentation

- Full Guide: `SMARTGIT-CREATED.md`
- Installation: `SMARTGIT-INSTALLATION.md`
- Quick Start: `SMARTGIT-QUICKSTART.md`

## License

MIT

---

**SmartGit: Making Git simple again.**
