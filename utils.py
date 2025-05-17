import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' +
                  'AppleWebKit/537.36 (KHTML, like Gecko) ' +
                  'Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}


def get_metadata_from_url(url):
    # Use requests to fetch the page content
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extracting common metadata (e.g., title, description, author, etc.)
    metadata = {}

    # Extracting title
    title_tag = soup.find('title')
    if title_tag:
        metadata['title'] = title_tag.text.strip()

    # Extracting description (meta tag)
    description_tag = soup.find('meta', attrs={'name': 'description'})
    if description_tag and description_tag.get('content'):
        metadata['description'] = description_tag['content'].strip()

    # Extracting author (meta tag)
    author_tag = soup.find('meta', attrs={'name': 'author'})
    if author_tag and author_tag.get('content'):
        metadata['author'] = author_tag['content'].strip()

    # Extracting publication date (if available)
    pub_date_tag = soup.find('meta', attrs={'name': 'pubdate'})
    if pub_date_tag and pub_date_tag.get('content'):
        metadata['pub_date'] = pub_date_tag['content'].strip()

    # You can add more metadata fields as needed
    return metadata
