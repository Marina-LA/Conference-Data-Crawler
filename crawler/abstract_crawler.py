from abc import ABC, abstractmethod
from utils.file_utils import FileUtils

class AbstractCrawler(ABC):
    def __init__(self, conference, years):
        self.conference = conference
        self.years = years
        self.first_year, self.last_year = years
        self.file_utils = FileUtils()

    def crawl(self):
        self.load_data()
        self.process_data()
        self.save_data()

    @abstractmethod
    def load_data(self):
        pass

    @abstractmethod
    def process_data(self):
        pass

    @abstractmethod
    def save_data(self):
        pass