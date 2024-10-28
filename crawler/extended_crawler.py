from crawler.abstract_crawler import AbstractCrawler
from utils.file_utils import FileUtils
from api_clients.factory import APIFactory
from utils.paper_data_builder import PaperDataBuilder
from config import BASE_CRAWLER_OUTPUT_DIR, EXTENDED_CRAWLER_OUTPUT_DIR, SEMANTIC_SCHOLAR_RATE_LIMIT
from fuzzywuzzy import fuzz
import unicodedata
import time
import logging


class ExtendedCrawler(AbstractCrawler):

    def __init__(self, conference, years):
        print("----------------- [Extended Crawler] -----------------")
        super().__init__(conference, years)
        # internal variables
        self.data_per_year = {}
        self.base_data = {}
        # utils and clients
        self.builder = PaperDataBuilder()
        self.file_utils = FileUtils()
        self.openalex_client = APIFactory.get_client("openalex")
        self.semantic_scholar_client = APIFactory.get_client("semantic_scholar")


    def load_data(self):
        print(f"\t> Loading data for {self.conference} from base data <")
        base_data_path = f"{BASE_CRAWLER_OUTPUT_DIR}/{self.conference}_base_data.json"
        if self.file_utils.exists(base_data_path):
            self.base_data = self.file_utils.load_json(base_data_path)
        else:
            raise FileNotFoundError(f"Base data not found at {base_data_path}")

    def process_data(self):
        print(f"\t> Processing data for {self.conference} <")
        new_authors_affiliations = None
        semantic_scholar_doi = None
        for year in range(self.first_year, self.last_year + 1):
            if str(year) not in self.base_data:
                logging.info(f"No data found for {year}. Skipping...")
                continue
            # process each paper in the base data
            for paper in self.base_data[str(year)]:
                title = paper["Title"]
                doi = paper["DOI Number"]
                openalex_link = paper["OpenAlex Link"]
                authors_affiliations = paper["Authors and Institutions"]
                # get data from semantic scholar
                semantic_scholar_data = self.__get_semantic_scholar_data(title, doi, authors_affiliations)
                if semantic_scholar_data:
                    if "data" in semantic_scholar_data:
                        semantic_scholar_data = semantic_scholar_data['data'][0]

                if (semantic_scholar_data and openalex_link is None):
                    semantic_scholar_doi = semantic_scholar_data.get("externalIds", None).get("DOI", None)
                    if semantic_scholar_doi:
                        new_authors_affiliations = self.openalex_client.get_paper_authors_and_affiliations_doi(semantic_scholar_doi)

                paper_data = (self.builder.add_field("Title", title)
                            .add_field("Year", str(year))
                            .add_field("DOI Number", doi, semantic_scholar_doi)
                            .add_field("OpenAlex Link", openalex_link)
                            .add_field("Authors and Institutions", new_authors_affiliations, authors_affiliations)
                            .add_field("S2 Paper ID", semantic_scholar_data.get("paperId", None))
                            .add_field("Abstract", semantic_scholar_data.get("abstract", None))
                            .add_field("TLDR", semantic_scholar_data.get("tldr", None).get("text", None))
                            .add_field("Citations", semantic_scholar_data.get("references", None))
                            .build()
                )
                if str(year) not in self.data_per_year:
                    self.data_per_year[str(year)] = []
                self.data_per_year[str(year)].append(paper_data)


    def save_data(self):
        print(f"\t> Saving data for {self.conference} in {EXTENDED_CRAWLER_OUTPUT_DIR} <")
        filename = f"{self.conference}_extended_data"
        self.file_utils.add_data_to_existing_file(f"{EXTENDED_CRAWLER_OUTPUT_DIR}/{filename}.json", self.data_per_year)


    def __get_semantic_scholar_data(self, title, doi, original_authors):
        if doi:
            data = self.semantic_scholar_client.request_by_doi(doi)
            if data:
                return data
        data = self.semantic_scholar_client.request_by_title(title)
        time.sleep(SEMANTIC_SCHOLAR_RATE_LIMIT)
        if self.__verify_paper(data, original_authors, title): # verify if the paper is the correct one
            return data
        return None
    

    def __verify_paper(self, paper_data, dblp_authors, paper_title):
        paper_data = paper_data['data'][0]
        list_authors_names = paper_data.get('authors', None)
        for elem in list_authors_names:
            s2_authors_names = [author['name'] for author in list_authors_names]
        if paper_data is not None:
            s2_num_authors = len(s2_authors_names)
            dblp_num_authors = len(dblp_authors)
            dblp_authors_names = [author['Author'] for author in dblp_authors]
            s2_paper_title = paper_data.get('title', None)

            if paper_title[-1] == '.' and s2_paper_title[-1] != '.':
                s2_paper_title = f"{paper_data['title']}."
            elif paper_title[-1] != '.' and s2_paper_title[-1] == '.': 
                s2_paper_title = paper_data['title'][:-1]

            if paper_title.lower() == s2_paper_title.lower():
                return True
            if s2_num_authors == dblp_num_authors and self.__compare_authors(dblp_authors_names, s2_authors_names):
                return True
        return False
    

    def __compare_authors(self, dblp_authors, s2_authors):
        similar_authors = 0
        for i in range(len(dblp_authors)):
            similarity = fuzz.ratio(self.__normalize_string(dblp_authors[i]), self.__normalize_string(s2_authors[i]))
            if similarity >= 75:
                similar_authors += 1
        return similar_authors >= (len(dblp_authors) / 2)


    def __normalize_string(self, name):
        name = ''.join(
            c for c in unicodedata.normalize('NFD', name)
            if unicodedata.category(c) != 'Mn'
        )
        return name.lower().strip()