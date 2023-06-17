# Web Crawler CLI

A web crawler that respects `robots.txt` rules, rate limits requests, and handles errors gracefully. It starts from a seed URL and follows links to a specified depth.

## Installation

This project requires Python 3 and the following Python libraries installed:

- BeautifulSoup
- requests
- urllib
- csv


If Python is not installed on your machine, you can install it from the official website - https://www.python.org/.

You can install BeautifulSoup, requests, urllib, and csv using pip:


```
pip install beautifulsoup4 requests urllib 

```

The `csv` module comes pre-installed with Python, so you don't need to install it separately.
## Usage

You can run the script using Python:

```
python crawler.py https://www.example.com/ --depth 2

```

Replace 'https://www.example.com/' with the URL you want to crawl. The script will print all links found on the webpage and follow these links to a depth specified by the `--depth` argument. If `--depth` is not provided, it defaults to 2.

The crawler respects the rules set out in the `robots.txt` file of the website. If the `robots.txt` file disallows crawling a particular page, the crawler will skip that page. The crawler also waits 1 second between requests to rate limit itself.

Errors encountered during the crawl, such as network errors or parsing errors, will be printed to the console, but the crawler will attempt to continue with the next URL.

The `--output` argument specifies the output CSV file where the URL and title of visited pages will be stored. If `--output` is not provided, it defaults to `output.csv`.

The crawler logs its activity to a file named `web_crawler.log`. This includes the URLs it visits, any errors it encounters, and other information.

## Limitations

This web crawler does not handle dynamic content loaded with JavaScript. It's a basic tool for educational purposes and should be used responsibly. 

## License

This project is licensed under the MIT License - see the LICENSE.md file for details
