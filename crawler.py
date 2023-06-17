import requests
from bs4 import BeautifulSoup
import argparse
import urllib.parse

def crawl(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    for link in soup.find_all('a'):
        href = link.get('href')
        
        # Resolve relative links
        if href and not href.startswith(('http://', 'https://')):
            href = urllib.parse.urljoin(url, href)
        
        print(href)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A simple web crawler that finds and prints all links on a webpage.')
    parser.add_argument('url', help='The URL to crawl.')
    args = parser.parse_args()
    
    crawl(args.url)
