"""
Policy Engine - Cryptographically Enforced Governance

Implements policy-based fingerprint lifecycle control with:
- PCR baseline validation
- Automatic expiry on state changes
- Boot state monitoring
- Firmware update detection
- Secure boot violation detection
"""

import json
import hmac
import hashlib
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

from .tpm_ops import TPMOperations
from .fingerprint_engine import DeviceFingerprint, FingerprintEngine
from .config import Config
from .exceptions import (
    PolicyViolationError,
    PCRMismatchError,
    BootStateChangedError,
    SecureBootViolationError,
    FirmwareUpdateDetectedError,
    FingerprintExpiredError
)


class PolicyViolationType(Enum):
    """Types of policy violations"""
    PCR_MISMATCH = "pcr_mismatch"
    FINGERPRINT_EXPIRED = "fingerprint_expired"
    BOOT_STATE_CHANGED = "boot_state_changed"
    SECURE_BOOT_VIOLATED = "secure_boot_violated"
    FIRMWARE_UPDATED = "firmware_updated"
    BASELINE_DEVIATION = "baseline_deviation"
    MAX_ATTEMPTS_EXCEEDED = "max_attempts_exceeded"


class PolicyAction(Enum):
    """Actions to take on policy violation"""
    ALLOW = "allow"
    DENY = "deny"
    REVOKE_CREDENTIALS = "revoke_credentials"
    LOCKDOWN_VAULT = "lockdown_vault"
    INVALIDATE_TOKENS = "invalidate_tokens"
    FORCE_REENROLLMENT = "force_reenrollment"
    AUDIT_LOG = "audit_log"
    ALERT = "alert"


