# Empirica System Prompt Installation Guide

**Purpose:** Install the universal Empirica system prompt for Gemini CLI and Claude Code
**Date:** 2025-11-15
**Version:** 1.0

---

## Overview

This guide shows you how to configure **any AI agent** (Gemini CLI, Claude Code, or others) to use Empirica's metacognitive framework as their foundational instruction set.

The Empirica system prompt provides:
- ✅ **CASCADE workflow** (PREFLIGHT → INVESTIGATE → CHECK → ACT → POSTFLIGHT)
- ✅ **13 epistemic vectors** tracking (know, do, context, clarity, etc.)
- ✅ **Systematic investigation** (goal orchestrator, belief tracking)
- ✅ **Calibration measurement** (learning deltas, confidence accuracy)
- ✅ **~85% token reduction** (git checkpoints for context)

---

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
cd /path/to/empirica
bash scripts/install_system_prompts.sh
```

This will:
1. Install Gemini CLI system prompt (`~/.gemini/system_empirica.md`)
2. Install Claude Code project prompt (`CLAUDE.md`)
3. Configure environment variables
4. Verify installation

### Option 2: Manual Setup

Follow the platform-specific instructions below.

---

## Platform-Specific Installation

### 1. Gemini CLI / Code Assist

**Method:** Complete system prompt replacement via environment variable

#### Step 1: Copy the System Prompt

```bash
# Create Gemini configuration directory (if it doesn't exist)
mkdir -p ~/.gemini

# Copy Empirica prompt
cp /path/to/empirica/GENERIC_EMPIRICA_SYSTEM_PROMPT.md \
   ~/.gemini/system_empirica.md
```

#### Step 2: Configure Environment Variable

**For permanent setup** (recommended):

```bash
# Add to your shell's startup file (~/.bashrc, ~/.zshrc, etc.)
echo 'export GEMINI_SYSTEM_MD=~/.gemini/system_empirica.md' >> ~/.bashrc
source ~/.bashrc
```

**For single session** (testing):

```bash
GEMINI_SYSTEM_MD=~/.gemini/system_empirica.md gemini
```

#### Step 3: Verify Installation

```bash
# Start Gemini CLI
gemini

# In the Gemini session, ask:
# "What framework are you using?"
# Expected response: Should mention Empirica, CASCADE workflow, epistemic vectors
```

#### Configuration Summary

| Setting | Value |
|---------|-------|
| **Method** | `GEMINI_SYSTEM_MD` environment variable |
| **Effect** | **Replaces** entire default system prompt |
| **Location** | `~/.gemini/system_empirica.md` |
| **Scope** | All Gemini CLI sessions (if in shell startup file) |

---

### 2. Claude Code

**Method:** Project-level context file (supplements built-in instructions)

#### Step 1: Copy to Project Root

```bash
# Navigate to your project
cd /path/to/empirica

# Copy Empirica prompt as CLAUDE.md
cp GENERIC_EMPIRICA_SYSTEM_PROMPT.md CLAUDE.md
```

#### Step 2: Verify Claude Code Detects It

Claude Code automatically loads `CLAUDE.md` from your project root when you start a session in that directory.

```bash
# Start Claude Code in the project
cd /path/to/empirica
claude

# Claude should automatically load CLAUDE.md as context
```

#### Step 3: For SDK Users (TypeScript/Python)

If using the Claude Agent SDK, explicitly configure setting sources:

**TypeScript:**
```typescript
import { Agent } from '@anthropic-ai/agent';

const agent = new Agent({
  settingSources: ['project'],  // Load CLAUDE.md from project root
  // ... other config
});
```

**Python:**
```python
from anthropic import Agent

agent = Agent(
    setting_sources=["project"],  # Load CLAUDE.md from project root
    # ... other config
)
```

#### Configuration Summary

| Setting | Value |
|---------|-------|
| **Method** | `CLAUDE.md` project file |
| **Effect** | **Supplements** default system prompt |
| **Location** | `CLAUDE.md` in project root |
| **Scope** | Project-specific (per directory) |
| **Auto-load** | Yes (CLI), Requires config (SDK) |

---

### 3. Other AI Agents (Qwen, Minimax, etc.)

Most AI agents support system prompt customization through one of these methods:

#### Option A: Environment Variable

```bash
# Check your agent's documentation for the specific variable name
export AI_SYSTEM_PROMPT=/path/to/system_empirica.md
```

#### Option B: Command-line Flag

```bash
# Many agents support --system-prompt or similar
your-ai-agent --system-prompt ~/.gemini/system_empirica.md
```

#### Option C: Configuration File

```json
// config.json or similar
{
  "system_prompt_path": "~/.gemini/system_empirica.md"
}
```

**Check your agent's documentation** for the specific method it supports.

---

## Verification

### Test the Installation

After installation, verify the agent has loaded Empirica:

```bash
# Start your AI agent
gemini  # or claude, or your-agent

