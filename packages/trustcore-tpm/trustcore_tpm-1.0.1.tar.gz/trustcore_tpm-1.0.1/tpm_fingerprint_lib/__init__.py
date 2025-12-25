"""
TrustCore-TPM: Hardware-Rooted Device Identity

A comprehensive cryptographically enforced device fingerprinting system
with TPM integration, policy enforcement, and consequence management.

Features:
- Non-exportable, non-replayable fingerprints
- TPM-bound anti-cloning protection
- Cryptographically enforced governance
- Offline verification capability
- Automatic policy enforcement and consequences
"""

__version__ = "1.0.0"
__author__ = "TrustCore-TPM"

from .config import Config
from .tpm_ops import TPMOperations
from .fingerprint_engine import FingerprintEngine
from .policy_engine import PolicyEngine
from .consequence_handler import ConsequenceHandler
from .offline_verifier import OfflineVerifier
from .exceptions import (
    TPMFingerprintError,
    TPMNotAvailableError,
    PCRMismatchError,
    FingerprintExpiredError,
    PolicyViolationError,
    AttestationFailedError
)

__all__ = [
    "Config",
    "TPMOperations",
    "FingerprintEngine",
    "PolicyEngine",
    "ConsequenceHandler",
    "OfflineVerifier",
    "TPMFingerprintError",
    "TPMNotAvailableError",
    "PCRMismatchError",
    "FingerprintExpiredError",
    "PolicyViolationError",
    "AttestationFailedError"
]
