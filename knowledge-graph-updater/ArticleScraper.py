import os
import requests
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient
from requests_html import HTMLSession


class ArticleScraper(ABC):

    def __init__(self):
        load_dotenv(dotenv_path=Path('../.env'))
        self.db_client = MongoClient(os.getenv("MONGODB_ADDRESS"))
        self.db = self.db_client["fnd"]
        self.db_collection = self.db["articles"]
        self.db_collection.create_index("source", unique=True)

    def execute(self, url):
        self.save_to_db(self.scrape(url))

    @abstractmethod
    def scrape(self, url):
        pass

    def save_to_db(self, article):
        self.db_collection.update_one({'source': article['source']}, {'$set': article}, upsert=True)


class BbcScraper(ArticleScraper):
    def scrape(self, url):
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        text_elements = soup.find_all('div', {'data-component': 'text-block'})
        texts = [elem.text for elem in text_elements]
        return {
            "headlines": [soup.find(id='main-heading').text],
            "date": datetime.fromisoformat(soup.time['datetime'].replace("Z", "+00:00")),
            "texts": texts,
            "source": url
        }


class IndependentScraper(ArticleScraper):
    def scrape(self, url):
        session = HTMLSession()
        page = session.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        header = soup.find(id='articleHeader')
        content = soup.find(id='main')
        text_elements = content.find_all('p')
        texts = [elem.text for elem in text_elements]
        return {
            "headlines": [header.find('h1').text, header.find('h2').text],
            "date": datetime.fromisoformat(header.find('amp-timeago')['datetime'].replace("Z", "+00:00")),
            "texts": texts,
            "source": url
        }


class GuardianScraper(ArticleScraper):

    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("GUARDIAN_API_KEY")

    def scrape(self, url):
        print(self.api_key)
        payload = {'api-key': self.api_key, 'show-fields': 'headline,body,trailText'}
        response = requests.get(url, params=payload).json()['response']['content']

        soup = BeautifulSoup(response['fields']['body'], 'html.parser')
        text_elements = soup.find_all('p')
        texts = [elem.text for elem in text_elements]
        return {
            "headlines": [response['fields']['headline'], response['fields']['trailText']],
            "date": datetime.fromisoformat(response['webPublicationDate'].replace("Z", "+00:00")),
            "texts": texts,
            "source": response['webUrl']
        }
