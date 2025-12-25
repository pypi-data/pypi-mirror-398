"""
Audit Logger - TPM-Sealed Audit Trail

Provides tamper-evident, TPM-sealed audit logging:
- All security events logged
- Logs sealed to TPM state
- Cannot be modified without detection
- Automatic log rotation and archiving
"""

import json
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from pathlib import Path
from enum import Enum
import hashlib

from .tpm_ops import TPMOperations
from .config import Config
from .exceptions import SealingError, UnsealingError


class AuditEventType(Enum):
    """Types of audit events"""
    FINGERPRINT_GENERATED = "fingerprint_generated"
    FINGERPRINT_VERIFIED = "fingerprint_verified"
    FINGERPRINT_VERIFICATION_FAILED = "fingerprint_verification_failed"
    FINGERPRINT_EXPIRED = "fingerprint_expired"
    FINGERPRINT_DELETED = "fingerprint_deleted"
    
    POLICY_CREATED = "policy_created"
    POLICY_UPDATED = "policy_updated"
    POLICY_VIOLATED = "policy_violated"
    POLICY_DELETED = "policy_deleted"
    
    CREDENTIAL_REGISTERED = "credential_registered"
    CREDENTIAL_REVOKED = "credential_revoked"
    
    TOKEN_ISSUED = "token_issued"
    TOKEN_INVALIDATED = "token_invalidated"
    
    VAULT_CREATED = "vault_created"
    VAULT_LOCKED = "vault_locked"
    VAULT_UNLOCKED = "vault_unlocked"
    
    PCR_MISMATCH = "pcr_mismatch"
    BOOT_STATE_CHANGED = "boot_state_changed"
    FIRMWARE_UPDATE_DETECTED = "firmware_update_detected"
    SECURE_BOOT_VIOLATION = "secure_boot_violation"
    
    ATTESTATION_SUCCESS = "attestation_success"
    ATTESTATION_FAILURE = "attestation_failure"
    
    DEVICE_ENROLLED = "device_enrolled"
    DEVICE_REENROLLMENT_REQUIRED = "device_reenrollment_required"
    
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    
    SYSTEM_ERROR = "system_error"


class AuditEvent:
    """Represents a single audit event"""
    
    def __init__(self, event_type: AuditEventType, details: Dict[str, Any],
                 fingerprint_id: Optional[str] = None,
                 policy_id: Optional[str] = None):
        self.event_id = self._generate_event_id()
        self.event_type = event_type
        self.details = details
        self.fingerprint_id = fingerprint_id
        self.policy_id = policy_id
        self.timestamp = datetime.now()
        self.sealed = False
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        data = f"{datetime.now().isoformat()}{id(self)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "details": self.details,
            "fingerprint_id": self.fingerprint_id,
            "policy_id": self.policy_id,
            "timestamp": self.timestamp.isoformat(),
            "sealed": self.sealed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """Deserialize from dictionary"""
        event = cls(
            event_type=AuditEventType(data["event_type"]),
            details=data["details"],
            fingerprint_id=data.get("fingerprint_id"),
            policy_id=data.get("policy_id")
        )
        event.event_id = data["event_id"]
        event.timestamp = datetime.fromisoformat(data["timestamp"])
        event.sealed = data.get("sealed", False)
        return event