class Policy:
    """Represents a fingerprint policy"""
    
    def __init__(self, policy_id: str, name: str,
                 pcr_baseline: Dict[int, str],
                 max_mismatch_attempts: int = 3,
                 validity_seconds: Optional[int] = None,
                 auto_expire_on_boot_change: bool = True,
                 auto_expire_on_firmware_update: bool = True,
                 require_secure_boot: bool = True,
                 actions: Optional[Dict[PolicyViolationType, List[PolicyAction]]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        
        self.policy_id = policy_id
        self.name = name
        self.pcr_baseline = pcr_baseline
        self.max_mismatch_attempts = max_mismatch_attempts
        self.validity_seconds = validity_seconds
        self.auto_expire_on_boot_change = auto_expire_on_boot_change
        self.auto_expire_on_firmware_update = auto_expire_on_firmware_update
        self.require_secure_boot = require_secure_boot
        self.actions = actions or self._default_actions()
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.mismatch_count = 0
    
    def _default_actions(self) -> Dict[PolicyViolationType, List[PolicyAction]]:
        """Default actions for each violation type"""
        return {
            PolicyViolationType.PCR_MISMATCH: [
                PolicyAction.DENY,
                PolicyAction.AUDIT_LOG,
                PolicyAction.ALERT
            ],
            PolicyViolationType.FINGERPRINT_EXPIRED: [
                PolicyAction.DENY,
                PolicyAction.FORCE_REENROLLMENT,
                PolicyAction.AUDIT_LOG
            ],
            PolicyViolationType.BOOT_STATE_CHANGED: [
                PolicyAction.REVOKE_CREDENTIALS,
                PolicyAction.FORCE_REENROLLMENT,
                PolicyAction.AUDIT_LOG
            ],
            PolicyViolationType.SECURE_BOOT_VIOLATED: [
                PolicyAction.DENY,
                PolicyAction.LOCKDOWN_VAULT,
                PolicyAction.REVOKE_CREDENTIALS,
                PolicyAction.AUDIT_LOG,
                PolicyAction.ALERT
            ],
            PolicyViolationType.FIRMWARE_UPDATED: [
                PolicyAction.FORCE_REENROLLMENT,
                PolicyAction.AUDIT_LOG
            ],
            PolicyViolationType.MAX_ATTEMPTS_EXCEEDED: [
                PolicyAction.LOCKDOWN_VAULT,
                PolicyAction.REVOKE_CREDENTIALS,
                PolicyAction.AUDIT_LOG,
                PolicyAction.ALERT
            ]
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "pcr_baseline": self.pcr_baseline,
            "max_mismatch_attempts": self.max_mismatch_attempts,
            "validity_seconds": self.validity_seconds,
            "auto_expire_on_boot_change": self.auto_expire_on_boot_change,
            "auto_expire_on_firmware_update": self.auto_expire_on_firmware_update,
            "require_secure_boot": self.require_secure_boot,
            "actions": {
                k.value: [a.value for a in v]
                for k, v in self.actions.items()
            },
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "mismatch_count": self.mismatch_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Policy':
        """Deserialize from dictionary"""
        policy = cls(
            policy_id=data["policy_id"],
            name=data["name"],
            pcr_baseline=data["pcr_baseline"],
            max_mismatch_attempts=data.get("max_mismatch_attempts", 3),
            validity_seconds=data.get("validity_seconds"),
            auto_expire_on_boot_change=data.get("auto_expire_on_boot_change", True),
            auto_expire_on_firmware_update=data.get("auto_expire_on_firmware_update", True),
            require_secure_boot=data.get("require_secure_boot", True),
            actions={
                PolicyViolationType(k): [PolicyAction(a) for a in v]
                for k, v in data.get("actions", {}).items()
            },
            metadata=data.get("metadata", {})
        )
        policy.created_at = datetime.fromisoformat(data["created_at"])
        policy.mismatch_count = data.get("mismatch_count", 0)
        return policy


class PolicyEngine:
    """
    Policy enforcement engine
    
    Enforces cryptographic governance over fingerprints through:
    - Baseline validation
    - State change detection
    - Automatic consequence triggering
    """
    
    def __init__(self, config: Optional[Config] = None,
                 tpm_ops: Optional[TPMOperations] = None,
                 fingerprint_engine: Optional[FingerprintEngine] = None):
        self.config = config or Config()
        self.tpm = tpm_ops or TPMOperations(self.config)
        self.fingerprint_engine = fingerprint_engine or FingerprintEngine(self.config, self.tpm)
        self._policies: Dict[str, Policy] = {}
        self._violation_handlers: Dict[PolicyViolationType, List[Callable]] = {}
        self._load_policies()
    
    def _load_policies(self):
        """Load policies from storage"""
        policy_storage = self.config.POLICY_STORAGE_PATH
        for policy_file in policy_storage.glob("*.json"):
            try:
                policy_data = json.loads(policy_file.read_text())
                policy = Policy.from_dict(policy_data)
                self._policies[policy.policy_id] = policy
            except Exception as e:
                print(f"Warning: Failed to load policy {policy_file}: {e}")
    
    def create_policy(self, name: str,
                     pcr_baseline: Optional[Dict[int, str]] = None,
                     **kwargs) -> Policy:
        """
        Create a new policy
        
        Args:
            name: Policy name
            pcr_baseline: PCR baseline values (default: current state)
            **kwargs: Additional policy parameters
            
        Returns:
            Created Policy object
        """
        # Use current PCR state as baseline if not provided
        if pcr_baseline is None:
            pcr_indices = kwargs.get("pcr_indices", self.config.DEFAULT_PCRS)
            pcr_baseline = self.tpm.read_pcrs(pcr_indices)
        
        # Generate policy ID
        policy_id = self._generate_policy_id(name, pcr_baseline)
        
        # Create policy
        policy = Policy(
            policy_id=policy_id,
            name=name,
            pcr_baseline=pcr_baseline,
            **kwargs
        )
        
        # Store policy
        self._policies[policy_id] = policy
        self._save_policy(policy)
        
        return policy
    
    def _generate_policy_id(self, name: str, pcr_baseline: Dict[int, str]) -> str:
        """Generate unique policy ID using HMAC"""
        data = f"{name}{json.dumps(pcr_baseline, sort_keys=True)}{datetime.now().isoformat()}"
        key = hashlib.sha256(name.encode()).digest()
        return hmac.new(key, data.encode(), hashlib.sha256).hexdigest()[:16]
    
    def _save_policy(self, policy: Policy):
        """Save policy to storage"""
        policy_file = self.config.POLICY_STORAGE_PATH / f"{policy.policy_id}.json"
        policy_file.write_text(json.dumps(policy.to_dict(), indent=2))
    
    def validate_fingerprint(self, fingerprint: DeviceFingerprint,
                           policy: Policy) -> bool:
        """
        Validate fingerprint against policy
        
        Args:
            fingerprint: Fingerprint to validate
            policy: Policy to validate against
            
        Returns:
            True if valid
            
        Raises:
            PolicyViolationError: If validation fails
        """
        violations = []
        
        # Check expiry
        if fingerprint.is_expired():
            violations.append(PolicyViolationType.FINGERPRINT_EXPIRED)
        
        # Check PCR baseline
        current_pcrs = self.tpm.read_pcrs(list(policy.pcr_baseline.keys()))
        
        pcr_mismatches = []
        for pcr_idx, baseline_value in policy.pcr_baseline.items():
            if current_pcrs[pcr_idx] != baseline_value:
                pcr_mismatches.append(pcr_idx)
        
        if pcr_mismatches:
            violations.append(PolicyViolationType.PCR_MISMATCH)
            policy.mismatch_count += 1
            self._save_policy(policy)
        
        # Check if max attempts exceeded
        if policy.mismatch_count >= policy.max_mismatch_attempts:
            violations.append(PolicyViolationType.MAX_ATTEMPTS_EXCEEDED)
        
        # Check boot state
        if policy.auto_expire_on_boot_change:
            if self._detect_boot_state_change(fingerprint, policy):
                violations.append(PolicyViolationType.BOOT_STATE_CHANGED)
        
        # Check firmware updates
        if policy.auto_expire_on_firmware_update:
            if self._detect_firmware_update(fingerprint, policy):
                violations.append(PolicyViolationType.FIRMWARE_UPDATED)
        
        # Check secure boot
        if policy.require_secure_boot:
            if not self._verify_secure_boot(current_pcrs):
                violations.append(PolicyViolationType.SECURE_BOOT_VIOLATED)
        
        # Process violations
        if violations:
            self._handle_violations(violations, policy, fingerprint)
            raise PolicyViolationError(
                f"Policy validation failed: {', '.join(v.value for v in violations)}"
            )
        
        # Reset mismatch count on success
        if policy.mismatch_count > 0:
            policy.mismatch_count = 0
            self._save_policy(policy)
        
        return True
    
    def _detect_boot_state_change(self, fingerprint: DeviceFingerprint,
                                  policy: Policy) -> bool:
        """Detect if boot state has changed"""
        # Check PCRs related to boot (0-7)
        boot_pcrs = [0, 1, 2, 3, 4, 7]
        current_pcrs = self.tpm.read_pcrs(boot_pcrs)
        
        for pcr_idx in boot_pcrs:
            if pcr_idx in fingerprint.pcr_values:
                if current_pcrs[pcr_idx] != fingerprint.pcr_values[pcr_idx]:
                    return True
        
        return False
    
    def _detect_firmware_update(self, fingerprint: DeviceFingerprint,
                               policy: Policy) -> bool:
        """Detect if firmware has been updated"""
        # Check PCRs 0, 1 (firmware measurements)
        firmware_pcrs = [0, 1]
        current_pcrs = self.tpm.read_pcrs(firmware_pcrs)
        
        for pcr_idx in firmware_pcrs:
            if pcr_idx in policy.pcr_baseline:
                if current_pcrs[pcr_idx] != policy.pcr_baseline[pcr_idx]:
                    return True
        
        return False
    
    def _verify_secure_boot(self, pcr_values: Dict[int, str]) -> bool:
        """Verify secure boot is enabled (check PCR 7)"""
        # PCR 7 contains secure boot state
        # A non-zero value typically indicates secure boot is enabled
        if 7 not in pcr_values:
            return False
        
        # Check if PCR 7 is not all zeros (which would indicate disabled)
        pcr7_value = pcr_values[7]
        return pcr7_value != "0" * len(pcr7_value)
    
    def _handle_violations(self, violations: List[PolicyViolationType],
                          policy: Policy, fingerprint: DeviceFingerprint):
        """Handle policy violations by triggering appropriate actions"""
        actions_to_execute = set()
        
        # Collect all actions for the violations
        for violation in violations:
            if violation in policy.actions:
                actions_to_execute.update(policy.actions[violation])
        
        # Execute actions
        for action in actions_to_execute:
            self._execute_action(action, violation, policy, fingerprint)
        
        # Call registered handlers
        for violation in violations:
            if violation in self._violation_handlers:
                for handler in self._violation_handlers[violation]:
                    try:
                        handler(violation, policy, fingerprint)
                    except Exception as e:
                        print(f"Violation handler error: {e}")
    
    def _execute_action(self, action: PolicyAction, violation: PolicyViolationType,
                       policy: Policy, fingerprint: DeviceFingerprint):
        """Execute a policy action"""
        # Action execution is delegated to ConsequenceHandler
        # This is a placeholder that logs the action
        print(f"Policy action: {action.value} for violation: {violation.value}")
    
    def register_violation_handler(self, violation_type: PolicyViolationType,
                                   handler: Callable):
        """
        Register a custom handler for policy violations
        
        Args:
            violation_type: Type of violation to handle
            handler: Callable that takes (violation, policy, fingerprint)
        """
        if violation_type not in self._violation_handlers:
            self._violation_handlers[violation_type] = []
        self._violation_handlers[violation_type].append(handler)
    
    def update_policy_baseline(self, policy: Policy,
                              new_baseline: Optional[Dict[int, str]] = None):
        """
        Update policy baseline to current state
        
        Args:
            policy: Policy to update
            new_baseline: New baseline (default: current PCR state)
        """
        if new_baseline is None:
            new_baseline = self.tpm.read_pcrs(list(policy.pcr_baseline.keys()))
        
        policy.pcr_baseline = new_baseline
        policy.mismatch_count = 0
        self._save_policy(policy)
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get policy by ID"""
        return self._policies.get(policy_id)
    
    def list_policies(self) -> List[Policy]:
        """List all policies"""
        return list(self._policies.values())
    
    def delete_policy(self, policy_id: str):
        """Delete a policy"""
        if policy_id in self._policies:
            del self._policies[policy_id]
            policy_file = self.config.POLICY_STORAGE_PATH / f"{policy_id}.json"
            if policy_file.exists():
                policy_file.unlink()
    
    def check_state_changes(self, fingerprint: DeviceFingerprint) -> Dict[str, Any]:
        """
        Check for state changes that would invalidate fingerprint
        
        Returns:
            Dictionary with state change information
        """
        state_changes = {
            "boot_state_changed": False,
            "firmware_updated": False,
            "secure_boot_violated": False,
            "pcr_mismatches": [],
            "timestamp": datetime.now().isoformat()
        }
        
        current_pcrs = self.tpm.read_pcrs(list(fingerprint.pcr_values.keys()))
        
        # Check each PCR
        for pcr_idx, expected_value in fingerprint.pcr_values.items():
            if current_pcrs[pcr_idx] != expected_value:
                state_changes["pcr_mismatches"].append({
                    "pcr": pcr_idx,
                    "expected": expected_value,
                    "current": current_pcrs[pcr_idx]
                })
                
                # Classify the change
                if pcr_idx in [0, 1, 2, 3, 4, 7]:
                    state_changes["boot_state_changed"] = True
                if pcr_idx in [0, 1]:
                    state_changes["firmware_updated"] = True
                if pcr_idx == 7:
                    state_changes["secure_boot_violated"] = True
        
        return state_changes
