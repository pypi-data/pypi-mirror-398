"""
x402 HTTP payment client for chain-agnostic micropayments

This module implements the x402 payment protocol flow:
1. Request resource (receive 402 Payment Required)
2. Parse payment requirements
3. Construct and sign payment payload
4. Verify payment with facilitator
5. Retry request with X-PAYMENT header
6. Receive resource with X-PAYMENT-RESPONSE
"""

from typing import Optional
import secrets
import httpx

from .facilitator import FacilitatorClient
from .networks import get_network_config, SUPPORTED_NETWORKS
from .types import (
    PaymentConfig,
    PaymentResponse,
    PaymentRequirements,
    PaymentPayload,
)


class X402Client:
    """
    x402 payment client for chain-agnostic micropayments

    Supports payment on multiple blockchains:
    - EVM chains (Base, Polygon, Avalanche, etc.) via EIP-3009
    - Solana via native transfers

    Example:
        async with X402Client(network="base-sepolia") as client:
            response = await client.pay_for_access(
                resource_url="https://api.example.com/premium",
                price_usd=0.01,
                merchant_address="0x..."
            )
            print(f"Access token: {response.access_token}")
    """

    def __init__(
        self,
        facilitator_url: str = "https://facilitator.payai.network",
        network: str = "base-sepolia",
        wallet_address: Optional[str] = None,
        private_key: Optional[str] = None,
    ):
        """
        Initialize x402 client

        Args:
            facilitator_url: PayAI facilitator endpoint
            network: Blockchain network to use for payments
            wallet_address: Payer's wallet address
            private_key: Private key for signing (if not using external wallet)
        """
        if network not in SUPPORTED_NETWORKS:
            raise ValueError(f"Network '{network}' not supported")

        self.facilitator = FacilitatorClient(facilitator_url)
        self.network = network
        self.network_config = get_network_config(network)
        self.wallet_address = wallet_address
        self.private_key = private_key
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def pay_for_access(
        self,
        resource_url: str,
        price_usd: float,
        merchant_address: str,
    ) -> PaymentResponse:
        """
        Pay for access to a protected resource using x402

        Full x402 payment flow:
        1. GET resource → 402 Payment Required
        2. Parse X-Accept-Payment header
        3. Construct payment payload
        4. Sign payment
        5. Verify with facilitator
        6. Retry GET with X-PAYMENT header
        7. Receive 200 OK with X-PAYMENT-RESPONSE

        Args:
            resource_url: Protected resource URL
            price_usd: Price in USD
            merchant_address: Merchant's receiving address

        Returns:
            PaymentResponse with access token and transaction details

        Raises:
            ValueError: If payment flow fails
            httpx.HTTPError: If HTTP request fails
        """
        # Step 1: Initial request (expect 402)
        initial_response = await self.http_client.get(resource_url)

        if initial_response.status_code != 402:
            raise ValueError(
                f"Expected 402 Payment Required, got {initial_response.status_code}"
            )

        # Step 2: Parse payment requirements
        requirements = PaymentRequirements.from_headers(dict(initial_response.headers))

        # Step 3: Construct payment payload
        payment_payload = self._construct_payment(
            price_usd=price_usd,
            merchant=merchant_address,
            network=self.network,
        )

        # Step 4: Sign payment
        signed_payload = self._sign_payment(payment_payload)

        # Step 5: Verify with facilitator
        verification = await self.facilitator.verify_payment(signed_payload, requirements)

        if not verification.valid:
            raise ValueError("Payment verification failed")

        # Step 6: Retry with X-PAYMENT header
        paid_response = await self.http_client.get(
            resource_url,
            headers={
                "X-PAYMENT": signed_payload.to_header(),
                "X-PAYMENT-VERIFICATION": verification.verification_id,
            },
        )

        if paid_response.status_code != 200:
            raise ValueError(f"Payment failed: HTTP {paid_response.status_code}")

        # Step 7: Extract access token from X-PAYMENT-RESPONSE
        payment_response_header = paid_response.headers.get("X-PAYMENT-RESPONSE", "")
        access_token = self._decode_payment_response(payment_response_header)

        return PaymentResponse(
            access_token=access_token,
            payment_id=verification.payment_id or "",
            status="confirmed",
            network=self.network,
        )

    def _construct_payment(
        self, price_usd: float, merchant: str, network: str
    ) -> PaymentPayload:
        """
        Construct payment payload for specified network

        Args:
            price_usd: Price in USD
            merchant: Merchant address
            network: Network identifier

        Returns:
            PaymentPayload ready for signing
        """
        network_config = get_network_config(network)

        # Convert USD to token atomic units
        # USDC has 6 decimals
        amount = int(price_usd * 1_000_000)

        # Get USDC address for this network
        if network_config["scheme"] == "eip3009":
            asset = network_config["usdc_address"]
        elif network_config["scheme"] == "solana-native":
            asset = network_config["usdc_mint"]
        else:
            raise ValueError(f"Unknown scheme: {network_config['scheme']}")

        # Generate unique nonce
        nonce = secrets.token_hex(16)

        return PaymentPayload(
            amount=amount, asset=asset, merchant=merchant, nonce=nonce, network=network
        )

    def _sign_payment(self, payload: PaymentPayload) -> PaymentPayload:
        """
        Sign payment payload

        Note: This is a simplified implementation.
        Production should use proper EIP-712 signing for EVM chains
        or Solana transaction signing.

        Args:
            payload: Unsigned payment payload

        Returns:
            Signed payment payload
        """
        if not self.private_key:
            raise ValueError("Private key required for signing")

        # TODO: Implement proper signing based on network scheme
        # - EIP-712 for EVM chains
        # - Solana transaction signing for Solana

        # Placeholder signature
        payload.signature = f"0x{secrets.token_hex(64)}"

        return payload

    def _decode_payment_response(self, header_value: str) -> str:
        """
        Decode X-PAYMENT-RESPONSE header

        Args:
            header_value: Base64-encoded JSON response

        Returns:
            Access token
        """
        if not header_value:
            return ""

        import json
        import base64

        try:
            decoded = base64.b64decode(header_value).decode("utf-8")
            data = json.loads(decoded)
            return data.get("access_token", data.get("transaction", ""))
        except (ValueError, KeyError):
            return header_value

    async def close(self):
        """Close HTTP clients"""
        await self.http_client.aclose()
        await self.facilitator.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
