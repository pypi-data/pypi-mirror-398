# sayou-core

[![PyPI version](https://img.shields.io/pypi/v/sayou-core.svg?color=blue)](https://pypi.org/project/sayou-core/)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Docs](https://img.shields.io/badge/docs-mkdocs-success.svg?logo=materialformkdocs)](https://sayouzone.github.io/sayou-fabric/library-guides/core/)

**The Fundamental Foundation for Sayou Fabric.**

`sayou-core` provides the shared DNA for all Sayou libraries. It defines the base architecture, standard data protocols, and utility decorators that ensure consistency across the entire ecosystem.

While you might not use `sayou-core` directly in your application, it acts as the **spinal cord** connecting Connector, Refinery, Document, and other modules.

## 💡 Core Philosophy

**"Stability through Standardization."**

To build a modular and scalable data pipeline, every component must speak the same language and behave predictably. `sayou-core` enforces this by providing:

1.  **Unified Component Architecture:** Every plugin (Fetcher, Parser, Refiner) inherits from `BaseComponent`, guaranteeing standardized logging and lifecycle management.
2.  **Strict Data Contracts:** Defines Pydantic schemas like `SayouPacket` and `SayouBlock` to ensure type safety between modules.
3.  **Resilience Patterns:** Provides decorators for retries, timing, and safe execution, reducing boilerplate code in downstream libraries.

## 📦 Installation

`sayou-core` is automatically installed when you install any Sayou library.

    pip install sayou-core

## 🔑 Key Components

### Base Architecture
* **`BaseComponent`**: The root class for all Sayou objects. It handles logger initialization (`self._log`) and configuration injection.

### Standard Schemas (The Protocol)
* **`SayouTask`**: Defines a unit of work (e.g., "Download this URL").
* **`SayouPacket`**: The universal container for transporting raw data between pipelines.
* **`SayouBlock`**: The atomic unit of refined content (Text, Markdown, Record) used by Refinery and Chunking.

### Decorators (The Safety Net)
* **`@safe_run`**: Prevents pipeline crashes by catching exceptions and returning a fallback value.
* **`@retry`**: Automatically retries operations (like API calls) with exponential backoff.
* **`@measure_time`**: logs execution duration for performance monitoring.

## 🤝 Usage Example

If you are building a custom plugin for Sayou Fabric, you will use `sayou-core` extensively.

```python
from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time, safe_run
from sayou.core.schemas import SayouPacket

class MyCustomPlugin(BaseComponent):
    component_name = "MyPlugin"

    @measure_time
    @safe_run(default_return=None)
    def process(self, data) -> SayouPacket:
        self._log(f"Processing {data}...")
        # Your logic here
        return SayouPacket(data="Processed", success=True)
```

## 📜 License

Apache 2.0 License © 2025 Sayouzone