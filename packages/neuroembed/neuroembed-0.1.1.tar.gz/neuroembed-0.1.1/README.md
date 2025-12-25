# 🧠 NeuroEmbed

**NeuroEmbed** is a **model-agnostic semantic embedding enrichment framework**.

It does **not replace embedding models**.  
Instead, it **modulates embeddings using semantic context**, producing controlled directional shifts in vector space while preserving dimensionality and normalization.

Designed for:
- RAG systems
- Conversational memory
- Knowledge-aware retrieval
- Agent architectures
- Local / offline-first AI systems

---
## ⭐ Why NeuroEmbed Exists

NeuroEmbed was built to explore context-aware vector representations in a simple, testable, and model-independent way — without hype or overengineering.
If you work on RAG, memory systems, or agent architectures, NeuroEmbed is designed to be a clean building block you can trust.

## ❌ What NeuroEmbed Is NOT

- Not a vector database
- Not a retriever
- Not a model replacement
- Not a “state-of-the-art accuracy” claim

 NeuroEmbed is a semantic modulation layer, designed to integrate cleanly into existing systems.

## 🏗️ Architecture Overview
```
Text Input
   │
   ▼
[ Base Encoder ]
   │
   ▼
Base Embedding  ──────────────┐
                              │
Context Texts ─▶ Encoder ─▶ Context Mean
                              │
                              ▼
                  Context Injector (α)
                              │
                              ▼
                   Enriched Embedding

```
GitHub: https://github.com/Umeshkumar667/NeuroEmbed

## 🚀 Installation

### Standard install (recommended)

```bash
pip install neuroembed
```
## ⚡ Quick Start
```
from neuroembed.core import NeuroEmbed
from neuroembed.encoders.sentence_transformer import SentenceTransformerEncoder

# Initialize encoder (replaceable)
encoder = SentenceTransformerEncoder()

# Initialize NeuroEmbed
ne = NeuroEmbed(encoder=encoder, alpha=0.6)

# Input text
query = "bank interest rate"

# Optional semantic context
context = [
    "RBI monetary policy",
    "repo rate",
    "inflation control"
]

# Generate enriched embedding
embedding = ne.embed(query, context)

print("Embedding shape:", embedding.shape)
print("Embedding norm:", (embedding @ embedding) ** 0.5)

embedding = ne.embed("hello world")

base = encoder.encode(["bank interest rate"])[0]
enriched = ne.embed("bank interest rate", context)

print("Cosine similarity:", base @ enriched)
```
