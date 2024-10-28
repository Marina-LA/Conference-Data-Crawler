class PaperDataBuilder:
    def __init__(self):
        self.paper_data = {}

    def add_field(self, field_name, *values):
        self.paper_data[field_name] = self.__safe_get(*values)
        return self  # To allow method chaining

    def build(self):
        results = self.paper_data
        self.paper_data = {}
        return results
    
    def __safe_get(self, *values):
        return next((arg for arg in values if arg is not None), None)