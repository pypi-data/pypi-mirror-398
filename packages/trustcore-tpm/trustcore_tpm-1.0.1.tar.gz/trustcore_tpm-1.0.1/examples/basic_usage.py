"""
Basic usage example for TPM Fingerprint Library

Demonstrates:
- Device enrollment
- Fingerprint generation
- Offline verification
- Policy enforcement
"""

from tpm_fingerprint_lib import (
    FingerprintEngine,
    PolicyEngine,
    ConsequenceHandler,
    OfflineVerifier
)
from tpm_fingerprint_lib.audit_logger import AuditLogger

def main():
    print("=" * 60)
    print("TPM Fingerprint Library - Basic Example")
    print("=" * 60)
    
    # Initialize the offline verifier (includes all components)
    print("\n1. Initializing offline verifier...")
    verifier = OfflineVerifier()
    
    # Enroll the device
    print("\n2. Enrolling device...")
    enrollment = verifier.enroll_device(
        device_name="MyWorkstation",
        validity_seconds=86400  # 24 hours
    )
    print(f"   Fingerprint ID: {enrollment['fingerprint_id']}")
    print(f"   Policy ID: {enrollment['policy_id']}")
    
    fingerprint_id = enrollment['fingerprint_id']
    policy_id = enrollment['policy_id']
    
    # Verify the device
    print("\n3. Verifying device...")
    try:
        result = verifier.verify_device(fingerprint_id, policy_id)
        print(f"   ✓ Verification successful: {result}")
    except Exception as e:
        print(f"   ✗ Verification failed: {e}")
    
    # Get device status
    print("\n4. Getting device status...")
    status = verifier.get_device_status(fingerprint_id)
    print(f"   Fingerprint valid: {status['fingerprint_status']['is_valid']}")
    print(f"   PCR state matches: {status['fingerprint_status']['pcr_state']['all_match']}")
    
    # Perform challenge-response verification
    print("\n5. Performing challenge-response verification...")
    challenge_result = verifier.challenge_response_verify(fingerprint_id)
    print(f"   ✓ Challenge verified: {challenge_result['verified']}")
    
    # Register a credential
    print("\n6. Registering credential...")
    credential = verifier.consequence_handler.register_credential(
        credential_id="api_key_001",
        credential_type="api_key",
        data={"key": "secret_api_key_value"},
        fingerprint_id=fingerprint_id
    )
    print(f"   ✓ Credential registered: {credential.credential_id}")
    
    # Register a vault
    print("\n7. Registering vault...")
    vault = verifier.consequence_handler.register_vault(
        vault_id="vault_001",
        name="My Secure Vault",
        fingerprint_id=fingerprint_id
    )
    print(f"   ✓ Vault registered: {vault.vault_id}")
    
    # Check vault accessibility
    print("\n8. Checking vault accessibility...")
    accessible = verifier.consequence_handler.is_vault_accessible(vault.vault_id)
    print(f"   Vault accessible: {accessible}")
    
    # Get verification proof
    print("\n9. Getting cryptographic proof...")
    proof = verifier.get_verification_proof(fingerprint_id, policy_id)
    print(f"   Proof signature: {proof.get('signature', 'N/A')[:32]}...")
    
    # Compare with baseline
    print("\n10. Comparing with baseline...")
    comparison = verifier.compare_with_baseline(fingerprint_id, policy_id)
    print(f"    All PCRs match baseline: {comparison['all_match']}")
    
    # Get audit statistics
    print("\n11. Audit log statistics...")
    audit_logger = AuditLogger()
    stats = audit_logger.get_statistics()
    print(f"    Total events: {stats['total_events']}")
    print(f"    Events by type: {len(stats['events_by_type'])} types")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
