"""
Advanced example: Policy violation and consequence enforcement

Demonstrates:
- Custom policy creation
- Policy violation detection
- Automatic consequence enforcement
- Credential revocation
- Vault lockdown
"""

from tpm_fingerprint_lib import (
    OfflineVerifier,
    PolicyViolationError
)
from tpm_fingerprint_lib.policy_engine import PolicyViolationType, PolicyAction
from tpm_fingerprint_lib.consequence_handler import ConsequenceType
from tpm_fingerprint_lib.audit_logger import AuditLogger, AuditEventType

def main():
    print("=" * 60)
    print("TPM Fingerprint Library - Advanced Example")
    print("Policy Violation & Consequence Enforcement")
    print("=" * 60)
    
    # Initialize
    verifier = OfflineVerifier()
    audit_logger = AuditLogger()
    
    # Enroll device
    print("\n1. Enrolling device...")
    enrollment = verifier.enroll_device("SecureWorkstation")
    fingerprint_id = enrollment['fingerprint_id']
    policy_id = enrollment['policy_id']
    print(f"   ✓ Device enrolled")
    
    # Register resources
    print("\n2. Registering protected resources...")
    
    # Register credentials
    credential1 = verifier.consequence_handler.register_credential(
        credential_id="db_creds_001",
        credential_type="database",
        data={"username": "admin", "password": "secret"},
        fingerprint_id=fingerprint_id
    )
    
    credential2 = verifier.consequence_handler.register_credential(
        credential_id="api_token_001",
        credential_type="api_token",
        data={"token": "abc123xyz"},
        fingerprint_id=fingerprint_id
    )
    
    # Register vault
    vault = verifier.consequence_handler.register_vault(
        vault_id="secure_vault_001",
        name="Production Secrets",
        fingerprint_id=fingerprint_id
    )
    
    print(f"   ✓ Registered {len([credential1, credential2])} credentials")
    print(f"   ✓ Registered vault: {vault.name}")
    
    # Create custom policy with strict enforcement
    print("\n3. Creating custom policy...")
    policy = verifier.policy_engine.get_policy(policy_id)
    
    # Customize policy actions
    policy.actions = {
        PolicyViolationType.PCR_MISMATCH: [
            PolicyAction.DENY,
            PolicyAction.AUDIT_LOG,
            PolicyAction.ALERT
        ],
        PolicyViolationType.BOOT_STATE_CHANGED: [
            PolicyAction.REVOKE_CREDENTIALS,
            PolicyAction.LOCKDOWN_VAULT,
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
    
    policy.max_mismatch_attempts = 3
    print(f"   ✓ Policy configured with strict enforcement")
    
    # Register custom violation handler
    print("\n4. Registering custom violation handler...")
    
    def custom_violation_handler(violation, policy, fingerprint):
        print(f"\n   !!! CUSTOM HANDLER TRIGGERED !!!")
        print(f"   Violation: {violation.value}")
        print(f"   Taking additional security measures...")
        
        # Additional custom actions could go here
        # e.g., send email, trigger external API, etc.
    
    verifier.policy_engine.register_violation_handler(
        PolicyViolationType.BOOT_STATE_CHANGED,
        custom_violation_handler
    )
    print(f"   ✓ Custom handler registered")
    
    # Verify device (should succeed initially)
    print("\n5. Performing initial verification...")
    try:
        verifier.verify_device(fingerprint_id, policy_id)
        print(f"   ✓ Verification successful")
    except PolicyViolationError as e:
        print(f"   ✗ Verification failed: {e}")
    
    # Check credential status
    print("\n6. Checking credential status...")
    cred_valid = verifier.consequence_handler.is_credential_valid(credential1.credential_id)
    vault_accessible = verifier.consequence_handler.is_vault_accessible(vault.vault_id)
    print(f"   Credentials valid: {cred_valid}")
    print(f"   Vault accessible: {vault_accessible}")
    
    # Simulate policy violations
    print("\n7. Simulating policy violation scenarios...")
    print("\n   Scenario A: Incrementing mismatch count...")
    
    # Manually increment mismatch count to trigger max attempts
    for i in range(4):
        policy.mismatch_count = i
        print(f"   Attempt {i+1}: mismatch_count = {policy.mismatch_count}")
        
        if policy.mismatch_count >= policy.max_mismatch_attempts:
            print(f"   !!! Maximum attempts exceeded !!!")
            
            # Trigger consequences
            verifier.consequence_handler.enforce_consequences(
                PolicyViolationType.MAX_ATTEMPTS_EXCEEDED,
                policy,
                verifier.fingerprint_engine.load_fingerprint(fingerprint_id)
            )
            break
    
    # Check consequences
    print("\n8. Checking consequences after violation...")
    cred_valid = verifier.consequence_handler.is_credential_valid(credential1.credential_id)
    vault_accessible = verifier.consequence_handler.is_vault_accessible(vault.vault_id)
    print(f"   Credentials valid: {cred_valid}")
    print(f"   Vault accessible: {vault_accessible}")
    
    # Get consequence history
    print("\n9. Reviewing consequence history...")
    history = verifier.consequence_handler.get_consequence_history(
        fingerprint_id=fingerprint_id,
        limit=10
    )
    print(f"   Total consequences: {len(history)}")
    for consequence in history:
        print(f"   - {consequence['consequence_type']}: {consequence['timestamp']}")
    
    # Get audit events
    print("\n10. Reviewing audit events...")
    events = audit_logger.get_events(
        fingerprint_id=fingerprint_id,
        limit=10
    )
    print(f"   Total audit events: {len(events)}")
    for event in events[-5:]:  # Show last 5
        print(f"   - {event.event_type.value}: {event.timestamp}")
    
    # Verify audit log integrity
    print("\n11. Verifying audit log integrity...")
    verification = audit_logger.verify_log_chain()
    print(f"   Chain verified: {verification['verified']}")
    print(f"   Sealed logs: {verification['log_count']}")
    
    # Get overall status
    print("\n12. Getting overall device status...")
    status = verifier.get_status_for_fingerprint(fingerprint_id)
    print(f"   Credentials: {len(status.get('credentials', []))}")
    print(f"   Tokens: {len(status.get('tokens', []))}")
    print(f"   Vaults: {len(status.get('vaults', []))}")
    
    print("\n" + "=" * 60)
    print("Advanced example completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
