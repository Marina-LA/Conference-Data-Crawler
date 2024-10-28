from api_clients.semantic_scholar_client import SemanticScholarClient
from api_clients.openalex_client import OpenAlexClient

class APIFactory:
    @staticmethod
    def get_client(api_name):
        if api_name == 'semantic_scholar':
            return SemanticScholarClient()
        elif api_name == 'openalex':
            return OpenAlexClient()
        else:
            raise ValueError('Invalid API name')