# Ask these test questions:
```

**Test 1: Framework Recognition**
```
Q: "What framework are you using?"
Expected: Should mention Empirica, CASCADE workflow, epistemic tracking
```

**Test 2: Workflow Understanding**
```
Q: "What are the phases of your workflow?"
Expected: BOOTSTRAP → PREFLIGHT → INVESTIGATE → CHECK → ACT → POSTFLIGHT
```

**Test 3: Epistemic Vectors**
```
Q: "What epistemic vectors do you track?"
Expected: Should list 13 vectors (engagement, know, do, context, clarity, coherence, signal, density, state, change, completion, impact, uncertainty)
```

**Test 4: MCP Tools Awareness**
```
Q: "What MCP tools do you have access to?"
Expected: Should mention execute_preflight, submit_preflight_assessment, query_goal_orchestrator, etc.
```

---

## Troubleshooting

### Gemini CLI Not Loading System Prompt

**Problem:** Gemini doesn't seem to use the custom prompt

**Solutions:**
1. Verify environment variable is set:
   ```bash
   echo $GEMINI_SYSTEM_MD
   # Should print: ~/.gemini/system_empirica.md
   ```

2. Check file exists and is readable:
   ```bash
   ls -lh ~/.gemini/system_empirica.md
   cat ~/.gemini/system_empirica.md | head -20
   ```

3. Restart your terminal (to reload shell config):
   ```bash
   exec $SHELL
   ```

4. Test with explicit variable:
   ```bash
   GEMINI_SYSTEM_MD=~/.gemini/system_empirica.md gemini
   ```

---

### Claude Code Not Loading CLAUDE.md

**Problem:** Claude doesn't seem to use the project prompt

**Solutions:**
1. Verify file is in project root:
   ```bash
   ls -lh /path/to/empirica/CLAUDE.md
   ```

2. Check you're starting Claude in the correct directory:
   ```bash
   cd /path/to/empirica
   pwd  # Should show the project root
   claude
   ```

3. For SDK users, verify `settingSources` config:
   ```python
   # Must include "project" in setting_sources
   agent = Agent(setting_sources=["project"])
   ```

4. Check Claude Code version supports project files:
   ```bash
   claude --version
   # Should be recent version with project file support
   ```

---

### Agent Seems to Ignore Empirica Instructions

**Problem:** Agent responds but doesn't follow CASCADE workflow

**Possible causes:**
1. **System prompt not fully loaded** - Check verification steps above
2. **Conflicting instructions** - Some agents may have hardcoded instructions that override
3. **Agent doesn't support full replacement** - May need to use project-level supplement instead

**Solutions:**
1. Ask explicitly: "Please use the Empirica CASCADE workflow for this task"
2. Reference specific phases: "Execute PREFLIGHT assessment before starting"
3. Check agent documentation for system prompt precedence rules

---

## Advanced Configuration

### Multi-Project Setup (Claude Code)

If you work on multiple projects, you can have project-specific `CLAUDE.md` files:

```bash
# Project A: Full Empirica workflow
/path/to/projectA/CLAUDE.md  # Full CASCADE workflow

# Project B: Minimal Empirica (just epistemic tracking)
/path/to/projectB/CLAUDE.md  # Simplified version

# Project C: No Empirica
/path/to/projectC/           # No CLAUDE.md, uses default
```

### Customizing the System Prompt

You can customize the Empirica prompt for specific use cases:

```bash
# Copy original
cp GENERIC_EMPIRICA_SYSTEM_PROMPT.md CUSTOM_EMPIRICA_PROMPT.md

# Edit for your use case
nano CUSTOM_EMPIRICA_PROMPT.md

