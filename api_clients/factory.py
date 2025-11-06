from api_clients.semantic_scholar_client import SemanticScholarClient
from api_clients.openalex_client import OpenAlexClient
from api_clients.crossref_client import CrossRefClient

class APIFactory:
    @staticmethod
    def get_client(api_name):
        if api_name == 'semantic_scholar':
            return SemanticScholarClient()
        elif api_name == 'openalex':
            return OpenAlexClient()
        elif api_name == 'crossref':
            return CrossRefClient()
        else:
            raise ValueError('Invalid API name')