"""
Configuration and constants for TPM Fingerprint Library
"""

import os
from typing import List, Dict
from pathlib import Path


class Config:
    """Configuration settings for TPM Fingerprint Library"""
    
    # TPM PCRs to use for attestation
    # PCR 0-7 are typically used for firmware and boot measurements
    DEFAULT_PCRS: List[int] = [0, 1, 2, 3, 7]  # Boot state, secure boot
    
    # Fingerprint validity duration (in seconds)
    # None = infinite validity (until state change)
    FINGERPRINT_VALIDITY_SECONDS: int = 86400  # 24 hours
    
    # Challenge nonce size (bytes)
    CHALLENGE_NONCE_SIZE: int = 32
    
    # Maximum allowed PCR deviation attempts before lockdown
    MAX_PCR_MISMATCH_ATTEMPTS: int = 3
    
    # Audit log location
    AUDIT_LOG_PATH: Path = Path.home() / ".tpm_fingerprint" / "audit.log"
    
    # Sealed data storage path
    SEALED_DATA_PATH: Path = Path.home() / ".tpm_fingerprint" / "sealed"
    
    # Fingerprint storage path (encrypted, TPM-bound)
    FINGERPRINT_STORAGE_PATH: Path = Path.home() / ".tpm_fingerprint" / "fingerprints"
    
    # Policy storage path
    POLICY_STORAGE_PATH: Path = Path.home() / ".tpm_fingerprint" / "policies"
    
    # Enable offline mode (no server verification)
    OFFLINE_MODE: bool = True
    
    # TPM path (for Linux systems)
    TPM_DEVICE_PATH: str = "/dev/tpm0"
    
    # Enable strict mode (enforce all policies)
    STRICT_MODE: bool = True
    
    # Hash algorithm for fingerprinting
    HASH_ALGORITHM: str = "sha256"
    
    # Consequence enforcement settings
    CONSEQUENCES_ENABLED: bool = True
    AUTO_REVOKE_CREDENTIALS: bool = True
    AUTO_LOCKDOWN_VAULT: bool = True
    AUTO_INVALIDATE_TOKENS: bool = True
    FORCE_REENROLLMENT: bool = True
    
    # Anti-replay settings
    NONCE_LIFETIME_SECONDS: int = 300  # 5 minutes
    ENABLE_TIMESTAMP_VALIDATION: bool = True
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    ENABLE_AUDIT_LOGGING: bool = True
    SEAL_AUDIT_LOGS: bool = True
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        directories = [
            cls.AUDIT_LOG_PATH.parent,
            cls.SEALED_DATA_PATH,
            cls.FINGERPRINT_STORAGE_PATH,
            cls.POLICY_STORAGE_PATH
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        config = cls()
        
        # Override with environment variables if present
        if pcrs := os.getenv("TPM_PCRS"):
            cls.DEFAULT_PCRS = [int(p) for p in pcrs.split(",")]
        
        if validity := os.getenv("FINGERPRINT_VALIDITY_SECONDS"):
            cls.FINGERPRINT_VALIDITY_SECONDS = int(validity)
        
        if offline := os.getenv("OFFLINE_MODE"):
            cls.OFFLINE_MODE = offline.lower() in ("true", "1", "yes")
        
        if strict := os.getenv("STRICT_MODE"):
            cls.STRICT_MODE = strict.lower() in ("true", "1", "yes")
        
        return config


# PCR indices and their meanings
PCR_DEFINITIONS: Dict[int, str] = {
    0: "BIOS/Platform firmware",
    1: "Platform configuration",
    2: "Option ROM code",
    3: "Option ROM configuration",
    4: "MBR/Boot loader",
    5: "GPT/Partition table",
    6: "State transition and wake events",
    7: "Secure Boot state",
    8: "Bootloader/Kernel",
    9: "Kernel command line",
    10: "IMA (Integrity Measurement Architecture)",
    11: "Kernel module measurements",
    12: "Reserved",
    13: "Reserved",
    14: "MokList/Shim verification",
    15: "Reserved",
    16: "Debug",
    23: "Application support"
}


# Initialize directories on import
Config.ensure_directories()
