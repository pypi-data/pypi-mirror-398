# TPM Fingerprint Library - Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                            │
│                                                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │  CLI Tool   │  │  Examples    │  │  Your Application      │ │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬─────────────┘ │
└─────────┼─────────────────┼──────────────────────┼───────────────┘
          │                 │                      │
          └─────────────────┴──────────────────────┘
                            │
┌───────────────────────────┼───────────────────────────────────────┐
│                    Library Core Layer                             │
│                           │                                       │
│              ┌────────────▼────────────┐                         │
│              │   OfflineVerifier       │                         │
│              │   (Orchestrator)        │                         │
│              └────────────┬────────────┘                         │
│                           │                                       │
│       ┌───────────────────┼───────────────────┐                 │
│       │                   │                   │                 │
│  ┌────▼─────┐      ┌──────▼──────┐    ┌─────▼──────┐          │
│  │Fingerprint│      │   Policy    │    │Consequence │          │
│  │  Engine   │◄────►│   Engine    │◄──►│  Handler   │          │
│  └────┬──────┘      └──────┬──────┘    └─────┬──────┘          │
│       │                    │                  │                 │
│       └────────────────────┼──────────────────┘                 │
│                            │                                     │
│                     ┌──────▼──────┐                             │
│                     │ Audit Logger│                             │
│                     └──────┬──────┘                             │
│                            │                                     │
│       ┌────────────────────┴────────────────────┐              │
│       │           TPM Operations Layer          │              │
│       │                                          │              │
│       │  ┌──────────┐  ┌──────────┐  ┌────────┐│              │
│       │  │PCR Read  │  │Challenge │  │Seal/   ││              │
│       │  │          │  │Response  │  │Unseal  ││              │
│       │  └──────────┘  └──────────┘  └────────┘│              │
│       └────────────────────┬─────────────────────┘              │
└────────────────────────────┼──────────────────────────────────┘
                             │
┌────────────────────────────┼──────────────────────────────────┐
│                Hardware Layer                                   │
│                            │                                     │
│               ┌────────────▼────────────┐                       │
│               │    TPM 2.0 Hardware     │                       │
│               │  (Trusted Platform      │                       │
│               │   Module)               │                       │
│               │                         │                       │
│               │  • PCR Registers        │                       │
│               │  • Signing Keys         │                       │
│               │  • Sealing Keys         │                       │
│               │  • Random Number Gen    │                       │
│               └─────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Enrollment Flow
```
1. Application Request
         │
         ▼
2. OfflineVerifier.enroll_device()
         │
         ├─► FingerprintEngine.generate_fingerprint()
         │           │
         │           ├─► TPMOps.read_pcrs()
         │           │        └─► TPM Hardware
         │           │
         │           ├─► TPMOps.get_tpm_quote()
         │           │        └─► TPM Hardware (Sign)
         │           │
         │           └─► TPMOps.seal_data()
         │                    └─► TPM Hardware (Seal)
         │
         ├─► PolicyEngine.create_policy()
         │           └─► Store baseline PCRs
         │
         └─► Return: fingerprint_id, policy_id
```

### Verification Flow
```
1. Application Request
         │
         ▼
2. OfflineVerifier.verify_device()
         │
         ├─► FingerprintEngine.load_fingerprint()
         │           │
         │           └─► TPMOps.unseal_data()
         │                    └─► TPM Hardware (Unseal)
         │                         │
         │                         └─► FAIL if PCRs changed ✗
         │
         ├─► FingerprintEngine.verify_fingerprint()
         │           │
         │           ├─► TPMOps.generate_challenge()
         │           │
         │           ├─► TPMOps.sign_challenge()
         │           │        └─► TPM Hardware (Sign)
         │           │
         │           └─► TPMOps.verify_challenge_response()
         │
         ├─► PolicyEngine.validate_fingerprint()
         │           │
         │           ├─► TPMOps.read_pcrs()
         │           │        └─► TPM Hardware
         │           │
         │           ├─► Compare with baseline
         │           │
         │           └─► IF violation detected
         │                    │
         │                    └─► Trigger consequences
         │
         └─► AuditLogger.log_event()
                  └─► TPMOps.seal_data() (for audit logs)
```

### Consequence Enforcement Flow
```
Policy Violation Detected
         │
         ▼
PolicyEngine triggers violation handlers
         │
         ├─► ConsequenceHandler.enforce_consequences()
         │           │
         │           ├─► revoke_credentials_for_fingerprint()
         │           │           │
         │           │           └─► Credential.revoke()
         │           │                    └─► Save state
         │           │
         │           ├─► lock_vaults_for_fingerprint()
         │           │           │
         │           │           └─► Vault.lock()
         │           │                    └─► Save state
         │           │
         │           ├─► invalidate_tokens_for_fingerprint()
         │           │           │
         │           │           └─► Token.invalidate()
         │           │                    └─► Save state
         │           │
         │           └─► record_consequence()
         │                    └─► Save to history
         │
         └─► AuditLogger.log_policy_violation()
                  └─► Sealed to TPM
```

## Component Interactions

