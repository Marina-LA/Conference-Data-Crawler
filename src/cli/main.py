import argparse
import sys
import logging
from typing import List, Tuple
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from crawler.base_crawler import BaseCrawler
from crawler.extended_crawler import ExtendedCrawler
from crawler.citations_crawler import CitationsCrawler
from src.config.settings import logging_config


def setup_logging():
    logging.basicConfig(
        level=getattr(logging, logging_config.log_level),
        format=logging_config.log_format,
        handlers=[
            logging.FileHandler(logging_config.log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def validate_years(years: List[int]) -> Tuple[int, int]:
    if len(years) > 2 or len(years) < 1:
        sys.exit("Error: The --years argument must have one or 2 values")
    
    if len(years) == 1:
        return (years[0], years[0])
    
    if years[0] > years[1]:
        sys.exit("Error: The first value of --years must be lower than the second value")
    
    return (years[0], years[1])


def validate_conferences(conferences: List[str]) -> List[str]:
    if len(conferences) < 1:
        sys.exit("Error: The --conferences argument must have at least one value")
    
    valid_conferences = [
        "nsdi", "cloud", "middleware", "eurosys", "icdcs", 
        "ccgrid", "europar", "sigcomm", "IEEEcloud", "ic2e", "usenix",
        "osdi", "asplos", "atc", "socc"
    ]
    
    invalid_conferences = [c for c in conferences if c not in valid_conferences]
    if invalid_conferences:
        print(f"Warning: Unknown conferences: {invalid_conferences}")
        print(f"Valid conferences: {valid_conferences}")
    
    return conferences


def run_crawler(conference: str, years: Tuple[int, int], crawler_type: str):
    logger = logging.getLogger(f"CLI.{conference}")
    
    try:
        if crawler_type == "base":
            crawler = BaseCrawler(conference, years)
        elif crawler_type == "extended":
            crawler = ExtendedCrawler(conference, years)
        elif crawler_type == "citations":
            crawler = CitationsCrawler(conference, years)
        else:
            raise ValueError(f"Unknown crawler type: {crawler_type}")
        
        result = crawler.crawl()
        
        if result.success:
            logger.info(f"Successfully completed {crawler_type} crawl for {conference}")
        else:
            logger.error(f"Failed {crawler_type} crawl for {conference}: {result.error}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error running {crawler_type} crawler for {conference}: {e}", exc_info=True)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Conference Data Crawler - Extract academic paper data from conferences",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Use --help for options."
    )

    # Required arguments
    parser.add_argument(
        '--conferences', '-c', 
        type=str, 
        nargs='+', 
        help='List of conferences to crawl',
        required=True
    )
    
    parser.add_argument(
        '--years', '-y', 
        type=int, 
        nargs='+', 
        help='List of years (1 or 2 values: start-end)',
        required=True
    )

    # Optional crawler type selection
    crawler_group = parser.add_mutually_exclusive_group()
    crawler_group.add_argument(
        '--extended', 
        action='store_true',
        help='Run extended crawler (requires base data)'
    )
    crawler_group.add_argument(
        '--citations', 
        action='store_true',
        help='Run citations crawler (requires extended data)'
    )

    # Additional options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually running'
    )

    args = parser.parse_args()

    if args.verbose:
        logging_config.log_level = 'DEBUG'
    setup_logging()
    
    logger = logging.getLogger("CLI")
    logger.info("Starting Conference Data Crawler CLI")

    conferences = validate_conferences(args.conferences)
    years = validate_years(args.years)
    
    if args.extended:
        crawler_type = "extended"
    elif args.citations:
        crawler_type = "citations"
    else:
        crawler_type = "base"

    logger.info(f"Configuration:")
    logger.info(f"  Conferences: {conferences}")
    logger.info(f"  Years: {years[0]}-{years[1]}")
    logger.info(f"  Crawler type: {crawler_type}")
    
    if args.dry_run:
        logger.info("DRY RUN - No actual crawling will be performed")
        return

    successful_crawls = 0
    failed_crawls = 0
    
    for conference in conferences:
        try:
            run_crawler(conference, years, crawler_type)
            successful_crawls += 1
        except SystemExit:
            failed_crawls += 1
            continue
        except Exception as e:
            logger.error(f"Unexpected error for {conference}: {e}")
            failed_crawls += 1
            continue

    logger.info(f"Crawl completed: {successful_crawls} successful, {failed_crawls} failed")
    
    if failed_crawls > 0:
        logger.warning(f"{failed_crawls} conferences failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
