import argparse
import csv
import json
import logging
import os
import pickle
import smtplib
import time
import urllib.parse

import nltk
import requests
import schedule
import sqlite3
import yaml

from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from nltk.classify import TextCat
from selenium.webdriver.chrome.options import Options
from urllib.robotparser import RobotFileParser
import importlib.util


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
        nltk.download('punkt', quiet=True)
        self.text_classifier = TextCat()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.config.get('user_agent', 'AdvancedWebCrawler/1.0')})
        self.broken_links = []
        self.plugins = self.load_plugins()

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
                response = self.session.get(url, timeout=5, proxies={'http': proxy, 'https': proxy})
                response.raise_for_status()
                content = response.text
                content_type = response.headers.get('content-type', '').split(';')[0]
                if not self.is_allowed_content_type(content_type):
                    return [], None
                soup = BeautifulSoup(content, 'html.parser')
                title = soup.title.string if soup.title else 'No title'
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error processing {url}: {e}")
            self.broken_links.append((url, str(e)))
            return [], None

        self.visited.add(url)
        self.logger.info(f"Crawled {url}, title: {title}")

        if self.should_detect_changes(url, content):
            self.notify_change(url, title)

        new_links = self.extract_links(url, content)
        metadata = self.extract_metadata(content)
        category = self.categorize_content(content)

        # Apply plugins
        for plugin in self.plugins:
            plugin.process(url, content, metadata, category)

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

    def is_allowed_content_type(self, content_type):
        allowed_types = self.config.get('content_types', [])
        if not allowed_types:  # If no types specified, allow all
            return True
        return any(allowed_type in content_type for allowed_type in allowed_types)

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
        crawl_pattern = self.config.get('crawl_pattern', 'breadth-first')
        if crawl_pattern == 'breadth-first':
            self.crawl_breadth_first()
        elif crawl_pattern == 'depth-first':
            self.crawl_depth_first()
        else:
            raise ValueError(f"Unsupported crawl pattern: {crawl_pattern}")

        self.output_handler.close()
        self.save_state()
        self.report_broken_links()

    def crawl_breadth_first(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.get('threads', 5)) as executor:
            while self.to_visit:
                current_url, current_depth = self.to_visit.pop(0)
                if current_depth > self.config['depth']:
                    continue

                future = executor.submit(self.process_url, current_url, current_depth)
                new_links, _ = future.result()

                for link in new_links[:self.config.get('breadth', 100)]:
                    self.to_visit.append((link, current_depth + 1))

    def crawl_depth_first(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.get('threads', 5)) as executor:
            while self.to_visit:
                current_url, current_depth = self.to_visit.pop()
                if current_depth > self.config['depth']:
                    continue

                future = executor.submit(self.process_url, current_url, current_depth)
                new_links, _ = future.result()

                for link in reversed(new_links[:self.config.get('breadth', 100)]):
                    self.to_visit.append((link, current_depth + 1))

    def save_state(self):
        state = {
            'visited': self.visited,
            'to_visit': self.to_visit,
            'content_store': self.content_store
        }
        with open('crawler_state.pkl', 'wb') as f:
            pickle.dump(state, f)

    def load_state(self):
        if os.path.exists('crawler_state.pkl'):
            with open('crawler_state.pkl', 'rb') as f:
                state = pickle.load(f)
            self.visited = state['visited']
            self.to_visit = state['to_visit']
            self.content_store = state['content_store']
            return True
        return False

    def report_broken_links(self):
        if self.broken_links:
            self.logger.info("Broken links found:")
            for url, error in self.broken_links:
                self.logger.info(f"{url}: {error}")

    def load_plugins(self):
        plugins = []
        plugin_dir = self.config.get('plugin_dir', 'plugins')
        if os.path.exists(plugin_dir):
            for filename in os.listdir(plugin_dir):
                if filename.endswith('.py'):
                    module_name = filename[:-3]
                    spec = importlib.util.spec_from_file_location(module_name, os.path.join(plugin_dir, filename))
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, 'CrawlerPlugin'):
                        plugins.append(module.CrawlerPlugin())
        return plugins

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
    parser.add_argument('--resume', action='store_true', help='Resume from previous state')
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
    
    if args.resume and crawler.load_state():
        print("Resuming from previous state.")
    
    if config.get('schedule'):
        schedule.every().day.at(config['schedule']).do(crawler.crawl)
        while True:
            schedule.run_pending()
            time.sleep(1)
    else:
        crawler.crawl()

if __name__ == "__main__":
    main()