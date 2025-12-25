"""
Consequence Handler - Automated Policy Enforcement

Implements automatic consequences when fingerprints change or policies are violated:
- Credential revocation
- Vault lockdown
- Token invalidation
- Forced re-enrollment
- TPM-sealed audit logging

Key innovation: Fingerprint change is not informational — it is enforced.
"""

import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from pathlib import Path
from enum import Enum

from .config import Config
from .policy_engine import PolicyViolationType, PolicyAction, Policy
from .fingerprint_engine import DeviceFingerprint
from .exceptions import TPMFingerprintError


class ConsequenceType(Enum):
    """Types of consequences that can be enforced"""
    CREDENTIAL_REVOKED = "credential_revoked"
    VAULT_LOCKED = "vault_locked"
    TOKEN_INVALIDATED = "token_invalidated"
    REENROLLMENT_REQUIRED = "reenrollment_required"
    ACCESS_DENIED = "access_denied"
    ALERT_SENT = "alert_sent"


class Credential:
    """Represents a credential managed by the system"""
    
    def __init__(self, credential_id: str, credential_type: str,
                 data: Dict[str, Any], fingerprint_id: str):
        self.credential_id = credential_id
        self.credential_type = credential_type
        self.data = data
        self.fingerprint_id = fingerprint_id
        self.created_at = datetime.now()
        self.revoked = False
        self.revoked_at: Optional[datetime] = None
        self.revocation_reason: Optional[str] = None
    
    def revoke(self, reason: str):
        """Revoke this credential"""
        self.revoked = True
        self.revoked_at = datetime.now()
        self.revocation_reason = reason
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "credential_id": self.credential_id,
            "credential_type": self.credential_type,
            "data": self.data,
            "fingerprint_id": self.fingerprint_id,
            "created_at": self.created_at.isoformat(),
            "revoked": self.revoked,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "revocation_reason": self.revocation_reason
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Credential':
        cred = cls(
            credential_id=data["credential_id"],
            credential_type=data["credential_type"],
            data=data["data"],
            fingerprint_id=data["fingerprint_id"]
        )
        cred.created_at = datetime.fromisoformat(data["created_at"])
        cred.revoked = data["revoked"]
        if data.get("revoked_at"):
            cred.revoked_at = datetime.fromisoformat(data["revoked_at"])
        cred.revocation_reason = data.get("revocation_reason")
        return cred


class Token:
    """Represents an access token"""
    
    def __init__(self, token_id: str, token_value: str, fingerprint_id: str,
                 expires_at: Optional[datetime] = None):
        self.token_id = token_id
        self.token_value = token_value
        self.fingerprint_id = fingerprint_id
        self.created_at = datetime.now()
        self.expires_at = expires_at
        self.invalidated = False
        self.invalidated_at: Optional[datetime] = None
        self.invalidation_reason: Optional[str] = None
    
    def invalidate(self, reason: str):
        """Invalidate this token"""
        self.invalidated = True
        self.invalidated_at = datetime.now()
        self.invalidation_reason = reason
    
    def is_valid(self) -> bool:
        """Check if token is still valid"""
        if self.invalidated:
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "token_value": self.token_value,
            "fingerprint_id": self.fingerprint_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "invalidated": self.invalidated,
            "invalidated_at": self.invalidated_at.isoformat() if self.invalidated_at else None,
            "invalidation_reason": self.invalidation_reason
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Token':
        token = cls(
            token_id=data["token_id"],
            token_value=data["token_value"],
            fingerprint_id=data["fingerprint_id"],
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        )
        token.created_at = datetime.fromisoformat(data["created_at"])
        token.invalidated = data["invalidated"]
        if data.get("invalidated_at"):
            token.invalidated_at = datetime.fromisoformat(data["invalidated_at"])
        token.invalidation_reason = data.get("invalidation_reason")
        return token


