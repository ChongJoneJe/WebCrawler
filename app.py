import requests
from bs4 import BeautifulSoup
import time
import json
import sys
import os
from urllib.parse import urljoin, urlparse
import string
import argparse

BASE_URL = "https://quotes.toscrape.com/"
DELAY= 6 
INDEX_FILE = "inverted_index.json"

class SearchTool:

    def __init__(self):
        self.index = {} 
        self.visited_urls = set()
        self.urls_to_visit = []

    def clean(self, text):
        if not text:
            return []
        text = text.lower()
        translator = str.maketrans('', '', string.punctuation)
        text = text.translate(translator)
        words = text.split()
        return [word for word in words if word]

    def process_page(self, url, html_content):
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            page_text = soup.get_text()
            words = self.clean(page_text)

            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1

            self.update_index(url, word_counts)

            links_to_follow = []
            for a_tag in soup.find_all('a', href=True):
                link = a_tag['href']
                absolute_link = urljoin(url, link)

                parsed_link = urlparse(absolute_link)
                if parsed_link.scheme in ['http', 'https'] and parsed_link.netloc == urlparse(BASE_URL).netloc and '#' not in parsed_link.fragment:

                     clean_link = parsed_link.scheme + "://" + parsed_link.netloc + parsed_link.path
                     if parsed_link.query:
                         clean_link += "?" + parsed_link.query
                     links_to_follow.append(clean_link)

            return links_to_follow

        except Exception as e:
            print(f"Error processing page {url}: {e}")
            return []

    def update_index(self, url, word_counts):
        for word, count in word_counts.items():
            if word not in self.index:
                self.index[word] = {}
            self.index[word][url] = count

    def crawl(self, start_url=BASE_URL):
        print(f"Starting crawl from {start_url}...")
        self.urls_to_visit = [start_url]
        self.visited_urls = set()     
        self.index = {}               

        while self.urls_to_visit:
            current_url = self.urls_to_visit.pop(0)

            if current_url in self.visited_urls:
                print(f"Skipping (already visited): {current_url}")
                continue

            print(f"Crawling: {current_url}")
            self.visited_urls.add(current_url)

            try:
                response = requests.get(current_url)
                response.raise_for_status() 

                found_links = self.process_page(current_url, response.text)

                for link in found_links:
                    if link not in self.visited_urls and link not in self.urls_to_visit:
                        self.urls_to_visit.append(link)

            except requests.exceptions.RequestException as e:
                print(f"Error fetching {current_url}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred while crawling {current_url}: {e}")

            if self.urls_to_visit:
                 print(f"Waiting {DELAY} seconds...")
                 time.sleep(DELAY)

        print("Crawl finished.")
        print(f"Total pages crawled: {len(self.visited_urls)}")
        print(f"Total unique words indexed: {len(self.index)}")

    def save_index(self, filepath=INDEX_FILE):
        try:
            output_dir = os.path.dirname(filepath)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                print(f"Created directory: {output_dir}")

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=4, ensure_ascii=False)
            print(f"Index successfully saved to {filepath}")
        except Exception as e:
            print(f"Error saving index to {filepath}: {e}")

    def load_index(self, filepath=INDEX_FILE):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.index = json.load(f)
            print(f"Index successfully loaded from {filepath}")
            return True 
        except FileNotFoundError:
            print(f"Error: Index file not found at {filepath}. Please build the index first using the 'build' command.")
            self.index = {}
            return False
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {filepath}. The file might be corrupted.")
            self.index = {}
            return False
        except Exception as e:
            print(f"Error loading index from {filepath}: {e}")
            self.index = {}
            return False

    def print_index(self, word):
        if not self.index:
            print("Index is not loaded. Please use the 'build' or 'load' command first.")
            return

        word = self.clean(word)
        if not word or len(word) > 1:
             print("Please provide a single word to print the index for.")
             return
        word = word[0] 

        if word in self.index:
            print(f"\n Inverted Index for '{word}' ")
            pages = self.index[word]
            sorted_pages = sorted(pages.items(), key=lambda item: item[1], reverse=True)
            for url, count in sorted_pages:
                print(f"  {url}: {count} occurrence(s)")
        else:
            print(f"Word '{word}' not found in the index.")

    def find_pages(self, query_phrase):
        if not self.index:
            print("Index is not loaded. Please use the 'build' or 'load' command first.")
            return []

        query_words = self.clean(query_phrase)

        if not query_words:
            print("Please provide valid search terms.")
            return []

        print(f"Searching for pages containing: '{query_phrase}' (keywords: {query_words})")

        first_word = query_words[0]
        if first_word not in self.index:
            print(f"Search term '{first_word}' not found in index. No pages match.")
            return [] 

        result_pages = set(self.index[first_word].keys())

        for i, word in enumerate(query_words[1:]):
            if word not in self.index:
                print(f"Search term '{word}' not found in index. No pages match.")
                result_pages = set() 
                break 

            pages_with_word = set(self.index[word].keys())

            result_pages.intersection_update(pages_with_word)

            if not result_pages:
                 print(f"Intersection became empty after processing word '{word}'.")
                 break

        return sorted(list(result_pages))


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    build_parser = subparsers.add_parser('build')
    build_parser.add_argument('--output', default=INDEX_FILE)
    build_parser.add_argument('--start-url', default=BASE_URL)

    load_parser = subparsers.add_parser('load')
    load_parser.add_argument('--input', default=INDEX_FILE)

    print_parser = subparsers.add_parser('print')
    print_parser.add_argument('word')

    find_parser = subparsers.add_parser('find')
    find_parser.add_argument('query', nargs='+')

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    tool = SearchTool()

    if args.command == 'build':
        tool.crawl(start_url=args.start_url)
        tool.save_index(filepath=args.output)

    elif args.command == 'load':
        tool.load_index(filepath=args.input)

    elif args.command == 'print':
        if not tool.index:
            print(f"Attempting to load default index file: {INDEX_FILE}")
            load_success = tool.load_index(INDEX_FILE)
            if not load_success:
                print("Cannot print index. Please build or load index first.")
                sys.exit(1)

        tool.print_index(args.word)

    elif args.command == 'find':
        if not tool.index:
            print(f"Attempting to load default index file: {INDEX_FILE}")
            load_success = tool.load_index(INDEX_FILE)
            if not load_success:
                print("Cannot search. Please build or load index first.")
                sys.exit(1)

        query_phrase = " ".join(args.query)
        result_urls = tool.find_pages(query_phrase)

        if result_urls:
            print("\n Pages containing all search terms ")
            for url in result_urls:
                print(url)
        else:
             pass 

    else:
        parser.print_help()

if __name__ == "__main__":
    main()