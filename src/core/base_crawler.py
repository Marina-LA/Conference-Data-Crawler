from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple
import logging
from dataclasses import dataclass
from src.core.utils import FileManager
from src.core.models import CrawlerResult
from src.config.settings import crawler_config, path_config


class AbstractCrawler(ABC):
    """Base class for crawlers."""
    
    def __init__(self, conference: str, years: Tuple[int, int]):
        """
        Initialize the crawler.
        
        Args:
            conference: Name of the conference to crawl
            years: Tuple of (start_year, end_year)
        """
        self.conference = conference
        self.years = years
        self.first_year, self.last_year = years
        self.file_manager = FileManager()
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{conference}")
        
        # Ensure output directories exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        directories = [
            path_config.base_crawler_output_dir,
            path_config.extended_crawler_output_dir,
            path_config.citations_crawler_output_dir,
            path_config.cache_dir,
            path_config.logs_dir
        ]
        
        for directory in directories:
            self.file_manager.create_dir(directory)
    
    def crawl(self) -> CrawlerResult:
        """Run load, process and save pipeline."""
        try:
            self.logger.info(f"Starting crawl for {self.conference} ({self.first_year}-{self.last_year})")
            
            # Load data
            self.load_data()
            
            # Process data
            result = self.process_data()
            
            # Save data
            self.save_data()
            
            self.logger.info(f"Successfully completed crawl for {self.conference}")
            return CrawlerResult(success=True, data=result)
            
        except Exception as e:
            error_msg = f"Error during crawl for {self.conference}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return CrawlerResult(success=False, error=error_msg)
    
    @abstractmethod
    def load_data(self) -> None:
        """Load input data."""
        pass
    
    @abstractmethod
    def process_data(self) -> Dict[str, Any]:
        """Process loaded data and return results."""
        pass
    
    @abstractmethod
    def save_data(self) -> None:
        """Persist processed data."""
        pass
    
    def _validate_years(self) -> bool:
        """Validate year range."""
        current_year = 2024
        if self.first_year < 1990 or self.last_year > current_year + 1:
            raise ValueError(f"Years {self.first_year}-{self.last_year} are out of reasonable range")
        if self.first_year > self.last_year:
            raise ValueError(f"Start year {self.first_year} cannot be after end year {self.last_year}")
        return True
    
    def _get_year_range(self) -> List[int]:
        """Return inclusive list of years to process."""
        return list(range(self.first_year, self.last_year + 1))
