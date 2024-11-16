#!/usr/bin/env python3
"""
Ekşi Sözlük Entry Scraper
A tool to scrape entries from Ekşi Sözlük topics
"""

from bs4 import BeautifulSoup
import requests
import pandas as pd
import sys
import concurrent.futures
import time
import random
import logging
from fake_useragent import UserAgent
import cloudscraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

class ScraperError(Exception):
    """Custom exception for scraper-specific errors"""
    pass

def get_soup(url: str, scraper, max_retries: int = 3) -> BeautifulSoup:
    """
    Fetch and parse a webpage with retry logic using cloudscraper
    
    Args:
        url (str): The URL to fetch
        scraper: Cloudscraper instance
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        BeautifulSoup: Parsed HTML content
        
    Raises:
        Exception: If all retry attempts fail
    """
    for attempt in range(max_retries):
        try:
            # Add random delay between requests
            time.sleep(random.uniform(2, 5))
            
            response = scraper.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt == max_retries - 1:
                logging.error(f"Failed to fetch {url} after {max_retries} attempts")
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
    return None

def get_page_count(soup: BeautifulSoup) -> int:
    """
    Extract page count with error handling
    
    Args:
        soup (BeautifulSoup): Parsed HTML content
        
    Returns:
        int: Number of pages
        
    Raises:
        ScraperError: If no entries or pagination found
    """
    try:
        # First try the original selector
        pager = soup.find("div", {"class": "pager"})
        if pager and pager.get("data-pagecount"):
            return int(pager.get("data-pagecount")) + 1
        
        # Fallback: look for last page number in pagination
        pagination = soup.find("div", {"class": "pager"})
        if pagination:
            page_links = pagination.find_all("a")
            page_numbers = [int(link.text) for link in page_links if link.text.isdigit()]
            return max(page_numbers) if page_numbers else 1
        
        # If no pagination found, check if there are any entries
        entries = soup.find("ul", {"id": "entry-item-list"})
        if entries and entries.find_all("li"):
            return 1
        
        raise ScraperError("No entries or pagination found")
    
    except Exception as e:
        logging.error(f"Error getting page count: {str(e)}")
        raise

def scrape_page(page_link: str, scraper) -> list:
    """
    Scrape a single page with error handling
    
    Args:
        page_link (str): URL of the page to scrape
        scraper: Cloudscraper instance
        
    Returns:
        list: List of tuples containing entry data
    """
    try:
        soup = get_soup(page_link, scraper)
        entries_block = soup.find("ul", {"id": "entry-item-list"})
        
        if not entries_block:
            logging.warning(f"No entries block found on {page_link}")
            return []

        entries = entries_block.find_all("li")
        page_entries = []
        
        for entry in entries:
            try:
                username = entry.get("data-author", "Unknown")
                content_div = entry.find("div", {"class": "content"})
                content = content_div.text.strip() if content_div else "No content"
                date_element = entry.find("a", {"class": "entry-date permalink"})
                date = date_element.text.strip() if date_element else "No date"
                
                # Add entry favorites count if available
                favorite_count = entry.get("data-favorite-count", "0")
                
                page_entries.append((username, content, date, favorite_count))
            except Exception as e:
                logging.warning(f"Error parsing entry: {str(e)}")
                continue

        return page_entries
    
    except Exception as e:
        logging.error(f"Error scraping page {page_link}: {str(e)}")
        return []

def main():
    """Main function to run the scraper"""
    if len(sys.argv) != 2:
        print("Usage: python eksi_scraper.py <url>")
        sys.exit(1)

    mainLink = sys.argv[1].split("?")[0]  # Remove query string if present
    
    # Create a cloudscraper instance
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )
    
    # Add random delay before first request
    time.sleep(random.uniform(1, 3))

    # Initial page fetch
    try:
        soup = get_soup(mainLink, scraper)
        pageCount = get_page_count(soup)
        logging.info(f"Found {pageCount} pages to scrape")
    except Exception as e:
        logging.error(f"Failed to initialize scraping: {str(e)}")
        sys.exit(1)

    all_entries = []
    page_links = [f"{mainLink}?p={i}" for i in range(1, pageCount + 1)]

    # Use a smaller number of workers to avoid triggering rate limits
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_to_url = {
            executor.submit(scrape_page, url, scraper): url 
            for url in page_links
        }
        
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                data = future.result()
                all_entries.extend(data)
                logging.info(f"Successfully scraped {url}")
            except Exception as e:
                logging.error(f"Error processing {url}: {str(e)}")

    if not all_entries:
        logging.error("No entries were collected")
        sys.exit(1)

    # Create DataFrame and save to CSV
    EntryDF = pd.DataFrame(all_entries, columns=["username", "entry", "date", "favorites"])
    EntryDF.set_index("username", inplace=True)
    
    output_file = "entries.csv"
    EntryDF.to_csv(output_file, encoding="utf-8-sig")
    logging.info(f"Successfully saved {len(EntryDF)} entries to {output_file}")

if __name__ == "__main__":
    main()
