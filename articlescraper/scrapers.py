import logging
import os
import requests

from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient
from requests_html import HTMLSession
from urllib.parse import urlparse


class ArticleScraper(ABC):
    """
    Base class for article scrapers. It scrapes articles and saves them to DB.
    """
    logger = logging.getLogger()

    def __init__(self):
        """
        Constructor method
        """
        load_dotenv(dotenv_path=Path('../.env'))
        self.db_client = MongoClient(os.getenv('MONGODB_ADDRESS'))
        self.db = self.db_client['fnd']
        self.db_collection = self.db['articles']
        self.db_collection.create_index("source", unique=True)

    def execute(self, url):
        """
        Scrapes article and saves them to DB if there is an article.

        :param url: Article url
        :type url: str
        """
        article = self.scrape(url)
        if article is not None:
            self.save_to_db(article)

    @abstractmethod
    def scrape(self, url):
        """
        Scrapes article.

        :param url:  Article url
        :type url: str
        :return: Dictionary of article in the format of {'headlines':..., 'date':..., 'text':..., 'source':...}
        :rtype: dict
        """
        pass

    def save_to_db(self, article):
        """
        Saves article to DB.

        :param article: News article text
        :type article: dict
        """
        try:
            self.db_collection.update_one({'source': article['source']}, {'$set': article}, upsert=True)
        except Exception as e:
            ArticleScraper.logger.exception('Exception occured when saving to DB')


class BbcScraper(ArticleScraper):
    """
    BBC articles scraper.
    """
    def scrape(self, url):
        """
        Scrapes BBC article.

        :param url:  Article url
        :type url: str
        :return: Dictionary of article in the format of {'headlines':..., 'date':..., 'text':..., 'source':...}
        :rtype: dict
        """
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        if soup.find(id='main-heading') is not None:
            headlines = soup.find(id='main-heading').text
        elif soup.find('h1', {'class': 'qa-story-headline-hidden'}) is not None:  # for sport news
            headlines = soup.find('h1', {'class': 'qa-story-headline-hidden'}).text
        elif soup.find('h1') is not None:
            headlines = soup.find('h1').text
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
        if len(text_elements) == 0 and soup.find('div', {'class': 'qa-story-body'}) is not None:
            div = soup.find('div', {'class': 'qa-story-body'})  # for sport news
            text_elements = div.find_all('p')
        list_elements = soup.find_all('div', {'data-component': 'ordered-list-block'})
        if list_elements is not None:
            for el in list_elements:
                text_elements.extend(el.find_all('li'))

        texts = headlines + '. ' + ' '.join([elem.text for elem in text_elements])
        return {
            'headlines': [headlines],
            'date': date,
            'texts': texts,
            'source': url
        }


class IndependentScraper(ArticleScraper):
    """
    Independent articles scraper.
    """
    def scrape(self, url):
        """
        Scrapes Independent article.

        :param url:  Article url
        :type url: str
        :return: Dictionary of article in the format of {'headlines':..., 'date':..., 'text':..., 'source':...}
        :rtype: dict
        """
        session = HTMLSession()
        page = session.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        header = soup.find(id='articleHeader')
        headlines = [header.find('h1').text, header.find('h2').text]
        if header is None:
            header = soup  # for IndyLife or Travel
        if header.find('amp-timeago') is not None:
            date = datetime.fromisoformat(header.find('amp-timeago')['datetime'].replace("Z", "+00:00"))
        else:
            date = None
        content = soup.find(id='main')
        texts = '. '.join(headlines)
        if content is not None:
            text_elements = content.find_all('p')
            texts += '. ' + ' '.join([elem.text for elem in text_elements])
        else:
            texts = None
        return {
            'headlines': headlines,
            'date': date,
            'texts': texts,
            'source': url
        }


