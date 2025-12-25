# 🧠 AgentRank

**The first embedding model that understands WHEN memories happened.**

[![PyPI version](https://badge.fury.io/py/agentrank.svg)](https://badge.fury.io/py/agentrank)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![HuggingFace](https://img.shields.io/badge/🤗-Models-yellow)](https://huggingface.co/vrushket)

---

## Why AgentRank?

Standard embeddings (OpenAI, Cohere, MiniLM) treat "yesterday" and "6 months ago" identically. For AI agent memory, this breaks everything.

AgentRank adds:
- **Temporal embeddings** — 10 learnable time buckets so the model understands recency
- **Memory type embeddings** — Distinguishes events, preferences, and instructions
- **21% better retrieval** on agent memory benchmarks

---

## Installation

```bash
pip install agentrank
```

---

## Quick Start

```python
from agentrank import AgentRankEmbedder

# Load model
model = AgentRankEmbedder.from_pretrained("vrushket/agentrank-base")

# Encode with temporal context
embeddings = model.encode(
    texts=["User prefers Python for backend development"],
    temporal_info=[7],        # 7 days ago
    memory_types=["semantic"] # It's a preference
)
```

---

## Models

| Model | Params | Use Case | HuggingFace |
|-------|--------|----------|-------------|
| AgentRank-Base | 149M | Best quality | [vrushket/agentrank-base](https://huggingface.co/vrushket/agentrank-base) |
| AgentRank-Small | 33M | Fast inference | [vrushket/agentrank-small](https://huggingface.co/vrushket/agentrank-small) |

---

## Benchmarks

| Model | MRR | Recall@5 |
|-------|-----|----------|
| **AgentRank-Base** | **0.65** | **99.6%** |
| AgentRank-Small | 0.64 | 97.4% |
| all-mpnet-base-v2 | 0.54 | 79.6% |
| all-MiniLM-L6-v2 | 0.53 | 75.2% |

---

## Works Great With

**[CogniHive](https://pypi.org/project/cognihive/)** — Multi-agent memory system with "who knows what" routing

```bash
pip install cognihive
```

Together: CogniHive routes questions to the right agent, AgentRank retrieves the right memories.

---

## Links

- **HuggingFace Models**: [huggingface.co/vrushket](https://huggingface.co/vrushket)
  - [agentrank-base](https://huggingface.co/vrushket/agentrank-base)
  - [agentrank-small](https://huggingface.co/vrushket/agentrank-small)
- **GitHub**: [github.com/vmore2/AgentRank-base](https://github.com/vmore2/AgentRank-base)
- **CogniHive**: [pypi.org/project/cognihive](https://pypi.org/project/cognihive/)

---

## Contact

- **Author**: Vrushket More
- **Email**: vrushket2604@gmail.com
- **Issues**: [GitHub Issues](https://github.com/vmore2/AgentRank-base/issues)

---

## License

Apache 2.0 — Free for commercial use.
