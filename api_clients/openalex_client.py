from api_clients.base_api_client import BaseApiClient
from config import OPENALEX_API_URL, OPENALEX_RATE_LIMIT
import logging

class OpenAlexClient(BaseApiClient):

    def __init__(self):
        super().__init__()

    def request_by_work_id(self, work_id):
        url = f"{OPENALEX_API_URL}/{work_id}"
        return self.make_request(url, api_name='openalex', rate_limit=OPENALEX_RATE_LIMIT)
    
    def request_by_doi(self, doi):
        if not doi:
            return None
        url = f"{OPENALEX_API_URL}/doi:{doi}"
        return self.make_request(url, api_name='openalex', rate_limit=OPENALEX_RATE_LIMIT)
    
    def get_referenced_works(self, doi=None, work_id=None):
        """Get the list of works referenced by this paper.
        
        Args:
            doi: Paper DOI
            work_id: OpenAlex work ID
            
        Returns:
            List of referenced work IDs, or None if not found
        """
        response = None
        if doi:
            response = self.request_by_doi(doi)
        elif work_id:
            response = self.request_by_work_id(work_id)
        
        if response and "referenced_works" in response:
            return response["referenced_works"]
        return None
    
    def get_paper_authors_and_affiliations_doi(self, doi, use_author_fallback=True):
        """Get authors and affiliations for a paper by DOI.
        
        Args:
            doi: Paper DOI
            use_author_fallback: If True, use author's last_known_institution as fallback
                                when paper has no institutions
        
        Returns:
            List of authors with institutions, or None if not found
        """
        response = self.request_by_doi(doi)
        authors_data = []
        if response is not None:
            authors = response["authorships"]
            for author in authors:
                author_name = author["author"]["display_name"]
                author_instituitons = author["institutions"]
                
                # If no institutions in paper and fallback enabled, try author profile
                if not author_instituitons and use_author_fallback:
                    author_id = author["author"].get("id")
                    if author_id:
                        author_profile = self._get_author_last_institution(author_id)
                        if author_profile:
                            author_instituitons = [author_profile]
                
                institutions = [{"Institution Name":institution["display_name"], "Country":institution["country_code"]}\
                                for institution in author_instituitons]
                authors_data.append({"Author": author_name, "Institutions": institutions})
            return authors_data
        return None
    
    def _get_author_last_institution(self, author_id):
        """Get author's last known institution from their profile.
        
        Args:
            author_id: OpenAlex author ID (can be URL or ID string)
            
        Returns:
            Institution dict or None (returns first from last_known_institutions)
        """
        try:
            # Convert web URL to API URL if needed
            # From: https://openalex.org/A5101567478
            # To:   https://api.openalex.org/authors/A5101567478
            if author_id.startswith("https://openalex.org/"):
                author_code = author_id.split("/")[-1]  # Extract "A5101567478"
                api_url = f"https://api.openalex.org/authors/{author_code}"
            else:
                api_url = author_id
            
            response = self.make_request(api_url, api_name='openalex', rate_limit=OPENALEX_RATE_LIMIT)
            
            # Try last_known_institutions (plural) first
            if response and "last_known_institutions" in response:
                insts = response["last_known_institutions"]
                if insts and len(insts) > 0:
                    # Return the first institution
                    inst = insts[0]
                    return {
                        "display_name": inst.get("display_name", ""),
                        "country_code": inst.get("country_code", "")
                    }
            
            # Fallback to last_known_institution (singular) if available
            if response and "last_known_institution" in response:
                inst = response["last_known_institution"]
                if inst:
                    return {
                        "display_name": inst.get("display_name", ""),
                        "country_code": inst.get("country_code", "")
                    }
        except Exception as e:
            logging.debug(f"Could not get author institution for {author_id}: {e}")
        return None
    
    def search_by_title(self, title, author_names=None):
        """Search for a paper in OpenAlex by title.
        
        Args:
            title: Paper title to search for
            author_names: Optional list of author names for verification
            
        Returns:
            Paper data if found, None otherwise
        """
        if not title:
            return None
        
        # Clean and prepare title for search
        # Remove special characters that might cause issues
        clean_title = title.strip()
        if clean_title.endswith('.'):
            clean_title = clean_title[:-1]
        
        # Use search parameter (not filter) for title matching
        params = {
            'search': clean_title,
            'per_page': 3  # Get top 3 results for better matching
        }
        
        url = OPENALEX_API_URL
        response = self.make_request(url, params=params, api_name='openalex', rate_limit=OPENALEX_RATE_LIMIT)
        
        if response and 'results' in response and len(response['results']) > 0:
            return response['results'][0]
        return None
    
    def get_institutions_by_title(self, title, dblp_author_names):
        """Get ONLY institutions by searching by title. Does not return author names.
        
        This method preserves DBLP author names and only adds institutional affiliations.
        
        Args:
            title: Paper title to search for
            dblp_author_names: List of author names from DBLP for verification
            
        Returns:
            List of institution lists (one per author), or None if not found/no match
        """
        if not dblp_author_names:
            return None
        
        response = self.search_by_title(title, dblp_author_names)
        
        if response is None:
            return None
        
        # Extract OpenAlex authors
        openalex_authors = response.get("authorships", [])
        openalex_author_names = [a.get("author", {}).get("display_name", "").lower() 
                                 for a in openalex_authors]
        
        # Verify authors match
        if not self._verify_authors_match(dblp_author_names, openalex_author_names):
            return None
        
        # Match DBLP authors with OpenAlex authors by name similarity
        # This handles cases where author counts don't exactly match
        institutions_only = []
        for dblp_author in dblp_author_names:
            best_match_institutions = None
            dblp_normalized = self._normalize_author_name(dblp_author)
            
            # Find best matching OpenAlex author
            for oa_author in openalex_authors:
                oa_name = oa_author.get("author", {}).get("display_name", "").lower()
                if dblp_normalized == oa_name or self._authors_similar(dblp_normalized, oa_name):
                    author_institutions = oa_author.get("institutions", [])
                    best_match_institutions = [{"Institution Name": inst.get("display_name", ""), 
                                              "Country": inst.get("country_code", "")}
                                             for inst in author_institutions]
                    break
            
            institutions_only.append(best_match_institutions if best_match_institutions else None)
        
        return institutions_only
    
    def _verify_authors_match(self, dblp_authors, openalex_authors):
        """Verify that DBLP and OpenAlex authors have significant overlap.
        
        Args:
            dblp_authors: List of author names from DBLP
            openalex_authors: List of author names from OpenAlex (already lowercase)
            
        Returns:
            True if authors match sufficiently, False otherwise
        """
        if not dblp_authors or not openalex_authors:
            return False
        
        # Normalize DBLP author names
        dblp_normalized = [self._normalize_author_name(name) for name in dblp_authors]
        
        # Count matches
        matches = 0
        for dblp_name in dblp_normalized:
            for openalex_name in openalex_authors:
                if self._authors_similar(dblp_name, openalex_name):
                    matches += 1
                    break
        
        # Require at least 50% of authors to match, or at least 2 authors
        min_required = max(2, len(dblp_authors) // 2)
        return matches >= min_required
    
    def _normalize_author_name(self, name):
        """Normalize author name for comparison."""
        return name.lower().strip()
    
    def _authors_similar(self, name1, name2):
        """Check if two author names are similar enough to be considered the same person.
        
        Handles variations like:
        - "John Smith" vs "john smith"
        - "J. Smith" vs "John Smith"
        - "Smith, John" vs "John Smith"
        """
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()
        
        # Exact match
        if name1 == name2:
            return True
        
        # Extract last names (assume last word is last name)
        parts1 = name1.split()
        parts2 = name2.split()
        
        if not parts1 or not parts2:
            return False
        
        last_name1 = parts1[-1]
        last_name2 = parts2[-1]
        
        # Last names must match
        if last_name1 != last_name2:
            return False
        
        # If last names match and at least one first initial matches, consider it a match
        first_initial1 = parts1[0][0] if parts1[0] else ''
        first_initial2 = parts2[0][0] if parts2[0] else ''
        
        return first_initial1 == first_initial2