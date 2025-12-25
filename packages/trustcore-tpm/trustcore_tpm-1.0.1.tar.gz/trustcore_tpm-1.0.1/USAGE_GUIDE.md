# TPM Fingerprint Library - Complete Usage Guide

## Table of Contents
1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Core Concepts](#core-concepts)
4. [Basic Operations](#basic-operations)
5. [Advanced Usage](#advanced-usage)
6. [Command-Line Interface](#command-line-interface)
7. [Configuration](#configuration)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Installation

### From Source
```bash
git clone <repository-url>
cd Device-fingerprinting-TPM
pip install -e .
```

### Install TPM Tools (Optional but Recommended)

**Windows:**
```powershell
# TPM 2.0 tools can be installed via chocolatey
choco install tpm2-tools
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tpm2-tools
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install tpm2-tools
```

## Quick Start

### 1. Basic Device Enrollment and Verification

```python
from tpm_fingerprint_lib import OfflineVerifier

# Initialize verifier
verifier = OfflineVerifier()

# Enroll device
enrollment = verifier.enroll_device("MyWorkstation")
print(f"Fingerprint ID: {enrollment['fingerprint_id']}")
print(f"Policy ID: {enrollment['policy_id']}")

# Save enrollment data
import json
with open('enrollment.json', 'w') as f:
    json.dump(enrollment, f)

# Verify device
try:
    result = verifier.verify_device(
        enrollment['fingerprint_id'],
        enrollment['policy_id']
    )
    print(" Device verified successfully")
except Exception as e:
    print(f" Verification failed: {e}")
```

### 2. Command-Line Quick Start

```bash
# Enroll device
tpm-fingerprint enroll MyDevice --output enrollment.json

# Verify device (using IDs from enrollment.json)
tpm-fingerprint verify <fingerprint_id> <policy_id>

# Get device status
tpm-fingerprint status <fingerprint_id>
```

## Core Concepts

### 1. TPM-Bound Fingerprints

Fingerprints are **not** static identifiers. They are **provable capabilities** that:
- Cannot be extracted from the device
- Require live TPM signing for verification
- Automatically expire when system state changes

```python
from tpm_fingerprint_lib import FingerprintEngine

engine = FingerprintEngine()

# Generate fingerprint bound to current TPM state
fingerprint = engine.generate_fingerprint(
    metadata={"purpose": "production_access"},
    validity_seconds=86400  # 24 hours
)

# Fingerprint contains:
# - fingerprint_id: Unique identifier
# - pcr_values: TPM PCR snapshot
# - tpm_quote: Signed attestation
# - created_at: Timestamp
# - expires_at: Expiry time
```

### 2. Policy-Based Governance

Policies define **what happens** when state changes:

```python
from tpm_fingerprint_lib import PolicyEngine
from tpm_fingerprint_lib.policy_engine import PolicyAction, PolicyViolationType

policy_engine = PolicyEngine()

# Create policy
policy = policy_engine.create_policy(
    name="Production Policy",
    max_mismatch_attempts=3,
    auto_expire_on_boot_change=True,
    auto_expire_on_firmware_update=True,
    require_secure_boot=True
)

# Customize consequences
policy.actions = {
    PolicyViolationType.BOOT_STATE_CHANGED: [
        PolicyAction.REVOKE_CREDENTIALS,
        PolicyAction.LOCKDOWN_VAULT,
        PolicyAction.FORCE_REENROLLMENT,
        PolicyAction.AUDIT_LOG
    ]
}
```

### 3. Automatic Consequence Enforcement

Consequences are **enforced**, not just logged:

```python
from tpm_fingerprint_lib import ConsequenceHandler

handler = ConsequenceHandler()

# Register protected resources
credential = handler.register_credential(
    credential_id="api_key_prod",
    credential_type="api_key",
    data={"key": "super_secret_key"},
    fingerprint_id=fingerprint_id
)

vault = handler.register_vault(
    vault_id="prod_secrets",
    name="Production Secrets Vault",
    fingerprint_id=fingerprint_id
)

# When policy is violated:
# - Credentials are automatically revoked
# - Vaults are automatically locked
# - Tokens are automatically invalidated
# - Re-enrollment is forced
```

### 4. Offline Operation

Complete operation without network:

```python
verifier = OfflineVerifier()

# Everything works offline:
# - Enrollment
# - Verification
# - Policy enforcement
# - Consequence management
# - Audit logging

# All trust anchored in local TPM
```

## Basic Operations

### Device Enrollment

```python
from tpm_fingerprint_lib import OfflineVerifier

verifier = OfflineVerifier()

# Standard enrollment
enrollment = verifier.enroll_device(
    device_name="Laptop-001",
    validity_seconds=86400  # 24 hours
)

# No expiry (state-based only)
enrollment = verifier.enroll_device(
    device_name="Server-001",
    validity_seconds=None  # No time-based expiry
)

# Custom PCRs
enrollment = verifier.enroll_device(
    device_name="Workstation-001",
    pcr_indices=[0, 1, 2, 3, 7, 8]  # Include additional PCRs
)
```

### Device Verification

```python
# Basic verification
try:
    verifier.verify_device(fingerprint_id, policy_id)
    print(" Verified")
except PolicyViolationError as e:
    print(f" Policy violated: {e}")
except BootStateChangedError as e:
    print(f" Boot state changed: {e}")
```

### Challenge-Response Verification

```python
# Perform anti-replay verification
result = verifier.challenge_response_verify(fingerprint_id)

if result['verified']:
    print(" Challenge verified - device is live")
    print(f"Challenge: {result['challenge']}")
    print(f"PCRs: {result['pcr_values']}")
else:
    print(" Challenge failed")
```

### State Comparison

```python
# Compare current state with baseline
comparison = verifier.compare_with_baseline(fingerprint_id, policy_id)

if comparison['all_match']:
    print(" All PCRs match baseline")
else:
    print(" Deviations detected:")
    for pcr, info in comparison['deviations'].items():
        if not info['match']:
            print(f"  PCR {pcr}: changed")
```

## Advanced Usage

### Custom Policy Enforcement

```python
from tpm_fingerprint_lib.policy_engine import PolicyViolationType

# Register custom handler
def send_security_alert(violation, policy, fingerprint):
    print(f"ALERT: {violation.value}")
    # Send email, SMS, webhook, etc.

verifier.policy_engine.register_violation_handler(
    PolicyViolationType.SECURE_BOOT_VIOLATED,
    send_security_alert
)
```

### Credential Management

```python
# Register multiple credentials
credentials = [
    {
        "credential_id": "db_admin",
        "credential_type": "database",
        "data": {"username": "admin", "password": "secret"}
    },
    {
        "credential_id": "api_key",
        "credential_type": "api",
        "data": {"key": "abc123xyz"}
    },
    {
        "credential_id": "ssh_key",
        "credential_type": "ssh",
        "data": {"private_key": "..."}
    }
]

for cred_data in credentials:
    verifier.consequence_handler.register_credential(
        **cred_data,
        fingerprint_id=fingerprint_id
    )

# Check credential status
for cred_data in credentials:
    valid = verifier.consequence_handler.is_credential_valid(
        cred_data['credential_id']
    )
    print(f"{cred_data['credential_id']}: {'' if valid else ''}")
```

### Vault Management

```python
# Create hierarchical vault structure
vaults = [
    {"vault_id": "dev_secrets", "name": "Development Secrets"},
    {"vault_id": "staging_secrets", "name": "Staging Secrets"},
    {"vault_id": "prod_secrets", "name": "Production Secrets"}
]

for vault_data in vaults:
    verifier.consequence_handler.register_vault(
        **vault_data,
        fingerprint_id=fingerprint_id
    )

# Check vault accessibility
def can_access_vault(vault_id):
    return verifier.consequence_handler.is_vault_accessible(vault_id)

# Grant access based on verification
try:
    verifier.verify_device(fingerprint_id, policy_id)
    if can_access_vault("prod_secrets"):
        # Access granted
        print("Access to production secrets granted")
except PolicyViolationError:
    print("Access denied - vaults locked")
```

### Audit Log Management

```python
from tpm_fingerprint_lib.audit_logger import AuditLogger, AuditEventType

logger = AuditLogger()

# Query events
events = logger.get_events(
    event_type=AuditEventType.POLICY_VIOLATED,
    fingerprint_id=fingerprint_id,
    limit=50
)

for event in events:
    print(f"{event.timestamp}: {event.event_type.value}")
    print(f"  Details: {event.details}")

# Get statistics
stats = logger.get_statistics()
print(f"Total events: {stats['total_events']}")
print(f"Sealed logs: {stats['sealed_logs']}")
print(f"Events by type: {stats['events_by_type']}")

# Verify audit log integrity
verification = logger.verify_log_chain()
if verification['verified']:
    print(" Audit log chain verified")
else:
    print(" Audit log integrity compromised")
    for error in verification['errors']:
        print(f"  - {error}")

# Force seal current logs
logger.force_seal()
```

### Regeneration After Updates

```python
# After legitimate system update
try:
    # Try to verify with old fingerprint
    verifier.verify_device(old_fingerprint_id, old_policy_id)
except BootStateChangedError:
    # Expected - regenerate
    new_enrollment = verifier.regenerate_after_update(
        old_fingerprint_id=old_fingerprint_id,
        device_name="MyDevice"
    )
    
    print(f"New fingerprint: {new_enrollment['fingerprint_id']}")
    print(f"New policy: {new_enrollment['policy_id']}")
    
    # Update your storage with new IDs
```

### Export/Import Verification Bundles

```python
# Export bundle for offline verification
bundle = verifier.export_offline_verification_bundle(
    fingerprint_id,
    policy_id
)

# Save to file
import json
with open('verification_bundle.json', 'w') as f:
    json.dump(bundle, f, indent=2)

# Transfer to offline system and verify
# (bundle contains everything needed for offline verification)
```

## Command-Line Interface

### Device Management

```bash
# Enroll device
tpm-fingerprint enroll MyDevice --validity 86400 -o enrollment.json

# Verify device
tpm-fingerprint verify <fingerprint_id> <policy_id>

# Get device status
tpm-fingerprint status <fingerprint_id>

# Challenge-response verification
tpm-fingerprint challenge <fingerprint_id>

# Compare with baseline
tpm-fingerprint compare <fingerprint_id> <policy_id>

# Regenerate after update
tpm-fingerprint regenerate <old_fingerprint_id> MyDevice

# Export verification bundle
tpm-fingerprint export <fingerprint_id> <policy_id> -o bundle.json
```

### Audit Management

```bash
# Show audit statistics
tpm-fingerprint audit stats

# Verify audit log chain
tpm-fingerprint audit verify

# List recent events
tpm-fingerprint audit events --limit 100

# Filter by fingerprint
tpm-fingerprint audit events --fingerprint-id <id> --limit 50
```

### List Resources

```bash
# List all fingerprints
tpm-fingerprint list-fingerprints

# List all policies
tpm-fingerprint list-policies
```

## Configuration

### Environment Variables

```bash
# PCRs to use for fingerprinting
export TPM_PCRS="0,1,2,3,7"

# Fingerprint validity (seconds)
export FINGERPRINT_VALIDITY_SECONDS=86400

# Enable offline mode
export OFFLINE_MODE=true

# Enable strict mode
export STRICT_MODE=true
```

### Programmatic Configuration

```python
from tpm_fingerprint_lib.config import Config

config = Config()

# Customize PCRs
config.DEFAULT_PCRS = [0, 1, 2, 3, 7, 8, 9]

# Set validity
config.FINGERPRINT_VALIDITY_SECONDS = 3600  # 1 hour

# Enable/disable features
config.CONSEQUENCES_ENABLED = True
config.AUTO_REVOKE_CREDENTIALS = True
config.AUTO_LOCKDOWN_VAULT = True
config.SEAL_AUDIT_LOGS = True

# Pass to components
from tpm_fingerprint_lib import OfflineVerifier
verifier = OfflineVerifier(config)
```

## Best Practices

### 1. PCR Selection

```python
# For general purpose (boot state + secure boot)
config.DEFAULT_PCRS = [0, 1, 2, 3, 7]

# For enhanced security (include kernel)
config.DEFAULT_PCRS = [0, 1, 2, 3, 7, 8, 9]

# For firmware-only verification
config.DEFAULT_PCRS = [0, 1]
```

### 2. Expiry Settings

```python
# Short-lived (hourly rotation)
validity_seconds = 3600

# Daily rotation
validity_seconds = 86400

# No time-based expiry (state-based only)
validity_seconds = None
```

### 3. Consequence Configuration

```python
# Strict mode (maximum security)
config.CONSEQUENCES_ENABLED = True
config.AUTO_REVOKE_CREDENTIALS = True
config.AUTO_LOCKDOWN_VAULT = True
config.FORCE_REENROLLMENT = True

# Monitoring mode (log only)
config.CONSEQUENCES_ENABLED = False
```

### 4. Error Handling

```python
from tpm_fingerprint_lib.exceptions import *

try:
    verifier.verify_device(fp_id, policy_id)
except TPMNotAvailableError:
    # TPM not available - handle gracefully
    logger.error("TPM required but not available")
except BootStateChangedError:
    # Boot state changed - regenerate
    new_enrollment = verifier.regenerate_after_update(fp_id, "Device")
except PolicyViolationError as e:
    # Policy violated - consequences already enforced
    logger.warning(f"Policy violation: {e}")
except FingerprintExpiredError:
    # Expired - require re-enrollment
    logger.info("Fingerprint expired - re-enrollment required")
```

## Troubleshooting

### TPM Not Available

**Problem:** `TPMNotAvailableError: TPM is not available`

**Solutions:**
1. Verify TPM is enabled in BIOS
2. Install tpm2-tools
3. Check TPM permissions

```bash
# Linux: Check TPM device
ls -l /dev/tpm0

# Windows: Check TPM status
Get-Tpm
```

### PCR Mismatch

**Problem:** `PCRMismatchError: PCR values don't match`

**Cause:** System state changed (update, boot, firmware)

**Solution:**
```python
# Regenerate fingerprint after legitimate change
new_enrollment = verifier.regenerate_after_update(
    old_fingerprint_id,
    "Device"
)
```

### Unsealing Failed

**Problem:** Cannot unseal fingerprints

**Cause:** TPM state changed since sealing

**Solution:** This is expected behavior - fingerprints are state-bound. Regenerate after confirming legitimate change.

### Permission Denied

**Problem:** Permission denied accessing TPM

**Solution:**
```bash
# Linux: Add user to tss group
sudo usermod -a -G tss $USER

# Restart session
```

## Support and Resources

- **Documentation:** See README.md
- **Examples:** See examples/ directory
- **Tests:** Run `pytest tests/ -v`
- **Issues:** GitHub Issues
- **Patent Information:** See PATENTS.md

---

**For additional help, consult the comprehensive README.md or open an issue on GitHub.**

