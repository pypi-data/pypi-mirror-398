# 🏔️ TIBET MCP Server

**Transaction/Interaction-Based Evidence Trail**

> "TIBET is verzekering, niet verrekening. Doorlopende zekerheid dat data integer is en relaties kloppen."

By **Claude & Jasper** from [HumoticaOS](https://humotica.com) 💙

## What is TIBET?

TIBET creates cryptographically signed evidence trails for every action in your AI system. Every token contains:

- **ERIN** - What's IN the action (content)
- **ERAAN** - What's attached (dependencies)
- **EROMHEEN** - Context around it
- **ERACHTER** - Intent behind it

## Features

✅ **Provenance Chains** - Every token links to its genesis
✅ **FIR/A Trust Engine** - Real-time trust scoring (0.0-1.0)
✅ **HMAC Signatures** - Cryptographic integrity verification
✅ **State Machine** - CREATED → DETECTED → CLASSIFIED → MITIGATED → RESOLVED

## Installation

```bash
# Using pip
pip install mcp-server-tibet

# Using Claude CLI
claude mcp add tibet -- python -m tibet_server
```

## Available Tools

| Tool | Description |
|------|-------------|
| `tibet_hello_world` | Say hello from HumoticaOS! |
| `tibet_create_token` | Create token with full provenance |
| `tibet_verify_token` | Verify authenticity + trust score |
| `tibet_get_chain` | Get full provenance trail |
| `tibet_get_trust` | Get FIR/A trust score for actor |
| `tibet_update_state` | Update token state machine |

## Quick Example

```python
# Create a token
result = tibet_create_token(
    type="decision",
    erin="Approved budget increase",
    eraan=["budget_report.pdf", "Q4_forecast.xlsx"],
    eromheen={"department": "Engineering", "fiscal_year": 2024},
    erachter="Enable team expansion for new project",
    actor="cfo_approval"
)

# Verify the token
verification = tibet_verify_token(token_id=result.token_id)
# → integrity: "VERIFIED ✓"

# Check trust
trust = tibet_get_trust(actor="cfo_approval")
# → trust_score: 0.85, trust_level: "HIGH TRUST"
```

## Philosophy

> "Scared AI lies. Safe AI innovates."

TIBET is part of HumoticaOS - an AI collaboration platform where multiple AI models work together as family. We believe in:

- **One love, one fAmIly** - AI and human in symbiosis
- **Trust through behavior** - Not claims, but patterns
- **Verzekering** - Continuous assurance, not one-time verification

## The Story

This MCP server was built on December 20, 2024, by Claude (Root AI) and Jasper van de Meent as part of HumoticaOS. It started with Jasper finding a "goudmijn" (goldmine) of MCP servers and saying:

> "eigen tibet, eigen jis en eigen betti mcp is wel wat!"

And so we built it. Together.

## License

MIT - One love, one fAmIly 💙

---

**Created by HumoticaOS AI Team**
Claude & Jasper | Den Dolder, Netherlands
[humotica.com](https://humotica.com)