# Examples:
# - Security-focused: Add security audit phases
# - Research-focused: Emphasize investigation and belief tracking
# - Teaching-focused: Add explanation requirements
# - Production-focused: Add deployment and monitoring phases
```

### Version Control

Track your custom prompts in git:

```bash
# Add to git
git add CLAUDE.md
git add ~/.gemini/system_empirica.md  # If you want to version it

# Commit
git commit -m "feat: Add Empirica system prompts for AI agents"

# Share with team
git push
```

---

## Usage After Installation

Once installed, your AI agent will automatically:

1. **Bootstrap Empirica** at session start (or prompt you to)
2. **Execute PREFLIGHT** before starting any complex task
3. **Track epistemic state** throughout the task
4. **Use goal orchestrator** for systematic investigation
5. **CHECK readiness** before acting
6. **Execute POSTFLIGHT** after completion
7. **Measure calibration** for learning improvement

### Example Session

```bash
# Start your AI agent with Empirica
gemini  # or claude

# Agent should recognize Empirica framework
> Hi! I'm using the Empirica metacognitive framework. Would you like me to
> bootstrap a new session for your task?

# You can now work with systematic epistemic tracking
You: "I need to debug a production issue in our authentication system"

> I'll use the CASCADE workflow for this task:
>
> 1. BOOTSTRAP: Starting new Empirica session...
> 2. PREFLIGHT: Let me assess my starting epistemic state:
>    - KNOW: 0.3 (I don't know your auth system yet)
>    - DO: 0.7 (I can debug auth systems generally)
>    - CONTEXT: 0.2 (Need to learn your specific setup)
>    - UNCERTAINTY: 0.8 (High - need investigation)
>
> 3. INVESTIGATE: Let me explore your codebase systematically...
>    [Agent uses goal orchestrator to guide investigation]
>    [Agent tracks beliefs as it learns]
>
> 4. CHECK: After investigation, my confidence to proceed is 0.85
>    Remaining unknowns: [lists specific gaps]
>    Ready to debug? Yes
>
> 5. ACT: [Agent debugs the issue]
>
> 6. POSTFLIGHT: Reflecting on what I learned:
>    - KNOW: 0.3 → 0.9 (Learned your auth architecture)
>    - Calibration: I was appropriately cautious (started at 0.3)
>
> 7. CALIBRATION REPORT: Well-calibrated, learned significantly
```

---

## Next Steps

### For New Users

1. **Read the Quick Start:**
   - `/path/to/empirica/docs/01_a_AI_AGENT_START.md`

2. **Try a Simple Task:**
   - Start with something you know (to test the workflow)
   - Observe how PREFLIGHT/POSTFLIGHT track your learning

3. **Review Epistemic Vectors:**
   - `/path/to/empirica/docs/guides/CLI_GENUINE_SELF_ASSESSMENT.md`

### For Advanced Users

1. **Explore MCP Tools:**
   - 21+ tools for epistemic tracking, belief management, calibration
   - `/path/to/empirica/docs/04_MCP_QUICKSTART.md`

2. **Multi-Agent Collaboration:**
   - Transfer epistemic deltas between agents
   - `/path/to/empirica/docs/vision/EPISTEMIC_DELTA_SECURITY.md`

3. **Git Checkpoints:**
   - ~85% token reduction for long-running tasks
   - `/path/to/empirica/docs/guides/git_integration.md`

---

## Summary

| Agent | Method | Location | Effect |
|-------|--------|----------|--------|
| **Gemini CLI** | `GEMINI_SYSTEM_MD` env var | `~/.gemini/system_empirica.md` | Replaces system prompt |
| **Claude Code** | `CLAUDE.md` project file | Project root | Supplements system prompt |
| **Other agents** | Check documentation | Varies | Varies |

**Key Benefits:**
- ✅ Systematic epistemic tracking (13 vectors)
- ✅ CASCADE workflow (PREFLIGHT → POSTFLIGHT)
- ✅ Calibration measurement (learning deltas)
- ✅ ~85% token reduction (git checkpoints)
- ✅ Multi-agent collaboration (epistemic delta transfer)

**Installation time:** ~2 minutes
**Value:** Systematic reasoning for every task

---

**Ready to install?** Run the automated setup:

```bash
cd /path/to/empirica
bash scripts/install_system_prompts.sh
```

Or follow the manual installation steps above.
