# Web Crawler CLI

A simple command-line web crawler that finds and prints all links on a webpage and follows these links to a specified depth.

## Installation

This project requires Python 3 and the following Python libraries installed:

- BeautifulSoup
- requests

If Python is not installed on your machine, you can install it from the official website - https://www.python.org/.

You can install BeautifulSoup and requests using pip:

```
pip install beautifulsoup4 requests

```

## Usage 

You can run the script using Python:

```
python crawler.py https://www.example.com/ --depth 2

```

Replace 'https://www.example.com/' with the URL you want to crawl. The script will print all links found on the webpage and follow these links to a depth specified by the `--depth` argument. If `--depth` is not provided, it defaults to 2.

## Limitations

This web crawler does not respect `robots.txt` rules and does not handle dynamic content loaded with JavaScript. It's a basic tool for educational purposes and should be used responsibly. 

## License

This project is licensed under the MIT License - see the LICENSE.md file for details


