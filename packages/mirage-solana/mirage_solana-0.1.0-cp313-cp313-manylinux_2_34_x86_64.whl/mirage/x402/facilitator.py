"""
PayAI Facilitator API client for x402 protocol

The facilitator handles payment verification and settlement on behalf of merchants.
"""

from typing import Dict, Any
import httpx

from .types import VerificationResponse, SettlementResponse, PaymentPayload, PaymentRequirements


class FacilitatorClient:
    """
    Client for PayAI x402 facilitator API

    The facilitator provides three main endpoints:
    - POST /verify: Validate payment payload
    - POST /settle: Execute on-chain transaction
    - GET /list: Discover available merchants
    """

    def __init__(self, base_url: str = "https://facilitator.payai.network"):
        """
        Initialize facilitator client

        Args:
            base_url: Facilitator API base URL
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def verify_payment(
        self, payment_payload: PaymentPayload, requirements: PaymentRequirements
    ) -> VerificationResponse:
        """
        Verify payment payload with facilitator

        The facilitator validates:
        - Signature is valid
        - Payer has sufficient balance
        - Amount meets requirements
        - Authorization is within time window
        - Parameters match payment requirements

        Args:
            payment_payload: Signed payment payload
            requirements: Payment requirements from merchant

        Returns:
            VerificationResponse with validation result

        Raises:
            httpx.HTTPError: If verification request fails
        """
        response = await self.client.post(
            f"{self.base_url}/verify",
            json={
                "payment_payload": payment_payload.to_dict(),
                "payment_requirements": requirements.to_dict(),
            },
        )
        response.raise_for_status()
        data = response.json()

        return VerificationResponse(
            valid=data["valid"],
            verification_id=data["verification_id"],
            payment_id=data.get("payment_id"),
        )

    async def settle_payment(
        self, payment_payload: PaymentPayload, verification_id: str
    ) -> SettlementResponse:
        """
        Settle payment on-chain via facilitator

        The facilitator:
        1. Submits transaction to blockchain
        2. Waits for confirmation
        3. Returns transaction details

        Args:
            payment_payload: Payment payload to settle
            verification_id: Verification ID from verify_payment

        Returns:
            SettlementResponse with transaction details

        Raises:
            httpx.HTTPError: If settlement request fails
        """
        response = await self.client.post(
            f"{self.base_url}/settle",
            json={
                "payment_payload": payment_payload.to_dict(),
                "verification_id": verification_id,
            },
        )
        response.raise_for_status()
        data = response.json()

        return SettlementResponse(
            tx_hash=data["tx_hash"], status=data["status"], network=data["network"]
        )

    async def list_merchants(self) -> Dict[str, Any]:
        """
        List available merchants on facilitator

        Returns:
            Dictionary of available merchants and their services
        """
        response = await self.client.get(f"{self.base_url}/list")
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
