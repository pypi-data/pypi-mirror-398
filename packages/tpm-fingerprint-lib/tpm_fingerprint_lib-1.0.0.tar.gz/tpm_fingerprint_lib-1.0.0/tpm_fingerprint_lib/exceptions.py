"""
Custom exceptions for TPM Fingerprint Library
"""


class TPMFingerprintError(Exception):
    """Base exception for all TPM fingerprint errors"""
    pass


class TPMNotAvailableError(TPMFingerprintError):
    """Raised when TPM is not available or accessible"""
    pass


class PCRMismatchError(TPMFingerprintError):
    """Raised when PCR values don't match expected baseline"""
    pass


class FingerprintExpiredError(TPMFingerprintError):
    """Raised when fingerprint has expired due to state change"""
    pass


class PolicyViolationError(TPMFingerprintError):
    """Raised when policy conditions are not satisfied"""
    pass


class AttestationFailedError(TPMFingerprintError):
    """Raised when TPM attestation fails"""
    pass


class SealingError(TPMFingerprintError):
    """Raised when data sealing to TPM fails"""
    pass


class UnsealingError(TPMFingerprintError):
    """Raised when data unsealing from TPM fails"""
    pass


class ChallengeResponseError(TPMFingerprintError):
    """Raised when challenge-response protocol fails"""
    pass


class FingerprintReplayError(TPMFingerprintError):
    """Raised when a fingerprint replay attack is detected"""
    pass


class BootStateChangedError(TPMFingerprintError):
    """Raised when boot state has changed since fingerprint creation"""
    pass


class SecureBootViolationError(TPMFingerprintError):
    """Raised when secure boot violation is detected"""
    pass


class FirmwareUpdateDetectedError(TPMFingerprintError):
    """Raised when firmware update is detected"""
    pass
