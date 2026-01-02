"""
x402 payment protocol integration for chain-agnostic micropayments

This subpackage provides x402 protocol support for paying to access
Mirage privacy services using any supported blockchain.

Supported networks:
- Base (Ethereum L2)
- Polygon
- Avalanche
- Solana
- And more via PayAI facilitator

Example usage:
    from mirage.x402 import X402Client, PaymentConfig

    client = X402Client(network="base-sepolia")
    payment = await client.pay_for_access(
        resource_url="https://mirage-api/shield",
        price_usd=0.01,
        merchant_address="0xMERCHANT..."
    )
"""

try:
    from .client import X402Client
    from .types import PaymentConfig, PaymentResponse, PaymentRequirements

    __all__ = ["X402Client", "PaymentConfig", "PaymentResponse", "PaymentRequirements"]
except ImportError:
    import warnings

    warnings.warn(
        "x402 dependencies not installed. "
        "Install with: pip install mirage-client[x402]"
    )
    X402Client = None  # type: ignore
    PaymentConfig = None  # type: ignore
    PaymentResponse = None  # type: ignore
    PaymentRequirements = None  # type: ignore
    __all__ = []

__version__ = "0.1.0"
