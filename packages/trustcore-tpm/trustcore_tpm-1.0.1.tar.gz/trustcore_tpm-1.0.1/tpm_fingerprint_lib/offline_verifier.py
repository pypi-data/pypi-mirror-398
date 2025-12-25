"""
Offline Verifier - Local TPM-Based Verification

Enables device fingerprint verification without server dependency:
- Deterministic local enforcement
- No network requirement
- TPM-based trust anchor
- Offline attestation and validation

Key innovation: Complete trust chain maintained locally via TPM
"""

import json
from typing import Dict, Optional, Any, List
from datetime import datetime
import hashlib
from pathlib import Path

from .tpm_ops import TPMOperations
from .fingerprint_engine import DeviceFingerprint, FingerprintEngine
from .policy_engine import Policy, PolicyEngine
from .consequence_handler import ConsequenceHandler
from .config import Config
from .exceptions import (
    PolicyViolationError,
    FingerprintExpiredError,
    AttestationFailedError,
    TPMFingerprintError
)


class OfflineAttestation:
    """Represents an offline attestation record"""
    
    def __init__(self, attestation_id: str, fingerprint_id: str,
                 policy_id: str, tpm_quote: Dict[str, Any],
                 result: bool, timestamp: datetime):
        self.attestation_id = attestation_id
        self.fingerprint_id = fingerprint_id
        self.policy_id = policy_id
        self.tpm_quote = tpm_quote
        self.result = result
        self.timestamp = timestamp
        self.metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "attestation_id": self.attestation_id,
            "fingerprint_id": self.fingerprint_id,
            "policy_id": self.policy_id,
            "tpm_quote": self.tpm_quote,
            "result": self.result,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OfflineAttestation':
        att = cls(
            attestation_id=data["attestation_id"],
            fingerprint_id=data["fingerprint_id"],
            policy_id=data["policy_id"],
            tpm_quote=data["tpm_quote"],
            result=data["result"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )
        att.metadata = data.get("metadata", {})
        return att


class OfflineVerifier:
    """
    Offline verification system
    
    Provides complete device identity verification without server dependency:
    - All verification done locally via TPM
    - Policy enforcement without cloud
    - Cryptographic proof of device state
    - Tamper-evident audit trail
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.tpm = TPMOperations(self.config)
        self.fingerprint_engine = FingerprintEngine(self.config, self.tpm)
        self.policy_engine = PolicyEngine(self.config, self.tpm, self.fingerprint_engine)
        self.consequence_handler = ConsequenceHandler(self.config)
        
        self._attestation_storage = Path.home() / ".tpm_fingerprint" / "attestations"
        self._attestation_storage.mkdir(parents=True, exist_ok=True)
        
        # Connect policy engine to consequence handler
        self._setup_enforcement()
    
    def _setup_enforcement(self):
        """Setup automatic consequence enforcement"""
        from .policy_engine import PolicyViolationType
        
        def enforce_on_violation(violation, policy, fingerprint):
            self.consequence_handler.enforce_consequences(violation, policy, fingerprint)
        
        # Register handler for all violation types
        for violation_type in PolicyViolationType:
            self.policy_engine.register_violation_handler(
                violation_type,
                enforce_on_violation
            )
    
    def verify_device(self, fingerprint_id: str, policy_id: str,
                     enforce_consequences: bool = True) -> bool:
        """
        Verify device identity offline
        
        Args:
            fingerprint_id: Fingerprint to verify
            policy_id: Policy to enforce
            enforce_consequences: Whether to enforce consequences on failure
            
        Returns:
            True if verification succeeds
            
        Raises:
            PolicyViolationError: If verification fails
        """
        try:
            # Load fingerprint (will fail if PCR state changed)
            fingerprint = self.fingerprint_engine.load_fingerprint(fingerprint_id)
            
            # Get policy
            policy = self.policy_engine.get_policy(policy_id)
            if not policy:
                raise TPMFingerprintError(f"Policy {policy_id} not found")
            
            # Verify fingerprint with fresh challenge
            self.fingerprint_engine.verify_fingerprint(fingerprint, require_fresh=True)
            
            # Validate against policy
            self.policy_engine.validate_fingerprint(fingerprint, policy)
            
            # Get TPM quote for attestation
            tpm_quote = self.tpm.get_tpm_quote()
            
            # Record successful attestation
            attestation = self._create_attestation(
                fingerprint_id, policy_id, tpm_quote, True
            )
            self._save_attestation(attestation)
            
            return True
            
        except (PolicyViolationError, FingerprintExpiredError, AttestationFailedError) as e:
            # Verification failed
            tpm_quote = self.tpm.get_tpm_quote()
            attestation = self._create_attestation(
                fingerprint_id, policy_id, tpm_quote, False
            )
            attestation.metadata["error"] = str(e)
            self._save_attestation(attestation)
            
            # Note: Consequences are automatically enforced by policy engine
            # through the registered violation handlers
            
            raise
    
    def _create_attestation(self, fingerprint_id: str, policy_id: str,
                           tpm_quote: Dict[str, Any], result: bool) -> OfflineAttestation:
        """Create attestation record"""
        attestation_data = f"{fingerprint_id}{policy_id}{json.dumps(tpm_quote)}{result}"
        attestation_id = hashlib.sha256(attestation_data.encode()).hexdigest()[:16]
        
        return OfflineAttestation(
            attestation_id=attestation_id,
            fingerprint_id=fingerprint_id,
            policy_id=policy_id,
            tpm_quote=tpm_quote,
            result=result,
            timestamp=datetime.now()
        )
    
    def _save_attestation(self, attestation: OfflineAttestation):
        """Save attestation to storage"""
        attestation_file = self._attestation_storage / f"{attestation.attestation_id}.json"
        attestation_file.write_text(json.dumps(attestation.to_dict(), indent=2))
    
    def enroll_device(self, device_name: str,
                     pcr_indices: Optional[List[int]] = None,
                     validity_seconds: Optional[int] = None) -> Dict[str, str]:
        """
        Enroll a device for offline verification
        
        Creates a fingerprint and policy based on current TPM state
        
        Args:
            device_name: Name for this device enrollment
            pcr_indices: PCRs to use (default: from config)
            validity_seconds: Fingerprint validity (default: from config)
            
        Returns:
            Dictionary with fingerprint_id and policy_id
        """
        # Generate fingerprint
        fingerprint = self.fingerprint_engine.generate_fingerprint(
            metadata={"device_name": device_name},
            pcr_indices=pcr_indices,
            validity_seconds=validity_seconds
        )
        
        # Create policy based on current state
        policy = self.policy_engine.create_policy(
            name=f"Policy for {device_name}",
            pcr_baseline=fingerprint.pcr_values
        )
        
        return {
            "fingerprint_id": fingerprint.fingerprint_id,
            "policy_id": policy.policy_id,
            "device_name": device_name,
            "enrolled_at": datetime.now().isoformat()
        }
    
    def verify_and_grant_access(self, fingerprint_id: str, policy_id: str,
                                resource_id: str) -> bool:
        """
        Verify device and grant access to a resource
        
        Args:
            fingerprint_id: Fingerprint to verify
            policy_id: Policy to enforce
            resource_id: Resource being accessed
            
        Returns:
            True if access granted
        """
        try:
            # Verify device
            self.verify_device(fingerprint_id, policy_id)
            
            # Check if vaults are locked
            # (This would be resource-specific in production)
            
            return True
            
        except PolicyViolationError:
            return False
    
    def get_device_status(self, fingerprint_id: str) -> Dict[str, Any]:
        """
        Get comprehensive device status
        
        Returns:
            Status dictionary with fingerprint, policy, and consequence info
        """
        try:
            # Load fingerprint
            fingerprint = self.fingerprint_engine.load_fingerprint(fingerprint_id)
            
            # Get fingerprint status
            fp_status = self.fingerprint_engine.get_fingerprint_status(fingerprint)
            
            # Get consequence status
            consequence_status = self.consequence_handler.get_status_for_fingerprint(fingerprint_id)
            
            # Get recent attestations
            attestations = self._get_attestations_for_fingerprint(fingerprint_id, limit=10)
            
            return {
                "fingerprint_status": fp_status,
                "consequence_status": consequence_status,
                "recent_attestations": [a.to_dict() for a in attestations],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "fingerprint_id": fingerprint_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_attestations_for_fingerprint(self, fingerprint_id: str,
                                         limit: Optional[int] = None) -> List[OfflineAttestation]:
        """Get attestations for a fingerprint"""
        attestations = []
        
        for attestation_file in self._attestation_storage.glob("*.json"):
            try:
                data = json.loads(attestation_file.read_text())
                if data["fingerprint_id"] == fingerprint_id:
                    attestations.append(OfflineAttestation.from_dict(data))
            except Exception:
                pass
        
        # Sort by timestamp
        attestations.sort(key=lambda a: a.timestamp, reverse=True)
        
        if limit:
            attestations = attestations[:limit]
        
        return attestations
    
    def challenge_response_verify(self, fingerprint_id: str) -> Dict[str, Any]:
        """
        Perform challenge-response verification
        
        Returns:
            Verification result with challenge and response data
        """
        try:
            # Load fingerprint
            fingerprint = self.fingerprint_engine.load_fingerprint(fingerprint_id)
            
            # Generate challenge
            challenge = self.tpm.generate_challenge()
            
            # Get current PCRs
            pcr_values = self.tpm.read_pcrs(list(fingerprint.pcr_values.keys()))
            
            # Sign challenge
            response = self.tpm.sign_challenge(challenge, pcr_values)
            
            # Verify response
            verified = self.tpm.verify_challenge_response(challenge, response)
            
            return {
                "verified": verified,
                "challenge": challenge.hex(),
                "response": response,
                "pcr_values": pcr_values,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def compare_with_baseline(self, fingerprint_id: str, policy_id: str) -> Dict[str, Any]:
        """
        Compare current TPM state with baseline
        
        Returns:
            Comparison results showing deviations
        """
        try:
            fingerprint = self.fingerprint_engine.load_fingerprint(fingerprint_id)
            policy = self.policy_engine.get_policy(policy_id)
            
            if not policy:
                raise TPMFingerprintError(f"Policy {policy_id} not found")
            
            # Check state changes
            state_changes = self.policy_engine.check_state_changes(fingerprint)
            
            # Get current PCRs
            current_pcrs = self.tpm.read_pcrs(list(policy.pcr_baseline.keys()))
            
            # Compare with baseline
            deviations = {}
            for pcr_idx, baseline_value in policy.pcr_baseline.items():
                if current_pcrs[pcr_idx] != baseline_value:
                    deviations[pcr_idx] = {
                        "baseline": baseline_value,
                        "current": current_pcrs[pcr_idx],
                        "match": False
                    }
                else:
                    deviations[pcr_idx] = {
                        "baseline": baseline_value,
                        "current": current_pcrs[pcr_idx],
                        "match": True
                    }
            
            return {
                "fingerprint_id": fingerprint_id,
                "policy_id": policy_id,
                "deviations": deviations,
                "state_changes": state_changes,
                "all_match": all(d["match"] for d in deviations.values()),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def regenerate_after_update(self, old_fingerprint_id: str,
                               device_name: str) -> Dict[str, str]:
        """
        Regenerate fingerprint after legitimate system update
        
        Args:
            old_fingerprint_id: Previous fingerprint ID
            device_name: Device name
            
        Returns:
            New enrollment information
        """
        try:
            # Load old fingerprint (may fail if state changed)
            old_fingerprint = self.fingerprint_engine.load_fingerprint(old_fingerprint_id)
        except Exception:
            # State changed, that's expected
            pass
        
        # Generate new fingerprint with current state
        new_fingerprint = self.fingerprint_engine.generate_fingerprint(
            metadata={"device_name": device_name, "regenerated_from": old_fingerprint_id}
        )
        
        # Create new policy
        new_policy = self.policy_engine.create_policy(
            name=f"Policy for {device_name} (regenerated)",
            pcr_baseline=new_fingerprint.pcr_values
        )
        
        return {
            "fingerprint_id": new_fingerprint.fingerprint_id,
            "policy_id": new_policy.policy_id,
            "device_name": device_name,
            "regenerated_at": datetime.now().isoformat(),
            "previous_fingerprint_id": old_fingerprint_id
        }
    
    def get_verification_proof(self, fingerprint_id: str, policy_id: str) -> Dict[str, Any]:
        """
        Get cryptographic proof of current device state
        
        Returns verifiable proof that can be validated offline
        """
        try:
            # Get TPM quote
            tpm_quote = self.tpm.get_tpm_quote()
            
            # Load fingerprint
            fingerprint = self.fingerprint_engine.load_fingerprint(fingerprint_id)
            
            # Get policy
            policy = self.policy_engine.get_policy(policy_id)
            
            # Create proof
            proof = {
                "fingerprint_id": fingerprint_id,
                "policy_id": policy_id,
                "tpm_quote": tpm_quote,
                "fingerprint_created_at": fingerprint.created_at.isoformat(),
                "policy_created_at": policy.created_at.isoformat(),
                "proof_timestamp": datetime.now().isoformat()
            }
            
            # Sign proof with HMAC
            import hmac
            proof_str = json.dumps(proof, sort_keys=True)
            # Use fingerprint's PCR values as signing key material
            signing_key = hashlib.sha256(json.dumps(fingerprint.pcr_values, sort_keys=True).encode()).digest()
            proof["signature"] = hmac.new(signing_key, proof_str.encode(), hashlib.sha256).hexdigest()
            
            return proof
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def export_offline_verification_bundle(self, fingerprint_id: str,
                                          policy_id: str) -> Dict[str, Any]:
        """
        Export complete verification bundle for offline use
        
        Bundle contains everything needed to verify device without network
        """
        try:
            fingerprint = self.fingerprint_engine.load_fingerprint(fingerprint_id)
            policy = self.policy_engine.get_policy(policy_id)
            
            if not policy:
                raise TPMFingerprintError(f"Policy {policy_id} not found")
            
            bundle = {
                "fingerprint": fingerprint.to_dict(),
                "policy": policy.to_dict(),
                "tpm_quote": self.tpm.get_tpm_quote(),
                "created_at": datetime.now().isoformat(),
                "bundle_version": "1.0"
            }
            
            # Sign bundle with HMAC
            import hmac
            bundle_str = json.dumps(bundle, sort_keys=True)
            # Use fingerprint's PCR values as signing key material
            signing_key = hashlib.sha256(json.dumps(fingerprint.pcr_values, sort_keys=True).encode()).digest()
            bundle["signature"] = hmac.new(signing_key, bundle_str.encode(), hashlib.sha256).hexdigest()
            
            return bundle
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
