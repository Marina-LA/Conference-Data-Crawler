from crawler.abstract_crawler import AbstractCrawler
from utils.file_utils import FileUtils
from api_clients.factory import APIFactory
from utils.paper_data_builder import PaperDataBuilder
from config import BASE_CRAWLER_OUTPUT_DIR, EXTENDED_CRAWLER_OUTPUT_DIR, MAX_WORKERS, ENABLE_PROGRESS_BAR
from fuzzywuzzy import fuzz
from concurrent.futures import ThreadPoolExecutor, as_completed
import unicodedata
import logging

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


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
        self.crossref_client = APIFactory.get_client("crossref")


    def load_data(self):
        print(f"\t> Loading data for {self.conference} from base data <")
        base_data_path = f"{BASE_CRAWLER_OUTPUT_DIR}/{self.conference}_base_data.json"
        if self.file_utils.exists(base_data_path):
            self.base_data = self.file_utils.load_json(base_data_path)
        else:
            raise FileNotFoundError(f"Base data not found at {base_data_path}")

    def process_data(self):
        print(f"\t> Processing data for {self.conference} <")
        
        # Collect all papers to process
        papers_to_process = []
        for year in range(self.first_year, self.last_year + 1):
            if str(year) not in self.base_data:
                logging.info(f"No data found for {year}. Skipping...")
                continue
            for paper in self.base_data[str(year)]:
                papers_to_process.append((str(year), paper))
        
        print(f"\t> Processing {len(papers_to_process)} papers with {MAX_WORKERS} workers <")
        
        # Use progress bar if available
        use_progress = ENABLE_PROGRESS_BAR and HAS_TQDM
        
        # Process papers concurrently
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all tasks
            future_to_paper = {
                executor.submit(self.__process_single_paper, year, paper): (year, paper)
                for year, paper in papers_to_process
            }
            
            # Collect results with optional progress bar
            futures = as_completed(future_to_paper)
            if use_progress:
                futures = tqdm(futures, total=len(future_to_paper), desc="Processing papers")
            
            for future in futures:
                try:
                    year, paper_data = future.result()
                    if not paper_data:
                        continue
                    # Normalize to dict for JSON serialization
                    if hasattr(paper_data, 'to_dict'):
                        record = paper_data.to_dict()
                    elif isinstance(paper_data, dict):
                        record = paper_data
                    else:
                        logging.error("Unsupported paper_data type; skipping")
                        continue
                    if year not in self.data_per_year:
                        self.data_per_year[year] = []
                    self.data_per_year[year].append(record)
                except Exception as e:
                    logging.error(f"Error processing paper: {e}")
    
    def __process_single_paper(self, year, paper):
        """Process a single paper and return its data.
        
        Args:
            year: Publication year
            paper: Paper data from base crawler
            
        Returns:
            Tuple of (year, paper_data)
        """
        try:
            title = paper["Title"]
            doi = paper["DOI Number"]
            openalex_link = paper["OpenAlex Link"]
            authors_affiliations = paper["Authors and Institutions"]  # FROM DBLP - NEVER MODIFY
            
            # Get data from Semantic Scholar (ONLY by DOI)
            semantic_scholar_data = self.__get_semantic_scholar_data(doi)
            
            enriched_authors = None
            semantic_scholar_doi = None
            
            if semantic_scholar_data:
                if "data" in semantic_scholar_data:
                    semantic_scholar_data = semantic_scholar_data['data'][0]
                
                # Try to get affiliation data if OpenAlex link is missing (ONLY via DOI)
                if openalex_link is None and authors_affiliations and doi:
                    openalex_data = self.openalex_client.get_paper_authors_and_affiliations_doi(doi)
                    if openalex_data:
                        enriched_authors = self._merge_institutions_only(authors_affiliations, openalex_data)
                        logging.info(f"Found via OpenAlex DOI: {title[:50]}...")
                
                # Use enriched authors if available, otherwise keep original DBLP data
                final_authors = enriched_authors if enriched_authors else authors_affiliations
                
                # Safely get TLDR
                tldr_obj = semantic_scholar_data.get("tldr")
                tldr_text = tldr_obj.get("text") if tldr_obj else None
                
                # Get S2 Paper ID for additional queries
                s2_paper_id = semantic_scholar_data.get("paperId")
                
                # Get OpenAlex Referenced Works
                openalex_referenced_works = None
                if doi or openalex_link:
                    try:
                        openalex_referenced_works = self.openalex_client.get_referenced_works(doi=doi)
                    except Exception as e:
                        logging.debug(f"Could not get OpenAlex references for {title[:50]}...: {e}")
                
                citations_s2 = semantic_scholar_data.get("citations")
                
                preferred_doi = doi
                paper_data = (self.builder
                            .add_title(title)
                            .add_year(year)
                            .add_doi(preferred_doi)
                            .add_openalex_link(openalex_link)
                            .add_authors_and_institutions(final_authors)
                            .add_field("S2 Paper ID", s2_paper_id)
                            .add_abstract(semantic_scholar_data.get("abstract"))
                            .add_field("TLDR", tldr_text)
                            .add_referenced_works(openalex_referenced_works)
                            .add_citations_s2(citations_s2)
                            .build())
                return (year, paper_data)
            
            return (year, None)
        except Exception as e:
            logging.error(f"Error processing paper '{paper.get('Title', 'Unknown')}': {e}")
            return (year, None)


    def _merge_institutions_only(self, dblp_authors, openalex_data):
        """Merge institutions from OpenAlex while preserving DBLP author names.
        
        Args:
            dblp_authors: Author data from DBLP (authoritative source for names)
            openalex_data: Author data from OpenAlex (source for institutions)
            
        Returns:
            List of authors with DBLP names and OpenAlex institutions
        """
        if not dblp_authors or not openalex_data:
            return dblp_authors
        
        # Verify author count matches
        if len(dblp_authors) != len(openalex_data):
            logging.warning(f"Author count mismatch in merge: DBLP={len(dblp_authors)}, OpenAlex={len(openalex_data)}")
            return dblp_authors
        
        result = []
        for i, dblp_author in enumerate(dblp_authors):
            author_entry = {
                "Author": dblp_author["Author"],  # ALWAYS from DBLP
                "Institutions": None
            }
            
            # Try to add institutions from OpenAlex
            if i < len(openalex_data):
                openalex_author = openalex_data[i]
                
                # Verify they are the same person (same position + similar name)
                if self._is_same_author(dblp_author["Author"], openalex_author.get("Author", "")):
                    author_entry["Institutions"] = openalex_author.get("Institutions")
                else:
                    logging.warning(f"Author mismatch at position {i}: '{dblp_author['Author']}' vs '{openalex_author.get('Author', 'N/A')}'")
            
            result.append(author_entry)
        
        return result
    
    def _combine_dblp_names_with_institutions(self, dblp_authors, institutions_list):
        """Combine DBLP author names with institutions from OpenAlex.
        
        Args:
            dblp_authors: Author data from DBLP
            institutions_list: List of institution lists from OpenAlex
            
        Returns:
            List of authors with DBLP names and OpenAlex institutions
        """
        if not dblp_authors or not institutions_list:
            return dblp_authors
        
        if len(dblp_authors) != len(institutions_list):
            logging.warning(f"Length mismatch: DBLP={len(dblp_authors)}, institutions={len(institutions_list)}")
            return dblp_authors
        
        result = []
        for i, dblp_author in enumerate(dblp_authors):
            result.append({
                "Author": dblp_author["Author"],  # ALWAYS from DBLP
                "Institutions": institutions_list[i]  # From OpenAlex
            })
        
        return result
    
    def _is_same_author(self, dblp_name, openalex_name):
        """Check if two author names refer to the same person.
        
        Tolerates minor variations in formatting.
        
        Args:
            dblp_name: Author name from DBLP
            openalex_name: Author name from OpenAlex
            
        Returns:
            True if they appear to be the same person
        """
        import re
        
        # Normalize
        dblp_norm = dblp_name.lower().strip()
        openalex_norm = openalex_name.lower().strip()
        
        # Exact match
        if dblp_norm == openalex_norm:
            return True
        
        # Remove special characters and extra spaces
        dblp_clean = re.sub(r'[^\w\s]', '', dblp_norm)
        openalex_clean = re.sub(r'[^\w\s]', '', openalex_norm)
        dblp_clean = ' '.join(dblp_clean.split())
        openalex_clean = ' '.join(openalex_clean.split())
        
        if dblp_clean == openalex_clean:
            return True
        
        # Check last name and first initial
        dblp_parts = dblp_clean.split()
        openalex_parts = openalex_clean.split()
        
        if not dblp_parts or not openalex_parts:
            return False
        
        # Last name must match
        if dblp_parts[-1] != openalex_parts[-1]:
            return False
        
        # First initial must match
        if len(dblp_parts) > 0 and len(openalex_parts) > 0:
            if dblp_parts[0][0] == openalex_parts[0][0]:
                return True
        
        return False

    def save_data(self):
        print(f"\t> Saving data for {self.conference} in {EXTENDED_CRAWLER_OUTPUT_DIR} <")
        filename = f"{self.conference}_extended_data"
        self.file_utils.add_data_to_existing_file(f"{EXTENDED_CRAWLER_OUTPUT_DIR}/{filename}.json", self.data_per_year)


    def __get_semantic_scholar_data(self, doi):
        """Get paper data from Semantic Scholar.
        
        Args:
            doi: Paper DOI
            
        Returns:
            Semantic Scholar data or None
        """
        if not doi:
            return None
        data = self.semantic_scholar_client.request_by_doi(doi)
        if data:
            return data
        return None
    

    def __verify_paper(self, paper_data, dblp_authors, paper_title):
        # Title-based verification disabled per spec (no title fallbacks)
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