import json
import os
from typing import Any, Dict, Optional, Union, List
import logging
from pathlib import Path


class FileManager:
    """File helpers with logging."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def load_json(self, path: str) -> Dict[str, Any]:
        """Load JSON file."""
        try:
            with open(path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            self.logger.error(f"File not found: {path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in file {path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error loading {path}: {e}")
            raise
    
    def save_json(self, path: str, data: Any, indent: int = 4) -> None:
        """Save JSON file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=indent)
                
            self.logger.debug(f"Successfully saved data to {path}")
            
        except OSError as e:
            self.logger.error(f"Error saving to {path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error saving {path}: {e}")
            raise
    
    def exists(self, path: str) -> bool:
        """Return True if path exists."""
        return os.path.exists(path)
    
    def create_dir(self, path: str) -> None:
        """Create directory if missing."""
        try:
            os.makedirs(path, exist_ok=True)
            self.logger.debug(f"Created directory: {path}")
        except OSError as e:
            self.logger.error(f"Error creating directory {path}: {e}")
            raise
    
    def add_data_to_existing_file(self, path: str, data: Dict[str, Any]) -> None:
        """Merge and save JSON data."""
        try:
            if not self.exists(path):
                self.save_json(path, data)
                self.logger.info(f"Created new file: {path}")
                return
            
            # Load existing data
            existing_data = self.load_json(path)
            
            # Merge data
            for key, value in data.items():
                existing_data[key] = value
            
            # Save merged data
            self.save_json(path, existing_data)
            self.logger.info(f"Updated existing file: {path}")
            
        except Exception as e:
            self.logger.error(f"Error updating file {path}: {e}")
            raise
    
    def get_file_size(self, path: str) -> Optional[int]:
        """Return file size in bytes or None."""
        try:
            return os.path.getsize(path)
        except OSError:
            return None
    
    def list_files(self, directory: str, pattern: str = "*") -> List[str]:
        """List files matching pattern."""
        try:
            path = Path(directory)
            if not path.exists():
                return []
            
            return [str(p) for p in path.glob(pattern) if p.is_file()]
        except Exception as e:
            self.logger.error(f"Error listing files in {directory}: {e}")
            return []


class PaperDataBuilder:
    """Builder for PaperData."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._data: Dict[str, Any] = {}
    
    def add_title(self, title: str) -> 'PaperDataBuilder':
        """Set title."""
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")
        self._data['title'] = title.strip()
        return self
    
    def add_year(self, year: Union[str, int]) -> 'PaperDataBuilder':
        """Set year."""
        if not year:
            raise ValueError("Year cannot be empty")
        self._data['year'] = str(year)
        return self
    
    def add_doi(self, doi: Optional[str]) -> 'PaperDataBuilder':
        """Set DOI."""
        if doi:
            # Basic DOI validation
            if not doi.startswith('10.'):
                self.logger.warning(f"DOI '{doi}' doesn't start with '10.' - may be invalid")
        self._data['doi_number'] = doi
        return self
    
    def add_openalex_link(self, link: Optional[str]) -> 'PaperDataBuilder':
        """Set OpenAlex link."""
        self._data['openalex_link'] = link
        return self
    
    def add_authors_and_institutions(self, authors: Optional[List[Dict[str, Any]]]) -> 'PaperDataBuilder':
        """Set authors and institutions."""
        self._data['authors_and_institutions'] = authors
        return self
    
    def add_referenced_works(self, works: Optional[List[str]]) -> 'PaperDataBuilder':
        """Set referenced works."""
        self._data['openalex_referenced_works'] = works
        return self
    
    def add_citations_s2(self, citations: Optional[List[Dict[str, Any]]]) -> 'PaperDataBuilder':
        """Set S2 citations."""
        self._data['citations_s2'] = citations
        return self
    
    def add_abstract(self, abstract: Optional[str]) -> 'PaperDataBuilder':
        """Set abstract."""
        self._data['abstract'] = abstract
        return self
    
    def add_venue(self, venue: Optional[str]) -> 'PaperDataBuilder':
        """Set venue."""
        self._data['venue'] = venue
        return self
    
    def add_field(self, field_name: str, value: Any) -> 'PaperDataBuilder':
        """Add custom field."""
        self._data[field_name] = value
        return self
    
    def build(self) -> 'PaperData':
        """Build a PaperData."""
        try:
            # Import here to avoid circular imports
            from src.core.models import PaperData
            
            # Extract required fields
            title = self._data.get('title')
            year = self._data.get('year')
            
            if not title:
                raise ValueError("Title is required")
            if not year:
                raise ValueError("Year is required")
            
            # Create PaperData object
            paper_data = PaperData(
                title=title,
                year=year,
                doi_number=self._data.get('doi_number'),
                openalex_link=self._data.get('openalex_link'),
                authors_and_institutions=self._data.get('authors_and_institutions'),
                openalex_referenced_works=self._data.get('openalex_referenced_works'),
                citations_s2=self._data.get('citations_s2'),
                abstract=self._data.get('abstract'),
                venue=self._data.get('venue'),
                additional_fields={k: v for k, v in self._data.items() 
                                if k not in ['title', 'year', 'doi_number', 'openalex_link', 
                                           'authors_and_institutions', 'openalex_referenced_works',
                                           'citations_s2', 'abstract', 'venue']}
            )
            
            # Reset builder state
            self._data = {}
            
            return paper_data
            
        except Exception as e:
            self.logger.error(f"Error building paper data: {e}")
            raise
    
    def build_dict(self) -> Dict[str, Any]:
        """Build and return as dict."""
        return self.build().to_dict()
    
    def reset(self) -> 'PaperDataBuilder':
        """Reset state."""
        self._data = {}
        return self
