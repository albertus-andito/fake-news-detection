import feedparser
import logging
import os
import schedule
import time
from article_scraper.scrapers import IndependentScraper, BbcScraper, GuardianScraper
from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient


class NewsPoller:
    """
    NewsPoller polls the RSS endpoints periodically (currently every minute) and uses scrapers to scrape articles.
    """
    BBC_RSS_URL = "http://feeds.bbci.co.uk/news/rss.xml"
    INDEPENDENT_RSS_URL = "https://www.independent.co.uk/news/rss"
    GUARDIAN_RSS_URL = "https://www.theguardian.com/uk/rss"
    logger = logging.getLogger()

    def __init__(self):
        """
        Constructor method
        """
        load_dotenv(dotenv_path=Path('../../.env'))
        self.db_client = MongoClient(os.getenv("MONGODB_ADDRESS"))
        self.db = self.db_client["fnd"] # TODO: parameterised
        self.db_collection = self.db["articles"] # TODO: parameterised
        self.db_collection.create_index("source", unique=True)
        NewsPoller.logger.info('NewsPoller initialised.')

    def start(self):
        """
        Starts the periodical polling process. Currently set to every minute.
        :return:
        """
        NewsPoller.logger.info('NewsPoller started.')

        bbc = BbcScraper()
        self.poll_news_feed(NewsPoller.BBC_RSS_URL, bbc)
        schedule.every().minute.do(self.poll_news_feed, NewsPoller.BBC_RSS_URL, bbc)

        independent = IndependentScraper()
        self.poll_news_feed(NewsPoller.INDEPENDENT_RSS_URL, independent)
        schedule.every().minute.do(self.poll_news_feed, NewsPoller.INDEPENDENT_RSS_URL, independent)

        guardian = GuardianScraper()
        self.poll_news_feed(NewsPoller.GUARDIAN_RSS_URL, guardian)
        schedule.every().minute.do(self.poll_news_feed, NewsPoller.GUARDIAN_RSS_URL, guardian)

        while True:
            schedule.run_pending()
            time.sleep(1)

    def poll_news_feed(self, rss_url, scraper):
        """
        Polls the news feed RSS and uses the scraper to scrape articles.
        :param rss_url: News feed RSS URL
        :type rss_url: str
        :param scraper: Scraper for the corresponding news website
        :type scraper: article_scraper.ArticleScraper
        """
        NewsPoller.logger.info('Polling %s ...', rss_url)
        entries = feedparser.parse(rss_url)['entries']
        for entry in entries:
            if self.db_collection.find_one({"source": entry['link']}) is None:
                NewsPoller.logger.info('Scraping %s %s...', entry['link'], entry['published'])
                scraper.execute(entry['link'])
