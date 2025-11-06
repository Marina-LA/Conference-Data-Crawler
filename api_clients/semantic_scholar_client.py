from api_clients.base_api_client import BaseApiClient
from config import (SEMANTIC_SCHOLAR_API_KEY, SEMANTIC_SCHOLAR_API_URL, 
                    USE_SEMANTIC_SCHOLAR_API_KEYS, SEMANTIC_SCHOLAR_RATE_LIMIT)

class SemanticScholarClient(BaseApiClient):

    def __init__(self):
        super().__init__()

    def request_by_doi(self, doi):
        if not doi:
            return None
        url = f"{SEMANTIC_SCHOLAR_API_URL}/{doi}"
        headers = {"x-api-key": SEMANTIC_SCHOLAR_API_KEY} if USE_SEMANTIC_SCHOLAR_API_KEYS else None
        params = {'fields': 'title,authors.name,abstract,tldr,embedding,citations,externalIds'}
        return self.make_request(url, params=params, headers=headers, 
                               api_name='semantic_scholar', rate_limit=SEMANTIC_SCHOLAR_RATE_LIMIT)
    
    def batch_request(self, citations):
        url = f"{SEMANTIC_SCHOLAR_API_URL}/batch"
        headers = {"x-api-key": SEMANTIC_SCHOLAR_API_KEY} if USE_SEMANTIC_SCHOLAR_API_KEYS else None
        params = {'fields': 'title,year,venue,externalIds,authors.name'}
        responses = []
        
        for i in range(0, len(citations), 500):
            batch_citations = citations[i:i+500]
            response = self.make_request(url, method='POST', params=params, 
                                        citations=batch_citations, headers=headers,
                                        api_name='semantic_scholar', rate_limit=SEMANTIC_SCHOLAR_RATE_LIMIT)
            if response:
                responses.extend(response)
        return responses