class GuardianScraper(ArticleScraper):
    """
    Guardian articles scraper.
    It requires the GUARDIAN_API_KEY to be set in the .env
    """
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("GUARDIAN_API_KEY")

    def scrape(self, url):
        """
        Scrapes Guardian article using Guardian Open Platform API (https://open-platform.theguardian.com/.

        :param url:  Article url
        :type url: str
        :return: Dictionary of article in the format of {'headlines':..., 'date':..., 'text':..., 'source':...}
        :rtype: dict
        """
        if url.startswith("https://www.theguardian"):
            api_url = url.replace("https://www.theguardian", "https://content.guardianapis")
        else:
            api_url = url
        payload = {'api-key': self.api_key, 'show-fields': 'headline,body,trailText'}
        # FIXME: try catch exception
        try:
            response = requests.get(api_url, params=payload).json()
            response = response['response']
            if response['status'] == 'ok':
                content = response['content']
                headlines = [content['fields']['headline'], content['fields']['trailText']]
                soup = BeautifulSoup(content['fields']['body'], 'html.parser')
                text_elements = soup.find_all('p')
                texts = '. '.join(headlines)
                texts += '. ' + ' '.join([elem.text for elem in text_elements])
                return {
                    'headlines': [content['fields']['headline'], content['fields']['trailText']],
                    'date': datetime.fromisoformat(content['webPublicationDate'].replace("Z", "+00:00")),
                    'texts': texts,
                    'source': content['webUrl']
                }
            return self.scrape_fallback(url)
        except KeyError as e:
            print(response)
            return {'source': url, 'message': response}
        except Exception as e:
            return {'source': url, 'message': e}

    def scrape_fallback(self, url):
        """
        Fallback scraping method if the Guardian API is having issues.

        :param url:  Article url
        :type url: str
        :return: Dictionary of article in the format of {'headlines':..., 'date':..., 'text':..., 'source':...}
        :rtype: dict
        """
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        headlines = [soup.find('h1').text]
        date = datetime.strptime(soup.find('label', attrs={'for': 'dateToggle'}).text, '%a %d %b %Y %H.%M %Z')

        texts = '. '.join(headlines)
        text_elements = soup.find_all('p')
        texts += '. ' + ' '.join([elem.text+'.' if i == 0 else elem.text for i, elem in enumerate(text_elements)
                                  if not elem.text.startswith('First published')
                                  and not elem.text.startswith('Last modified')])
        return {
            'headlines': headlines,
            'date': date,
            'texts': texts,
            'source': url
        }


class GenericScraper(ArticleScraper):
    """
    Scraper for a generic website.
    """
    def scrape(self, url):
        """
        Scrapes text from <p> tags of the webpage.

        :param url: url
        :type url: str
        :return: Dictionary of article in the format of {'headlines':..., 'date':..., 'text':..., 'source':...}
        :rtype: dict
        """
        session = HTMLSession()
        page = session.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        text = soup.find_all(text=True)
        # ps = soup.find_all('p')
        # text = ''
        # for p in ps:
        #     text += ' ' + p.getText()
        return {
            'headlines': '',
            'date': '',
            'texts': text,
            'source': url
        }


class Scrapers:
    """
    Collection of scrapers.
    """
    def __init__(self):
        self.bbc_scraper = BbcScraper()
        self.guardian_scraper = GuardianScraper()
        self.independent_scraper = IndependentScraper()
        self.generic_scraper = GenericScraper()

    def scrape_text_from_url(self, url, save_to_db=False):
        """
        Scrapes text from the url given. It uses the generic scraper if the url is not for BBC, Guardian, or Independent.

        :param url: url
        :type url: str
        :param save_to_db: whether to save the scraped text to the database or not. This is only applicable for BBC,
            Independent, and Guardian URLs.
        :type save_to_db: bool
        :return: text scraped from the url
        :rtype: str
        """
        if urlparse(url).netloc == 'www.bbc.co.uk':
            scraped = self.bbc_scraper.scrape(url)
            if save_to_db is True:
                self.bbc_scraper.save_to_db(scraped)
        elif urlparse(url).netloc == 'www.theguardian.com':
            scraped = self.guardian_scraper.scrape(url)
            if save_to_db is True:
                self.guardian_scraper.save_to_db(scraped)
        elif urlparse(url).netloc == 'www.independent.co.uk':
            scraped = self.independent_scraper.scrape(url)
            if save_to_db is True:
                self.guardian_scraper.save_to_db(scraped)
        else:
            scraped = self.generic_scraper.scrape(url)
        return scraped['texts']
