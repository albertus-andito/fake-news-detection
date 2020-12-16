import feedparser
import os
import schedule
import time
from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient
from scrapers import IndependentScraper, BbcScraper, GuardianScraper


class NewsPoller:
    BBC_RSS_URL = "http://feeds.bbci.co.uk/news/rss.xml"
    INDEPENDENT_RSS_URL = "https://www.independent.co.uk/news/rss"
    GUARDIAN_RSS_URL = "https://www.theguardian.com/uk/rss"

    def __init__(self):
        load_dotenv(dotenv_path=Path('../.env'))
        self.db_client = MongoClient(os.getenv("MONGODB_ADDRESS"))
        self.db = self.db_client["fnd"]
        self.db_collection = self.db["articles"]
        self.db_collection.create_index("source", unique=True)

    def start(self):
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
        entries = feedparser.parse(rss_url)['entries']
        print("starting...", rss_url)
        for entry in entries:
            if self.db_collection.find_one({"source": entry['link']}) is None:
                print(entry['link'])
                print(entry['published'])
                scraper.execute(entry['link'])
