# Architecture Diagram Index

This document provides a quick reference to all architectural diagrams included in the TrustCore-TPM documentation.

---

## Quick Navigation

| Diagram | Location | Description |
|---------|----------|-------------|
| **High-Level Component Architecture** | [README.md](README.md#system-architecture) | Mermaid diagram showing all components and layers |
| **Data Flow Architecture** | [README.md](README.md#system-architecture) | Sequence diagram of enrollment and verification flows |
| **Component Interaction Matrix** | [README.md](README.md#system-architecture) | ASCII table showing component dependencies |
| **Trust Chain Architecture** | [README.md](README.md#system-architecture) | Visual hierarchy from hardware to application |
| **Cryptographic Operations Flow** | [README.md](README.md#system-architecture) | Step-by-step crypto operations |
| **Storage Architecture** | [README.md](README.md#system-architecture) | File system layout and data structures |
| **Innovation 1: Governance Lifecycle** | [README.md](README.md#key-innovations) | State machine for fingerprint lifecycle |
| **Innovation 2: Anti-Cloning Flow** | [README.md](README.md#key-innovations) | How cloning attacks fail |
| **Innovation 3: Consequence Flow** | [README.md](README.md#key-innovations) | Automatic enforcement diagram |
| **Innovation 4: Offline Architecture** | [README.md](README.md#key-innovations) | Traditional vs offline comparison |
| **Basic Usage Flow** | [README.md](README.md#quick-start) | Simple enrollment → verification flow |
| **PCR Extend Operation** | [README.md](README.md#tpm-pcr-definitions) | How PCR measurements work |
| **State Change Detection** | [README.md](README.md#tpm-pcr-definitions) | Mermaid diagram of boot process |
| **Component Overview** | [README.md](README.md#core-components) | Mermaid graph of all engines |
| **Security Properties** | [README.md](README.md#security-features) | Comprehensive security guarantees |

---

## Diagram Types Used

### Mermaid Diagrams
- Component graphs (`graph TB`, `graph LR`)
- Sequence diagrams (`sequenceDiagram`)
- State machines (`stateDiagram-v2`)

Benefits:
- GitHub rendering support
- Interactive and scalable
- Easy to modify

### ASCII Art Diagrams
- Component matrices
- Trust chains
- Flow diagrams
- Data structures

Benefits:
- Plain text compatibility
- Terminal viewing
- Universal compatibility

---

## Visual Style Guide

### Color Coding (Mermaid)
- Red (#e74c3c): Errors, failures, security threats
- Green (#2ecc71): Success, valid states, approved
- Blue (#3498db): TPM operations, core components
- Orange (#f39c12): Warnings, consequences

### Box Types (ASCII)
- `┌─┐` Single line: Normal components
- `╔═╗` Double line: Hardware/critical components
- `╭─╮` Rounded: User-facing elements

---

## Detailed Diagram Descriptions

### 1. High-Level Component Architecture
```
Shows: 5 layers of the system
- Application Layer (your code)
- Library API Layer (OfflineVerifier)
- Core Engine Layer (4 engines)
- TPM Abstraction Layer
- Hardware Layer (TPM 2.0 chip)

Purpose: Understand overall system structure
Audience: Architects, developers
```

### 2. Data Flow Architecture
```
Shows: Complete sequence of operations
- Device enrollment flow (13 steps)
- Verification with violation (15 steps)
- Actor interactions between components

Purpose: Understand operational flow
Audience: Developers, security auditors
```

### 3. Cryptographic Operations Flow
```
Shows: Step-by-step crypto operations
- Fingerprint generation (6 steps)
- Verification process (5 steps)
- All crypto algorithms used

Purpose: Understand security implementation
Audience: Security engineers, auditors
```

### 4. Trust Chain Architecture
```
Shows: Hardware-to-application trust hierarchy
- TPM 2.0 as root of trust
- PCR-based sealing
- Sealed credentials and logs
- Application-level trust derivation

Purpose: Understand security foundation
Audience: Security architects, compliance teams
```

### 5. Storage Architecture
```
Shows: File system layout
- ~/.tpm_fingerprint/ structure
- JSON file formats
- TPM-sealed data organization

Purpose: Understand data persistence
Audience: Developers, system administrators
```

### 6. Innovation Diagrams (4 Total)
```
Shows: Patent-worthy innovations
- Governance lifecycle state machine
- Anti-cloning attack flow
- Consequence enforcement comparison
- Offline vs cloud architecture

Purpose: Highlight novel contributions
Audience: Patent attorneys, investors, researchers
```

### 7. PCR State Change Detection
```
Shows: Boot process measurements
- UEFI firmware measurement
- Option ROM loading
- Secure Boot checking
- PCR extend operations
- Unseal success/failure

Purpose: Understand TPM binding
Audience: Platform engineers, security teams
```

### 8. Component Interaction Matrix
```
Shows: Dependencies between components
- Which components call which
- Data flow between engines
- TPM usage by each component

Purpose: Understand component relationships
Audience: Developers, system designers
```

---

## How to Use These Diagrams

### For Learning
1. Start with **High-Level Component Architecture**
2. Follow **Basic Usage Flow** for simple operations
3. Study **Data Flow Architecture** for complete understanding
4. Deep dive into **Cryptographic Operations** for security

### For Development
1. Reference **Component Overview** for API design
2. Check **Component Interaction Matrix** for dependencies
3. Use **Storage Architecture** for data persistence
4. Follow **Cryptographic Operations** for implementation

### For Security Review
1. Study **Trust Chain Architecture** for security foundation
2. Review **Cryptographic Operations** for algorithm choices
3. Analyze **Anti-Cloning Flow** for attack resistance
4. Examine **Consequence Flow** for enforcement logic

### For Documentation
1. Use **Innovation Diagrams** for patent documentation
2. Reference **Architecture Diagrams** for technical specs
3. Include **Flow Diagrams** in user guides
4. Cite **Security Diagrams** in compliance docs

---

## Modifying Diagrams

### Mermaid Diagrams
```bash
# Edit the diagram code in README.md
# Syntax: https://mermaid.js.org/intro/

# Preview online:
# https://mermaid.live/

# Example:
graph TB
    A[Start] --> B[Process]
    B --> C[End]
```

### ASCII Diagrams
```bash
# Use online tools:
# - https://asciiflow.com/
# - https://textik.com/

# Or draw manually with box-drawing characters:
# ─ ═ │ ║ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼
# ╔ ╗ ╚ ╝ ╠ ╣ ╦ ╩ ╬
```

---

## Diagram Statistics

| Type | Count | Total Lines |
|------|-------|-------------|
| Mermaid Diagrams | 6 | ~300 |
| ASCII Diagrams | 12 | ~400 |
| Tables | 8 | ~150 |
| Code Examples | 25+ | ~800 |
| **Total Visual Elements** | **50+** | **~1,650** |

---

## Best Practices

### When Creating New Diagrams

1. **Keep it Simple**: One concept per diagram
2. **Use Consistent Notation**: Follow existing style
3. **Add Context**: Include title and description
4. **Color Code**: Use meaningful colors (green=good, red=bad)
5. **Label Everything**: Clear labels for all components
6. **Show Direction**: Use arrows to indicate flow
7. **Include Legend**: Explain symbols when needed

### Diagram Checklist
- [ ] Clear title and purpose
- [ ] Consistent with other diagrams
- [ ] All components labeled
- [ ] Flow direction indicated
- [ ] Colors used meaningfully
- [ ] Legend included (if complex)
- [ ] Rendered correctly on GitHub
- [ ] Accessible in plain text

---

## Related Resources

- [README.md](README.md) - Main documentation with all diagrams
- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed architecture documentation
- [USAGE_GUIDE.md](USAGE_GUIDE.md) - Usage examples with code
- [PATENTS.md](PATENTS.md) - Patent documentation with innovation diagrams

---

*This index helps navigate the 50+ visual elements across the TrustCore-TPM documentation.*
