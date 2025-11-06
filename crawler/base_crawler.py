from crawler.abstract_crawler import AbstractCrawler
from utils.file_utils import FileUtils
from api_clients.factory import APIFactory
from utils.paper_data_builder import PaperDataBuilder
import requests
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import BASE_CRAWLER_OUTPUT_DIR, SKIP_SECTIONS, REQUEST_TIMEOUT, MAX_WORKERS, ENABLE_PROGRESS_BAR
import logging

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


class BaseCrawler(AbstractCrawler):

    def __init__(self, conference, years):
        print("----------------- [Base Crawler] -----------------")
        super().__init__(conference, years)
        # internal variables
        self.data_per_year = {}
        self.data_to_process = []
        # utils and clients
        self.file_utils = FileUtils()
        self.builder = PaperDataBuilder()
        self.openalex_client = APIFactory.get_client("openalex")


    def load_data(self):
        print(f"\t> Loading data for {self.conference} from DBLP <")
        self.data_to_process = self.__obtain_dblp_data()
        print(f"\t> Obtained {len(self.data_to_process)} papers from DBLP <")


    def process_data(self):
        print(f"\t> Processing {len(self.data_to_process)} papers with {MAX_WORKERS} workers <")
        
        # Use progress bar if available and enabled
        use_progress = ENABLE_PROGRESS_BAR and HAS_TQDM
        iterator = tqdm(self.data_to_process, desc="Processing papers") if use_progress else self.data_to_process
        
        # Process papers concurrently
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all tasks
            future_to_pub = {executor.submit(self.__get_dblp_paper_data, pub): pub 
                           for pub in self.data_to_process}
            
            # Collect results as they complete
            for future in as_completed(future_to_pub):
                try:
                    paper_data = future.result()
                    if not paper_data:
                        continue
                    # Support both dict and PaperData object
                    if hasattr(paper_data, 'to_dict'):
                        year = str(getattr(paper_data, 'year', None))
                        record = paper_data.to_dict()
                    elif isinstance(paper_data, dict):
                        year = str(paper_data.get("Year"))
                        record = paper_data
                    else:
                        logging.error("Unsupported paper_data type; skipping")
                        continue
                    if not year:
                        logging.error("Missing year on paper_data; skipping")
                        continue
                    if year not in self.data_per_year:
                        self.data_per_year[year] = []
                    self.data_per_year[year].append(record)
                except Exception as e:
                    logging.error(f"Error processing publication: {e}")


    def save_data(self):
        print(f"\t> Saving data for {self.conference} in {BASE_CRAWLER_OUTPUT_DIR} <")
        filename = f"{self.conference}_base_data"
        self.file_utils.add_data_to_existing_file(f"{BASE_CRAWLER_OUTPUT_DIR}/{filename}.json", self.data_per_year)


    def __obtain_dblp_data(self):
        data_to_process = []
        links = self.__get_links()
        valid_links = []
        for link in links:
            if self.__filter_dblp_links(link) and \
                any(str(year) in link for year in range(self.first_year, self.last_year + 1)):
                valid_links.append(link)

        for link in valid_links:
            resp = requests.get(link, timeout=REQUEST_TIMEOUT)
            soup = BeautifulSoup(resp.content, features="lxml")
            pub_list_raw = soup.findAll("ul", attrs={"class": "publ-list"})
            for pub in pub_list_raw:
                article_items = pub.find_all('li', {'itemtype': 'http://schema.org/ScholarlyArticle'})
                header_h2 = pub.find_previous('h2')
                header_h3 = pub.find_previous('h3')
                header_h4 = pub.find_previous('h4')
                if not self.__filter_section(header_h2, header_h3, header_h4):
                    for article in article_items:
                        data_to_process.append(article)
        return data_to_process

    
    def __get_links(self):
        # ATC is under usenix directory in DBLP
        dblp_directory = "usenix" if self.conference == "atc" else self.conference
        url = "https://dblp.org/db/conf/" + dblp_directory + "/"
        html_page = requests.get(url, timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(html_page.text, 'html.parser')
        link_list = set()
        for link_elem in soup.findAll('a'):
            link = link_elem.get('href')
            if link and url in link:  # to avoid repeated links
                link_list.add(link)
        return link_list  # list with all the papers for each year
    

    def __filter_dblp_links(self, link):
        # Special cases for conference naming in DBLP
        if self.conference == "cloud": 
            conf_pattern = "socc"
            directory = "cloud"
        elif self.conference == "atc": 
            conf_pattern = "usenix"
            directory = "usenix"
        else:
            conf_pattern = self.conference
            directory = self.conference
        
        # Pattern accepts both single volume (europar2024.html) and multiple volumes (europar2024-1.html)
        # but excludes workshops (europar2024w1.html)
        pattern = rf"https://dblp.org/db/conf/{directory}/{conf_pattern}\d{{4}}(-\d+)?\.html"
        
        # Additional check: exclude workshop links (containing 'w' before digit)
        if re.search(r'\d{{4}}w\d+\.html', link):
            return False
        
        return bool(re.match(pattern, link))
    

    def __filter_section(self, header_h2, header_h3, header_h4):
        header_h2_text = header_h2.text if header_h2 is not None else ""
        header_h3_text = header_h3.text if header_h3 is not None else ""
        header_h4_text = header_h4.text if header_h4 is not None else ""
        lower_header_h2 = header_h2_text.lower().replace('\n', '')
        lower_header_h3 = header_h3_text.lower().replace('\n', '')
        lower_header_h4 = header_h4_text.lower().replace('\n', '')
        if any(section in lower_header_h2 for section in SKIP_SECTIONS):
            return True
        if any(section in lower_header_h3 for section in SKIP_SECTIONS):
            return True
        if any(section in lower_header_h4 for section in SKIP_SECTIONS):
            return True
        return False


    def __get_dblp_paper_data(self, publication):
        publication_year = None
        paper_title = 'nothing'
        authors_names =[]
        openalex_data = None
        for content_item in publication.contents:
            class_of_content_item = content_item.attrs.get('class', [0])
            if 'data' in class_of_content_item:
                # get the paper title from dblp
                paper_title = content_item.find('span', attrs={"class": "title", "itemprop": "name"}).text
                if self.__filter_paper_title(paper_title):
                    return None
                # get the publication year from dblp
                for datePublished in content_item.findAll('span', attrs={"itemprop": "datePublished"}):
                    publication_year = datePublished.text
                if publication_year == None:
                    publication_year = content_item.find('meta', attrs={"itemprop": "datePublished"}).get("content")
                # get the author's names from dblp paper
                for author in content_item.findAll('span', attrs={"itemprop": "author"}):
                    author_name = author.text
                    if author_name not in authors_names:
                        authors_names.append(author_name)
            if 'publ' in class_of_content_item:
                # Search for links in the entire element, not just contents[0]
                links = content_item.findAll("a")
                
                # Extract OpenAlex link
                openalex_link = [l.get("href") for l in links if l.get("href") and "openalex" in l.get("href")]
                openalex_link = openalex_link[0] if openalex_link else None
                
                # Extract DOI - Try multiple sources for maximum coverage
                doi_number = None
                
                # Strategy 1: Direct DOI link from DBLP (MOST COMMON)
                doi_links = [l.get("href") for l in links if l.get("href") and "doi.org" in l.get("href")]
                if doi_links:
                    doi_url = doi_links[0]
                    # Clean DOI from URL
                    doi_number = doi_url.replace("https://doi.org/", "").replace("http://doi.org/", "")
                    doi_number = doi_number.replace("https://dx.doi.org/", "").replace("http://dx.doi.org/", "")
                    # Remove any trailing query parameters
                    if '?' in doi_number:
                        doi_number = doi_number.split('?')[0]
                
                # Strategy 2: Extract from OpenAlex link (if no direct DOI)
                elif openalex_link and "doi:" in openalex_link:
                    doi_number = openalex_link.replace("https://api.openalex.org/works/doi:", "")
                
                # get the openalex data using DOI
                openalex_data = self.openalex_client.get_paper_authors_and_affiliations_doi(doi_number) 
                
                # get OpenAlex Referenced Works
                openalex_referenced_works = None
                if doi_number:
                    try:
                        referenced_works = self.openalex_client.get_referenced_works(doi=doi_number)
                        if referenced_works:
                            # Extract only the ID part from URLs like "https://openalex.org/W1580997674"
                            openalex_referenced_works = []
                            for work in referenced_works:
                                if work and work.startswith("https://openalex.org/"):
                                    work_id = work.split("/")[-1]  # Extract "W1580997674"
                                    openalex_referenced_works.append(work_id)
                                else:
                                    openalex_referenced_works.append(work)
                    except Exception as e:
                        logging.debug(f"Could not get OpenAlex references for {paper_title[:50]}...: {e}")
            
            # Fallback: If no DOI/OpenAlex data, try searching by title
            if openalex_data is None and authors_names:
                try:
                    institutions_list = self.openalex_client.get_institutions_by_title(paper_title, authors_names)
                    if institutions_list:
                        auth_list = []
                        for idx, author in enumerate(authors_names):
                            institutions = institutions_list[idx] if idx < len(institutions_list) else None
                            auth_list.append({'Author': author, 'Institutions': institutions})
                        openalex_data = auth_list
                except Exception as e:
                    logging.debug(f"Could not find institutions by title for {paper_title[:50]}...: {e}")
            
            if openalex_data is None:
                auth_list = []
                for author in authors_names:
                    auth_list.append({'Author': author, 'Institutions': None})
        
        authors_and_institutions = openalex_data if openalex_data is not None else auth_list
        return (self.builder
                .add_title(paper_title)
                .add_year(publication_year)
                .add_doi(doi_number)
                .add_openalex_link(openalex_link)
                .add_authors_and_institutions(authors_and_institutions)
                .add_referenced_works(openalex_referenced_works)
                .build())

    
    def __filter_paper_title(self, title):
        pattern = r'^(Demo:|Poster:|Welcome Message|Poster Paper:|Demo Paper:)'
        coincidence = re.match(pattern, title)
        return bool(coincidence)