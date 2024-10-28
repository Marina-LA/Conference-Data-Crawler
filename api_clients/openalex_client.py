from api_clients.base_api_client import BaseApiClient
from config import OPENALEX_API_URL

class OpenAlexClient(BaseApiClient):

    def __init__(self):
        super().__init__()

    def request_by_work_id(self, work_id):
        url = f"{OPENALEX_API_URL}/{work_id}"
        return self.make_request(url)
    
    def request_by_doi(self, doi):
        url = f"{OPENALEX_API_URL}/doi:{doi}"
        return self.make_request(url)
    
    def get_paper_title_work_id(self, work_id):
        response = self.request_by_work_id(work_id)
        if response is not None:
            return response["title"]
        return None
    
    def get_paper_authors_work_id(self, work_id):
        response = self.request_by_work_id(work_id)
        if response is not None:
            authors = response["authorships"]
            return [author["author"]["display_name"] for author in authors]
        return None
    
    def get_paper_authors_and_affiliations_work_id(self, work_id):
        response = self.request_by_work_id(work_id)
        authors_data = []
        if response is not None:
            authors = response["authorships"]
            for author in authors:
                author_name = author["author"]["display_name"]
                author_instituitons = author["institutions"]
                institutions = [{"Institution Name":institution["display_name"], "Country":institution["country_code"]}\
                                for institution in author_instituitons]
                authors_data.append({"Author": author_name, "Institutions": institutions})
            return authors_data
        return None
    
    def get_paper_title_doi(self, doi):
        response = self.request_by_doi(doi)
        if response is not None:
            return response["title"]
        return None
    
    def get_paper_authors_doi(self, doi):
        response = self.request_by_doi(doi)
        if response is not None:
            authors = response["authorships"]
            return [author["author"]["display_name"] for author in authors]
        return None
    
    def get_paper_authors_and_affiliations_doi(self, doi):
        response = self.request_by_doi(doi)
        authors_data = []
        if response is not None:
            authors = response["authorships"]
            for author in authors:
                author_name = author["author"]["display_name"]
                author_instituitons = author["institutions"]
                institutions = [{"Institution Name":institution["display_name"], "Country":institution["country_code"]}\
                                for institution in author_instituitons]
                authors_data.append({"Author": author_name, "Institutions": institutions})
            return authors_data
        return None