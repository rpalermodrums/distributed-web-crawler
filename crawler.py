import requests
from bs4 import BeautifulSoup
import argparse
import urllib.parse
import time
import csv
from urllib.robotparser import RobotFileParser

def crawl(url, depth, output_file):
    visited = set()
    to_visit = {(url, 0)} # (url, depth)

    rp = RobotFileParser()
    rp.set_url(urllib.parse.urljoin(url, "/robots.txt"))
    try:
        rp.read()
    except Exception as e:
        print(f"Error reading robots.txt: {e}")
        return

    with open(output_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['URL', 'Title'])

        while to_visit:
            current_url, current_depth = to_visit.pop()

            if current_depth > depth or not rp.can_fetch("*", current_url):
                continue

            try:
                response = requests.get(current_url, timeout=5)
                response.raise_for_status()
            except (requests.HTTPError, requests.ConnectionError) as e:
                print(f"Error fetching {current_url}: {e}")
                continue

            try:
                soup = BeautifulSoup(response.text, 'html.parser')
            except Exception as e:
                print(f"Error parsing {current_url}: {e}")
                continue

            visited.add(current_url)

            title = soup.title.string if soup.title else 'No title'
            writer.writerow([current_url, title])

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

            time.sleep(1)  # Delay between requests

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A web crawler that respects robots.txt rules, rate limits requests, and stores the URL and title of visited pages.')
    parser.add_argument('url', help='The URL to crawl.')
    parser.add_argument('--depth', type=int, default=2, help='The maximum depth to crawl.')
    parser.add_argument('--output', default='output.csv', help='The output file where the URL and title of visited pages will be stored.')
    args = parser.parse_args()

    crawl(args.url, args.depth, args.output)
