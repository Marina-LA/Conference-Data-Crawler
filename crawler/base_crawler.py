from crawler.abstract_crawler import AbstractCrawler
from utils.file_utils import FileUtils
from api_clients.factory import APIFactory
from utils.paper_data_builder import PaperDataBuilder
import requests
import re
from bs4 import BeautifulSoup
from config import BASE_CRAWLER_OUTPUT_DIR, SKIP_SECTIONS, REQUEST_TIMEOUT


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
        print(f"\t> Processing data for {self.conference} <")
        for publication in self.data_to_process:
            paper_data = self.__get_dblp_paper_data(publication)
            if paper_data:
                if paper_data["Year"] not in self.data_per_year:
                    self.data_per_year[paper_data["Year"]] = []
                self.data_per_year[paper_data["Year"]].append(paper_data)


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
        # obtain the links for every year
        url = "https://dblp.org/db/conf/" + self.conference + "/"
        html_page = requests.get(url, timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(html_page.text, 'html.parser')
        link_list = set()
        for link_elem in soup.findAll('a'):
            link = link_elem.get('href')
            if link and url in link:  # to avoid repeated links
                link_list.add(link)
        return link_list  # list with all the papers for each year
    

    def __filter_dblp_links(self, link):
        # Specific case for SOCC and SOCC/Cloud
        if self.conference == "cloud": conf2 = "socc"
        else: conf2 = self.conference
        pattern = rf"https://dblp.org/db/conf/{self.conference}/{conf2}\d{{4}}\.html"
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
                    authors_names.append(author.text)
            if 'publ' in class_of_content_item:
                links = content_item.contents[0].findAll("a")
                openalex_link = [l.get("href") for l in links if "openalex" in l.get("href")]
                openalex_link = openalex_link[0] if openalex_link != [] else None
                doi_number = openalex_link.replace("https://api.openalex.org/works/doi:", "") if openalex_link is not None else None
                # get the openalex data
                openalex_data = self.openalex_client.get_paper_authors_and_affiliations_doi(doi_number) 
            if openalex_data is None:
                auth_list = []
                for author in authors_names:
                    auth_list.append({'Author': author, 'Institutions': None})
        
        return (self.builder.add_field("Title", paper_title)
                .add_field("Year", publication_year)
                .add_field("DOI Number", doi_number)
                .add_field("OpenAlex Link", openalex_link)
                .add_field("Authors and Institutions", openalex_data , auth_list)
                .build()
        )

    
    def __filter_paper_title(self, title):
        pattern = r'^(Demo:|Poster:|Welcome Message|Poster Paper:|Demo Paper:)'
        coincidence = re.match(pattern, title)
        return bool(coincidence)