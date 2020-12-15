from pollers import BbcPoller
from scrapers import BbcScraper

if __name__ == '__main__':
    x = BbcPoller(BbcScraper())
    x.start()