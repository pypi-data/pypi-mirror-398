"""
Example: Offline verification without network

Demonstrates:
- Complete offline operation
- No server dependency
- Local TPM-based trust
- Export/import verification bundles
"""

from tpm_fingerprint_lib import OfflineVerifier
from tpm_fingerprint_lib.audit_logger import AuditLogger
import json

def main():
    print("=" * 60)
    print("TPM Fingerprint Library - Offline Verification")
    print("=" * 60)
    
    # Initialize offline verifier
    print("\n1. Initializing offline verifier...")
    verifier = OfflineVerifier()
    print("   ✓ No network connection required")
    
    # Enroll device
    print("\n2. Enrolling device...")
    enrollment = verifier.enroll_device(
        device_name="OfflineDevice",
        validity_seconds=None  # No expiry
    )
    fingerprint_id = enrollment['fingerprint_id']
    policy_id = enrollment['policy_id']
    print(f"   ✓ Device enrolled offline")
    print(f"   Fingerprint: {fingerprint_id[:16]}...")
    
    # Export verification bundle
    print("\n3. Exporting verification bundle...")
    bundle = verifier.export_offline_verification_bundle(
        fingerprint_id,
        policy_id
    )
    print(f"   ✓ Bundle created")
    print(f"   Bundle size: {len(json.dumps(bundle))} bytes")
    print(f"   Bundle signature: {bundle.get('signature', '')[:32]}...")
    
    # Save bundle to file
    bundle_file = "verification_bundle.json"
    with open(bundle_file, 'w') as f:
        json.dump(bundle, f, indent=2)
    print(f"   ✓ Bundle saved to {bundle_file}")
    
    # Perform offline verification
    print("\n4. Performing offline verification...")
    try:
        result = verifier.verify_device(fingerprint_id, policy_id)
        print(f"   ✓ Device verified offline: {result}")
    except Exception as e:
        print(f"   ✗ Verification failed: {e}")
    
    # Get cryptographic proof
    print("\n5. Generating cryptographic proof...")
    proof = verifier.get_verification_proof(fingerprint_id, policy_id)
    print(f"   ✓ Proof generated")
    print(f"   Proof components:")
    print(f"   - TPM Quote: {len(str(proof.get('tpm_quote', {})))} bytes")
    print(f"   - Signature: {proof.get('signature', '')[:32]}...")
    
    # Compare with baseline
    print("\n6. Comparing current state with baseline...")
    comparison = verifier.compare_with_baseline(fingerprint_id, policy_id)
    print(f"   All PCRs match: {comparison['all_match']}")
    
    if not comparison['all_match']:
        print(f"   Deviations detected:")
        for pcr, info in comparison['deviations'].items():
            if not info['match']:
                print(f"   - PCR {pcr}: baseline={info['baseline'][:16]}..., current={info['current'][:16]}...")
    
    # Challenge-response verification
    print("\n7. Performing challenge-response (anti-replay)...")
    challenge_result = verifier.challenge_response_verify(fingerprint_id)
    print(f"   ✓ Challenge verified: {challenge_result['verified']}")
    print(f"   Response timestamp: {challenge_result['timestamp']}")
    
    # Register offline-accessible vault
    print("\n8. Creating offline-accessible vault...")
    vault = verifier.consequence_handler.register_vault(
        vault_id="offline_vault_001",
        name="Offline Secure Vault",
        fingerprint_id=fingerprint_id
    )
    print(f"   ✓ Vault created: {vault.name}")
    
    # Verify access to vault
    print("\n9. Verifying vault access...")
    can_access = verifier.verify_and_grant_access(
        fingerprint_id,
        policy_id,
        vault.vault_id
    )
    print(f"   Access granted: {can_access}")
    
    # Get device status
    print("\n10. Getting device status...")
    status = verifier.get_device_status(fingerprint_id)
    print(f"    Fingerprint valid: {status['fingerprint_status']['is_valid']}")
    print(f"    Recent attestations: {len(status['recent_attestations'])}")
    
    # Demonstrate state change detection
    print("\n11. Monitoring for state changes...")
    fingerprint = verifier.fingerprint_engine.load_fingerprint(fingerprint_id)
    state_changes = verifier.policy_engine.check_state_changes(fingerprint)
    print(f"    Boot state changed: {state_changes['boot_state_changed']}")
    print(f"    Firmware updated: {state_changes['firmware_updated']}")
    print(f"    PCR mismatches: {len(state_changes['pcr_mismatches'])}")
    
    # Show audit trail
    print("\n12. Reviewing offline audit trail...")
    audit_logger = AuditLogger()
    stats = audit_logger.get_statistics()
    print(f"    Total events: {stats['total_events']}")
    print(f"    Sealed logs: {stats['sealed_logs']}")
    print(f"    Events by type:")
    for event_type, count in list(stats['events_by_type'].items())[:5]:
        print(f"    - {event_type}: {count}")
    
    print("\n" + "=" * 60)
    print("Offline verification completed successfully!")
    print("All operations performed without network connectivity.")
    print("=" * 60)

if __name__ == "__main__":
    main()