class AuditLogger:
    """
    TPM-sealed audit logging system
    
    Features:
    - All events logged with timestamps
    - Logs sealed to TPM state (tamper-evident)
    - Cannot modify past events without breaking seal
    - Automatic rotation and archiving
    """
    
    def __init__(self, config: Optional[Config] = None,
                 tpm_ops: Optional[TPMOperations] = None):
        self.config = config or Config()
        self.tpm = tpm_ops or TPMOperations(self.config)
        
        self._audit_log_path = self.config.AUDIT_LOG_PATH
        self._sealed_log_path = self.config.AUDIT_LOG_PATH.parent / "sealed_logs"
        self._sealed_log_path.mkdir(parents=True, exist_ok=True)
        
        self._current_log: List[AuditEvent] = []
        self._max_events_before_seal = 100
        
        # Setup Python logging
        self._setup_logging()
        
        # Load current log
        self._load_current_log()
    
    def _setup_logging(self):
        """Setup Python logging"""
        log_level = getattr(logging, self.config.LOG_LEVEL.upper(), logging.INFO)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self._audit_log_path),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("TPMFingerprint.Audit")
    
    def _load_current_log(self):
        """Load current unsealed log"""
        log_file = self._audit_log_path.parent / "current_log.json"
        if log_file.exists():
            try:
                data = json.loads(log_file.read_text())
                self._current_log = [AuditEvent.from_dict(e) for e in data]
            except Exception as e:
                self.logger.error(f"Failed to load current log: {e}")
    
    def _save_current_log(self):
        """Save current unsealed log"""
        log_file = self._audit_log_path.parent / "current_log.json"
        log_file.write_text(json.dumps(
            [e.to_dict() for e in self._current_log],
            indent=2
        ))
    
    def log_event(self, event_type: AuditEventType, details: Dict[str, Any],
                  fingerprint_id: Optional[str] = None,
                  policy_id: Optional[str] = None):
        """
        Log an audit event
        
        Args:
            event_type: Type of event
            details: Event details
            fingerprint_id: Associated fingerprint ID
            policy_id: Associated policy ID
        """
        # Create event
        event = AuditEvent(event_type, details, fingerprint_id, policy_id)
        
        # Add to current log
        self._current_log.append(event)
        
        # Log to Python logger
        self.logger.info(f"{event_type.value}: {json.dumps(details)}")
        
        # Save current log
        self._save_current_log()
        
        # Check if we should seal
        if len(self._current_log) >= self._max_events_before_seal:
            if self.config.SEAL_AUDIT_LOGS:
                self._seal_and_rotate()
    
    def _seal_and_rotate(self):
        """Seal current log to TPM and rotate"""
        if not self._current_log:
            return
        
        try:
            # Create log bundle
            log_bundle = {
                "events": [e.to_dict() for e in self._current_log],
                "sealed_at": datetime.now().isoformat(),
                "event_count": len(self._current_log)
            }
            
            # Create chain hash (links to previous sealed log)
            previous_hash = self._get_latest_log_hash()
            log_bundle["previous_log_hash"] = previous_hash
            
            # Compute HMAC of this log for integrity
            import hmac
            log_data = json.dumps(log_bundle, sort_keys=True).encode()
            # Use previous hash as HMAC key for chaining
            hmac_key = previous_hash.encode() if previous_hash else b"initial_key"
            log_hash = hmac.new(hmac_key, log_data, hashlib.sha256).hexdigest()
            log_bundle["log_hash"] = log_hash
            
            # Seal to TPM
            sealed_data = self.tpm.seal_data(log_data)
            
            # Save sealed log
            sealed_file = self._sealed_log_path / f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sealed"
            sealed_file.write_bytes(sealed_data)
            
            # Mark events as sealed
            for event in self._current_log:
                event.sealed = True
            
            # Clear current log
            self._current_log = []
            self._save_current_log()
            
            self.logger.info(f"Sealed {len(log_bundle['events'])} events to TPM")
            
        except Exception as e:
            self.logger.error(f"Failed to seal audit log: {e}")
    
    def _get_latest_log_hash(self) -> Optional[str]:
        """Get hash of the latest sealed log (for chaining)"""
        sealed_logs = sorted(self._sealed_log_path.glob("*.sealed"))
        if not sealed_logs:
            return None
        
        try:
            # Read the latest sealed log
            latest_log = sealed_logs[-1]
            sealed_data = latest_log.read_bytes()
            
            # Unseal
            unsealed_data = self.tpm.unseal_data(sealed_data)
            log_bundle = json.loads(unsealed_data.decode())
            
            return log_bundle.get("log_hash")
        except Exception:
            return None
    
    def force_seal(self):
        """Force sealing of current log"""
        if self.config.SEAL_AUDIT_LOGS:
            self._seal_and_rotate()
    
    def get_events(self, event_type: Optional[AuditEventType] = None,
                   fingerprint_id: Optional[str] = None,
                   policy_id: Optional[str] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   include_sealed: bool = True,
                   limit: Optional[int] = None) -> List[AuditEvent]:
        """
        Query audit events
        
        Args:
            event_type: Filter by event type
            fingerprint_id: Filter by fingerprint
            policy_id: Filter by policy
            start_time: Filter by start time
            end_time: Filter by end time
            include_sealed: Whether to include sealed logs
            limit: Maximum number of events to return
            
        Returns:
            List of matching audit events
        """
        events = []
        
        # Get current unsealed events
        events.extend(self._current_log)
        
        # Get sealed events if requested
        if include_sealed:
            sealed_events = self._get_sealed_events()
            events.extend(sealed_events)
        
        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if fingerprint_id:
            events = [e for e in events if e.fingerprint_id == fingerprint_id]
        
        if policy_id:
            events = [e for e in events if e.policy_id == policy_id]
        
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        
        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        # Apply limit
        if limit:
            events = events[:limit]
        
        return events
    
    def _get_sealed_events(self) -> List[AuditEvent]:
        """Retrieve events from sealed logs"""
        events = []
        
        sealed_logs = sorted(self._sealed_log_path.glob("*.sealed"))
        
        for sealed_log in sealed_logs:
            try:
                # Read sealed data
                sealed_data = sealed_log.read_bytes()
                
                # Unseal
                unsealed_data = self.tpm.unseal_data(sealed_data)
                log_bundle = json.loads(unsealed_data.decode())
                
                # Extract events
                for event_data in log_bundle.get("events", []):
                    event = AuditEvent.from_dict(event_data)
                    events.append(event)
                    
            except UnsealingError:
                # Log cannot be unsealed - TPM state changed
                self.logger.warning(f"Cannot unseal log {sealed_log.name} - TPM state changed")
            except Exception as e:
                self.logger.error(f"Error reading sealed log {sealed_log.name}: {e}")
        
        return events
    
    def verify_log_chain(self) -> Dict[str, Any]:
        """
        Verify integrity of sealed log chain
        
        Returns:
            Verification result with details
        """
        sealed_logs = sorted(self._sealed_log_path.glob("*.sealed"))
        
        if not sealed_logs:
            return {
                "verified": True,
                "message": "No sealed logs to verify",
                "log_count": 0
            }
        
        results = {
            "verified": True,
            "log_count": len(sealed_logs),
            "logs": [],
            "errors": []
        }
        
        previous_hash = None
        
        for sealed_log in sealed_logs:
            log_result = {
                "filename": sealed_log.name,
                "can_unseal": False,
                "hash_valid": False,
                "chain_valid": False
            }
            
            try:
                # Try to unseal
                sealed_data = sealed_log.read_bytes()
                unsealed_data = self.tpm.unseal_data(sealed_data)
                log_result["can_unseal"] = True
                
                # Parse log
                log_bundle = json.loads(unsealed_data.decode())
                
                # Verify hash with HMAC
                stored_hash = log_bundle.get("log_hash")
                log_bundle_copy = {k: v for k, v in log_bundle.items() if k != "log_hash"}
                log_data_verify = json.dumps(log_bundle_copy, sort_keys=True).encode()
                
                import hmac
                # Use previous hash as HMAC key for verification
                hmac_key = previous_hash.encode() if previous_hash else b"initial_key"
                computed_hash = hmac.new(hmac_key, log_data_verify, hashlib.sha256).hexdigest()
                
                log_result["hash_valid"] = (stored_hash == computed_hash)
                
                # Verify chain
                if previous_hash is None:
                    # First log
                    log_result["chain_valid"] = True
                else:
                    log_result["chain_valid"] = (
                        log_bundle.get("previous_log_hash") == previous_hash
                    )
                
                previous_hash = stored_hash
                
                if not log_result["hash_valid"] or not log_result["chain_valid"]:
                    results["verified"] = False
                    results["errors"].append(f"Integrity check failed for {sealed_log.name}")
                
            except UnsealingError:
                log_result["error"] = "Cannot unseal - TPM state changed"
                results["verified"] = False
                results["errors"].append(f"Cannot unseal {sealed_log.name}")
            except Exception as e:
                log_result["error"] = str(e)
                results["verified"] = False
                results["errors"].append(f"Error verifying {sealed_log.name}: {e}")
            
            results["logs"].append(log_result)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get audit log statistics"""
        all_events = self.get_events(include_sealed=True)
        
        stats = {
            "total_events": len(all_events),
            "unsealed_events": len(self._current_log),
            "sealed_logs": len(list(self._sealed_log_path.glob("*.sealed"))),
            "events_by_type": {},
            "oldest_event": None,
            "newest_event": None
        }
        
        # Count by type
        for event in all_events:
            event_type = event.event_type.value
            stats["events_by_type"][event_type] = stats["events_by_type"].get(event_type, 0) + 1
        
        # Get oldest and newest
        if all_events:
            sorted_events = sorted(all_events, key=lambda e: e.timestamp)
            stats["oldest_event"] = sorted_events[0].timestamp.isoformat()
            stats["newest_event"] = sorted_events[-1].timestamp.isoformat()
        
        return stats
    
    # Convenience methods for common events
    
    def log_fingerprint_generated(self, fingerprint_id: str, details: Dict[str, Any]):
        """Log fingerprint generation"""
        self.log_event(AuditEventType.FINGERPRINT_GENERATED, details, fingerprint_id=fingerprint_id)
    
    def log_fingerprint_verified(self, fingerprint_id: str, details: Dict[str, Any]):
        """Log fingerprint verification"""
        self.log_event(AuditEventType.FINGERPRINT_VERIFIED, details, fingerprint_id=fingerprint_id)
    
    def log_policy_violation(self, fingerprint_id: str, policy_id: str, details: Dict[str, Any]):
        """Log policy violation"""
        self.log_event(AuditEventType.POLICY_VIOLATED, details, fingerprint_id, policy_id)
    
    def log_credential_revoked(self, fingerprint_id: str, details: Dict[str, Any]):
        """Log credential revocation"""
        self.log_event(AuditEventType.CREDENTIAL_REVOKED, details, fingerprint_id=fingerprint_id)
    
    def log_vault_locked(self, fingerprint_id: str, details: Dict[str, Any]):
        """Log vault lockdown"""
        self.log_event(AuditEventType.VAULT_LOCKED, details, fingerprint_id=fingerprint_id)
    
    def log_access_denied(self, fingerprint_id: str, details: Dict[str, Any]):
        """Log access denial"""
        self.log_event(AuditEventType.ACCESS_DENIED, details, fingerprint_id=fingerprint_id)
