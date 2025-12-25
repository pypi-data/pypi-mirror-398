# AI Project OS

## Version 2.5 – Governance Kernel (Spec Frozen)

This release represents a frozen governance kernel. 
Core governance semantics, lifecycle rules, audit invariants, 
and freeze mechanics are considered stable and MUST NOT be modified 
without a new major version.

This version prioritizes governance correctness over extensibility, 
performance, or usability.

[![PyPI Version](https://img.shields.io/pypi/v/ai-project-os-mcp)](https://pypi.org/project/ai-project-os-mcp/)
[![License](https://img.shields.io/pypi/l/ai-project-os-mcp)](https://pypi.org/project/ai-project-os-mcp/)
[![Python Versions](https://img.shields.io/pypi/pyversions/ai-project-os-mcp)](https://pypi.org/project/ai-project-os-mcp/)

**AI Project Operating System**  
Turn AI coding into real, auditable software engineering.

## Core Governance Principles

AI Project OS v2.5 implements a **non-bypassable, auditable, and evolvable** governance system with the following core invariants:

1. **Single Entry Point**: GovernanceEngine is the sole entry for all AI governance operations
2. **Actor Mandatory**: No anonymous AI behavior is permitted
3. **Event Closure**: All events produce governance outcomes
4. **Violation Enforcement**: Violations trigger defined actions
5. **Freeze Irreversibility**: Freeze state is irreversible within the same stage
6. **State Integrity**: No direct state modification
7. **Audit Completeness**: All actions produce append-only audit records
8. **Policy Priority**: System policies override project policies
9. **CI Enforcement**: Governance invariants are automatically verified in CI

For the complete governance constitution, see [GOVERNANCE_INVARIANTS.md](docs/GOVERNANCE_INVARIANTS.md).

## Quick Start

### 5-Minute Governance Test Drive

```bash
# Install the package
pip install ai-project-os-mcp

# Run the minimal governance example
python -c "from ai_project_os_mcp.core import GovernanceEngine; print('✅ GovernanceEngine loaded')"

# Run the complete governance flow example
git clone https://github.com/wuxiaolong123121/ai-project-os-mcp.git
cd ai-project-os-mcp
python examples/minimal_governance.py
```

### Installation

```bash
pip install ai-project-os-mcp
```

### Usage

1. **Initialize a new project**:
   ```bash
   ai-project-os init my-project
   cd my-project
   ```

2. **Start with S1 Scope stage**:
   ```bash
   ai-project-os s1
   ```

3. **Follow the 5S workflow**:
   ```bash
   # After completing S1, move to S2
   ai-project-os s2
   
   # Then S3, S4, and finally S5
   ai-project-os s3
   ai-project-os s4
   ai-project-os s5
   ```

4. **Check project status**:
   ```bash
   ai-project-os status
   ```

### For Non-Technical Users

If you don't want to use the command line, check out our [Zero-Code Guide](docs/example-no-code.md) to use AI Project OS with just your AI tool.

## Status

⚠️ AI Project OS v2.5 is currently in **Spec-Frozen / Implementation-in-Progress** state.

- Architecture and module design are frozen
- Core governance engine implementation is ongoing
- APIs, modules, and governance behaviors may change until v2.5.0 release
- Not yet suitable for production use

For stable v1.x version, please check the v1 branch.

## What is this?

AI Project OS is an engineering-grade operating system for AI-driven software projects.

It does **not** try to make AI "smarter".  
It makes AI **obedient to real-world engineering rules**.

AI Project OS enforces:
- Clear project stages
- Frozen decisions
- Guarded code generation
- Mandatory audit trails

No freeze, no code.  
No audit, no ship.

## What AI Project OS is NOT

- ❌ Not an AI code quality checker
- ❌ Not responsible for business logic correctness
- ❌ Not a replacement for human review

## Why AI Project OS?

AI coding fails in real projects because:

- AI skips steps
- AI rewrites architecture
- AI patches instead of redesigning
- Humans cannot tell when AI crossed the line

AI Project OS fixes this by introducing **engineering governance**.

## Core Concepts

### 1. State over Prompt
Project truth lives in `state.json`, not in conversation memory.

### 2. Freeze over Generate
All decisions must be frozen before execution.

### 3. Audit over Output
Code without audit is not considered done.

## The 5S Workflow

| Stage | Meaning | Code Allowed | 
|------|--------|--------------|
| S1 | Scope | ❌ |
| S2 | Spec | ❌ |
| S3 | Structure | ❌ |
| S4 | Schedule | ❌ |
| S5 | Ship | ✅ |

## MCP-Based Governance

AI Project OS is implemented as a **Model Context Protocol (MCP)** server.

This allows:
- Claude
- Cursor
- Trae
- Local agents

To act as **governed engineering executors**, not free-form chatbots.

## S5 Stability Guard (Mandatory)

Every S5 task must include:

- **Context Refresh**
- **Change Fuse**
- **Pseudo-TDD**
- **Audit Record**

No exception.

## Approval Field

Approval MUST be provided by a human reviewer. In audit logs:
- AI may suggest content
- Human reviewer must explicitly sign off

AI self-approval is forbidden for compliance reasons.

## Who is this for?

- Non-technical founders
- Product managers using AI coding
- Teams tired of AI-generated mess
- Anyone who wants AI to behave like a real engineer

## License

MIT License

## MCP Server Runtime Modes

| Mode | Usage | Security Features |
|------|-------|------------------|
| STDIO | Claude / Cursor / Trae | Lightweight, for development |
| HTTP | Dashboard / Enterprise | Supports authentication, for production |

## Core Principle

> **拒绝违规执行**
> **比勉强完成任务更正确**

AI Project OS believes that refusing to execute violations is more correct than勉强 completing tasks.

## Version Semantics

We follow **Semantic Versioning**:

- **MAJOR (x.0.0)**: Governance model or MCP protocol changes
- **MINOR (1.x.0)**: New governance capabilities, backward compatible
- **PATCH (1.0.x)**: Bug fixes, documentation, or non-behavioral changes

## Release & Rollback Policy

- **Release**: Git tags trigger GitHub Actions for automatic PyPI publishing
- **Rollback**: Never delete published versions, only release fix versions (e.g., v1.0.1)

## LTS Support

v2.5.x will maintain backward compatibility for governance schemas.

## Enterprise Edition Roadmap

The following capabilities are reserved for future enterprise editions:

- Multi-project isolation
- Centralized audit logging
- Private MCP Registry
- SSO / RBAC support

## Philosophy

> AI should not be creative about structure.  
> AI should be creative only within frozen boundaries.
