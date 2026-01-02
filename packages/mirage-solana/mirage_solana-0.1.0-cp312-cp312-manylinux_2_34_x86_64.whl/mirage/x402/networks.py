"""
Supported blockchain networks for x402 payments

This module defines the networks supported by the PayAI facilitator.
Each network has its own configuration for USDC addresses and payment schemes.
"""

from typing import Dict, Any

# Network configurations for x402 payments
# Source: https://docs.payai.network/x402/supported-networks
SUPPORTED_NETWORKS: Dict[str, Dict[str, Any]] = {
    # Base (Ethereum L2) - Mainnet
    "base": {
        "chain_id": 8453,
        "facilitator_network": "base",
        "usdc_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "scheme": "eip3009",
        "rpc_url": "https://mainnet.base.org",
        "block_explorer": "https://basescan.org",
    },
    # Base Sepolia - Testnet
    "base-sepolia": {
        "chain_id": 84532,
        "facilitator_network": "base-sepolia",
        "usdc_address": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        "scheme": "eip3009",
        "rpc_url": "https://sepolia.base.org",
        "block_explorer": "https://sepolia.basescan.org",
    },
    # Polygon - Mainnet
    "polygon": {
        "chain_id": 137,
        "facilitator_network": "polygon",
        "usdc_address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "scheme": "eip3009",
        "rpc_url": "https://polygon-rpc.com",
        "block_explorer": "https://polygonscan.com",
    },
    # Polygon Amoy - Testnet
    "polygon-amoy": {
        "chain_id": 80002,
        "facilitator_network": "polygon-amoy",
        "usdc_address": "0x41E94Eb019C0762f9Bfcf9Fb1E58725BfB0e7582",
        "scheme": "eip3009",
        "rpc_url": "https://rpc-amoy.polygon.technology",
        "block_explorer": "https://amoy.polygonscan.com",
    },
    # Avalanche - Mainnet
    "avalanche": {
        "chain_id": 43114,
        "facilitator_network": "avalanche",
        "usdc_address": "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",
        "scheme": "eip3009",
        "rpc_url": "https://api.avax.network/ext/bc/C/rpc",
        "block_explorer": "https://snowtrace.io",
    },
    # Avalanche Fuji - Testnet
    "avalanche-fuji": {
        "chain_id": 43113,
        "facilitator_network": "avalanche-fuji",
        "usdc_address": "0x5425890298aed601595a70AB815c96711a31Bc65",
        "scheme": "eip3009",
        "rpc_url": "https://api.avax-test.network/ext/bc/C/rpc",
        "block_explorer": "https://testnet.snowtrace.io",
    },
    # Solana - Mainnet
    "solana": {
        "facilitator_network": "solana",
        "usdc_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "scheme": "solana-native",
        "rpc_url": "https://api.mainnet-beta.solana.com",
        "block_explorer": "https://explorer.solana.com",
    },
    # Solana Devnet - Testnet
    "solana-devnet": {
        "facilitator_network": "solana-devnet",
        "usdc_mint": "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",
        "scheme": "solana-native",
        "rpc_url": "https://api.devnet.solana.com",
        "block_explorer": "https://explorer.solana.com?cluster=devnet",
    },
    # IoTeX
    "iotex": {
        "chain_id": 4689,
        "facilitator_network": "iotex",
        "usdc_address": "0x3B2bf2b523f54C4E454F08Aa286D03115aFF326c",
        "scheme": "eip3009",
        "rpc_url": "https://babel-api.mainnet.iotex.io",
        "block_explorer": "https://iotexscan.io",
    },
    # Peaq
    "peaq": {
        "chain_id": 3338,
        "facilitator_network": "peaq",
        "usdc_address": "0xfFfFFFffFFFfFFFF0000000000000000000000C1",  # Placeholder
        "scheme": "eip3009",
        "rpc_url": "https://peaq.api.onfinality.io/public",
        "block_explorer": "https://peaq.subscan.io",
    },
    # Sei
    "sei": {
        "chain_id": 1329,
        "facilitator_network": "sei",
        "usdc_address": "0x3894085Ef7Ff0f0aeDf52E2A2704928d1Ec074F1",
        "scheme": "eip3009",
        "rpc_url": "https://evm-rpc.sei-apis.com",
        "block_explorer": "https://seitrace.com",
    },
    # Sei Testnet
    "sei-testnet": {
        "chain_id": 713715,
        "facilitator_network": "sei-testnet",
        "usdc_address": "0xdFb8434A90f86ED2b1d0548F826C2F49f70F655E",
        "scheme": "eip3009",
        "rpc_url": "https://evm-rpc-testnet.sei-apis.com",
        "block_explorer": "https://seitrace.com/?chain=atlantic-2",
    },
    # XLayer
    "xlayer": {
        "chain_id": 196,
        "facilitator_network": "xlayer",
        "usdc_address": "0x74b7F16337b8972027F6196A17a631aC6dE26d22",
        "scheme": "eip3009",
        "rpc_url": "https://rpc.xlayer.tech",
        "block_explorer": "https://www.oklink.com/xlayer",
    },
    # XLayer Testnet
    "xlayer-testnet": {
        "chain_id": 195,
        "facilitator_network": "xlayer-testnet",
        "usdc_address": "0x9C3f01E4831e885F9Ee3C88d4C0b13c8f1f4d3F0",
        "scheme": "eip3009",
        "rpc_url": "https://testrpc.xlayer.tech",
        "block_explorer": "https://www.oklink.com/xlayer-test",
    },
}


def get_network_config(network: str) -> Dict[str, Any]:
    """
    Get configuration for a specific network

    Args:
        network: Network identifier (e.g., "base", "polygon", "solana")

    Returns:
        Network configuration dictionary

    Raises:
        ValueError: If network is not supported
    """
    if network not in SUPPORTED_NETWORKS:
        supported = ", ".join(sorted(SUPPORTED_NETWORKS.keys()))
        raise ValueError(
            f"Network '{network}' is not supported. "
            f"Supported networks: {supported}"
        )

    return SUPPORTED_NETWORKS[network]


def is_testnet(network: str) -> bool:
    """Check if a network is a testnet"""
    testnet_keywords = ["sepolia", "testnet", "devnet", "fuji", "amoy"]
    return any(keyword in network.lower() for keyword in testnet_keywords)


def get_mainnet_networks() -> list[str]:
    """Get list of mainnet network identifiers"""
    return [net for net in SUPPORTED_NETWORKS.keys() if not is_testnet(net)]


def get_testnet_networks() -> list[str]:
    """Get list of testnet network identifiers"""
    return [net for net in SUPPORTED_NETWORKS.keys() if is_testnet(net)]
