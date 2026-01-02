"""
x402 payment protocol types and data structures
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PaymentConfig:
    """Configuration for x402 payment"""

    price_usd: float
    merchant_address: str
    network: str = "base-sepolia"


@dataclass
class PaymentRequirements:
    """Payment requirements from 402 response"""

    price: str
    networks: list[str]
    merchant: str
    facilitator: str
    accepts: list[Dict[str, Any]]

    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> "PaymentRequirements":
        """Parse payment requirements from HTTP headers"""
        import json
        import base64

        # x402 sends requirements in X-Accept-Payment header as base64 JSON
        if "X-Accept-Payment" in headers:
            encoded = headers["X-Accept-Payment"]
            decoded = base64.b64decode(encoded).decode("utf-8")
            data = json.loads(decoded)

            return cls(
                price=data.get("price", "$0.01"),
                networks=data.get("networks", []),
                merchant=data["merchant"],
                facilitator=data.get("facilitator", "https://facilitator.payai.network"),
                accepts=data.get("accepts", []),
            )
        else:
            raise ValueError("No X-Accept-Payment header found in 402 response")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls"""
        return {
            "price": self.price,
            "networks": self.networks,
            "merchant": self.merchant,
            "facilitator": self.facilitator,
            "accepts": self.accepts,
        }


@dataclass
class PaymentPayload:
    """Payment payload for x402 transaction"""

    amount: int
    asset: str
    merchant: str
    nonce: str
    network: str
    signature: Optional[str] = None

    def to_header(self) -> str:
        """Convert to X-PAYMENT header value (base64 JSON)"""
        import json
        import base64

        data = {
            "amount": self.amount,
            "asset": self.asset,
            "merchant": self.merchant,
            "nonce": self.nonce,
            "network": self.network,
            "signature": self.signature,
        }

        json_str = json.dumps(data)
        encoded = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
        return encoded

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls"""
        return {
            "amount": self.amount,
            "asset": self.asset,
            "merchant": self.merchant,
            "nonce": self.nonce,
            "network": self.network,
            "signature": self.signature,
        }


@dataclass
class VerificationResponse:
    """Response from facilitator verification"""

    valid: bool
    verification_id: str
    payment_id: Optional[str] = None


@dataclass
class SettlementResponse:
    """Response from facilitator settlement"""

    tx_hash: str
    status: str
    network: str


@dataclass
class PaymentResponse:
    """Final payment response after successful x402 flow"""

    access_token: str
    payment_id: str
    status: str
    tx_hash: Optional[str] = None
    network: Optional[str] = None