### Component Dependency Graph
```
┌─────────────────┐
│OfflineVerifier │ (Facade - coordinates everything)
└────────┬────────┘
         │
    ┌────┼────┬─────────┬────────┐
    │    │    │         │        │
    │    │    │         │        │
    ▼    ▼    ▼         ▼        ▼
┌────┐┌────┐┌────┐ ┌─────┐ ┌─────┐
│FP  ││Pol ││Cons│ │Audit│ │TPM  │
│Eng ││Eng ││Hdlr│ │Log  │ │Ops  │
└─┬──┘└─┬──┘└──┬─┘ └──┬──┘ └──┬──┘
  │     │      │      │       │
  └─────┴──────┴──────┴───────┘
                │
                ▼
         ┌─────────────┐
         │TPM Hardware │
         └─────────────┘

FP Eng   = FingerprintEngine
Pol Eng  = PolicyEngine
Cons Hdlr = ConsequenceHandler
Audit Log = AuditLogger
TPM Ops  = TPMOperations
```

## Storage Layout

```
~/.tpm_fingerprint/
├── fingerprints/              # Sealed fingerprints
│   ├── abc123...sealed
│   ├── def456...sealed
│   └── ghi789...sealed
│
├── policies/                  # Policy definitions
│   ├── policy_001.json
│   ├── policy_002.json
│   └── policy_003.json
│
├── consequences/              # Consequence state
│   ├── credentials.json       # Registered credentials
│   ├── tokens.json           # Registered tokens
│   ├── vaults.json           # Registered vaults
│   └── consequence_history.json
│
├── sealed_logs/              # TPM-sealed audit logs
│   ├── log_20240101_120000.sealed
│   ├── log_20240101_130000.sealed
│   └── log_20240101_140000.sealed
│
├── current_log.json          # Current unsealed log
└── audit.log                 # Text audit log
```

## Security Boundaries

```
┌─────────────────────────────────────────────────────┐
│              Untrusted Environment                   │
│  ┌────────────────────────────────────────────┐    │
│  │         Application Code                    │    │
│  └────────────────┬───────────────────────────┘    │
│                   │                                  │
│  ════════════════ Security Boundary ════════════════│
│                   │                                  │
│  ┌────────────────▼───────────────────────────┐    │
│  │      TPM Fingerprint Library               │    │
│  │  (Software - Protected by TPM binding)     │    │
│  └────────────────┬───────────────────────────┘    │
│                   │                                  │
│  ════════════════ Hardware Boundary ════════════════│
│                   │                                  │
│  ┌────────────────▼───────────────────────────┐    │
│  │            TPM 2.0 Hardware                │    │
│  │  • Protected Keys                          │    │
│  │  • Sealed Storage                          │    │
│  │  • PCR Registers                           │    │
│  │  • Hardware RNG                            │    │
│  │  ✓ Tamper-resistant                        │    │
│  │  ✓ Physically protected                    │    │
│  └────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

## Trust Chain

```
Root of Trust: TPM Hardware
         │
         ├─► PCR Values (Platform State)
         │   └─► Measured by firmware
         │
         ├─► TPM Keys (Non-exportable)
         │   └─► Used for signing & sealing
         │
         └─► TPM Quote (Signed Attestation)
             └─► Binds PCR state + timestamp

Fingerprint Trust:
    Fingerprint sealed to PCR state
         ↓
    Can only be unsealed if PCRs match
         ↓
    Requires live TPM signing
         ↓
    Cannot be replayed (challenge-response)
         ↓
    Trust anchored in hardware
```

## Threat Model & Mitigations

| Threat | Mitigation |
|--------|------------|
| Fingerprint cloning | TPM-bound, requires live signing ✓ |
| Replay attacks | Challenge-response with nonces ✓ |
| State tampering | PCR-sealed storage ✓ |
| Boot tampering | PCR 0-7 monitoring ✓ |
| Firmware modification | PCR 0-1 monitoring ✓ |
| Secure boot bypass | PCR 7 verification ✓ |
| Credential theft | Automatic revocation on change ✓ |
| Vault access after compromise | Automatic lockdown ✓ |
| Log tampering | TPM-sealed audit logs ✓ |
| Offline attacks | All trust in local TPM ✓ |

## Performance Optimization

### Caching Strategy
```
┌─────────────────────────────┐
│ Memory Cache                │
│ ┌─────────────────────────┐ │
│ │ Fingerprints (unsealed) │ │
│ │ Policies (active)       │ │
│ │ Challenge nonces        │ │
│ └─────────────────────────┘ │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Disk Storage                │
│ ┌─────────────────────────┐ │
│ │ Sealed fingerprints     │ │
│ │ Policy definitions      │ │
│ │ Consequence state       │ │
│ │ Audit logs (sealed)     │ │
│ └─────────────────────────┘ │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ TPM Hardware (slow)         │
│ • PCR reads: ~50ms          │
│ • Signing: ~100ms           │
│ • Sealing: ~100ms           │
└─────────────────────────────┘
```

### Batch Operations
```python
# BAD: Multiple TPM operations
for fp_id in fingerprint_ids:
    pcrs = tpm.read_pcrs()  # 50ms each
    
# GOOD: Single TPM operation
pcrs = tpm.read_pcrs()  # 50ms once
for fp_id in fingerprint_ids:
    # Use cached PCRs
```

---

**This architecture ensures security, performance, and patent-worthy innovation.**
