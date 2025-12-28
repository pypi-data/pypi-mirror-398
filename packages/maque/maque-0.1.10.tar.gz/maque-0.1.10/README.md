<h1 align="center">maque (麻雀)</h1>

<p align="center">
    <strong>Python toolkit for ML, CV, NLP and multimodal AI development</strong>
</p>

<p align="center">
    <a href="https://pypi.org/project/maque/">
        <img src="https://img.shields.io/pypi/v/maque?color=brightgreen&style=flat-square" alt="PyPI version">
    </a>
    <a href="https://github.com/KenyonY/maque/blob/main/LICENSE">
        <img alt="License" src="https://img.shields.io/github/license/KenyonY/maque.svg?color=blue&style=flat-square">
    </a>
    <a href="https://github.com/KenyonY/maque/actions/workflows/run_tests.yml">
        <img alt="tests" src="https://img.shields.io/github/actions/workflow/status/KenyonY/maque/run_tests.yml?style=flat-square&label=tests">
    </a>
    <a href="https://pypistats.org/packages/maque">
        <img alt="pypi downloads" src="https://img.shields.io/pypi/dm/maque?style=flat-square">
    </a>
</p>

---

## Features

- **MLLM Processing** - Batch image analysis with OpenAI/Gemini compatible APIs
- **LLM Server** - Local LLM inference with Transformers backend
- **Embedding Service** - Text/multimodal embedding API server
- **Clustering Pipeline** - UMAP + HDBSCAN for vector clustering and visualization
- **Async Executor** - Priority queue-based concurrent task execution with retry
- **Rich CLI** - Modular command groups for various tasks

## Installation

```bash
# Basic installation
pip install maque

# With specific feature sets
pip install maque[torch,nlp,cv]          # ML/NLP/CV features
pip install maque[clustering,embedding]  # ML pipeline features
pip install maque[dev,test]              # Development setup

# From source
pip install -e .
pip install -e .[dev,test]
```

## CLI Usage

Commands are organized into groups: `maque <group> <command>`. Short alias `mq` is also available.

### Config Management

```bash
maque config show                 # Show current configuration
maque config edit                 # Open config in editor
maque config init                 # Initialize config file
```

### MLLM (Multimodal LLM)

```bash
# Process images from a table
maque mllm call-table data.xlsx --image_col="image_path" --model="gpt-4o"

# Process images from a folder
maque mllm call-images ./photos --recursive=True --output_file="results.csv"
```

### LLM Server

```bash
# Start LLM inference server
maque llm serve Qwen/Qwen2.5-7B-Instruct --port=8000

# Interactive chat
maque llm chat --model="gpt-4o"
```

### Embedding Service

```bash
# Start embedding API server
maque embedding serve --model=BAAI/bge-m3 --port=8001

# Test embedding endpoint
maque embedding test --text="Hello world"
```

### Data Processing

```bash
# Interactive table viewer (Streamlit)
maque data table-viewer data.csv --port=8501

# Convert between formats
maque data convert input.json output.csv
```

### System Utilities

```bash
# Kill processes on ports
maque system kill 8000 8001

# Pack directory
maque system pack ./folder

# Split large file
maque system split large_file.dat --chunk_size=1GB
```

### Git Helpers

```bash
# Clone with options
maque git clone https://github.com/user/repo --branch=dev

# Generate SSH key
maque git gen-key project_name --email=your@email.com
```

## Python API

### IO Utilities

```python
from maque import yaml_load, yaml_dump, json_load, json_dump, jsonl_load, jsonl_dump

# Load/save YAML
config = yaml_load("config.yaml")
yaml_dump(data, "output.yaml")

# Load/save JSONL
records = jsonl_load("data.jsonl")
jsonl_dump(records, "output.jsonl")
```

### MLLM Client

```python
from maque.mllm import MllmClient

client = MllmClient(
    base_url="https://api.openai.com/v1",
    api_key="your-api-key",
    model="gpt-4o"
)

# Single image
response = client.call("Describe this image", image_path="photo.jpg")

# Batch processing
from maque.mllm import TableProcessor
processor = TableProcessor(client)
results = processor.process("data.xlsx", image_col="image_path", prompt="Describe the image")
```

### Async Executor

```python
from maque.async_api import ConcurrentExecutor

async def process_item(item):
    # Your async processing logic
    return result

executor = ConcurrentExecutor(
    max_concurrent=10,
    max_qps=5,
    max_retries=3
)

results = await executor.run(
    process_item,
    items,
    progress=True
)
```

### Embedding & Retrieval

```python
from maque.embedding import TextEmbedding
from maque.retriever import ChromaRetriever, Document

# Initialize
embedding = TextEmbedding(base_url="http://localhost:8001/v1", model="bge-m3")
retriever = ChromaRetriever(
    embedding,
    persist_dir="./chroma_db",
    collection_name="my_data"
)

# Insert documents
documents = [Document(id="1", content="text...", metadata={"source": "file1"})]
retriever.upsert_batch(documents, batch_size=32, skip_existing=True)

# Search
results = retriever.search("query text", top_k=10)
```

### Clustering Pipeline

```python
from maque.clustering import ClusterAnalyzer

analyzer = ClusterAnalyzer(algorithm="hdbscan", min_cluster_size=15)

# Analyze from ChromaDB
result = analyzer.analyze_chroma(
    persist_dir="./chroma_db",
    collection_name="my_data",
    output_dir="./results",
    sample_size=10000,
    visualize=True
)

# Access results
print(f"Found {result.n_clusters} clusters")
print(result.labels)
print(result.cluster_stats)
```

### Performance Measurement

```python
from maque import MeasureTime

with MeasureTime("model inference", gpu=True):
    output = model(input)
# Prints: model inference took 0.123s (GPU: 0.089s)
```

## Configuration

maque uses hierarchical configuration (highest priority first):

1. `./maque_config.yaml` (current directory)
2. Project root config
3. `~/.maque/config.yaml` (user config)

Example configuration:

```yaml
mllm:
  model: gpt-4o
  base_url: https://api.openai.com/v1
  api_key: ${OPENAI_API_KEY}

embedding:
  model: BAAI/bge-m3
  base_url: http://localhost:8001/v1

llm:
  default_port: 8000
```

Initialize config:
```bash
maque config init
```

## Development

```bash
# Install development dependencies
pip install -e .[dev,test]

# Run tests
pytest
pytest -m "not slow"  # Skip slow tests

# Format code
black .
isort .
```

## License

MIT License - see [LICENSE](LICENSE) for details.
