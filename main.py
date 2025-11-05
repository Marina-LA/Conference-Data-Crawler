# main.py
from crawler.base_crawler import BaseCrawler
from crawler.citations_crawler import CitationsCrawler
from crawler.extended_crawler import ExtendedCrawler
from logs.logging_config import setup_logging

if __name__ == "__main__":
    setup_logging()
    # example of conferences (use the same name as in the dblp url)
    conferences = ["nsdi", "cloud", "middleware", "eurosys", "icdcs", "ccgrid", "europar", "sigcomm", "IEEEcloud", "ic2e", "atc", "asplos", "osdi"]
    # conferences = ["nsdi"]
    years = (2012, 2024)

    for conference in conferences:
        base_crawler = BaseCrawler(conference, years)
        base_crawler.crawl()
        
        
        extended_crawler = ExtendedCrawler(conference, years)
        extended_crawler.crawl()


        citations_crawler = CitationsCrawler(conference, years)
        citations_crawler.crawl()