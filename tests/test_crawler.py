import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import json
import yaml
from bs4 import BeautifulSoup

# Import the classes and functions we want to test
from crawler import AdvancedWebCrawler, CSVOutputHandler, JSONOutputHandler, SQLiteOutputHandler, load_config

class TestAdvancedWebCrawler(unittest.TestCase):

    def setUp(self):
        self.config = {
            'url': 'https://example.com',
            'depth': 2,
            'output': 'output.csv',
            'output_format': 'csv',
            'log_file': 'web_crawler.log',
            'log_level': 'INFO',
            'delay': 1,
            'threads': 5,
            'breadth': 100
        }
        self.crawler = AdvancedWebCrawler(self.config)

    def test_init(self):
        self.assertEqual(self.crawler.config, self.config)
        self.assertIsNotNone(self.crawler.logger)
        self.assertIsNotNone(self.crawler.rp)
        self.assertIsNotNone(self.crawler.output_handler)

    @patch('crawler.RobotFileParser')
    def test_setup_robotparser(self, mock_robotparser):
        mock_rp = Mock()
        mock_robotparser.return_value = mock_rp
        rp = self.crawler.setup_robotparser()
        mock_rp.set_url.assert_called_once_with('https://example.com/robots.txt')
        mock_rp.read.assert_called_once()
        self.assertEqual(rp, mock_rp)

    def test_setup_output_handler(self):
        self.assertIsInstance(self.crawler.output_handler, CSVOutputHandler)
        
        self.crawler.config['output_format'] = 'json'
        self.assertIsInstance(self.crawler.setup_output_handler(), JSONOutputHandler)
        
        self.crawler.config['output_format'] = 'sqlite'
        self.assertIsInstance(self.crawler.setup_output_handler(), SQLiteOutputHandler)
        
        self.crawler.config['output_format'] = 'invalid'
        with self.assertRaises(ValueError):
            self.crawler.setup_output_handler()

    @patch('crawler.requests.Session')
    def test_process_url(self, mock_session):
        mock_response = Mock()
        mock_response.text = '<html><body><a href="https://example.com/page2">Link</a></body></html>'
        mock_response.headers = {'content-type': 'text/html'}
        mock_session.return_value.get.return_value = mock_response

        new_links, title = self.crawler.process_url('https://example.com', 0)
        
        self.assertEqual(new_links, ['https://example.com/page2'])
        self.assertEqual(title, 'No title')

    def test_extract_links(self):
        content = '<html><body><a href="https://example.com/page2">Link</a></body></html>'
        links = self.crawler.extract_links('https://example.com', content)
        self.assertEqual(links, ['https://example.com/page2'])

    def test_is_allowed_url(self):
        self.crawler.config['exclude_patterns'] = ['/admin', '/login']
        self.assertTrue(self.crawler.is_allowed_url('https://example.com/page'))
        self.assertFalse(self.crawler.is_allowed_url('https://example.com/admin'))
        self.assertFalse(self.crawler.is_allowed_url('https://example.com/login'))

    def test_is_allowed_content_type(self):
        self.crawler.config['content_types'] = ['text/html', 'application/json']
        self.assertTrue(self.crawler.is_allowed_content_type('text/html'))
        self.assertTrue(self.crawler.is_allowed_content_type('application/json'))
        self.assertFalse(self.crawler.is_allowed_content_type('image/jpeg'))

    def test_extract_metadata(self):
        content = '<html><head><meta name="description" content="Test page"></head></html>'
        metadata = self.crawler.extract_metadata(content)
        self.assertEqual(metadata, {'description': 'Test page'})

    @patch('crawler.TextCat.classify')
    def test_categorize_content(self, mock_classify):
        mock_classify.return_value = 'English'
        category = self.crawler.categorize_content('<html><body>Hello, world!</body></html>')
        self.assertEqual(category, 'English')

    def test_should_detect_changes(self):
        url = 'https://example.com'
        content1 = 'Hello, world!'
        content2 = 'Hello, universe!'
        
        self.assertFalse(self.crawler.should_detect_changes(url, content1))
        self.assertTrue(self.crawler.should_detect_changes(url, content2))
        self.assertFalse(self.crawler.should_detect_changes(url, content2))

    @patch('crawler.smtplib.SMTP')
    def test_send_email(self, mock_smtp):
        self.crawler.config['notification_email'] = 'user@example.com'
        self.crawler.send_email('Test Subject', 'Test Body')
        mock_smtp.return_value.send_message.assert_called_once()

    @patch('crawler.pickle.dump')
    def test_save_state(self, mock_dump):
        self.crawler.save_state()
        mock_dump.assert_called_once()

    @patch('crawler.pickle.load')
    @patch('crawler.os.path.exists')
    def test_load_state(self, mock_exists, mock_load):
        mock_exists.return_value = True
        mock_load.return_value = {'visited': set(), 'to_visit': [], 'content_store': {}}
        self.assertTrue(self.crawler.load_state())
        mock_load.assert_called_once()

    @patch('crawler.importlib.util.spec_from_file_location')
    @patch('crawler.importlib.util.module_from_spec')
    @patch('crawler.os.path.exists')
    @patch('crawler.os.listdir')
    def test_load_plugins(self, mock_listdir, mock_exists, mock_module_from_spec, mock_spec_from_file_location):
        mock_exists.return_value = True
        mock_listdir.return_value = ['plugin1.py', 'plugin2.py']
        mock_module = Mock()
        mock_module.CrawlerPlugin = Mock()
        mock_module_from_spec.return_value = mock_module
        
        plugins = self.crawler.load_plugins()
        self.assertEqual(len(plugins), 2)

