import requests
import re
from lite_taskman import TaskMan

# Base URL for a safe, educational scraping site
BASE_URL = "https://quotes.toscrape.com"

def fetch_page(url):
    """Fetches a page and returns HTML content."""
    response = requests.get(url, timeout=5)
    return response.text

def demo_crawler():
    tman = TaskMan(max_workers=3)
    
    # Start with the first page
    tman.add(fetch_page, BASE_URL, _tm_name="Page-1")
    
    print(f"Starting incremental crawler on {BASE_URL}...")
    
    all_quotes = []

    with tman:
        # process() will keep running as long as new 'Next' pages are added
        for r in tman.process():
            if r.error:
                print(f"Error fetching {r.name}: {r.error}")
                continue
            
            html = r.result
            
            # 1. Extract quotes (using simple regex for demo purposes)
            quotes = re.findall(r'<span class="text".*?>(.*?)</span>', html)
            all_quotes.extend(quotes)
            print(f"[{r.name}] Found {len(quotes)} quotes.")

            # 2. Find the 'Next' page link
            next_match = re.search(r'<li class="next">\s*<a href="(.*?)">', html)
            if next_match:
                next_url = BASE_URL + next_match.group(1)
                page_num = next_url.split('/')[-2] if '/' in next_url else "Next"
                
                # Dynamically add the next page task
                tman.add(fetch_page, next_url, _tm_name=f"Page-{page_num}")
                print(f"  --> Discovery: Found next page, adding task...")

    print(f"\nCrawler Finished!")
    print(f"Total Quotes Collected: {len(all_quotes)}")
    print(f"Sample Quote: {all_quotes[0][:50]}...")

if __name__ == '__main__':
    demo_crawler()