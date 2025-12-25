# MAQET Documentation

This directory contains comprehensive documentation for the MAQET project, organized by topic and purpose.

## Quick Navigation

### For Users

- [User Guide](user-guide/) - Installation, configuration, and usage instructions
  - [Storage Lifecycle Management](user-guide/storage-lifecycle.md) - VM deletion, orphaned storage, and recovery
  - [Storage Management](user-guide/storage.md) - QEMU storage types, snapshots, and performance
  - [Quickstart Guide](user-guide/quickstart.md) - Getting started with MAQET
  - [Configuration](user-guide/configuration.md) - VM configuration details
- [API Reference](api/) - Python API documentation

### For Developers

- [Development Guide](../CLAUDE.md) - Claude Code instructions, coding standards
- [Testing Guide](development/TESTING.md) - How to run and write tests
- [Linting Guide](development/linting.md) - Ruff integration and code quality
- [Architecture Documentation](architecture/) - System design and decisions

### For Architecture Review

- [Layered Architecture](architecture.md) - 5-layer clean architecture overview, protocols, and DI pattern
- [Architecture Audit Report](architecture/ARCHITECTURE_AUDIT_REPORT.md) - Comprehensive Phase 5 review
- [Architectural Decisions](architecture/ARCHITECTURAL_DECISIONS.md) - 23 key design decisions
- [Per-VM Process Architecture](architecture/PER_VM_PROCESS_ARCHITECTURE.md) - Core architecture specification

## Directory Structure

```
docs/
├── README.md                    (this file)
├── architecture/                Architecture specifications and design docs
│   ├── ARCHITECTURAL_DECISIONS.md
│   ├── ARCHITECTURAL_REVIEW.md
│   ├── ARCHITECTURE_AUDIT_REPORT.md
│   ├── DAEMON_ARCHITECTURE_RESEARCH.md
│   ├── PERSISTENT_QEMUMACHINE_ARCHITECTURE.md
│   └── PER_VM_PROCESS_ARCHITECTURE.md
├── development/                 Development process and implementation docs
│   ├── phases/                  Phase implementation summaries
│   └── reports/                 Technical reports and fixes
├── deployment/                  Deployment guides
├── user-guide/                  End-user documentation
├── reference/                   API and CLI reference
└── api/                        Generated API documentation

../                              (Repository root)
├── README.md                    Project overview and quick start
└── CLAUDE.md                   Development guide for Claude Code
```

## Document Categories

### Architecture (architecture/)

Core system design documents - specification, decisions, audit results

### Development Phases (development/phases/)

Phase-by-phase implementation summaries

### Technical Reports (development/reports/)

Specific fixes, cleanups, and technical investigations

## Key Documents by Purpose

### Understanding the Architecture

1. Start with [Layered Architecture](architecture.md) for component organization
2. Read [PER_VM_PROCESS_ARCHITECTURE.md](architecture/PER_VM_PROCESS_ARCHITECTURE.md) for process model
3. Review [ARCHITECTURAL_DECISIONS.md](architecture/ARCHITECTURAL_DECISIONS.md) for design rationale
4. Check [ARCHITECTURE_AUDIT_REPORT.md](architecture/ARCHITECTURE_AUDIT_REPORT.md) for implementation status

### Contributing to Development

1. Read [CLAUDE.md](../CLAUDE.md) for development guidelines
2. Check [TESTING.md](development/TESTING.md) for testing procedures
3. Review [linting.md](development/linting.md) for code quality standards
4. Review relevant phase documents for context

### Debugging Issues

1. Check [CODE_ISSUES_REPORT.md](development/reports/CODE_ISSUES_REPORT.md)
2. Review specific fix reports
3. Consult [CLAUDE.md](../CLAUDE.md) troubleshooting section
