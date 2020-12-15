import feedparser
import os
import schedule
import time
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient


class NewsPoller(ABC):

    def __init__(self, scraper):
        load_dotenv(dotenv_path=Path('../.env'))
        self.db_client = MongoClient(os.getenv("MONGODB_ADDRESS"))
        self.db = self.db_client["fnd"]
        self.db_collection = self.db["articles"]
        self.db_collection.create_index("source", unique=True)

        self.scraper = scraper

    def start(self):
        self.poll_news_feed()
        schedule.every().minute.do(self.poll_news_feed)
        while True:
            schedule.run_pending()
            time.sleep(1)

    @abstractmethod
    def poll_news_feed(self):
        pass


class BbcPoller(NewsPoller):
    rss_url = "http://feeds.bbci.co.uk/news/rss.xml"

    def poll_news_feed(self):
        print("starting...")
        entries = feedparser.parse(self.rss_url)['entries']
        for entry in entries:
            if self.db_collection.find_one({"source": entry['id']}) is None:
                print(entry['id'])
                print(entry['published'])
                self.scraper.execute(entry['id'])
