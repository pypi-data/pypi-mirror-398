# TrustCore-TPM

**TPM-Based Device Fingerprinting Library**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![TPM 2.0](https://img.shields.io/badge/TPM-2.0-green.svg)](https://trustedcomputinggroup.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

TrustCore-TPM is a Python library for hardware-based device fingerprinting using Trusted Platform Module (TPM) 2.0. It provides cryptographically enforced device identity with automatic policy enforcement.

## Features

- Hardware-rooted device fingerprinting using TPM 2.0
- PCR-based state binding for platform integrity
- Cryptographic sealing with AES-256-GCM
- Challenge-response authentication protocol
- Automatic policy enforcement
- Offline verification capability
- Comprehensive audit logging

## Installation

```bash
pip install trustcore-tpm
```

### Requirements

- Python 3.8 or higher
- TPM 2.0 hardware (or software simulator)
- Windows: WMI access for TPM operations
- Linux: tpm2-tools package

## Quick Start

### Basic Usage

```python
from tpm_fingerprint_lib import OfflineVerifier

# Initialize verifier
verifier = OfflineVerifier()

# Enroll device
device_id = "device-001"
result = verifier.enroll_device(device_id)

if result["success"]:
    print(f"Device enrolled: {result['fingerprint_id']}")
    
# Verify device
verification = verifier.verify_device(device_id)
print(f"Valid: {verification['valid']}")
```

### With Policy Enforcement

```python
from tpm_fingerprint_lib import PolicyEngine, ConsequenceHandler

# Define policy
policy = {
    "max_failures": 3,
    "require_tpm": True,
    "allowed_pcrs": [0, 1, 2, 3, 7]
}

# Verify with policy
engine = PolicyEngine()
result = engine.evaluate(device_id, policy)

if result["violated"]:
    # Handle consequences
    handler = ConsequenceHandler()
    handler.execute(device_id, result["violations"])
```

## Architecture

### Core Components

```
┌─────────────────────────────────────────────┐
│           Application Layer                  │
│          (Your Application)                  │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Library API Layer                    │
│  OfflineVerifier, PolicyEngine, etc.        │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Core Engine Layer                    │
│  - FingerprintEngine                        │
│  - PolicyEngine                             │
│  - ConsequenceHandler                       │
│  - AuditLogger                              │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│       TPM Abstraction Layer                  │
│         TPMOperations                        │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Hardware Layer                       │
│         TPM 2.0 Chip                        │
└─────────────────────────────────────────────┘
```

### Key Capabilities

#### 1. Hardware-Enforced Fingerprint Governance

Device fingerprints are cryptographically bound to TPM Platform Configuration Registers (PCRs). The fingerprint lifecycle is managed through hardware state:

- **Enrollment**: Device attributes are collected and sealed to current PCR values
- **Verification**: TPM unseals data only if PCR values match enrollment state
- **Expiry**: Fingerprint automatically becomes invalid when:
  - Boot state changes (PCR 0-3)
  - Firmware is updated (PCR 0-2)
  - Secure Boot state changes (PCR 7)
  - Custom policy conditions are triggered

**State Machine**:
```
Generated → Valid → Expired → Re-enrollment Required
         ↑      ↓
         └──────┘
    (Successful Verification)
```

**Comparison with Traditional Approaches**:

| Traditional Fingerprinting | TrustCore-TPM |
|---------------------------|---------------|
| Software-based hash | Hardware-rooted cryptographic seal |
| Copyable identifier | Non-exportable capability |
| Manual revocation | Automatic expiry on state change |
| No hardware binding | TPM PCR binding |
| Replay vulnerable | Challenge-response protocol |

#### 2. TPM-Bound Anti-Cloning

The fingerprint is not a static value—it is a cryptographic capability bound to specific TPM hardware.

**Cloning Attack Resistance**:

An attacker who steals the fingerprint file cannot use it on another device because:

1. **Different TPM**: Each TPM has unique internal state
2. **Different PCR Values**: Each device has unique boot measurements
3. **Sealed Data**: AES-GCM ciphertext can only be unsealed with correct PCR-derived key
4. **Challenge-Response**: Each verification requires fresh TPM signature

**Technical Details**:

```
Sealed Data Structure:
┌────────────────────────────────────────┐
│ nonce (96-bit random)                  │
│ ciphertext (AES-256-GCM encrypted)     │
│ authentication_tag (128-bit GMAC)      │
└────────────────────────────────────────┘

Unsealing Process:
1. Read current PCRs from TPM
2. Derive key = KDF(PCR_0 || PCR_1 || ... || PCR_7)
3. Attempt AES-GCM decryption
4. Fail if PCRs don't match original enrollment state
```

**Challenge-Response Protocol**:

```
Verifier                              Device
   │                                     │
   ├──── Challenge (32-byte nonce) ────>│
   │                                     │
   │                              ┌──────▼──────┐
   │                              │     TPM     │
   │                              │ Read PCRs   │
   │                              │ Sign HMAC   │
   │                              └──────┬──────┘
   │                                     │
   │<─── Response: {signature, PCRs} ────┤
   │                                     │
   ├─ Verify:                            │
   │  • Timestamp fresh (< 5 min)        │
   │  • Nonce matches                    │
   │  • Signature = HMAC(nonce||PCRs)    │
   │  • PCRs match baseline              │
   │                                     │
   └─> Valid or Invalid                  │
```

#### 3. Integrated Policy Enforcement

Device verification is coupled with automatic consequence execution. Policy violations trigger immediate enforcement actions.

**Policy Evaluation Flow**:

```
Device Verification
        │
        ▼
┌───────────────┐
│ Check Valid?  │
└───────┬───────┘
        │
    ┌───┴───┐
    │ Yes   │ No
    ▼       ▼
  Access  Policy Violation
  Granted      │
               ▼
         Execute Consequences:
         • Revoke credentials
         • Lock secure storage
         • Invalidate tokens
         • Log audit event
         • Require re-enrollment
               │
               ▼
         Access Denied
```

**Example Policies**:

- Maximum verification failures
- Required PCR values
- Time-based restrictions
- Geographic limitations
- Custom business logic

#### 4. Offline Verification

Unlike cloud-based attestation systems, TrustCore-TPM operates entirely offline:

**Architecture Comparison**:

```
Traditional Cloud Attestation:
Device → Network → Cloud Server → Database → Response
        (Latency, availability dependency)

TrustCore-TPM:
Device → Local TPM → Verification Result
        (No network, instant, always available)
```

**Benefits**:
- Zero network latency
- No cloud infrastructure required
- Works in air-gapped environments
- No data leaves the device
- Reduced attack surface

## Security Model

### Cryptographic Primitives

- **Symmetric Encryption**: AES-256-GCM (NIST approved)
- **Message Authentication**: HMAC-SHA256
- **Key Derivation**: HKDF-SHA256
- **Random Generation**: TPM RNG (FIPS 140-2 Level 2)

### TPM PCR Usage

| PCR | Purpose | Use Case |
|-----|---------|----------|
| 0-3 | BIOS/UEFI firmware, boot components | Detect firmware changes |
| 4-5 | Boot loader, boot configuration | Detect boot tampering |
| 7 | Secure Boot state | Detect Secure Boot disable |
| 8-15 | OS and application measurements | Custom application binding |

### Trust Model

**Root of Trust**: TPM 2.0 hardware provides:
- Protected storage for cryptographic keys
- Secure crypto operations
- Platform integrity measurements (PCRs)
- Random number generation

**Trust Chain**:
```
TPM Hardware Root
        ↓
PCR Measurements (Platform State)
        ↓
Sealed Credentials
        ↓
Application Trust
```

### Security Properties

1. **Confidentiality**: Fingerprint data encrypted with AES-256-GCM
2. **Integrity**: HMAC-SHA256 signatures prevent tampering
3. **Authenticity**: TPM-signed challenges prove device identity
4. **Non-repudiation**: Audit logs sealed to TPM
5. **Freshness**: Challenge-response prevents replay attacks

## API Reference

### OfflineVerifier

Main interface for device fingerprinting operations.

```python
class OfflineVerifier:
    def __init__(self, storage_path: str = "~/.tpm_fingerprint/")
    
    def enroll_device(self, device_id: str, 
                     metadata: dict = None) -> dict
    
    def verify_device(self, device_id: str, 
                     strict: bool = True) -> dict
    
    def revoke_device(self, device_id: str) -> bool
    
    def list_devices(self) -> list
```

### FingerprintEngine

Core fingerprinting logic.

```python
class FingerprintEngine:
    def generate_fingerprint(self, device_id: str) -> dict
    
    def verify_fingerprint(self, device_id: str, 
                          challenge: bytes) -> dict
```

### PolicyEngine

Policy evaluation and enforcement.

```python
class PolicyEngine:
    def evaluate(self, device_id: str, 
                policy: dict) -> dict
    
    def register_policy(self, policy_id: str, 
                       policy: dict) -> bool
```

### ConsequenceHandler

Automatic enforcement actions.

```python
class ConsequenceHandler:
    def execute(self, device_id: str, 
               violations: list) -> dict
    
    def register_consequence(self, name: str, 
                            handler: callable) -> bool
```

## Configuration

### Environment Variables

```bash
# TPM device path (Linux)
export TPM_DEVICE=/dev/tpm0

# Storage location
export TPM_FP_STORAGE=~/.tpm_fingerprint/

# Log level
export TPM_FP_LOG_LEVEL=INFO
```

### Configuration File

```python
# config.py
TPM_CONFIG = {
    "pcr_selection": [0, 1, 2, 3, 7],
    "challenge_timeout": 300,  # seconds
    "max_failures": 3,
    "require_secure_boot": True,
    "audit_retention_days": 90
}
```

## Storage

### Directory Structure

```
~/.tpm_fingerprint/
├── fingerprints/
│   ├── device-001.json
│   └── device-002.json
├── policies/
│   └── default.json
├── audit/
│   └── 2024-01-15.log
└── tpm_state.json
```

### Fingerprint File Format

```json
{
  "device_id": "device-001",
  "fingerprint_id": "fp_a1b2c3d4",
  "created_at": "2024-01-15T10:30:00Z",
  "pcr_values": {
    "0": "base64_encoded_value",
    "1": "base64_encoded_value"
  },
  "sealed_data": "base64_encrypted_blob",
  "metadata": {
    "hostname": "workstation-01",
    "os": "Windows 11"
  }
}
```

## CLI Usage

```bash
# Enroll device
trustcore-tpm enroll --device-id device-001

# Verify device
trustcore-tpm verify --device-id device-001

# List devices
trustcore-tpm list

# Revoke device
trustcore-tpm revoke --device-id device-001

# Show TPM info
trustcore-tpm tpm-info
```

## Advanced Usage

### Custom Policy

```python
def custom_policy(device_id: str, context: dict) -> dict:
    # Business logic
    if context['time_of_day'] not in ['09:00', '17:00']:
        return {
            "violated": True,
            "reason": "Outside business hours"
        }
    return {"violated": False}

# Register policy
engine = PolicyEngine()
engine.register_policy("business_hours", custom_policy)
```

### Custom Consequence

```python
def send_alert(device_id: str, violation: dict):
    # Send notification
    print(f"Alert: {device_id} violated policy")

# Register consequence
handler = ConsequenceHandler()
handler.register_consequence("alert", send_alert)
```

### Batch Operations

```python
devices = ["device-001", "device-002", "device-003"]

for device_id in devices:
    result = verifier.verify_device(device_id)
    print(f"{device_id}: {result['valid']}")
```

## Testing

### Unit Tests

```bash
python -m pytest tests/
```

### Integration Tests

```bash
python -m pytest tests/integration/
```

### TPM Simulator

For development without hardware TPM:

```bash
# Install TPM simulator (Linux)
sudo apt-get install swtpm

# Run tests with simulator
export TPM_DEVICE=/dev/tpm_sim
python -m pytest
```

## Troubleshooting

### TPM Not Detected

**Windows**:
```powershell
# Check TPM status
Get-Tpm

# Enable TPM in BIOS/UEFI
```

**Linux**:
```bash
# Check TPM device
ls -l /dev/tpm0

# Install tools
sudo apt-get install tpm2-tools
```

### Permission Denied

```bash
# Add user to tpm group (Linux)
sudo usermod -a -G tss $USER

# Windows: Run as Administrator for TPM access
```

### PCR Mismatch

PCR values change when:
- BIOS/UEFI firmware is updated
- Secure Boot is enabled/disabled
- Boot configuration changes

Solution: Re-enroll device after platform changes.

## Performance

### Benchmarks

Tested on Intel Core i7-8650U with TPM 2.0:

| Operation | Time | Notes |
|-----------|------|-------|
| Enrollment | ~150ms | Includes PCR reads and sealing |
| Verification | ~80ms | Challenge-response protocol |
| Policy Evaluation | ~10ms | In-memory computation |
| Audit Log Write | ~5ms | Async write |

## Security Considerations

### Best Practices

1. **Secure Boot**: Enable Secure Boot for PCR 7 binding
2. **BIOS Password**: Protect BIOS/UEFI settings
3. **Physical Security**: Prevent hardware tampering
4. **Regular Updates**: Keep firmware and OS updated
5. **Audit Logs**: Monitor for unusual patterns
6. **Backup**: Secure backup of fingerprint data

### Known Limitations

- TPM 2.0 required (TPM 1.2 not supported)
- Platform-specific (cannot migrate between devices)
- PCR changes require re-enrollment
- Software TPM emulators provide reduced security

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License - see [LICENSE](LICENSE) file.

## References

- [TCG TPM 2.0 Specification](https://trustedcomputinggroup.org/resource/tpm-library-specification/)
- [NIST SP 800-57: Key Management](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)
- [FIPS 140-2: Security Requirements](https://csrc.nist.gov/publications/detail/fips/140/2/final)

## Support

- GitHub Issues: https://github.com/Johnsonajibi/Trustcore-TPM/issues
- Documentation: https://github.com/Johnsonajibi/Trustcore-TPM

## Changelog

### Version 1.0.1 (2024-01-15)
- Fixed package name to trustcore-tpm
- Updated documentation
- Production release

### Version 1.0.0 (2024-01-15)
- Initial release
- TPM 2.0 support
- Complete fingerprinting system
- Policy enforcement
- Audit logging
