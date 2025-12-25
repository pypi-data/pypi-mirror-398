# Contributing to Empirica

Thank you for your interest in contributing to Empirica! This document outlines our development workflow and guidelines.

## Development Workflow

We use **Git Flow** for version management with the following branch structure:

```
main (stable, production-ready)
  ├── develop (integration branch)
  │   ├── feature/your-feature-name
  │   ├── bugfix/issue-description
  │   └── experimental/research-idea
  └── hotfix/critical-bug (emergency fixes from main)
```

## Branch Strategy

### Main Branch
- **Purpose**: Production-ready, stable code that users install
- **Protection**: Requires PR review + passing tests
- **Direct commits**: Not allowed
- **Install from**: `pip install git+https://github.com/Nubaeon/empirica.git@main`

### Develop Branch
- **Purpose**: Integration and testing of new features
- **Protection**: Requires passing tests
- **Direct commits**: Allowed for maintainers
- **Install from**: `pip install git+https://github.com/Nubaeon/empirica.git@develop`

See full branching workflow and contribution guidelines in the file.

## Using Empirica to Develop Empirica (Meta-Development)

We practice what we preach: **use Empirica to manage Empirica development**.

### Why Dogfooding?

- If Empirica helps us build Empirica, it'll help others
- We discover edge cases and UX issues firsthand
- Our sessions become real-world examples
- We validate the framework with every contribution

### Quick Start

For complex tasks (new features, refactoring, bug investigations), use the CASCADE workflow:

```bash
# 1. Start session
empirica session-create --ai-id your-ai-id

# 2. PREFLIGHT: Assess what you know
empirica preflight-submit /tmp/preflight.json

# 3. Work naturally (investigate, code, test)

# 4. CHECK: Decision gate before major changes
empirica check /tmp/check.json

# 5. POSTFLIGHT: Measure learning
empirica postflight-submit /tmp/postflight.json
```

### Full Documentation

See `.empirica-project/README.md` for:
- Complete meta-development guide
- Example session workflows
- Benefits and philosophy
- Project configuration

### Meta-Principles

1. ✅ Use Empirica for non-trivial contributions
2. ✅ Track findings and unknowns honestly
3. ✅ Demonstrate value by using it ourselves
4. ✅ If we wouldn't use it, why should users?
