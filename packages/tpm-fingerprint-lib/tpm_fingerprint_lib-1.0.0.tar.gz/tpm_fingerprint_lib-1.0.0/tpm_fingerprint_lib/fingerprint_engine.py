"""
Fingerprint Engine - Core Fingerprinting System

Generates TPM-bound, non-exportable, non-replayable device fingerprints.

Key features:
- Fingerprints require live TPM signing
- Cannot be reproduced without TPM
- Challenge-response verification
- Automatic expiry on state changes
"""

import hashlib
import json
import secrets
import hmac
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import base64

from .tpm_ops import TPMOperations
from .config import Config
from .exceptions import (
    FingerprintExpiredError,
    FingerprintReplayError,
    BootStateChangedError,
    AttestationFailedError
)


class DeviceFingerprint:
    """
    Represents a TPM-bound device fingerprint
    
    This is not a static identifier but a provable capability
    """
    
    def __init__(self, fingerprint_id: str, pcr_values: Dict[int, str],
                 created_at: datetime, expires_at: Optional[datetime],
                 tpm_quote: Dict[str, Any], metadata: Dict[str, Any]):
        self.fingerprint_id = fingerprint_id
        self.pcr_values = pcr_values
        self.created_at = created_at
        self.expires_at = expires_at
        self.tpm_quote = tpm_quote
        self.metadata = metadata
        self._validated = False
        self._last_validation = None
    
    def is_expired(self) -> bool:
        """Check if fingerprint has expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if fingerprint is still valid"""
        return self._validated and not self.is_expired()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "fingerprint_id": self.fingerprint_id,
            "pcr_values": self.pcr_values,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "tpm_quote": self.tpm_quote,
            "metadata": self.metadata,
            "validated": self._validated,
            "last_validation": self._last_validation.isoformat() if self._last_validation else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeviceFingerprint':
        """Deserialize from dictionary"""
        fp = cls(
            fingerprint_id=data["fingerprint_id"],
            pcr_values=data["pcr_values"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None,
            tpm_quote=data["tpm_quote"],
            metadata=data["metadata"]
        )
        fp._validated = data.get("validated", False)
        if data.get("last_validation"):
            fp._last_validation = datetime.fromisoformat(data["last_validation"])
        return fp


class FingerprintEngine:
    """
    Core fingerprinting engine
    
    Generates and manages TPM-bound device fingerprints that are:
    - Non-exportable (bound to TPM state)
    - Non-replayable (requires fresh TPM signing)
    - Cryptographically enforced (policy-based release)
    """
    
    def __init__(self, config: Optional[Config] = None, 
                 tpm_ops: Optional[TPMOperations] = None):
        self.config = config or Config()
        self.tpm = tpm_ops or TPMOperations(self.config)
        self._fingerprint_cache: Dict[str, DeviceFingerprint] = {}
    
    def generate_fingerprint(self, metadata: Optional[Dict[str, Any]] = None,
                           pcr_indices: Optional[List[int]] = None,
                           validity_seconds: Optional[int] = None) -> DeviceFingerprint:
        """
        Generate a new TPM-bound device fingerprint
        
        Args:
            metadata: Optional metadata to associate with fingerprint
            pcr_indices: PCRs to bind to (default: from config)
            validity_seconds: Validity duration (default: from config)
            
        Returns:
            DeviceFingerprint object
            
        The fingerprint is generated through:
        1. Reading current TPM PCR state
        2. Generating TPM quote (signed PCR values)
        3. Creating fingerprint ID from TPM quote + system data
        4. Sealing fingerprint to current PCR state
        """
        pcr_indices = pcr_indices or self.config.DEFAULT_PCRS
        validity_seconds = validity_seconds or self.config.FINGERPRINT_VALIDITY_SECONDS
        metadata = metadata or {}
        
        # Read current TPM state
        pcr_values = self.tpm.read_pcrs(pcr_indices)
        
        # Get TPM quote (signed attestation)
        nonce = secrets.token_bytes(32)
        tpm_quote = self.tpm.get_tpm_quote(pcr_indices, nonce)
        
        # Generate fingerprint components
        system_data = self._collect_system_data()
        
        # Create fingerprint ID
        # This combines TPM quote, system data, and timestamp
        # It cannot be reproduced without the TPM
        fingerprint_components = {
            "tpm_quote": tpm_quote,
            "system_data": system_data,
            "nonce": base64.b64encode(nonce).decode(),
            "timestamp": datetime.now().isoformat()
        }
        
        fingerprint_id = self._generate_fingerprint_id(fingerprint_components)
        
        # Set expiry
        created_at = datetime.now()
        expires_at = None
        if validity_seconds:
            expires_at = created_at + timedelta(seconds=validity_seconds)
        
        # Create fingerprint object
        fingerprint = DeviceFingerprint(
            fingerprint_id=fingerprint_id,
            pcr_values=pcr_values,
            created_at=created_at,
            expires_at=expires_at,
            tpm_quote=tpm_quote,
            metadata={
                **metadata,
                "system_data": system_data,
                "pcr_indices": pcr_indices,
                "nonce": base64.b64encode(nonce).decode()
            }
        )
        
        # Seal fingerprint to TPM state
        self._seal_fingerprint(fingerprint)
        
        # Cache fingerprint
        self._fingerprint_cache[fingerprint_id] = fingerprint
        
        return fingerprint
    
    def _collect_system_data(self) -> Dict[str, Any]:
        """
        Collect system data for fingerprinting
        
        Integrates with device-fingerprinting-pro library if available
        """
        system_data = {}
        
        try:
            # Try to use device-fingerprinting-pro
            from devicefingerprintingpro import DeviceFingerprintingPro
            
            fp_pro = DeviceFingerprintingPro()
            system_data["hardware_id"] = fp_pro.get_hardware_id()
            system_data["device_profile"] = fp_pro.get_device_profile()
        except ImportError:
            # Fallback: collect basic system info
            import platform
            import uuid
            
            system_data = {
                "platform": platform.system(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node(),
                "python_version": platform.python_version()
            }
            
            # Try to get machine-specific IDs
            try:
                if platform.system() == "Windows":
                    import subprocess
                    result = subprocess.run(
                        ["powershell", "-Command", 
                         "(Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Cryptography' -Name MachineGuid).MachineGuid"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        system_data["machine_guid"] = result.stdout.strip()
            except Exception:
                pass
        
        return system_data
    
    def _generate_fingerprint_id(self, components: Dict[str, Any]) -> str:
        """
        Generate fingerprint ID from components using HMAC
        
        The ID is deterministic but requires TPM quote to reproduce
        """
        components_str = json.dumps(components, sort_keys=True)
        # Use TPM quote signature as HMAC key
        tpm_sig = components.get('tpm_quote', {}).get('signature', '')
        key = hashlib.sha256(tpm_sig.encode()).digest()
        fingerprint_hash = hmac.new(key, components_str.encode(), hashlib.sha256).hexdigest()
        return fingerprint_hash
    
    def _seal_fingerprint(self, fingerprint: DeviceFingerprint):
        """Seal fingerprint to TPM PCR state"""
        fingerprint_data = json.dumps(fingerprint.to_dict()).encode()
        sealed_data = self.tpm.seal_data(
            fingerprint_data,
            list(fingerprint.pcr_values.keys())
        )
        
        # Store sealed fingerprint
        storage_path = self.config.FINGERPRINT_STORAGE_PATH / f"{fingerprint.fingerprint_id}.sealed"
        storage_path.write_bytes(sealed_data)
    
    def load_fingerprint(self, fingerprint_id: str) -> DeviceFingerprint:
        """
        Load and unseal a fingerprint
        
        Will fail if PCR state has changed
        """
        # Check cache
        if fingerprint_id in self._fingerprint_cache:
            return self._fingerprint_cache[fingerprint_id]
        
        # Load from storage
        storage_path = self.config.FINGERPRINT_STORAGE_PATH / f"{fingerprint_id}.sealed"
        if not storage_path.exists():
            raise FileNotFoundError(f"Fingerprint {fingerprint_id} not found")
        
        try:
            sealed_data = storage_path.read_bytes()
            unsealed_data = self.tpm.unseal_data(sealed_data)
            fingerprint_dict = json.loads(unsealed_data.decode())
            fingerprint = DeviceFingerprint.from_dict(fingerprint_dict)
            
            # Cache
            self._fingerprint_cache[fingerprint_id] = fingerprint
            
            return fingerprint
        except Exception as e:
            raise BootStateChangedError(
                f"Failed to load fingerprint - boot state may have changed: {e}"
            )
    
    def verify_fingerprint(self, fingerprint: DeviceFingerprint,
                          require_fresh: bool = True) -> bool:
        """
        Verify a fingerprint through challenge-response
        
        Args:
            fingerprint: Fingerprint to verify
            require_fresh: Require fresh TPM signing (prevents replay)
            
        Returns:
            True if fingerprint is valid
        """
        # Check expiry
        if fingerprint.is_expired():
            raise FingerprintExpiredError("Fingerprint has expired")
        
        # Check if boot state changed
        current_pcrs = self.tpm.read_pcrs(list(fingerprint.pcr_values.keys()))
        for pcr_idx, expected_value in fingerprint.pcr_values.items():
            if current_pcrs[pcr_idx] != expected_value:
                raise BootStateChangedError(
                    f"PCR {pcr_idx} changed: expected {expected_value}, "
                    f"got {current_pcrs[pcr_idx]}"
                )
        
        if require_fresh:
            # Perform challenge-response to prevent replay
            challenge = self.tpm.generate_challenge()
            response = self.tpm.sign_challenge(challenge, current_pcrs)
            
            if not self.tpm.verify_challenge_response(challenge, response):
                raise FingerprintReplayError("Challenge-response verification failed")
        
        # Mark as validated
        fingerprint._validated = True
        fingerprint._last_validation = datetime.now()
        
        return True
    
    def regenerate_fingerprint(self, old_fingerprint: DeviceFingerprint,
                              force: bool = False) -> DeviceFingerprint:
        """
        Regenerate fingerprint after state change
        
        Args:
            old_fingerprint: Previous fingerprint
            force: Force regeneration even if state matches
            
        Returns:
            New DeviceFingerprint
        """
        if not force:
            # Check if regeneration is needed
            try:
                self.verify_fingerprint(old_fingerprint, require_fresh=False)
                # State matches, no need to regenerate
                return old_fingerprint
            except (BootStateChangedError, FingerprintExpiredError):
                # State changed, regeneration needed
                pass
        
        # Generate new fingerprint with same metadata
        new_fingerprint = self.generate_fingerprint(
            metadata=old_fingerprint.metadata,
            pcr_indices=old_fingerprint.metadata.get("pcr_indices"),
            validity_seconds=None  # Use default
        )
        
        return new_fingerprint
    
    def list_fingerprints(self) -> List[str]:
        """List all stored fingerprint IDs"""
        storage_path = self.config.FINGERPRINT_STORAGE_PATH
        return [
            f.stem for f in storage_path.glob("*.sealed")
        ]
    
    def delete_fingerprint(self, fingerprint_id: str):
        """Delete a fingerprint"""
        storage_path = self.config.FINGERPRINT_STORAGE_PATH / f"{fingerprint_id}.sealed"
        if storage_path.exists():
            storage_path.unlink()
        
        if fingerprint_id in self._fingerprint_cache:
            del self._fingerprint_cache[fingerprint_id]
    
    def get_fingerprint_status(self, fingerprint: DeviceFingerprint) -> Dict[str, Any]:
        """
        Get detailed status of a fingerprint
        
        Returns:
            Status dictionary with validation state, expiry, PCR state
        """
        status = {
            "fingerprint_id": fingerprint.fingerprint_id,
            "created_at": fingerprint.created_at.isoformat(),
            "expires_at": fingerprint.expires_at.isoformat() if fingerprint.expires_at else None,
            "is_expired": fingerprint.is_expired(),
            "is_valid": fingerprint.is_valid(),
            "last_validation": fingerprint._last_validation.isoformat() if fingerprint._last_validation else None
        }
        
        # Check current PCR state
        try:
            current_pcrs = self.tpm.read_pcrs(list(fingerprint.pcr_values.keys()))
            pcr_matches = {}
            all_match = True
            
            for pcr_idx, expected_value in fingerprint.pcr_values.items():
                matches = current_pcrs[pcr_idx] == expected_value
                pcr_matches[pcr_idx] = matches
                all_match = all_match and matches
            
            status["pcr_state"] = {
                "all_match": all_match,
                "individual_matches": pcr_matches,
                "current_pcrs": current_pcrs,
                "expected_pcrs": fingerprint.pcr_values
            }
        except Exception as e:
            status["pcr_state"] = {
                "error": str(e)
            }
        
        return status
