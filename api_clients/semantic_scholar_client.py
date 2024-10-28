from api_clients.base_api_client import BaseApiClient
from config import SEMANTIC_SCHOLAR_API_KEY, SEMANTIC_SCHOLAR_API_URL, USE_SEMANTIC_SCHOLAR_API_KEYS

class SemanticScholarClient(BaseApiClient):

    def __init__(self):
        super().__init__()

    def request_by_doi(self, doi):
        url = f"{SEMANTIC_SCHOLAR_API_URL}/{doi}"
        headers = {"x-api-key": SEMANTIC_SCHOLAR_API_KEY} if USE_SEMANTIC_SCHOLAR_API_KEYS else None
        params = {'fields': 'title,authors.name,abstract,tldr,embedding,references,externalIds'}
        return self.make_request(url, params=params, headers=headers)
    
    def request_by_title(self, title):
        url = f"{SEMANTIC_SCHOLAR_API_URL}/search/match?"
        headers = {"x-api-key": SEMANTIC_SCHOLAR_API_KEY} if USE_SEMANTIC_SCHOLAR_API_KEYS else None
        params = {'query': f'{title}.', 'fields': 'title,externalIds,abstract,tldr,references,year,authors.name'}
        return self.make_request(url, params=params, headers=headers)

    def batch_request(self, citations):
        url = f"{SEMANTIC_SCHOLAR_API_URL}/batch"
        params={'fields': 'title,year,venue,externalIds,authors.name'}
        responses = []
        # Split the citations into batches of 500 (limit of the API)
        for i in range(0, len(citations), 500):
            batch_citations = citations[i:i+10]
            response = self.make_request(url, method='POST', params=params, citations=batch_citations)
            if response:
                responses.extend(response)
        return responses
