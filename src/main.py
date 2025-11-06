import sys
import logging
from typing import List, Tuple
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from crawler.base_crawler import BaseCrawler
from crawler.citations_crawler import CitationsCrawler
from crawler.extended_crawler import ExtendedCrawler
from src.config.settings import crawler_config, logging_config


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, logging_config.log_level),
        format=logging_config.log_format,
        handlers=[
            logging.FileHandler(logging_config.log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def crawl_conference(conference: str, years: Tuple[int, int], 
                    crawler_types: List[str] = None) -> None:
    if crawler_types is None:
        crawler_types = ['base', 'extended', 'citations']
    
    logger = logging.getLogger(f"Main.{conference}")
    logger.info(f"Starting crawl for {conference} ({years[0]}-{years[1]})")
    
    try:
        # Base crawler - always run first
        if 'base' in crawler_types:
            logger.info("Running base crawler...")
            base_crawler = BaseCrawler(conference, years)
            base_crawler.crawl()
        
        # Extended crawler - depends on base crawler
        if 'extended' in crawler_types:
            logger.info("Running extended crawler...")
            extended_crawler = ExtendedCrawler(conference, years)
            extended_crawler.crawl()
        
        # Citations crawler - depends on extended crawler
        if 'citations' in crawler_types:
            logger.info("Running citations crawler...")
            citations_crawler = CitationsCrawler(conference, years)
            citations_crawler.crawl()
            
    except Exception as e:
        logger.error(f"Error crawling {conference}: {e}", exc_info=True)
        raise


def main():
    setup_logging()
    logger = logging.getLogger("Main")
    
    # Crawl for 2019 (13 conferences)
    conferences = [
        "nsdi", "cloud", "middleware", "eurosys", "icdcs", 
        "ccgrid", "europar", "sigcomm", "IEEEcloud", "ic2e",
        "osdi", "asplos", "atc"
    ]
    years = (2019, 2019)
    
    logger.info(f"Starting crawl for {len(conferences)} conferences")
    logger.info(f"Years: {years[0]}-{years[1]}")
    
    successful_crawls = 0
    failed_crawls = 0
    
    for conference in conferences:
        try:
            crawl_conference(conference, years)
            successful_crawls += 1
            logger.info(f"Successfully crawled {conference}")
            
        except Exception as e:
            failed_crawls += 1
            logger.error(f"Failed to crawl {conference}: {e}")
            continue
    
    logger.info(f"Crawl completed: {successful_crawls} successful, {failed_crawls} failed")
    
    if failed_crawls > 0:
        logger.warning(f"{failed_crawls} conferences failed to crawl")
        sys.exit(1)


if __name__ == "__main__":
    main()