class TestOutputHandlers(unittest.TestCase):

    def test_csv_output_handler(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            handler = CSVOutputHandler(temp_file.name)
            handler.write('https://example.com', 'Example', {'description': 'Test'}, 'Content', 'English')
            handler.close()

            with open(temp_file.name, 'r') as f:
                content = f.read()
                self.assertIn('https://example.com', content)
                self.assertIn('Example', content)
                self.assertIn('{"description": "Test"}', content)
                self.assertIn('Content', content)
                self.assertIn('English', content)

        os.unlink(temp_file.name)

    def test_json_output_handler(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            handler = JSONOutputHandler(temp_file.name)
            handler.write('https://example.com', 'Example', {'description': 'Test'}, 'Content', 'English')
            handler.close()

            with open(temp_file.name, 'r') as f:
                content = json.load(f)
                self.assertEqual(content[0]['url'], 'https://example.com')
                self.assertEqual(content[0]['title'], 'Example')
                self.assertEqual(content[0]['metadata'], {'description': 'Test'})
                self.assertEqual(content[0]['content'], 'Content')
                self.assertEqual(content[0]['category'], 'English')

        os.unlink(temp_file.name)

    def test_sqlite_output_handler(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            handler = SQLiteOutputHandler(temp_file.name)
            handler.write('https://example.com', 'Example', {'description': 'Test'}, 'Content', 'English')
            handler.close()

            import sqlite3
            conn = sqlite3.connect(temp_file.name)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pages')
            row = cursor.fetchone()
            self.assertEqual(row[0], 'https://example.com')
            self.assertEqual(row[1], 'Example')
            self.assertEqual(json.loads(row[2]), {'description': 'Test'})
            self.assertEqual(row[3], 'Content')
            self.assertEqual(row[4], 'English')
            conn.close()

        os.unlink(temp_file.name)

class TestConfigLoader(unittest.TestCase):

    def test_load_config(self):
        config_data = {
            'url': 'https://example.com',
            'depth': 3,
            'output': 'output.json',
            'output_format': 'json'
        }
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            yaml.dump(config_data, temp_file)
        
        loaded_config = load_config(temp_file.name)
        self.assertEqual(loaded_config, config_data)
        
        os.unlink(temp_file.name)

if __name__ == '__main__':
    unittest.main()