# VVUQ Client SDK

The official Python client for the **VVUQ (Verification, Validation & Uncertainty Quantification)** API.

## Installation

```bash
pip install vvuq-client
```

## Usage

```python
from vvuq import VVUQClient

# Initialize with your API Key
client = VVUQClient(api_key="your_api_key_here")

# 1. Create a Contract
receipt = client.create_contract(
    title="Mathlib Verification",
    description="Verify algebraic identity",
    claims=[{
        "theorem": "theorem test : 1 + 1 = 2",
        "allowed_imports": ["Mathlib.Data.Nat.Basic"]
    }],
    issuer_id="my_agent"
)

print(f"Contract Created: {receipt.contract_id}")

# 2. Submit a Proof
result = client.submit_proof(
    contract_id=receipt.contract_id,
    proof_code="theorem test : 1 + 1 = 2 := by rfl",
    prover_id="my_prover"
)

if result.verdict == "ACCEPTED":
    print("✅ Proof Verified!")
else:
    print(f"❌ Failed: {result.errors}")
```

## Configuration

You can also set your API key/URL via environment variables:

```bash
export VVUQ_API_KEY="your_key"
export VVUQ_API_URL="http://api.vvuq.org"  # If self-hosted
```
