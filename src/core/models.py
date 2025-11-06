from typing import Any, Dict, Optional, Union, List
from dataclasses import dataclass, field
import logging


@dataclass
class CrawlerResult:
    """Result for a crawler run."""
    success: bool
    data: Dict[str, Any] = None
    error: str = None
    processed_count: int = 0
    skipped_count: int = 0


@dataclass
class PaperData:
    """Normalized paper record."""
    title: str
    year: Union[str, int]
    doi_number: Optional[str] = None
    openalex_link: Optional[str] = None
    authors_and_institutions: Optional[List[Dict[str, Any]]] = None
    openalex_referenced_works: Optional[List[str]] = None
    citations_s2: Optional[List[Dict[str, Any]]] = None
    abstract: Optional[str] = None
    venue: Optional[str] = None
    additional_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate data after initialization."""
        if not self.title or not self.title.strip():
            raise ValueError("Title cannot be empty")
        
        if not self.year:
            raise ValueError("Year cannot be empty")
        
        # Convert year to string for consistency
        self.year = str(self.year)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        result = {
            "Title": self.title,
            "Year": self.year,
            "DOI Number": self.doi_number,
            "OpenAlex Link": self.openalex_link,
            "Authors and Institutions": self.authors_and_institutions,
            "OpenAlex Referenced Works": self.openalex_referenced_works,
            "Citations S2": self.citations_s2,
            "Abstract": self.abstract,
            "Venue": self.venue
        }
        
        # Add additional fields
        result.update(self.additional_fields)
        
        # Remove None values for cleaner output
        return {k: v for k, v in result.items() if v is not None}
