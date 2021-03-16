from nltk import word_tokenize
from urllib.parse import urlparse

from articlescraper.scrapers import BbcScraper, GuardianScraper, IndependentScraper, GenericScraper

bbc_scraper = BbcScraper()
guardian_scraper = GuardianScraper()
independent_scraper = IndependentScraper()
generic_scraper = GenericScraper()

def camelise(sentence):
    """
    Util function to convert words into camelCase
    :param sentence: sentence
    :type sentence: str
    :return: camelCase words
    :rtype: str
    """
    sentence = sentence.replace('_', ' ')
    words = word_tokenize(sentence)
    if len(words) <= 1:
        return sentence.lower()
    else:
        s = "".join(word[0].upper() + word[1:].lower() for word in words)
        return s[0].lower() + s[1:]


def convert_to_dbpedia_resource(resource):
    return 'http://dbpedia.org/resource/' + resource.replace(' ', '_')


def convert_to_dbpedia_ontology(predicate):
    return 'http://dbpedia.org/ontology/' + camelise(predicate).lstrip()

# FIXME: move out of util
def scrape_text_from_url(url, save_to_db=False):
    """
    Scrapes text from the url given. It uses the generic scraper if the url is not for BBC, Guardian, or Independent.
    :param url: url
    :type url: str
    :return: text scraped from the url
    :rtype: str
    """
    if urlparse(url).netloc == 'www.bbc.co.uk':
        scraped = bbc_scraper.scrape(url)
        if save_to_db is True:
            bbc_scraper.save_to_db(scraped)
    elif urlparse(url).netloc == 'www.theguardian.com':
        scraped = guardian_scraper.scrape(url)
        if save_to_db is True:
            guardian_scraper.save_to_db(scraped)
    elif urlparse(url).netloc == 'www.independent.co.uk':
        scraped = independent_scraper.scrape(url)
        if save_to_db is True:
            guardian_scraper.save_to_db(scraped)
    else:
        scraped = generic_scraper.scrape(url)
    return scraped['texts']