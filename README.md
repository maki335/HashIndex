# HashIndex ⚡️
### Ultra-fast, LLM-optimized document indexing in Python.
**Built by the team at [Pardus AI](https://pardusai.org) – The fastest AI Data Analysis Platform.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Discord](https://img.shields.io/discord/1331614742468399124?color=5865F2&label=Discord&logo=discord&logoColor=white)](https://discord.gg/2ufPARqz)

---

HashIndex is the core indexing engine we use at **Pardus AI** to process 50MB+ CSVs and PDFs in seconds. We are open-sourcing our Python implementation so you can build better RAG pipelines without the bloat of LangChain.

> **Want to analyze documents without coding?**
> Try our no-code platform: [Pardus AI Dashboard](https://pardusai.org) (Free for huge files).

## Installation

```bash
git clone https://github.com/JasonHonKL/HashIndex.git
uv venv
uv sync
source .venv/bin/activate
python main.py
```

## Comparative Analysis
HashIndex outperforms standard paradigms in specific Long-Context Narrative tasks where causality matters more than keyword matching.

| Method           | Topology            | Context Management          | Robustness (Unstructured Data) | Latency         |
| ---------------- | ------------------- | --------------------------- | ------------------------------ | --------------- |
| Vector RAG       | Disconnected Chunks | Additive (FIFO overflow)    | High                           | Low (O(1))      |
| PageIndex        | Hierarchical Tree   | Path-Dependent              | Low (Requires Clean Headers)   | High (O(log n)) |
| RAPTOR           | Recursive Tree      | Cluster-Based               | Medium                         | Medium          |
| **HashIndex (Ours)** | **Hash Table**      | **Dynamic Pruning (Agent-led)** | **High (Mechanical Split)**    | **Medium-Low**  |

> *By treating document chunks as Hash Table entries rather than Vector Embeddings, HashIndex avoids the 'Lost in the Middle' phenomenon common in vector search.*

## Citation

If you use HashIndex in your research or project, please cite it as follows:

```bibtex
@software{HashIndex2026,
  author = {Hon, Jason and Pardus AI Team},
  title = {HashIndex: LLM-optimized Document Indexing without vector search},
  year = {2026},
  publisher = {Pardus AI}
}
```
