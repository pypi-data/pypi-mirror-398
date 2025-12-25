# sayou-connector

[![PyPI version](https://img.shields.io/pypi/v/sayou-connector.svg?color=blue)](https://pypi.org/project/sayou-connector/)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Docs](https://img.shields.io/badge/docs-mkdocs-success.svg?logo=materialformkdocs)](https://sayouzone.github.io/sayou-fabric/library-guides/connector/)

**The Universal Data Ingestion Engine for Sayou Fabric.**

`sayou-connector` provides a unified interface to fetch data from diverse sources—Local Files, Web URLs, and Databases—normalizing everything into a standard format called **SayouPacket**.

It separates the logic of **Navigation** (Generator) from **Retrieval** (Fetcher), enabling complex recursive crawling and pagination strategies out of the box.

## 💡 Core Philosophy

**"Navigate First, Fetch Later."**

Data collection is not just about downloading; it's about discovery. We decouple the responsibility into two roles:

1.  **Generator (Navigator):** The "Brain". It decides *what* to fetch next (e.g., calculates DB offsets, finds next page links) and yields a Task.
2.  **Fetcher (Driver):** The "Muscle". It executes the actual retrieval (e.g., HTTP GET, SQL Query) and returns a Packet.

This separation enables the **Feedback Loop**, where the result of a fetch (e.g., found links) feeds back into the Generator to discover more targets.

## 📦 Installation

```bash
pip install sayou-connector
```

## ⚡ Quick Start

The `ConnectorPipeline` manages the feedback loop between Generators and Fetchers.

```python
from sayou.connector.pipeline import ConnectorPipeline

def run_demo():
    # 1. Initialize Pipeline
    pipeline = ConnectorPipeline()
    pipeline.initialize()

    # 2. Run (Example: Web Crawling)
    print("Starting Web Crawl...")
    
    # Returns an iterator of 'SayouPacket' objects
    packets = pipeline.run(
        source="https://news.daum.net/tech",
        strategy="requests",
        link_pattern=r"https://v\.daum\.net/v/\d+",
        max_depth=1
    )

    # 3. Process Results (Stream)
    for packet in packets:
        if packet.success:
            print(f"[Fetched] {packet.task.uri}")
            # packet.data contains the extracted content (dict, bytes, etc.)
            print(f"   Data: {str(packet.data)[:50]}...")
        else:
            print(f"[Error] {packet.error}")

if __name__ == "__main__":
    run_demo()
```

## 🔑 Key Concepts

### Generators
* **`FileGenerator`**: Recursively scans directories to find files matching extensions or patterns.
* **`SqlGenerator`**: Generates paginated SQL queries (LIMIT/OFFSET) to fetch large tables in batches.
* **`WebCrawlGenerator`**: Manages a URL frontier queue for BFS/DFS web crawling with depth control.

### Fetchers
* **`FileFetcher`**: Reads binary or text content from the local file system.
* **`SqliteFetcher`**: Executes SQL queries against SQLite databases securely.
* **`SimpleWebFetcher`**: Fetches HTML pages and extracts data/links using BeautifulSoup.

## 🤝 Contributing

We welcome contributions for new Fetchers (e.g., `S3Fetcher`, `KafkaFetcher`) or Generators (e.g., `SitemapGenerator`)!

## 📜 License

Apache 2.0 License © 2025 Sayouzone