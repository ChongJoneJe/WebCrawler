* Web Crawler & Command-Line Search Tool

This project is a command-line search tool built in Python, designed to crawl a target website, build an inverted index of its content, and allow users to perform search queries against that index.

The primary goal of this project is to demonstrate the fundamental concepts behind modern search engines, including web crawling, data indexing, and query processing. The application specifically targets the website [quotes.toscrape.com](http://quotes.toscrape.com/) to build its search index.

## Key Features

*   **Polite Web Crawler:** Crawls all pages of the target website while observing a 6-second delay between requests to respect the server's resources.
*   **Inverted Index Creation:** Parses the HTML of each page to build an inverted index, mapping every word to the pages it appears on and its frequency of occurrence.
*   **Data Persistence:** The generated index can be saved to a local file, allowing it to be loaded for future sessions without needing to re-crawl the website.
*   **Command-Line Interface:** The tool is operated via a simple and clear set of commands:
    *   `build`: Initiates the web crawler and builds the index from scratch.
    *   `load`: Loads a previously built index from the file system.
    *   `print`: Displays the full inverted index entry for a specific word.
    *   `find`: Searches the index for pages containing a single word or a combination of words.
