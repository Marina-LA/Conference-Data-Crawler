from api_clients.base_api_client import BaseApiClient
import logging


class CrossRefClient(BaseApiClient):
    
    CROSSREF_API_URL = "https://api.crossref.org/works"
    
    def __init__(self):
        super().__init__()
    
    def request_by_doi(self, doi):
        if not doi:
            return None
        
        url = f"{self.CROSSREF_API_URL}/{doi}"
        return self.make_request(url, api_name='crossref', rate_limit=0.1)
    
    def get_institutions_by_doi(self, doi, dblp_author_names):
        if not doi or not dblp_author_names:
            return None
        
        response = self.request_by_doi(doi)
        
        if not response or 'message' not in response:
            return None
        
        message = response['message']
        crossref_authors = message.get('author', [])
        
        if not crossref_authors:
            return None
        
        # Verify author count matches (strict)
        if len(crossref_authors) != len(dblp_author_names):
            logging.warning(f"CrossRef author count mismatch: DBLP={len(dblp_author_names)}, CrossRef={len(crossref_authors)}")
            return None
        
        # Verify authors match
        crossref_names = []
        for author in crossref_authors:
            given = author.get('given', '')
            family = author.get('family', '')
            full_name = f"{given} {family}".strip()
            crossref_names.append(full_name)
        
        if not self._verify_authors_match(dblp_author_names, crossref_names):
            logging.warning(f"CrossRef authors don't match DBLP authors")
            return None
        
        # Extract ONLY institutions (no author names)
        institutions_only = []
        for author in crossref_authors:
            affiliations = author.get('affiliation', [])
            if affiliations:
                # CrossRef doesn't provide country, only institution name
                institutions = [{
                    "Institution Name": aff.get('name', ''),
                    "Country": ""  # CrossRef doesn't have country
                } for aff in affiliations]
                institutions_only.append(institutions)
            else:
                institutions_only.append(None)
        
        return institutions_only
    
    def _verify_authors_match(self, dblp_authors, crossref_authors):
        if not dblp_authors or not crossref_authors:
            return False
        
        if len(dblp_authors) != len(crossref_authors):
            return False
        
        matches = 0
        for i in range(len(dblp_authors)):
            if self._authors_similar(dblp_authors[i], crossref_authors[i]):
                matches += 1
        
        required = max(1, int(len(dblp_authors) * 0.8))
        return matches >= required
    
    def _authors_similar(self, name1, name2):
        import re
        
        n1 = name1.lower().strip()
        n2 = name2.lower().strip()
        
        # Exact match
        if n1 == n2:
            return True
        
        # Remove special characters
        n1_clean = re.sub(r'[^\w\s]', '', n1)
        n2_clean = re.sub(r'[^\w\s]', '', n2)
        n1_clean = ' '.join(n1_clean.split())
        n2_clean = ' '.join(n2_clean.split())
        
        if n1_clean == n2_clean:
            return True
        
        # Check last name and first initial
        parts1 = n1_clean.split()
        parts2 = n2_clean.split()
        
        if not parts1 or not parts2:
            return False
        
        # Last name must match
        if parts1[-1] != parts2[-1]:
            return False
        
        # First initial must match
        if parts1[0][0] == parts2[0][0]:
            return True
        
        return False






