# Batch Runner

## 📌 Overview

Process large datasets efficiently using OpenAI's batch API.

---

## 🚀 Installation

Install the latest release via PyPI:

```bash
pip install -U hamtaa-batch-runner
```

---

## ⚡ Quick Start

```python
from pydantic import BaseModel
from texttools import BatchRunner, BatchConfig

config = BatchConfig(
    system_prompt="Extract entities from the text",
    job_name="entity_extraction",
    input_data_path="data.json",
    output_data_filename="results.json",
    model="gpt-4o-mini"
)

class Output(BaseModel):
    entities: list[str]

runner = BatchRunner(config, output_model=Output)
runner.run()
```