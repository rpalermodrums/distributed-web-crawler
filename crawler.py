import requests
from bs4 import BeautifulSoup
import argparse
import urllib.parse
import time
import csv
import logging
from urllib.robotparser import RobotFileParser
import concurrent.futures
import threading

def setup_logger():
    logger = logging.getLogger('web_crawler')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler('web_crawler.log')
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def process_url(url, depth, rp, visited, logger):
    if url is None or not rp.can_fetch("*", url):
        return [], 'No title'

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except (requests.HTTPError, requests.ConnectionError) as e:
        print(f"Error fetching {url}: {e}, thread: {threading.current_thread().name}")
        logger.error(f"Error fetching {url}: {e}, thread: {threading.current_thread().name}")
        return [], 'No title'

    try:
        soup = BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error parsing {url}: {e}, thread: {threading.current_thread().name}")
        logger.error(f"Error parsing {url}: {e}, thread: {threading.current_thread().name}")
        return [], 'No title'

    visited.add(url)

    title = soup.title.string if soup.title else 'No title'
    print(f"Crawled {url}, title: {title}, thread: {threading.current_thread().name}")
    logger.info(f"Crawled {url}, title: {title}, thread: {threading.current_thread().name}")

    new_links = []
    for link in soup.find_all('a'):
        href = link.get('href')

        # Ignore mailto links and telephone links
        if href and (href.startswith(('mailto:', 'tel:', 'fax:', 'file:', 'data:', 'sms:', 'news:', 'irc:', 'magnet:'))):
            continue

        # Resolve relative links
        if href and not href.startswith(('http://', 'https://')):
            href = urllib.parse.urljoin(url, href)

        if href and href not in visited:
            new_links.append(href)

    time.sleep(1)  # Delay between requests
    return new_links, title

def crawl(url, depth, output_file):
    visited = set()
    to_visit = [(url, 0)] # (url, depth)
    logger = setup_logger()

    rp = RobotFileParser()
    rp.set_url(urllib.parse.urljoin(url, "/robots.txt"))
    try:
        rp.read()
    except Exception as e:
        print(f"Error reading robots.txt: {e}, thread: {threading.current_thread().name}")
        logger.error(f"Error reading robots.txt: {e}, thread: {threading.current_thread().name}")
        return

    with open(output_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['URL', 'Title'])

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            while to_visit:
                current_url, current_depth = to_visit.pop()

                if current_depth > depth:
                    continue

                future = executor.submit(process_url, current_url, current_depth, rp, visited, logger)
                new_links, title = future.result()

                writer.writerow([current_url, title])

                for link in new_links:
                    to_visit.append((link, current_depth + 1))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A web crawler that respects robots.txt rules, rate limits requests, and stores the URL and title of visited pages.')
    parser.add_argument('url', help='The URL to crawl.')
    parser.add_argument('--depth', type=int, default=2, help='The maximum depth to crawl.')
    parser.add_argument('--output', default='output.csv', help='The output file where the URL and title of visited pages will be stored.')
    args = parser.parse_args()

    crawl(args.url, args.depth, args.output)
