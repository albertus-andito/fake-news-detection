import requests
import pprint
from bs4 import BeautifulSoup

urls = [
    "https://www.bbc.co.uk/news/world-us-canada-55210243",
    "https://www.bbc.co.uk/news/uk-55206518",
    "https://www.bbc.co.uk/news/uk-55206518",
    "https://www.bbc.co.uk/news/uk-wales-55105307",
    "https://www.bbc.co.uk/news/stories-54526345"
]


def scrape_bbc(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    headline = soup.find(id='main-heading').text
    text_elems = soup.find_all('div', {'data-component': 'text-block'})
    texts = [elem.text for elem in text_elems]
    return {
        "headline": headline,
        "texts": texts
    }


for url in urls:
    pprint.pprint(scrape_bbc(url))
