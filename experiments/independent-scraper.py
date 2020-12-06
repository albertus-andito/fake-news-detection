from requests_html import HTMLSession
import pprint
from bs4 import BeautifulSoup

urls = [
    "https://www.independent.co.uk/news/science/archaeology/oxford-archaeology-dig-skeleton-hertfordshire-b1767027.html",
    "https://www.independent.co.uk/news/uk/home-news/queen-elizabeth-covid-vaccine-royal-family-b1766920.html",
    "https://www.independent.co.uk/news/uk/politics/self-isolate-payment-discretionary-fund-boris-johnson-b1766402.html",
    "https://www.independent.co.uk/news/uk/home-news/tier-2-pub-restrictions-coronavirus-substantial-meal-b1767116.html",
    "https://www.independent.co.uk/news/uk/crime/covid-antisemitism-jewish-hate-crime-b1766987.html"
]

def scrape_independent(url):
    session = HTMLSession()
    page = session.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    header = soup.find(id='articleHeader')
    headlines = [header.find('h1').text, header.find('h2').text]

    content = soup.find(id='main')
    text_elems = content.find_all('p')
    texts = [elem.text for elem in text_elems]
    return {
        "headline": headlines,
        "texts": texts
    }


for url in urls:
    pprint.pprint(scrape_independent(url))
