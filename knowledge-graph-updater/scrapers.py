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
        article = self.scrape(url)
        if article is not None:
            self.save_to_db(article)

    @abstractmethod
    def scrape(self, url):
        pass

    def save_to_db(self, article):
        self.db_collection.update_one({'source': article['source']}, {'$set': article}, upsert=True)


class BbcScraper(ArticleScraper):
    def scrape(self, url):
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        if soup.find(id='main-heading') is not None:
            headlines = soup.find(id='main-heading').text
        elif soup.find('h1', {'class': 'qa-story-headline-hidden'}) is not None:  # for sport news
            headlines = soup.find('h1', {'class': 'qa-story-headline-hidden'}).text
        else:
            headlines = None

        if soup.time is not None:
            try:
                date = datetime.fromisoformat(soup.time['datetime'].replace("Z", "+00:00"))
            except ValueError:
                date = None
        else:
            date = None

        text_elements = soup.find_all('div', {'data-component': 'text-block'})
        if len(text_elements) == 0 and soup.find('div', {'aria-live': 'polite'}) is not None:
            video_div = soup.find('div', {'aria-live': 'polite'})  # for video news
            text_elements = video_div.find_all('p')
        elif len(text_elements) == 0 and soup.find('div', {'class': 'qa-story-body'}) is not None:
            div = soup.find('div', {'class': 'qa-story-body'})  # for sport news
            text_elements = div.find_all('p')

        texts = [elem.text for elem in text_elements]
        return {
            "headlines": [headlines],
            "date": date,
            "texts": texts,
            "source": url
        }


class IndependentScraper(ArticleScraper):
    def scrape(self, url):
        session = HTMLSession()
        page = session.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        header = soup.find(id='articleHeader')
        if header is None:
            header = soup  # for IndyLife or Travel
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
        if url.startswith("https://www.theguardian"):
            api_url = url.replace("https://www.theguardian", "https://content.guardianapis")
        else:
            api_url = url
        payload = {'api-key': self.api_key, 'show-fields': 'headline,body,trailText'}
        response = requests.get(api_url, params=payload).json()['response']
        if response['status'] == 'ok':
            content = response['content']
            soup = BeautifulSoup(content['fields']['body'], 'html.parser')
            text_elements = soup.find_all('p')
            texts = [elem.text for elem in text_elements]
            return {
                "headlines": [content['fields']['headline'], content['fields']['trailText']],
                "date": datetime.fromisoformat(content['webPublicationDate'].replace("Z", "+00:00")),
                "texts": texts,
                "source": content['webUrl']
            }
        return {"source": url}
