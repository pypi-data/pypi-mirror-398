import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import os

def get_table_urls(wikipedia_url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(wikipedia_url, headers=headers)

        if response.status_code != 200:
            print("Failed to retrieve the page. Status code:", response.status_code)
            return []
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table', {'class': 'wikitable'})
        urls = set()
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                links = row.find_all('td', href=True)
                for link in links:
                    url = link['href']
                    if re.match(r'https?://', url):
                        urls.add(url)
                    else:
                        absolute_url = urljoin(wikipedia_url, url)
                        urls.add(absolute_url)
                text = row.get_text()
                domain_matches = re.findall(r'\b[A-Za-z0-9.-]+\.[a-z]{2,}\b', text)
                for domain in domain_matches:
                    if not re.match(r'https?://', domain):
                        full_url = 'https://' + domain
                        urls.add(full_url)

        return list(urls)
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the page: {e}")
        return []


def main():
    # Get URLs from Wikipedia page
    url = "https://en.wikipedia.org/wiki/List_of_most-visited_websites"
    urls = get_table_urls(url)
    
    if not urls:
        print("No URLs found, please make sure the Wikipedia page is available.")
        return
    
    # Use the correct path to save 'url_file.txt' in the virtual environment assets folder
    assets_dir = 'myvenv/lib/python3.13/site-packages/stealth_chopper/assets'
    
    # Ensure the directory exists, if not create it
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)

    url_file_path = os.path.join(assets_dir, "url_file.txt")

    # Write the URLs to the file
    with open(url_file_path, 'w') as f:
        for u in urls:
            f.write(u + '\n')

    print(f"URLs have been saved to '{url_file_path}'.")

if __name__ == '__main__':
    main()


    