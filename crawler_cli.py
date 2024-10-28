import argparse
import sys
from crawler.base_crawler import BaseCrawler
from crawler.extended_crawler import ExtendedCrawler
from crawler.citations_crawler import CitationsCrawler


def process():
    """Function that processes the arguments passed to the crawler.
    """
    parser = argparse.ArgumentParser()

    # Arguments
    parser.add_argument('--c', type=str, nargs='+', help='List of the conference we want to get the papers from', required=True)
    parser.add_argument('--y', type=int, nargs='+', help='List of the years we want to get (from - to)', required=True)
    parser.add_argument('--extended', nargs='?', const='default_value', help='Flag to indicate if we want to use the extended crawler')
    parser.add_argument('--citations', nargs='?', const='default_value', help='Flag to indicate if we want to use the citations crawler')

    args = parser.parse_args()

    # --years
    if len(args.y) > 2 or len(args.y) < 1:
        sys.exit("Error: The --years argument must have one or 2 values")
    if len(args.y) > 1 and args.y[0] > args.y[1]:
        sys.exit("Error: The first value of --years must be lower than the second value")
    if len(args.y) == 1:
        args.y.append(args.y[0])

    # --c argument
    if len(args.c) < 1:
        sys.exit("Error: The --c argument must have at least one value")
    
    # crawler selection
    for conference in args.c:
        if args.extended:
            extended = ExtendedCrawler(conference, args.y)
            extended.crawl()
        elif args.citations:
            citations = CitationsCrawler(conference, args.y)
            citations.crawl()
        else:
            base = BaseCrawler(conference, args.y)
            base.crawl()



if __name__ == "__main__":
    process()