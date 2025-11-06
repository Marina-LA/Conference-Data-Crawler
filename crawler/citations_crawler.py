from crawler.abstract_crawler import AbstractCrawler
from utils.file_utils import FileUtils
from api_clients.factory import APIFactory
from utils.paper_data_builder import PaperDataBuilder
from config import CITATIONS_CRAWLER_OUTPUT_DIR, EXTENDED_CRAWLER_OUTPUT_DIR, MAX_WORKERS, ENABLE_PROGRESS_BAR
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


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
        
        total_papers = len(paper_citations_ids)
        print(f"\t> Processing citations for {total_papers} papers <")

        # Step 1: Use batch requests for Semantic Scholar API
        use_progress = ENABLE_PROGRESS_BAR and HAS_TQDM
        iterator = paper_citations_ids.items()
        
        if use_progress:
            iterator = tqdm(iterator, total=total_papers, desc="Fetching citations from S2")
        
        for paper_title, citations_ids in iterator:
            if citations_ids:
                semantic_scholar_data = self.semantic_scholar_client.batch_request(citations_ids)
                self.semantic_scholar_citations_data[paper_title] = semantic_scholar_data
            else:
                self.semantic_scholar_citations_data[paper_title] = []
        
        # Step 2: Process responses concurrently using OpenAlex API for affiliation data
        print(f"\t> Enriching citation data with OpenAlex ({MAX_WORKERS} workers) <")
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_title = {
                executor.submit(self.__process_openalex_for_paper, title, response): title
                for title, response in self.semantic_scholar_citations_data.items()
            }
            
            futures = as_completed(future_to_title)
            if use_progress:
                futures = tqdm(futures, total=len(future_to_title), desc="Enriching citations")
            
            for future in futures:
                try:
                    title, cited_data = future.result()
                    self.all_citations_data[title] = cited_data
                except Exception as e:
                    logging.error(f"Error processing citations: {e}")
        

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
                citations = paper.get("Citations")
                # Accept both legacy and S2 key names
                if citations is None:
                    citations = paper.get("Citations S2")
                # Handle None or empty citations
                if citations is None:
                    papers_ids = []
                else:
                    papers_ids = [c.get("paperId") for c in citations if c and c.get("paperId")]
                paper_citations_ids[paper_title] = papers_ids
        return paper_citations_ids
    

    def __process_openalex_for_paper(self, title, response):
        """Process citations for a paper using OpenAlex to get affiliation data.
        
        Args:
            title: Title of the citing paper
            response: List of cited papers from Semantic Scholar
            
        Returns:
            Tuple of (title, cited_data)
        """
        cited_data = []
        
        if not response:
            return (title, cited_data)
        
        for cited_paper in response:
            try:
                external_ids = cited_paper.get("externalIds", {})
                doi = external_ids.get("DOI") if external_ids else None
                
                if doi:
                    openalex_data = self.openalex_client.get_paper_authors_and_affiliations_doi(doi)
                    year_value = str(cited_paper.get("year")) if cited_paper.get("year") else None
                    title_value = cited_paper.get("title")

                    # Normalize authors according to spec:
                    # - If no authors, set to None
                    # - If authors exist but have no institutions, set Institutions=None
                    normalized_authors = None
                    if openalex_data and isinstance(openalex_data, list):
                        tmp = []
                        for a in openalex_data:
                            author_name = a.get("Author") if isinstance(a, dict) else None
                            institutions = None
                            if isinstance(a, dict):
                                institutions = a.get("Institutions", None)
                            tmp.append({
                                "Author": author_name,
                                "Institutions": institutions if institutions else None
                            })
                        if len(tmp) > 0:
                            normalized_authors = tmp

                    # Require title and year for builder; allow authors None
                    if title_value and year_value:
                        paper_data = (self.builder
                                        .add_title(title_value)
                                        .add_year(year_value)
                                        .add_doi(doi)
                                        .add_venue(cited_paper.get("venue"))
                                        .add_authors_and_institutions(normalized_authors)
                                        .build())
                        # Store as dict for JSON serialization
                        if hasattr(paper_data, 'to_dict'):
                            cited_data.append(paper_data.to_dict())
                        else:
                            cited_data.append(paper_data)
                        
            except Exception as e:
                logging.error(f"Error processing cited paper: {e}")
                continue
        
        return (title, cited_data)