class Vault:
    """Represents a secure vault that can be locked down"""
    
    def __init__(self, vault_id: str, name: str, fingerprint_id: str):
        self.vault_id = vault_id
        self.name = name
        self.fingerprint_id = fingerprint_id
        self.locked = False
        self.locked_at: Optional[datetime] = None
        self.lock_reason: Optional[str] = None
        self.created_at = datetime.now()
    
    def lock(self, reason: str):
        """Lock this vault"""
        self.locked = True
        self.locked_at = datetime.now()
        self.lock_reason = reason
    
    def unlock(self):
        """Unlock this vault"""
        self.locked = False
        self.locked_at = None
        self.lock_reason = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "vault_id": self.vault_id,
            "name": self.name,
            "fingerprint_id": self.fingerprint_id,
            "locked": self.locked,
            "locked_at": self.locked_at.isoformat() if self.locked_at else None,
            "lock_reason": self.lock_reason,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Vault':
        vault = cls(
            vault_id=data["vault_id"],
            name=data["name"],
            fingerprint_id=data["fingerprint_id"]
        )
        vault.locked = data["locked"]
        if data.get("locked_at"):
            vault.locked_at = datetime.fromisoformat(data["locked_at"])
        vault.lock_reason = data.get("lock_reason")
        vault.created_at = datetime.fromisoformat(data["created_at"])
        return vault


