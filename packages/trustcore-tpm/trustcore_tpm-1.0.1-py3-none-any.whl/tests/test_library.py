"""
Unit tests for TPM Fingerprint Library

Run with: pytest tests/test_library.py -v
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from tpm_fingerprint_lib import (
    FingerprintEngine,
    PolicyEngine,
    ConsequenceHandler,
    OfflineVerifier
)
from tpm_fingerprint_lib.tpm_ops import TPMOperations
from tpm_fingerprint_lib.config import Config
from tpm_fingerprint_lib.audit_logger import AuditLogger, AuditEventType
from tpm_fingerprint_lib.exceptions import (
    PolicyViolationError,
    FingerprintExpiredError,
    PCRMismatchError
)
from tpm_fingerprint_lib.policy_engine import PolicyViolationType


@pytest.fixture
def temp_config():
    """Create temporary configuration for testing"""
    temp_dir = Path(tempfile.mkdtemp())
    config = Config()
    config.AUDIT_LOG_PATH = temp_dir / "audit.log"
    config.SEALED_DATA_PATH = temp_dir / "sealed"
    config.FINGERPRINT_STORAGE_PATH = temp_dir / "fingerprints"
    config.POLICY_STORAGE_PATH = temp_dir / "policies"
    config.ensure_directories()
    
    yield config
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestTPMOperations:
    """Test TPM operations"""
    
    def test_tpm_availability(self, temp_config):
        """Test TPM availability check"""
        tpm = TPMOperations(temp_config)
        # Should not raise exception
        is_available = tpm.is_tpm_available()
        assert isinstance(is_available, bool)
    
    def test_read_pcrs(self, temp_config):
        """Test reading PCRs"""
        tpm = TPMOperations(temp_config)
        pcrs = tpm.read_pcrs([0, 1, 2, 3, 7])
        
        assert isinstance(pcrs, dict)
        assert len(pcrs) == 5
        for pcr_idx, value in pcrs.items():
            assert isinstance(pcr_idx, int)
            assert isinstance(value, str)
            assert len(value) > 0
    
    def test_challenge_generation(self, temp_config):
        """Test challenge generation"""
        tpm = TPMOperations(temp_config)
        challenge = tpm.generate_challenge()
        
        assert isinstance(challenge, bytes)
        assert len(challenge) == temp_config.CHALLENGE_NONCE_SIZE
    
    def test_challenge_response(self, temp_config):
        """Test challenge-response protocol"""
        tpm = TPMOperations(temp_config)
        
        # Generate challenge
        challenge = tpm.generate_challenge()
        
        # Get PCRs
        pcrs = tpm.read_pcrs([0, 1, 2, 3])
        
        # Sign challenge
        response = tpm.sign_challenge(challenge, pcrs)
        
        # Verify response
        verified = tpm.verify_challenge_response(challenge, response)
        assert verified is True
    
    def test_seal_unseal(self, temp_config):
        """Test data sealing and unsealing"""
        tpm = TPMOperations(temp_config)
        
        data = b"secret data to seal"
        
        # Seal
        sealed = tpm.seal_data(data, [0, 1, 2])
        assert isinstance(sealed, bytes)
        
        # Unseal
        unsealed = tpm.unseal_data(sealed)
        assert unsealed == data


class TestFingerprintEngine:
    """Test fingerprint engine"""
    
    def test_fingerprint_generation(self, temp_config):
        """Test fingerprint generation"""
        engine = FingerprintEngine(temp_config)
        
        fingerprint = engine.generate_fingerprint(
            metadata={"device": "test"},
            validity_seconds=3600
        )
        
        assert fingerprint.fingerprint_id is not None
        assert len(fingerprint.pcr_values) > 0
        assert fingerprint.expires_at is not None
    
    def test_fingerprint_verification(self, temp_config):
        """Test fingerprint verification"""
        engine = FingerprintEngine(temp_config)
        
        fingerprint = engine.generate_fingerprint()
        
        # Should verify successfully
        result = engine.verify_fingerprint(fingerprint)
        assert result is True
    
    def test_fingerprint_expiry(self, temp_config):
        """Test fingerprint expiry"""
        engine = FingerprintEngine(temp_config)
        
        # Create fingerprint that expires immediately
        fingerprint = engine.generate_fingerprint(validity_seconds=0)
        
        # Should be expired
        assert fingerprint.is_expired() is True
    
    def test_fingerprint_persistence(self, temp_config):
        """Test fingerprint storage and loading"""
        engine = FingerprintEngine(temp_config)
        
        # Generate and save
        fp1 = engine.generate_fingerprint()
        fp_id = fp1.fingerprint_id
        
        # Load
        fp2 = engine.load_fingerprint(fp_id)
        
        assert fp2.fingerprint_id == fp1.fingerprint_id
        assert fp2.pcr_values == fp1.pcr_values


class TestPolicyEngine:
    """Test policy engine"""
    
    def test_policy_creation(self, temp_config):
        """Test policy creation"""
        tpm = TPMOperations(temp_config)
        engine = PolicyEngine(temp_config, tpm)
        
        policy = engine.create_policy(
            name="Test Policy",
            max_mismatch_attempts=3
        )
        
        assert policy.policy_id is not None
        assert policy.name == "Test Policy"
        assert len(policy.pcr_baseline) > 0
    
    def test_policy_validation_success(self, temp_config):
        """Test successful policy validation"""
        tpm = TPMOperations(temp_config)
        fp_engine = FingerprintEngine(temp_config, tpm)
        policy_engine = PolicyEngine(temp_config, tpm, fp_engine)
        
        # Create fingerprint and policy
        fingerprint = fp_engine.generate_fingerprint()
        policy = policy_engine.create_policy(
            name="Test",
            pcr_baseline=fingerprint.pcr_values
        )
        
        # Should validate successfully
        result = policy_engine.validate_fingerprint(fingerprint, policy)
        assert result is True
    
    def test_policy_violation_detection(self, temp_config):
        """Test policy violation detection"""
        tpm = TPMOperations(temp_config)
        fp_engine = FingerprintEngine(temp_config, tpm)
        policy_engine = PolicyEngine(temp_config, tpm, fp_engine)
        
        # Create fingerprint
        fingerprint = fp_engine.generate_fingerprint()
        
        # Create policy with different baseline
        different_pcrs = {k: "0" * 64 for k in fingerprint.pcr_values.keys()}
        policy = policy_engine.create_policy(
            name="Test",
            pcr_baseline=different_pcrs
        )
        
        # Should raise PolicyViolationError
        with pytest.raises(PolicyViolationError):
            policy_engine.validate_fingerprint(fingerprint, policy)


class TestConsequenceHandler:
    """Test consequence handler"""
    
    def test_credential_registration(self, temp_config):
        """Test credential registration"""
        handler = ConsequenceHandler(temp_config)
        
        cred = handler.register_credential(
            credential_id="test_cred",
            credential_type="api_key",
            data={"key": "secret"},
            fingerprint_id="fp_001"
        )
        
        assert cred.credential_id == "test_cred"
        assert handler.is_credential_valid("test_cred") is True
    
    def test_credential_revocation(self, temp_config):
        """Test credential revocation"""
        handler = ConsequenceHandler(temp_config)
        
        cred = handler.register_credential(
            credential_id="test_cred",
            credential_type="api_key",
            data={"key": "secret"},
            fingerprint_id="fp_001"
        )
        
        handler.revoke_credential("test_cred", "Test revocation")
        
        assert handler.is_credential_valid("test_cred") is False
    
    def test_vault_management(self, temp_config):
        """Test vault management"""
        handler = ConsequenceHandler(temp_config)
        
        vault = handler.register_vault(
            vault_id="vault_001",
            name="Test Vault",
            fingerprint_id="fp_001"
        )
        
        # Initially accessible
        assert handler.is_vault_accessible("vault_001") is True
        
        # Lock vault
        handler.lock_vault("vault_001", "Test lock")
        assert handler.is_vault_accessible("vault_001") is False
        
        # Unlock vault
        handler.unlock_vault("vault_001")
        assert handler.is_vault_accessible("vault_001") is True
    
    def test_token_management(self, temp_config):
        """Test token management"""
        handler = ConsequenceHandler(temp_config)
        
        token = handler.register_token(
            token_id="token_001",
            token_value="abc123",
            fingerprint_id="fp_001"
        )
        
        assert handler.is_token_valid("token_001") is True
        
        handler.invalidate_token("token_001", "Test invalidation")
        assert handler.is_token_valid("token_001") is False


class TestOfflineVerifier:
    """Test offline verifier"""
    
    def test_device_enrollment(self, temp_config):
        """Test device enrollment"""
        verifier = OfflineVerifier(temp_config)
        
        enrollment = verifier.enroll_device("TestDevice")
        
        assert "fingerprint_id" in enrollment
        assert "policy_id" in enrollment
        assert enrollment["device_name"] == "TestDevice"
    
    def test_device_verification(self, temp_config):
        """Test device verification"""
        verifier = OfflineVerifier(temp_config)
        
        # Enroll
        enrollment = verifier.enroll_device("TestDevice")
        
        # Verify
        result = verifier.verify_device(
            enrollment["fingerprint_id"],
            enrollment["policy_id"]
        )
        
        assert result is True
    
    def test_device_status(self, temp_config):
        """Test getting device status"""
        verifier = OfflineVerifier(temp_config)
        
        enrollment = verifier.enroll_device("TestDevice")
        status = verifier.get_device_status(enrollment["fingerprint_id"])
        
        assert "fingerprint_status" in status
        assert "consequence_status" in status
    
    def test_verification_bundle_export(self, temp_config):
        """Test exporting verification bundle"""
        verifier = OfflineVerifier(temp_config)
        
        enrollment = verifier.enroll_device("TestDevice")
        bundle = verifier.export_offline_verification_bundle(
            enrollment["fingerprint_id"],
            enrollment["policy_id"]
        )
        
        assert "fingerprint" in bundle
        assert "policy" in bundle
        assert "signature" in bundle


class TestAuditLogger:
    """Test audit logger"""
    
    def test_event_logging(self, temp_config):
        """Test logging events"""
        logger = AuditLogger(temp_config)
        
        logger.log_event(
            AuditEventType.FINGERPRINT_GENERATED,
            {"test": "data"},
            fingerprint_id="fp_001"
        )
        
        events = logger.get_events()
        assert len(events) >= 1
    
    def test_event_retrieval(self, temp_config):
        """Test retrieving events"""
        logger = AuditLogger(temp_config)
        
        # Log multiple events
        for i in range(5):
            logger.log_event(
                AuditEventType.FINGERPRINT_VERIFIED,
                {"iteration": i},
                fingerprint_id=f"fp_{i}"
            )
        
        # Get all events
        events = logger.get_events()
        assert len(events) >= 5
        
        # Get events for specific fingerprint
        events_fp0 = logger.get_events(fingerprint_id="fp_0")
        assert len(events_fp0) >= 1
    
    def test_audit_statistics(self, temp_config):
        """Test audit statistics"""
        logger = AuditLogger(temp_config)
        
        # Log some events
        logger.log_fingerprint_generated("fp_001", {"test": "data"})
        logger.log_fingerprint_verified("fp_001", {"test": "data"})
        
        stats = logger.get_statistics()
        
        assert "total_events" in stats
        assert "events_by_type" in stats
        assert stats["total_events"] >= 2


class TestIntegration:
    """Integration tests"""
    
    def test_full_workflow(self, temp_config):
        """Test complete workflow"""
        verifier = OfflineVerifier(temp_config)
        
        # 1. Enroll device
        enrollment = verifier.enroll_device("IntegrationTest")
        fp_id = enrollment["fingerprint_id"]
        policy_id = enrollment["policy_id"]
        
        # 2. Register resources
        verifier.consequence_handler.register_credential(
            credential_id="test_cred",
            credential_type="api",
            data={"key": "value"},
            fingerprint_id=fp_id
        )
        
        # 3. Verify device
        result = verifier.verify_device(fp_id, policy_id)
        assert result is True
        
        # 4. Check credential validity
        assert verifier.consequence_handler.is_credential_valid("test_cred") is True
        
        # 5. Get status
        status = verifier.get_device_status(fp_id)
        assert status["fingerprint_status"]["is_valid"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
