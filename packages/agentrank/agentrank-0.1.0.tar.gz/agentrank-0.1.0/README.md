# 🧠 AgentRank

**The First Retrieval Model Family Optimized for AI Agent Memory**

Every existing agent memory system (Mem0, Letta, CogniHive, etc.) uses generic embeddings. AgentRank is the first specialized solution.

## Model Family

| Model | Size | Base | Use Case |
|-------|------|------|----------|
| `agentrank-small` | 33M | MiniLM | Edge/fast |
| `agentrank-base` | 110M | ModernBERT-base | Standard |
| `agentrank-reranker` | 140M | Cross-encoder | Top-k reranking |

## Novel Features

1. **Temporal Position Embeddings** - Understands when memories were created
2. **Memory Type Embeddings** - Distinguishes episodic/semantic/procedural
3. **Importance Prediction** - Auxiliary task for ranking critical memories

## Quick Start

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("vrushank/agentrank-base")

# Encode memories
memories = [
    "User prefers dark mode in all applications",
    "Yesterday we discussed Python debugging",
    "To deploy: run pytest → build docker → push to ECR"
]
embeddings = model.encode(memories)

# Encode query and find relevant memories
query = "What are the user's UI preferences?"
query_emb = model.encode(query)
similarities = model.similarity(query_emb, embeddings)
```

## Project Structure

```
agentrank/
├── data/
│   ├── generators/      # Memory & query generators
│   └── datasets/        # Generated training data
├── models/
│   ├── embedder.py      # AgentRank embedder
│   └── reranker.py      # AgentRank reranker
├── training/
│   ├── train_embedder.py
│   └── train_reranker.py
├── evaluation/
│   └── agentmembench.py
└── scripts/
    ├── generate_data.py
    └── upload_to_hub.py
```

## Training Data

- 500K synthetic agent memory traces
- 3 memory types: Episodic (40%), Semantic (35%), Procedural (25%)
- 5 types of hard negatives for robust training

## License

Apache 2.0
