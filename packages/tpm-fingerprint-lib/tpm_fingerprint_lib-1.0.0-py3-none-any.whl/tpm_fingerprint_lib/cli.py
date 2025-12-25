"""
Command-line interface for TPM Fingerprint Library
"""

import argparse
import json
import sys
from pathlib import Path

from tpm_fingerprint_lib import OfflineVerifier
from tpm_fingerprint_lib.audit_logger import AuditLogger
from tpm_fingerprint_lib.config import Config


def cmd_enroll(args):
    """Enroll a device"""
    verifier = OfflineVerifier()
    
    enrollment = verifier.enroll_device(
        device_name=args.name,
        validity_seconds=args.validity if args.validity else None
    )
    
    print(json.dumps(enrollment, indent=2))
    
    # Save to file if requested
    if args.output:
        Path(args.output).write_text(json.dumps(enrollment, indent=2))
        print(f"\nEnrollment saved to: {args.output}")


def cmd_verify(args):
    """Verify a device"""
    verifier = OfflineVerifier()
    
    try:
        result = verifier.verify_device(args.fingerprint_id, args.policy_id)
        print(f"✓ Verification successful: {result}")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        sys.exit(1)


def cmd_status(args):
    """Get device status"""
    verifier = OfflineVerifier()
    
    status = verifier.get_device_status(args.fingerprint_id)
    print(json.dumps(status, indent=2, default=str))


def cmd_challenge(args):
    """Perform challenge-response verification"""
    verifier = OfflineVerifier()
    
    result = verifier.challenge_response_verify(args.fingerprint_id)
    print(json.dumps(result, indent=2, default=str))


def cmd_compare(args):
    """Compare with baseline"""
    verifier = OfflineVerifier()
    
    comparison = verifier.compare_with_baseline(args.fingerprint_id, args.policy_id)
    print(json.dumps(comparison, indent=2, default=str))


def cmd_regenerate(args):
    """Regenerate fingerprint after update"""
    verifier = OfflineVerifier()
    
    new_enrollment = verifier.regenerate_after_update(
        args.fingerprint_id,
        args.name
    )
    print(json.dumps(new_enrollment, indent=2))


def cmd_export(args):
    """Export verification bundle"""
    verifier = OfflineVerifier()
    
    bundle = verifier.export_offline_verification_bundle(
        args.fingerprint_id,
        args.policy_id
    )
    
    if args.output:
        Path(args.output).write_text(json.dumps(bundle, indent=2))
        print(f"Bundle exported to: {args.output}")
    else:
        print(json.dumps(bundle, indent=2, default=str))


def cmd_audit_stats(args):
    """Show audit statistics"""
    logger = AuditLogger()
    stats = logger.get_statistics()
    print(json.dumps(stats, indent=2, default=str))


def cmd_audit_verify(args):
    """Verify audit log chain"""
    logger = AuditLogger()
    verification = logger.verify_log_chain()
    print(json.dumps(verification, indent=2, default=str))
    
    if verification['verified']:
        print("\n✓ Audit log chain verified")
        sys.exit(0)
    else:
        print("\n✗ Audit log chain verification failed")
        sys.exit(1)


def cmd_audit_events(args):
    """List audit events"""
    logger = AuditLogger()
    
    events = logger.get_events(
        fingerprint_id=args.fingerprint_id if hasattr(args, 'fingerprint_id') else None,
        limit=args.limit if hasattr(args, 'limit') else None
    )
    
    for event in events:
        print(f"{event.timestamp} - {event.event_type.value} - {event.fingerprint_id or 'N/A'}")


def cmd_list_fingerprints(args):
    """List all fingerprints"""
    verifier = OfflineVerifier()
    fingerprints = verifier.fingerprint_engine.list_fingerprints()
    
    print(f"Found {len(fingerprints)} fingerprints:")
    for fp_id in fingerprints:
        print(f"  - {fp_id}")


def cmd_list_policies(args):
    """List all policies"""
    verifier = OfflineVerifier()
    policies = verifier.policy_engine.list_policies()
    
    print(f"Found {len(policies)} policies:")
    for policy in policies:
        print(f"  - {policy.policy_id}: {policy.name}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="TPM Fingerprint Library CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Enroll command
    enroll_parser = subparsers.add_parser('enroll', help='Enroll a device')
    enroll_parser.add_argument('name', help='Device name')
    enroll_parser.add_argument('--validity', type=int, help='Validity in seconds')
    enroll_parser.add_argument('-o', '--output', help='Output file for enrollment data')
    enroll_parser.set_defaults(func=cmd_enroll)
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify a device')
    verify_parser.add_argument('fingerprint_id', help='Fingerprint ID')
    verify_parser.add_argument('policy_id', help='Policy ID')
    verify_parser.set_defaults(func=cmd_verify)
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get device status')
    status_parser.add_argument('fingerprint_id', help='Fingerprint ID')
    status_parser.set_defaults(func=cmd_status)
    
    # Challenge command
    challenge_parser = subparsers.add_parser('challenge', help='Challenge-response verification')
    challenge_parser.add_argument('fingerprint_id', help='Fingerprint ID')
    challenge_parser.set_defaults(func=cmd_challenge)
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare with baseline')
    compare_parser.add_argument('fingerprint_id', help='Fingerprint ID')
    compare_parser.add_argument('policy_id', help='Policy ID')
    compare_parser.set_defaults(func=cmd_compare)
    
    # Regenerate command
    regen_parser = subparsers.add_parser('regenerate', help='Regenerate fingerprint')
    regen_parser.add_argument('fingerprint_id', help='Old fingerprint ID')
    regen_parser.add_argument('name', help='Device name')
    regen_parser.set_defaults(func=cmd_regenerate)
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export verification bundle')
    export_parser.add_argument('fingerprint_id', help='Fingerprint ID')
    export_parser.add_argument('policy_id', help='Policy ID')
    export_parser.add_argument('-o', '--output', help='Output file')
    export_parser.set_defaults(func=cmd_export)
    
    # Audit commands
    audit_parser = subparsers.add_parser('audit', help='Audit log commands')
    audit_subparsers = audit_parser.add_subparsers(dest='audit_command')
    
    audit_stats_parser = audit_subparsers.add_parser('stats', help='Show audit statistics')
    audit_stats_parser.set_defaults(func=cmd_audit_stats)
    
    audit_verify_parser = audit_subparsers.add_parser('verify', help='Verify audit log chain')
    audit_verify_parser.set_defaults(func=cmd_audit_verify)
    
    audit_events_parser = audit_subparsers.add_parser('events', help='List audit events')
    audit_events_parser.add_argument('--fingerprint-id', help='Filter by fingerprint ID')
    audit_events_parser.add_argument('--limit', type=int, default=50, help='Number of events')
    audit_events_parser.set_defaults(func=cmd_audit_events)
    
    # List commands
    list_fp_parser = subparsers.add_parser('list-fingerprints', help='List fingerprints')
    list_fp_parser.set_defaults(func=cmd_list_fingerprints)
    
    list_pol_parser = subparsers.add_parser('list-policies', help='List policies')
    list_pol_parser.set_defaults(func=cmd_list_policies)
    
    # Parse and execute
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if hasattr(args, 'func'):
        try:
            args.func(args)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
