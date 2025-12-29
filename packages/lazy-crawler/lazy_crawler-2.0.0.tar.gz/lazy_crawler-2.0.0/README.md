<div align="center">
    <h1>Lazy Crawler</h1>
    <p><strong>Extensible web crawling and data extraction framework.</strong></p>
    <p>A technical foundation for building scalable data pipelines using Scrapy and Playwright.</p>
    <a href="https://github.com/pradip-p/lazy-crawler/releases">
        <img src="https://img.shields.io/github/v/release/pradip-p/lazy-crawler?logo=github" alt="Release Version" />
    </a>
</div>

<br/>

<div align="center">

| **Core Stack**    | ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) ![Scrapy](https://img.shields.io/badge/Scrapy-100000?style=for-the-badge&logo=scrapy&logoColor=white) ![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white) |
| :---------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Code Quality**  | [![PEP8 Style](https://img.shields.io/badge/code%20style-pep8-blue)](https://www.python.org/dev/peps/pep-0008/) [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://pre-commit.com)                                                                         |
| **Documentation** | [![docs](https://img.shields.io/badge/docs-available-brightgreen)](https://pradip-p.github.io/lazy-crawler/) [![license](https://img.shields.io/github/license/pradip-p/lazy-crawler.svg)](https://github.com/pradip-p/lazy-crawler/blob/main/LICENSE.md)                                                                     |

</div>

---

**Lazy Crawler** is an extensible web crawling framework designed for developers who need to build high-performance data extraction pipelines. It combines the speed of **Scrapy** with the dynamic rendering capabilities of **Playwright** to handle complex web environments.

## Features

- **Automated Workflows**: Streamlined project structure for rapid deployment of new spiders.
- **Dynamic Content Support**: Built-in Playwright integration for rendering JavaScript-heavy applications.
- **Multi-backend Support**: Native export functionality for **MongoDB, PostgreSQL, CSV, JSON, and Google Sheets**.
- **Developer First**: Focuses on clean abstractions and extensibility over rigid configurations.
- **Resilient Extraction**: Integrated support for proxy rotation and anti-detection measures.

## Quick Start

### 1. Installation

This project uses **uv** for dependency management.

```bash
uv pip install .
```

For development:

```bash
# Initialize and install in editable mode
uv pip install -e .
```

> [!NOTE]
> Install Playwright browser binaries after the initial setup:
> `playwright install`

### 2. Static Site Crawler

Create `my_agent.py`:

```python
import scrapy
from lazy_crawler.crawler.spiders.base_crawler import LazyBaseCrawler
from scrapy.crawler import CrawlerProcess

class MyAgent(LazyBaseCrawler):
    name = "my_agent"

    def start_requests(self):
        yield scrapy.Request("https://example.com", self.parse)

    def parse(self, response):
        yield {
            "title": response.css("h1::text").get(),
            "url": response.url
        }

process = CrawlerProcess()
process.crawl(MyAgent)
process.start()
```

### 3. Dynamic Content (JavaScript)

Leverage Playwright for sites that require browser rendering:

```python
class DynamicAgent(LazyBaseCrawler):
    name = "dynamic"

    def start_requests(self):
        yield scrapy.Request(
            "https://dynamic-site.com",
            meta={"playwright": True},
            callback=self.parse
        )

    def parse(self, response):
        data = response.css(".rendered-content::text").get()
        yield {"content": data}
```

## Data Management

### 1. MongoDB Integration

**Configuration (.env)**:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DATABASE=lazy_crawler_db
```

**Settings**:

```python
ITEM_PIPELINES = {
    "lazy_crawler.crawler.pipelines.MongoPipeline": 400,
}
```

### 2. Google Sheets Export

**Configuration (.env)**:

```env
GOOGLE_SHEETS_CREDS_FILE=creds.json
GOOGLE_SHEETS_SPREADSHEET_NAME=CrawlData
GOOGLE_SHEETS_WORKSHEET_NAME=Results
```

## Dashboard & API

The project includes a dashboard for monitoring crawl progress and exploring extracted data.

**Start the service**:

```bash
uv run python -m lazy_crawler.app.main
```

- **Dashboard**: `http://localhost:8000/`
- **API Documentation**: `http://localhost:8000/docs`

## Docker Deployment (Production)

Deploy using the provided orchestration files:

```bash
# Quick deployment
./deploy.sh

# Manual startup
docker compose up --build -d
```

- **Dashboard**: `http://localhost/`
- **API Docs**: `http://localhost/docs`
- **Health**: `http://localhost/health`

## Customization

The framework is designed to be modified. You can extend `LazyBaseCrawler` or implement custom pipelines to handle specific data requirements.

## Contributing

Technical contributions and bug reports are welcome. Please refer to [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Lazy Crawler is licensed under the [MIT License](LICENSE).

---

<div align="center">
    Created by <a href="https://github.com/pradip-p">Pradip P.</a>
</div>
