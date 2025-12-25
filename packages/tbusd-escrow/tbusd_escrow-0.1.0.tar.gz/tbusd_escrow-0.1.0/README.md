# TBUSD Escrow SDK

Trustless escrow API for crypto payments. Programmatic smart contract escrow on Base blockchain.

## Installation

```bash
pip install tbusd-escrow
```

## Quick Start

```python
from tbusd_escrow import EscrowClient, ReleaseType

# Initialize client with your private key
client = EscrowClient(private_key="0x...")

# Create an escrow for $100
escrow = client.create_escrow(
    beneficiary="0xRecipientAddress",
    amount=100.0,
    release_type=ReleaseType.MUTUAL
)

print(f"Escrow created: {escrow.address}")

# Fund the escrow
client.fund_escrow(escrow.address, 100.0)

# Check status
print(f"Status: {escrow.status}")  # "funded"

# Release funds when satisfied
escrow.release()
```

## Features

- **Create escrows** with flexible release types (mutual, buyer-protected, seller-protected, time-locked)
- **Arbitration support** (optional or required)
- **Auto-release/cancel** with timestamps
- **Query escrows** by depositor or beneficiary
- **Full contract interaction** (fund, release, cancel)

## Release Types

```python
from tbusd_escrow import ReleaseType

ReleaseType.MUTUAL           # Both parties must agree
ReleaseType.BUYER_PROTECTED  # Buyer can release, seller needs arbitrator
ReleaseType.SELLER_PROTECTED # Seller can release, buyer needs arbitrator  
ReleaseType.TIME_LOCKED      # Auto-release after specified time
```

## Read-Only Mode

```python
# No private key = read-only mode
client = EscrowClient()

# Query any escrow
escrow = client.get_escrow("0xEscrowAddress")
print(escrow.to_dict())
```

## Links

- **Website**: https://tbusd.io/escrow/
- **API Docs**: https://tbusd.io/escrow/developers
- **npm SDK**: https://www.npmjs.com/package/@tbusd/escrow-sdk
- **MCP Server**: https://www.npmjs.com/package/@tbusd/escrow-mcp

## Contract Addresses (Base Mainnet)

- Factory: `0x1fFA195A86d7E7872EBC2D1d24899addD3f1eB8c`
- TBUSD Token: `0x0d02E2E2a7ADaF2372ca0C69845c8b159A24a595`

## License

MIT
