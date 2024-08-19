# Distributed Web Crawler

A high-performance, feature-rich web crawler designed for distributed operation, efficiency, and ease of use. This tool respects `robots.txt` rules, implements intelligent rate limiting, handles errors gracefully, and utilizes concurrent processing for optimal speed.

## Key Features

- **Dockerized for Easy Deployment**: Run the crawler consistently across any environment
- **Distributed Architecture**: Designed to run across multiple nodes for increased performance and scalability
- **Intelligent Crawling**: Respects `robots.txt` rules and implements adaptive rate limiting
- **Concurrent Processing**: Utilizes multiple threads for efficient page downloads
- **Robust Error Handling**: Gracefully manages network issues and parsing errors
- **Comprehensive Data Collection**: Stores URL, title, metadata, and full content of visited pages
- **Flexible Output Options**: Supports CSV, JSON, and SQLite storage formats
- **Advanced Logging**: Detailed activity logs with configurable verbosity
- **Customizable Depth and Breadth**: Control the scope of your crawl with precision
- **Content Filtering**: Specify content types to include or exclude
- **Proxy Support**: Rotate through a list of proxies for anonymity and load balancing
- **Resume Capability**: Pause and resume crawls seamlessly
- **JavaScript Rendering**: Option to render JavaScript-heavy pages using Selenium
- **Customizable Crawl Patterns**: Choose between breadth-first and depth-first crawling strategies
- **Content Change Detection**: Monitor websites for updates and receive notifications
- **Broken Link Checker**: Identify and report broken links within crawled sites
- **Custom Plugin System**: Extend the crawler's functionality with custom plugins

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/distributed-web-crawler.git
   cd distributed-web-crawler
   ```

2. Build the Docker image:
   ```
   docker-compose build
   ```

3. Run the crawler:
   ```
   docker-compose run --rm crawler python crawler.py https://example.com --depth 3 --output results.csv
   ```

## Usage

### Basic Usage

```bash
docker-compose run --rm crawler python crawler.py https://example.com --depth 3 --output results.csv
```

### Advanced Options

```bash
docker-compose run --rm crawler python crawler.py https://example.com \
  --depth 3 \
  --output results.json \
  --config config.yaml
```

### Configuration File

For complex setups, use a YAML configuration file. Mount it to the Docker container like this:

```bash
docker-compose run --rm -v $(pwd)/config.yaml:/app/config.yaml crawler python crawler.py --config config.yaml
```

Example `config.yaml`:

```yaml
url: https://example.com
depth: 3
breadth: 100
output_format: json
output: results.json
log_level: INFO
log_file: web_crawler.log
delay: 1
threads: 5
render_js: false
crawl_pattern: breadth-first
content_types: [text/html, application/pdf]
exclude_patterns: ['/login', '/admin']
user_agent: 'DistributedWebCrawler/1.0'
proxy_list: proxies.txt
plugin_dir: plugins
notification_email: user@example.com
schedule: '02:00'
```

## Distributed Operation

To run the crawler in a distributed manner:

1. Set up multiple Docker hosts (e.g., using Docker Swarm or Kubernetes)
2. Deploy the crawler containers across these hosts
3. Configure each instance with a unique starting URL or URL range
4. Use a shared database or message queue for coordination (implementation details depend on your specific setup)

## Output

Crawler output will be saved in the mounted volume. Make sure to mount a volume to persist the output:

```bash
docker-compose run --rm -v $(pwd)/output:/app/output crawler python crawler.py https://example.com --output /app/output/results.csv
```

## Logging

Logs are stored in the file specified by `log_file` in the configuration. To access logs, mount a volume:

```bash
docker-compose run --rm -v $(pwd)/logs:/app/logs crawler python crawler.py https://example.com --log-file /app/logs/crawler.log
```

## Plugins

To use custom plugins, mount your plugins directory to the Docker container:

```bash
docker-compose run --rm -v $(pwd)/plugins:/app/plugins crawler python crawler.py https://example.com --plugin-dir /app/plugins
```

Each plugin should define a `CrawlerPlugin` class with a `process` method:

```python
class CrawlerPlugin:
    def process(self, url, content, metadata, category):
        # Custom processing logic here
        pass
```

## Resume Capability

Use the `--resume` flag to continue a previously interrupted crawl:

```bash
docker-compose run --rm crawler python crawler.py --config config.yaml --resume
```

## Development

To run tests or develop the crawler locally, you can use Docker to ensure a consistent environment:

```bash
# Run tests
docker-compose run --rm crawler pytest tests/

# Open a shell in the container for development
docker-compose run --rm crawler /bin/bash
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational and research purposes only. Always respect website terms of service and `robots.txt` files. Use responsibly and ethically.