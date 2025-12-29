# Tork Governance SDK

[![PyPI version](https://img.shields.io/pypi/v/tork-governance)](https://pypi.org/project/tork-governance/)
[![Python versions](https://img.shields.io/pypi/pyversions/tork-governance)](https://pypi.org/project/tork-governance/)
[![License: MIT](https://img.shields.io/github/license/torkjacobs/tork-governance)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/github/actions/workflow/status/torkjacobs/tork-governance/ci.yml?label=tests)](https://github.com/torkjacobs/tork-governance/actions)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://torkjacobs.github.io/tork-governance/)

**Enterprise-grade governance layer for AI agents.** Enforce policies, redact PII, scan for vulnerabilities, and maintain compliance - all in one SDK.

## 🚀 Quick Start

```bash
pip install tork-governance
```

```python
from tork.core import GovernanceEngine, PIIRedactor
from tork.core.models import EvaluationRequest

# Initialize with PII protection
engine = GovernanceEngine(pii_redactor=PIIRedactor())

# Protect your payload
result = engine.evaluate(EvaluationRequest(
    agent_id="my-agent",
    payload={"msg": "Contact me at test@example.com"}
))

print(result.decision) # PolicyDecision.REDACT
print(result.modified_payload["msg"]) # "Contact me at [REDACTED_EMAIL]"
```

## ✨ Features

- **Governance Engine**: Declarative rules with ALLOW/DENY/REDACT decisions. Supports nested fields and regex.
- **PII Redactor**: Automatic detection and redaction of Emails, SSNs, Credit Cards, IPs, and API Keys.
- **MCP Security Scanner**: Built-in scanner with 10 rules to detect hardcoded secrets, permissive CORS, and insecure configs.
- **Compliance Receipts**: HMAC-signed audit trails with tamper detection for every governed action.
- **Interactive Playground**: Built-in Policy Playground UI for testing policies and redaction in real-time.
- **5 Framework Integrations**: Native support for LangChain, CrewAI, AutoGen, OpenAI Agents, and HTTP Proxy.

## 🔌 Framework Integrations

### LangChain
```python
from tork.adapters.langchain import create_governed_chain
governed_chain = create_governed_chain(your_chain, engine)
```

### CrewAI
```python
from tork.adapters.crewai import TorkCrewAIMiddleware
governed_agent = TorkCrewAIMiddleware().wrap_agent(base_agent)
```

### AutoGen
```python
from tork.adapters.autogen import TorkAutoGenMiddleware
governed_agent = TorkAutoGenMiddleware().wrap_agent(base_agent)
```

### OpenAI Agents SDK
```python
from tork.adapters.openai_agents import TorkOpenAIAgentsMiddleware
governed_agent = TorkOpenAIAgentsMiddleware().wrap_agent(base_agent)
```

### HTTP Proxy
Comprehensive `GovernedProxy` server to wrap any API with governance controls.

## 📖 Documentation

Visit our [Documentation Site](https://torkjacobs.github.io/tork-governance/) for:
- [Quickstart Guide](https://torkjacobs.github.io/tork-governance/quickstart/)
- [API Reference](https://torkjacobs.github.io/tork-governance/api/)
- [Framework Integrations](https://torkjacobs.github.io/tork-governance/integrations/)
- [Policy Examples](https://torkjacobs.github.io/tork-governance/examples/)

## 🛠️ CLI Tools

```bash
# Scan configuration files for security vulnerabilities
tork scan ./configs --severity high

# Check version
tork --version
```

## 🧪 Development

```bash
git clone https://github.com/torkjacobs/tork-governance.git
pip install -e ".[dev]"
pytest tests/
```

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

## 🔗 Links

- [PyPI](https://pypi.org/project/tork-governance/)
- [GitHub](https://github.com/torkjacobs/tork-governance)
- [Documentation](https://torkjacobs.github.io/tork-governance/)
- [Tork Network](https://tork.network)