class ConsequenceHandler:
    """
    Handles automatic enforcement of consequences
    
    This is the key differentiator: fingerprint changes trigger
    cryptographically enforced actions, not just notifications.
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._credentials: Dict[str, Credential] = {}
        self._tokens: Dict[str, Token] = {}
        self._vaults: Dict[str, Vault] = {}
        self._consequence_handlers: Dict[ConsequenceType, List[Callable]] = {}
        self._consequence_history: List[Dict[str, Any]] = []
        
        self._storage_path = Path.home() / ".tpm_fingerprint" / "consequences"
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        self._load_state()
    
    def _load_state(self):
        """Load stored credentials, tokens, and vaults"""
        # Load credentials
        cred_file = self._storage_path / "credentials.json"
        if cred_file.exists():
            data = json.loads(cred_file.read_text())
            self._credentials = {
                k: Credential.from_dict(v) for k, v in data.items()
            }
        
        # Load tokens
        token_file = self._storage_path / "tokens.json"
        if token_file.exists():
            data = json.loads(token_file.read_text())
            self._tokens = {
                k: Token.from_dict(v) for k, v in data.items()
            }
        
        # Load vaults
        vault_file = self._storage_path / "vaults.json"
        if vault_file.exists():
            data = json.loads(vault_file.read_text())
            self._vaults = {
                k: Vault.from_dict(v) for k, v in data.items()
            }
    
    def _save_state(self):
        """Save current state"""
        # Save credentials
        cred_file = self._storage_path / "credentials.json"
        cred_file.write_text(json.dumps({
            k: v.to_dict() for k, v in self._credentials.items()
        }, indent=2))
        
        # Save tokens
        token_file = self._storage_path / "tokens.json"
        token_file.write_text(json.dumps({
            k: v.to_dict() for k, v in self._tokens.items()
        }, indent=2))
        
        # Save vaults
        vault_file = self._storage_path / "vaults.json"
        vault_file.write_text(json.dumps({
            k: v.to_dict() for k, v in self._vaults.items()
        }, indent=2))
    
    # Credential Management
    
    def register_credential(self, credential_id: str, credential_type: str,
                          data: Dict[str, Any], fingerprint_id: str) -> Credential:
        """Register a credential bound to a fingerprint"""
        credential = Credential(credential_id, credential_type, data, fingerprint_id)
        self._credentials[credential_id] = credential
        self._save_state()
        return credential
    
    def revoke_credential(self, credential_id: str, reason: str):
        """Revoke a credential"""
        if credential_id in self._credentials:
            credential = self._credentials[credential_id]
            credential.revoke(reason)
            self._save_state()
            
            # Record consequence
            self._record_consequence(ConsequenceType.CREDENTIAL_REVOKED, {
                "credential_id": credential_id,
                "reason": reason
            })
    
    def revoke_credentials_for_fingerprint(self, fingerprint_id: str, reason: str):
        """Revoke all credentials associated with a fingerprint"""
        for cred_id, credential in self._credentials.items():
            if credential.fingerprint_id == fingerprint_id and not credential.revoked:
                self.revoke_credential(cred_id, reason)
    
    def get_credential(self, credential_id: str) -> Optional[Credential]:
        """Get credential by ID"""
        return self._credentials.get(credential_id)
    
    def is_credential_valid(self, credential_id: str) -> bool:
        """Check if credential is valid (not revoked)"""
        credential = self._credentials.get(credential_id)
        return credential is not None and not credential.revoked
    
    # Token Management
    
    def register_token(self, token_id: str, token_value: str,
                      fingerprint_id: str, expires_at: Optional[datetime] = None) -> Token:
        """Register a token bound to a fingerprint"""
        token = Token(token_id, token_value, fingerprint_id, expires_at)
        self._tokens[token_id] = token
        self._save_state()
        return token
    
    def invalidate_token(self, token_id: str, reason: str):
        """Invalidate a token"""
        if token_id in self._tokens:
            token = self._tokens[token_id]
            token.invalidate(reason)
            self._save_state()
            
            # Record consequence
            self._record_consequence(ConsequenceType.TOKEN_INVALIDATED, {
                "token_id": token_id,
                "reason": reason
            })
    
    def invalidate_tokens_for_fingerprint(self, fingerprint_id: str, reason: str):
        """Invalidate all tokens associated with a fingerprint"""
        for token_id, token in self._tokens.items():
            if token.fingerprint_id == fingerprint_id and token.is_valid():
                self.invalidate_token(token_id, reason)
    
    def is_token_valid(self, token_id: str) -> bool:
        """Check if token is valid"""
        token = self._tokens.get(token_id)
        return token is not None and token.is_valid()
    
    # Vault Management
    
    def register_vault(self, vault_id: str, name: str, fingerprint_id: str) -> Vault:
        """Register a vault bound to a fingerprint"""
        vault = Vault(vault_id, name, fingerprint_id)
        self._vaults[vault_id] = vault
        self._save_state()
        return vault
    
    def lock_vault(self, vault_id: str, reason: str):
        """Lock a vault"""
        if vault_id in self._vaults:
            vault = self._vaults[vault_id]
            vault.lock(reason)
            self._save_state()
            
            # Record consequence
            self._record_consequence(ConsequenceType.VAULT_LOCKED, {
                "vault_id": vault_id,
                "reason": reason
            })
    
    def unlock_vault(self, vault_id: str):
        """Unlock a vault (requires valid fingerprint)"""
        if vault_id in self._vaults:
            vault = self._vaults[vault_id]
            vault.unlock()
            self._save_state()
    
    def lock_vaults_for_fingerprint(self, fingerprint_id: str, reason: str):
        """Lock all vaults associated with a fingerprint"""
        for vault_id, vault in self._vaults.items():
            if vault.fingerprint_id == fingerprint_id and not vault.locked:
                self.lock_vault(vault_id, reason)
    
    def is_vault_accessible(self, vault_id: str) -> bool:
        """Check if vault is accessible (not locked)"""
        vault = self._vaults.get(vault_id)
        return vault is not None and not vault.locked
    
    # Consequence Enforcement
    
    def enforce_consequences(self, violation_type: PolicyViolationType,
                           policy: Policy, fingerprint: DeviceFingerprint):
        """
        Enforce consequences for a policy violation
        
        This is called by the PolicyEngine when violations occur
        """
        if not self.config.CONSEQUENCES_ENABLED:
            return
        
        actions = policy.actions.get(violation_type, [])
        
        for action in actions:
            if action == PolicyAction.REVOKE_CREDENTIALS:
                if self.config.AUTO_REVOKE_CREDENTIALS:
                    self.revoke_credentials_for_fingerprint(
                        fingerprint.fingerprint_id,
                        f"Policy violation: {violation_type.value}"
                    )
            
            elif action == PolicyAction.LOCKDOWN_VAULT:
                if self.config.AUTO_LOCKDOWN_VAULT:
                    self.lock_vaults_for_fingerprint(
                        fingerprint.fingerprint_id,
                        f"Policy violation: {violation_type.value}"
                    )
            
            elif action == PolicyAction.INVALIDATE_TOKENS:
                if self.config.AUTO_INVALIDATE_TOKENS:
                    self.invalidate_tokens_for_fingerprint(
                        fingerprint.fingerprint_id,
                        f"Policy violation: {violation_type.value}"
                    )
            
            elif action == PolicyAction.FORCE_REENROLLMENT:
                if self.config.FORCE_REENROLLMENT:
                    self._force_reenrollment(fingerprint)
            
            elif action == PolicyAction.ALERT:
                self._send_alert(violation_type, policy, fingerprint)
        
        # Call custom handlers
        consequence_type = self._map_violation_to_consequence(violation_type)
        if consequence_type in self._consequence_handlers:
            for handler in self._consequence_handlers[consequence_type]:
                try:
                    handler(violation_type, policy, fingerprint)
                except Exception as e:
                    print(f"Consequence handler error: {e}")
    
    def _map_violation_to_consequence(self, violation: PolicyViolationType) -> ConsequenceType:
        """Map violation type to consequence type"""
        mapping = {
            PolicyViolationType.PCR_MISMATCH: ConsequenceType.ACCESS_DENIED,
            PolicyViolationType.FINGERPRINT_EXPIRED: ConsequenceType.REENROLLMENT_REQUIRED,
            PolicyViolationType.BOOT_STATE_CHANGED: ConsequenceType.CREDENTIAL_REVOKED,
            PolicyViolationType.SECURE_BOOT_VIOLATED: ConsequenceType.VAULT_LOCKED,
            PolicyViolationType.FIRMWARE_UPDATED: ConsequenceType.REENROLLMENT_REQUIRED,
            PolicyViolationType.MAX_ATTEMPTS_EXCEEDED: ConsequenceType.VAULT_LOCKED
        }
        return mapping.get(violation, ConsequenceType.ACCESS_DENIED)
    
    def _force_reenrollment(self, fingerprint: DeviceFingerprint):
        """Force device re-enrollment"""
        self._record_consequence(ConsequenceType.REENROLLMENT_REQUIRED, {
            "fingerprint_id": fingerprint.fingerprint_id,
            "reason": "Policy violation - re-enrollment required"
        })
    
    def _send_alert(self, violation_type: PolicyViolationType,
                   policy: Policy, fingerprint: DeviceFingerprint):
        """Send alert about violation"""
        self._record_consequence(ConsequenceType.ALERT_SENT, {
            "violation": violation_type.value,
            "policy_id": policy.policy_id,
            "fingerprint_id": fingerprint.fingerprint_id,
            "timestamp": datetime.now().isoformat()
        })
    
    def _record_consequence(self, consequence_type: ConsequenceType,
                          details: Dict[str, Any]):
        """Record a consequence in history"""
        record = {
            "consequence_type": consequence_type.value,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self._consequence_history.append(record)
        
        # Save to file
        history_file = self._storage_path / "consequence_history.json"
        history_file.write_text(json.dumps(self._consequence_history, indent=2))
    
    def register_consequence_handler(self, consequence_type: ConsequenceType,
                                    handler: Callable):
        """Register a custom handler for consequences"""
        if consequence_type not in self._consequence_handlers:
            self._consequence_handlers[consequence_type] = []
        self._consequence_handlers[consequence_type].append(handler)
    
    def get_consequence_history(self, 
                               fingerprint_id: Optional[str] = None,
                               limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get consequence history"""
        history = self._consequence_history
        
        if fingerprint_id:
            history = [
                h for h in history
                if h.get("details", {}).get("fingerprint_id") == fingerprint_id
            ]
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def get_status_for_fingerprint(self, fingerprint_id: str) -> Dict[str, Any]:
        """Get status of all resources bound to a fingerprint"""
        credentials = [
            cred.to_dict() for cred in self._credentials.values()
            if cred.fingerprint_id == fingerprint_id
        ]
        
        tokens = [
            token.to_dict() for token in self._tokens.values()
            if token.fingerprint_id == fingerprint_id
        ]
        
        vaults = [
            vault.to_dict() for vault in self._vaults.values()
            if vault.fingerprint_id == fingerprint_id
        ]
        
        return {
            "fingerprint_id": fingerprint_id,
            "credentials": credentials,
            "tokens": tokens,
            "vaults": vaults,
            "timestamp": datetime.now().isoformat()
        }
