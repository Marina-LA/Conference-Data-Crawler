import json
import os

class FileUtils:
    def load_json(self, path):
        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)
        
    def save_json(self, path, data):
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def exists(self, path):
        return os.path.exists(path)
    
    def create_dir(self, path):
        os.makedirs(path, exist_ok=True)

    def add_data_to_existing_file(self, path, data):
        if not self.exists(path):
            self.save_json(path, data)
            return
        existing_data = self.load_json(path)
        for key in data.keys():
            existing_data[key] = data[key]
        self.save_json(path, existing_data)