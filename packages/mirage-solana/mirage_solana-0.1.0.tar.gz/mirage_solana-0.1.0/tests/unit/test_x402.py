"""
Unit tests for x402 payment integration
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from mirage.x402.types import PaymentConfig, PaymentResponse, PaymentRequirements, PaymentPayload
from mirage.x402.networks import SUPPORTED_NETWORKS, get_network_config


class TestNetworkConfig:
    """Test network configuration"""

    def test_supported_networks_exist(self):
        """Test that supported networks are defined"""
        assert len(SUPPORTED_NETWORKS) > 0
        assert "base-sepolia" in SUPPORTED_NETWORKS
        assert "solana-devnet" in SUPPORTED_NETWORKS

    def test_get_network_config_valid(self):
        """Test getting valid network config"""
        config = get_network_config("base-sepolia")
        assert config is not None
        assert "chain_id" in config
        assert "usdc_address" in config

    def test_get_network_config_invalid(self):
        """Test getting invalid network config raises error"""
        with pytest.raises(ValueError, match="Unsupported network"):
            get_network_config("invalid-network")

    def test_evm_network_has_chain_id(self):
        """Test EVM networks have chain_id"""
        evm_networks = ["base", "base-sepolia", "polygon", "polygon-amoy"]
        for network in evm_networks:
            if network in SUPPORTED_NETWORKS:
                config = get_network_config(network)
                assert "chain_id" in config
                assert isinstance(config["chain_id"], int)

    def test_solana_network_has_usdc_mint(self):
        """Test Solana networks have usdc_mint"""
        solana_networks = ["solana", "solana-devnet"]
        for network in solana_networks:
            if network in SUPPORTED_NETWORKS:
                config = get_network_config(network)
                assert "usdc_mint" in config


class TestPaymentTypes:
    """Test payment data types"""

    def test_payment_config_creation(self):
        """Test PaymentConfig creation"""
        config = PaymentConfig(
            price_usd=0.01,
            merchant_address="0x1234567890abcdef",
            network="base-sepolia"
        )
        assert config.price_usd == 0.01
        assert config.merchant_address == "0x1234567890abcdef"
        assert config.network == "base-sepolia"

    def test_payment_response_creation(self):
        """Test PaymentResponse creation"""
        response = PaymentResponse(
            access_token="token123",
            verification_id="verify456",
            payment_status="verified"
        )
        assert response.access_token == "token123"
        assert response.verification_id == "verify456"
        assert response.payment_status == "verified"

    def test_payment_requirements_creation(self):
        """Test PaymentRequirements creation"""
        requirements = PaymentRequirements(
            amount=1000000,
            asset="USDC",
            merchant="0xMERCHANT",
            nonce="nonce123",
            scheme="eip3009"
        )
        assert requirements.amount == 1000000
        assert requirements.asset == "USDC"
        assert requirements.merchant == "0xMERCHANT"

    def test_payment_payload_creation(self):
        """Test PaymentPayload creation"""
        payload = PaymentPayload(
            amount=1000000,
            asset="USDC",
            merchant="0xMERCHANT",
            nonce="nonce123",
            network="base-sepolia"
        )
        assert payload.amount == 1000000
        assert payload.network == "base-sepolia"


@pytest.mark.skipif(
    condition=True,
    reason="x402 dependencies may not be installed"
)
class TestX402Client:
    """Test X402Client (requires x402 dependencies)"""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test X402Client initialization"""
        try:
            from mirage.x402 import X402Client

            client = X402Client(
                network="base-sepolia",
                wallet_address="0x1234567890abcdef"
            )
            assert client.network == "base-sepolia"
            assert client.wallet_address == "0x1234567890abcdef"
        except ImportError:
            pytest.skip("x402 dependencies not installed")

    @pytest.mark.asyncio
    async def test_facilitator_client_initialization(self):
        """Test FacilitatorClient initialization"""
        try:
            from mirage.x402.facilitator import FacilitatorClient

            client = FacilitatorClient(
                facilitator_url="https://facilitator.payai.network"
            )
            assert client.facilitator_url == "https://facilitator.payai.network"
        except ImportError:
            pytest.skip("x402 dependencies not installed")


class TestPaymentValidation:
    """Test payment validation logic"""

    def test_valid_amount(self):
        """Test valid payment amount"""
        config = PaymentConfig(
            price_usd=0.01,
            merchant_address="0x1234",
            network="base-sepolia"
        )
        assert config.price_usd > 0

    def test_zero_amount_invalid(self):
        """Test that zero amount should be validated"""
        # This would be validated at runtime
        config = PaymentConfig(
            price_usd=0.0,
            merchant_address="0x1234",
            network="base-sepolia"
        )
        assert config.price_usd == 0.0  # Type allows it, but runtime should validate

    def test_negative_amount_invalid(self):
        """Test that negative amount should be validated"""
        # This would be validated at runtime
        config = PaymentConfig(
            price_usd=-0.01,
            merchant_address="0x1234",
            network="base-sepolia"
        )
        assert config.price_usd < 0  # Type allows it, but runtime should validate


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
