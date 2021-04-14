import logging.config
import os

from articlescraper.poller import NewsPoller
from definitions import ROOT_DIR, LOGGER_CONFIG_PATH


def main():
    """
    Driver class for Article Scraper. If run, this will periodically poll the RSS endpoints and scrape articles.
    """
    LOGFILE_PATH = os.path.join(ROOT_DIR, 'logs', 'article-scraper.log').replace("\\", "/")
    logging.config.fileConfig(LOGGER_CONFIG_PATH,
                              defaults={'logfilename': LOGFILE_PATH},
                              disable_existing_loggers=False)
    logger = logging.getLogger()

    logger.info('Initialising NewsPoller...')
    poller = NewsPoller()
    poller.start()


if __name__ == '__main__':
    main()
