# Quick Start Guide

## Installation

```bash
# Navigate to the project directory
cd Device-fingerprinting-TPM

# Install the library
pip install -e .

# Install optional TPM tools (recommended)
# Windows:
choco install tpm2-tools

# Linux (Ubuntu/Debian):
sudo apt-get install tpm2-tools
```

## 5-Minute Quick Start

### 1. Enroll Your Device (CLI)
```bash
tpm-fingerprint enroll MyDevice -o enrollment.json
```

### 2. Verify Device (CLI)
```bash
# Use the IDs from enrollment.json
tpm-fingerprint verify <fingerprint_id> <policy_id>
```

### 3. Python Quick Start
```python
from tpm_fingerprint_lib import OfflineVerifier

# Initialize
verifier = OfflineVerifier()

# Enroll
enrollment = verifier.enroll_device("MyDevice")

# Verify
verifier.verify_device(
    enrollment['fingerprint_id'],
    enrollment['policy_id']
)

print("✓ Device verified!")
```

## Run Examples

```bash
# Basic usage
python examples/basic_usage.py

# Advanced policy enforcement
python examples/advanced_policy_enforcement.py

# Offline verification
python examples/offline_verification.py
```

## Run Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/test_library.py -v

# Run with coverage
pytest tests/ --cov=tpm_fingerprint_lib
```

## Project Structure

```
Device-fingerprinting-TPM/
├── tpm_fingerprint_lib/      # Main library
│   ├── tpm_ops.py             # TPM operations
│   ├── fingerprint_engine.py  # Fingerprinting
│   ├── policy_engine.py       # Policy enforcement
│   ├── consequence_handler.py # Consequence management
│   ├── offline_verifier.py    # Offline verification
│   ├── audit_logger.py        # Audit logging
│   └── cli.py                 # Command-line interface
│
├── examples/                  # Usage examples
│   ├── basic_usage.py
│   ├── advanced_policy_enforcement.py
│   └── offline_verification.py
│
├── tests/                     # Test suite
│   └── test_library.py
│
├── README.md                  # Main documentation
├── USAGE_GUIDE.md            # Detailed usage guide
├── ARCHITECTURE.md           # Architecture documentation
├── PATENTS.md                # Patent information
├── PROJECT_SUMMARY.md        # Project overview
├── requirements.txt          # Dependencies
└── setup.py                  # Installation script
```

## Key Features at a Glance

✅ **TPM-Bound Fingerprints** - Cannot be cloned or exported  
✅ **Non-Replayable** - Requires live TPM signing  
✅ **Automatic Consequences** - Enforced, not just logged  
✅ **Offline Verification** - No server required  
✅ **Policy Enforcement** - State-based governance  
✅ **Audit Logging** - TPM-sealed, tamper-evident  

## Common Commands

```bash
# Device Management
tpm-fingerprint enroll <name>                      # Enroll device
tpm-fingerprint verify <fp_id> <policy_id>        # Verify device
tpm-fingerprint status <fp_id>                     # Get status
tpm-fingerprint challenge <fp_id>                  # Challenge-response

# List Resources
tpm-fingerprint list-fingerprints                  # List all fingerprints
tpm-fingerprint list-policies                      # List all policies

# Audit Management
tpm-fingerprint audit stats                        # Audit statistics
tpm-fingerprint audit verify                       # Verify audit chain
tpm-fingerprint audit events --limit 50            # List events
```

## Next Steps

1. **Read the full documentation**: [README.md](README.md)
2. **Learn detailed usage**: [USAGE_GUIDE.md](USAGE_GUIDE.md)
3. **Understand architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
4. **Review patent info**: [PATENTS.md](PATENTS.md)
5. **Check examples**: [examples/](examples/)

## Getting Help

- **Documentation**: See README.md and USAGE_GUIDE.md
- **Examples**: See examples/ directory
- **Tests**: See tests/test_library.py
- **Issues**: Open an issue on GitHub

## License

[Your License Here]

---

**Start securing your devices with TPM-based fingerprinting today!**
