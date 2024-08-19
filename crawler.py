import requests
from bs4 import BeautifulSoup
import argparse
import urllib.parse
import time
import csv
import json
import sqlite3
import logging
from urllib.robotparser import RobotFileParser
import concurrent.futures
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import yaml
import schedule
import nltk
from nltk.classify import TextCat
import smtplib
from email.mime.text import MIMEText

class AdvancedWebCrawler:
    def __init__(self, config):
        self.config = config
        self.visited = set()
        self.to_visit = [(config['url'], 0)]
        self.logger = self.setup_logger()
        self.rp = self.setup_robotparser()
        self.output_handler = self.setup_output_handler()
        self.proxy_list = self.load_proxy_list()
        self.current_proxy_index = 0
        self.content_store = {}
        nltk.download('punkt')
        self.text_classifier = TextCat()

    def setup_logger(self):
        logger = logging.getLogger('advanced_web_crawler')
        logger.setLevel(getattr(logging, self.config.get('log_level', 'INFO')))
        handler = logging.FileHandler(self.config.get('log_file', 'web_crawler.log'))
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def setup_robotparser(self):
        rp = RobotFileParser()
        rp.set_url(urllib.parse.urljoin(self.config['url'], "/robots.txt"))
        try:
            rp.read()
        except Exception as e:
            self.logger.error(f"Error reading robots.txt: {e}")
        return rp

    def setup_output_handler(self):
        output_format = self.config.get('output_format', 'csv')
        if output_format == 'csv':
            return CSVOutputHandler(self.config['output'])
        elif output_format == 'json':
            return JSONOutputHandler(self.config['output'])
        elif output_format == 'sqlite':
            return SQLiteOutputHandler(self.config['output'])
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def load_proxy_list(self):
        proxy_file = self.config.get('proxy_list')
        if proxy_file:
            with open(proxy_file, 'r') as f:
                return f.read().splitlines()
        return []

    def get_next_proxy(self):
        if not self.proxy_list:
            return None
        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy

    def process_url(self, url, depth):
        if url is None or not self.rp.can_fetch("*", url):
            return [], None

        proxy = self.get_next_proxy()
        try:
            if self.config.get('render_js', False):
                content, title = self.fetch_with_javascript(url)
            else:
                response = requests.get(url, timeout=5, proxies={'http': proxy, 'https': proxy})
                response.raise_for_status()
                content = response.text
                soup = BeautifulSoup(content, 'html.parser')
                title = soup.title.string if soup.title else 'No title'
        except Exception as e:
            self.logger.error(f"Error processing {url}: {e}")
            return [], None

        self.visited.add(url)
        self.logger.info(f"Crawled {url}, title: {title}")

        if self.should_detect_changes(url, content):
            self.notify_change(url, title)

        new_links = self.extract_links(url, content)
        metadata = self.extract_metadata(content)
        category = self.categorize_content(content)

        self.output_handler.write(url, title, metadata, content, category)

        time.sleep(self.config.get('delay', 1))
        return new_links, title

    def fetch_with_javascript(self, url):
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(5)  # Wait for JavaScript to render
        content = driver.page_source
        title = driver.title
        driver.quit()
        return content, title

    def extract_links(self, base_url, content):
        soup = BeautifulSoup(content, 'html.parser')
        new_links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and not href.startswith(('mailto:', 'tel:', 'javascript:')):
                full_url = urllib.parse.urljoin(base_url, href)
                if full_url not in self.visited and self.is_allowed_url(full_url):
                    new_links.append(full_url)
        return new_links

    def is_allowed_url(self, url):
        for pattern in self.config.get('exclude_patterns', []):
            if pattern in url:
                return False
        return True

    def extract_metadata(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        metadata = {}
        for meta in soup.find_all('meta'):
            key = meta.get('name') or meta.get('property')
            if key:
                metadata[key] = meta.get('content')
        return metadata

    def categorize_content(self, content):
        text = BeautifulSoup(content, 'html.parser').get_text()
        return self.text_classifier.classify(text)

    def should_detect_changes(self, url, content):
        if url in self.content_store:
            return content != self.content_store[url]
        self.content_store[url] = content
        return False

    def notify_change(self, url, title):
        if 'notification_email' in self.config:
            subject = f"Content change detected: {title}"
            body = f"The content at {url} has changed."
            self.send_email(subject, body)

    def send_email(self, subject, body):
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = "crawler@example.com"
        msg['To'] = self.config['notification_email']
        
        s = smtplib.SMTP('localhost')
        s.send_message(msg)
        s.quit()

    def crawl(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.get('threads', 5)) as executor:
            while self.to_visit:
                current_url, current_depth = self.to_visit.pop(0)
                if current_depth > self.config['depth']:
                    continue

                future = executor.submit(self.process_url, current_url, current_depth)
                new_links, _ = future.result()

                for link in new_links[:self.config.get('breadth', 100)]:
                    self.to_visit.append((link, current_depth + 1))

        self.output_handler.close()

class CSVOutputHandler:
    def __init__(self, filename):
        self.file = open(filename, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['URL', 'Title', 'Metadata', 'Content', 'Category'])

    def write(self, url, title, metadata, content, category):
        self.writer.writerow([url, title, json.dumps(metadata), content, category])

    def close(self):
        self.file.close()

class JSONOutputHandler:
    def __init__(self, filename):
        self.file = open(filename, 'w')
        self.file.write('[\n')
        self.first = True

    def write(self, url, title, metadata, content, category):
        if not self.first:
            self.file.write(',\n')
        self.first = False
        json.dump({'url': url, 'title': title, 'metadata': metadata, 'content': content, 'category': category}, self.file)

    def close(self):
        self.file.write('\n]')
        self.file.close()

class SQLiteOutputHandler:
    def __init__(self, filename):
        self.conn = sqlite3.connect(filename)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS pages
                               (url TEXT PRIMARY KEY, title TEXT, metadata TEXT, content TEXT, category TEXT)''')

    def write(self, url, title, metadata, content, category):
        self.cursor.execute('INSERT OR REPLACE INTO pages VALUES (?, ?, ?, ?, ?)',
                            (url, title, json.dumps(metadata), content, category))
        self.conn.commit()

    def close(self):
        self.conn.close()

def load_config(config_file):
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description='Advanced Web Crawler')
    parser.add_argument('url', help='The URL to start crawling from')
    parser.add_argument('--depth', type=int, default=2, help='The maximum depth to crawl (default: 2)')
    parser.add_argument('--output', default='output.csv', help='The output file name (default: output.csv)')
    parser.add_argument('--config', help='Path to YAML configuration file')
    args = parser.parse_args()

    if args.config:
        config = load_config(args.config)
    else:
        config = {
            'url': args.url,
            'depth': args.depth,
            'output': args.output,
            'output_format': 'csv',
            'log_file': 'web_crawler.log',
            'log_level': 'INFO',
            'delay': 1,
            'threads': 5,
            'breadth': 100
        }

    crawler = AdvancedWebCrawler(config)
    
    if config.get('schedule'):
        schedule.every().day.at(config['schedule']).do(crawler.crawl)
        while True:
            schedule.run_pending()
            time.sleep(1)
    else:
        crawler.crawl()

if __name__ == "__main__":
    main()