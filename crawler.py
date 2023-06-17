import requests
from bs4 import BeautifulSoup
import argparse
import urllib.parse
from urllib.robotparser import RobotFileParser

def crawl(url, depth):
    visited = set()
    to_visit = {(url, 0)} # (url, depth)

    rp = RobotFileParser()
    rp.set_url(urllib.parse.urljoin(url, "/robots.txt"))
    rp.read()

    while to_visit:
        current_url, current_depth = to_visit.pop()

        if current_depth > depth or not rp.can_fetch("*", current_url):
            continue

        try:
            response = requests.get(current_url, timeout=5)
            response.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError):
            continue

        soup = BeautifulSoup(response.text, 'html.parser')

        visited.add(current_url)
        print(current_url)

        for link in soup.find_all('a'):
            href = link.get('href')

            # Ignore mailto links and telephone links
            if href and (href.startswith(('mailto:', 'tel:', 'fax:', 'file:', 'data:', 'sms:', 'news:', 'irc:', 'magnet:'))):
                continue

            # Resolve relative links
            if href and not href.startswith(('http://', 'https://')):
                href = urllib.parse.urljoin(current_url, href)

            if href not in visited:
                to_visit.add((href, current_depth + 1))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A web crawler that respects robots.txt rules.')
    parser.add_argument('url', help='The URL to crawl.')
    parser.add_argument('--depth', type=int, default=2, help='The maximum depth to crawl.')
    args = parser.parse_args()

    crawl(args.url, args.depth)
