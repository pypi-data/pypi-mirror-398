# PHTokenizer

Dynamic Hybrid Tokenizer optimized for micro-datasets (100–500 samples).

## Features
- Optimized for small datasets to prevent over-fragmentation.
- Hybrid strategy using atomic tokens and selective BPE.
- Low CPU and RAM usage with LRU cache.
- Supports JSON, CSV, and raw text formats.

## Quick Start
```python
from phtokenizer import DynamicHybridTokenizer, TokenizerConfig

config = TokenizerConfig(vocab_size=1000)
tokenizer = DynamicHybridTokenizer(config=config)

data = ["sample text one", "sample text two"]
tokenizer.fit(data)

tokens = tokenizer.tokenize("sample text")
print(tokens)