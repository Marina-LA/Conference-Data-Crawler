from crawler.abstract_crawler import AbstractCrawler
from utils.file_utils import FileUtils
from api_clients.factory import APIFactory
from utils.paper_data_builder import PaperDataBuilder
from config import CITATIONS_CRAWLER_OUTPUT_DIR, EXTENDED_CRAWLER_OUTPUT_DIR
import logging


class CitationsCrawler(AbstractCrawler):
    def __init__(self, conference, years):
        print("----------------- [Citations Crawler] -----------------")
        super().__init__(conference, years)
        # inetrnal variables
        self.extended_data = {}
        self.all_citations_data = {}
        self.semantic_scholar_citations_data = {}
        # utils and clients
        self.builder = PaperDataBuilder()
        self.file_utils = FileUtils()
        self.openalex_client = APIFactory.get_client("openalex")
        self.semantic_scholar_client = APIFactory.get_client("semantic_scholar")


    def load_data(self):
        print(f"\t> Loading data for {self.conference} from extended data <")
        extended_data_path = f"{EXTENDED_CRAWLER_OUTPUT_DIR}/{self.conference}_extended_data.json"
        if self.file_utils.exists(extended_data_path):
            self.extended_data = self.file_utils.load_json(extended_data_path)
        else:
            raise FileNotFoundError(f"Base data not found at {extended_data_path}")

    def process_data(self):
        print(f"\t> Processing data for {self.conference} <")
        paper_citations_ids = self.__get_all_papers_ids()

        # Step 1: Use batch requests for Semantic Scholar API
        for paper_title, paper_citations_ids in paper_citations_ids.items():
            semantic_scholar_data = self.semantic_scholar_client.batch_request(paper_citations_ids)
            self.semantic_scholar_citations_data[paper_title] = semantic_scholar_data
        
        # Step 2: Process responses from Semantic Scholar usaing OpenAlex API for more data
        for paper_title, response in self.semantic_scholar_citations_data.items():
            self.__process_openalex_for_paper(paper_title, response)
        

    def save_data(self):
        print(f"\t> Saving data for {self.conference} in {CITATIONS_CRAWLER_OUTPUT_DIR} <")
        filename = f"{self.conference}_citations_data"
        self.file_utils.add_data_to_existing_file(f"{CITATIONS_CRAWLER_OUTPUT_DIR}/{filename}.json", self.all_citations_data)


    def __get_all_papers_ids(self):
        paper_citations_ids = {}
        for year in range(self.first_year, self.last_year + 1):
            if str(year) not in self.extended_data:
                logging.info(f"No data found for {year}. Skipping...")
                continue
            for paper in self.extended_data[str(year)]:
                paper_title = paper["Title"]
                papers_ids = [c.get("paperId") for c in paper["Citations"] if c.get("paperId")]
                paper_citations_ids[paper_title] = papers_ids
        return paper_citations_ids
    

    def __process_openalex_for_paper(self, title, response):
        cited_data = []
        for cited_paper in response:
            doi = cited_paper.get("externalIds", {}).get("DOI")
            if doi:
                openalex_data = self.openalex_client.get_paper_authors_and_affiliations_doi(doi)
                if openalex_data:
                    cited_data.append(self.builder.add_field("Title", cited_paper.get("title"))
                                    .add_field("DOI Number", doi)
                                    .add_field("Venue", cited_paper.get("venue", None))
                                    .add_field("Year", str(cited_paper.get("year", None)))
                                    .add_field("Authors and Institutions", openalex_data)
                                    .build())
        # store all the citations data
        self.all_citations_data[title] = cited_data
