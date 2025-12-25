# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.2] - 2025-12-22

### Added

- 🔒 **Enterprise Redaction** - Added PII patterns for Azure OpenAI and Google Cloud (GCP) API keys.
- 🛡️ **Thread-Safe Analytics** - Implemented locking for global statistics to support parallel testing with `pytest-xdist`.

### Fixed

- ⚡ **Non-blocking Async Latency** - Fixed a critical issue where `time.sleep` in jitter simulation would block the async event loop; now uses `asyncio.sleep` for async tests.
- 🔗 **LangChain Parity** - Updated LangChain integration to correctly handle async delays and error simulation.

## [0.2.0] - 2025-12-22

### Added

- 🚀 **True Async Support** - Replaced fake async with real coroutines and async iterators for OpenAI, Anthropic, Gemini, and LangChain.
- 🎯 **Accurate Tokenizers** - Integrated `tiktoken` for OpenAI and improved Claude heuristics for high-fidelity token counting.
- 📊 **Cost Analytics Dashboard** - Professional terminal summary showing USD saved per test run.
- ⚡ **Chaos Engineering** - New `simulate_jitter` and `simulate_random_errors` tools to test application resilience.
- 🔒 **Secure Recording** - Automatic PII redaction (API keys, Bearer tokens) in cassettes using the new `PIIRedactor`.
- 🐍 **Python 3.14 Support** - Full compatibility and CI verification for the latest Python version.

### Fixed

- Resolved `TypeError` when calling async methods on mock clients.
- Improved MyPy type fidelity for provider-specific response objects.
- Fixed intermittent CI failures on Windows and MacOS runners.

## [0.1.0] - 2024-12-22

### Added

- 🎉 Initial release of pytest-mockllm
- ✨ Zero-config pytest plugin with automatic discovery
- 🤖 **OpenAI mock** - Full support for Chat Completions, Embeddings, and Images API
  - Streaming responses with proper SSE format
  - Function calling / tool use support
  - Token usage simulation
- 🧠 **Anthropic mock** - Claude Messages API support
  - Streaming responses
  - Tool use support
- 💎 **Google Gemini mock** - GenerativeAI API support  
  - Chat and content generation
  - Streaming support
- 🦜 **LangChain integration** - Native support for LangChain's ChatModel interface
- 📼 **Response recording** - VCR-like recording and replay for golden tests
- 💰 **Cost estimation** - Mock and assert on token usage and API costs
- ⚡ **Chaos testing** - Simulate rate limits, timeouts, and API errors
- 📝 Comprehensive documentation and examples

### Security

- No external network calls in mock mode (completely isolated testing)

[Unreleased]: https://github.com/godhiraj-code/pytest-mockllm/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/godhiraj-code/pytest-mockllm/releases/tag/v0.1.0
