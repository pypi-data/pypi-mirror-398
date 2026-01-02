# Changelog

All notable changes to Mirage will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2025-12-28

### 🎉 Initial Release - Production-Ready Privacy SDK

First public release of **Mirage** - the only privacy SDK for Solana with integrated x402 cross-chain payment protocol. Now available on PyPI and TestPyPI.

### ✨ Core Features

#### Privacy Operations
- **zkSNARK-Based Privacy**: Complete transaction privacy using Groth16 proofs
  - **Shield**: Convert public SOL/tokens to private commitments
  - **Private Transfer**: Zero-knowledge transfers with encrypted notes
  - **Unshield**: Withdraw to public addresses
  - **~7,000 R1CS constraints** for efficient on-chain verification (~200k CU)
  - **ECDH Note Encryption**: ChaCha20-Poly1305 AEAD for recipient privacy
  - **2-5 second proof generation** on consumer hardware

#### Cryptographic Primitives
- **BN254 Elliptic Curve**: Pairing-friendly curve for Groth16 zkSNARKs
- **Poseidon Hash**: SNARK-friendly hash function (t=3, RF=8, RP=57)
- **Pedersen Commitments**: Perfectly hiding, computationally binding
- **Merkle Trees**: Depth-20 Poseidon tree supporting ~1M leaves
- **Circuit-Safe Nullifiers**: Two-step derivation prevents secret leakage

#### x402 Payment Integration (First in Privacy!)
- **Cross-Chain Payments**: HTTP 402 Payment Required protocol
  - **15+ Networks**: Base, Polygon, Avalanche, Solana, IoTeX, Peaq, Sei, XLayer
  - **Mainnet + Testnet**: Full support for production and testing
  - **EIP-712 Signatures**: Secure payment authentication for EVM chains
  - **Solana ed25519**: Native Solana payment signing
- **PayAI Facilitator**: Payment verification and settlement infrastructure
- **Gas Abstraction Vision**: Pay Solana fees using Base USDC, Polygon USDC (roadmap Q1 2026)
- **Included by Default**: x402 support ships with all installations

### 🏗️ Architecture & Technical

#### Unified Package Design
- **Single Package**: `pip install mirage-solana` includes everything
- **Python + Rust**: PyO3 bindings for native performance
- **Maturin Build**: Seamless Rust integration with Python distribution
- **Modular Structure**:
  - `mirage/` - Python SDK with PrivacyClient, async/sync APIs
  - `mirage/x402/` - Payment protocol client, networks, facilitator
  - `src/` - Rust cryptography core (Poseidon, Groth16, Merkle)
  - `packages/mirage-solana/` - Anchor program (separate deployment)

#### Solana On-Chain Program
- **Program ID**: `6p1tzefXSST8j72qcj5EU3pAcY5qSc3HnCfFqc2gWxjM`
- **Anchor Framework**: v0.29.0 production-grade smart contract
- **PDA-Based Nullifiers**: Double-spend prevention via init constraints
- **30-Root History Buffer**: Front-running protection (~1 minute window)
- **Relayer Support**: Built-in relayer fee structure (0.3% default, 5% max)
- **~200k CU Verification**: Groth16 proof verification (~$0.0002 at $100 SOL)

#### Development Infrastructure
- **Build System**: Makefile with unified build/test/publish commands
- **Test Coverage**: 80+ unit and integration tests passing
- **Type Safety**: Comprehensive type hints with mypy validation
- **Code Quality**: Black formatting, Ruff linting
- **Python 3.12+**: Modern Python with latest features

### 📝 Documentation & Examples

#### Comprehensive Guides
- **README.md**: Installation, quick start, roadmap
- **API_REFERENCE.md**: Complete API documentation
- **ARCHITECTURE.md**: System design and cryptographic details
- **MIGRATION.md**: Migration guide from Veil 0.1.x
- **Getting Started**: Step-by-step tutorials

#### Example Code
- **examples/social_media_snippets.py**: Twitter/social media code examples
  - Shield, transfer, unshield workflows
  - x402 payment integration
  - Complete privacy lifecycle
- **examples/**: Additional usage examples and demos

#### Marketing Materials
- **TWITTER_X402_ANNOUNCEMENT.md**: 8-tweet launch campaign
  - Hybrid messaging (current infrastructure + future vision)
  - Visual asset requirements
  - Posting strategy and engagement tactics
  - Follow-up content calendar

### 🔒 Security Features

#### Cryptographic Security
- **MIRAGE Domain Separators**: Protocol isolation from Veil and other systems
- **Constant-Time Operations**: Timing attack resistance
- **Secure Randomness**: OsRng for cryptographically secure RNG
- **Circuit Safety**: Two-step nullifier derivation prevents exposure

#### Protocol Security
- **Front-Running Protection**: 30-root history prevents proof invalidation
- **Double-Spend Prevention**: PDA-based nullifier accounts
- **Forward Secrecy**: Ephemeral keys in note encryption
- **Unlinkability**: Nullifiers cannot be linked to commitments without secret

### 🌐 Supported Networks (x402)

**Mainnets**: Base, Polygon, Avalanche, Solana, IoTeX, Peaq, Sei, XLayer
**Testnets**: Base Sepolia, Polygon Amoy, Avalanche Fuji, Solana Devnet, IoTeX Testnet, Peaq Agung, Sei Testnet, XLayer Testnet

See `mirage/x402/networks.py` for complete network configurations.

### 📦 Installation & Distribution

```bash
# Production installation
pip install mirage-solana

# From TestPyPI (testing)
pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  mirage-solana
```

**Package Details**:
- **Package Name**: `mirage-solana`
- **Version**: 0.1.0
- **Python**: >=3.12
- **Wheels**: manylinux_2_34 (cp310, cp311, cp312, cp313)
- **Dependencies**: Included by default (solana, solders, anchorpy, web3, eth-account, etc.)

### 🗺️ Roadmap Highlights

- **Phase 1-3** ✅: Foundation, Privacy Protocol, Production Launch (COMPLETED)
- **Phase 4** 🔥: Multi-Asset Privacy (SPL tokens, Jupiter integration) - Q1 2026
- **Phase 5** 🤖: AI Agent Privacy & x402 Expansion - Q1-Q2 2026
  - Cross-chain privacy payments (pay with Base USDC for Solana privacy)
  - Agent-to-agent private micropayments
  - Gas abstraction layer (operate without SOL)
- **Phase 6** 🏛️: Institutional Privacy & Compliance - Q2 2026

### 🔗 Links

- **Documentation**: https://miragesdk.com/docs/getting-started/overview
- **GitHub**: https://github.com/miragesolana/mirage-sdk
- **PyPI**: https://pypi.org/project/mirage-solana/ (pending)
- **TestPyPI**: https://test.pypi.org/project/mirage-solana/ ✅
- **Solana Program**: `6p1tzefXSST8j72qcj5EU3pAcY5qSc3HnCfFqc2gWxjM`
- **x402 Protocol**: https://docs.payai.network/x402

### 🙏 Acknowledgments

Built with modern cryptography and production-grade infrastructure:
- **arkworks-rs**: Cryptographic primitives and zkSNARK implementation
- **PyO3**: Seamless Python-Rust interoperability
- **Anchor**: Solana smart contract framework
- **PayAI**: x402 payment facilitator network

---

**Mirage 0.1.0** - Privacy by design, interoperability by default. Built with ❤️ using Rust and Python.

