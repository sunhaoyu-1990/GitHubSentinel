import json

class HtmlManager:
    def __init__(self, html_file):
        self.html_file = html_file
        self.html = self.load_html()
    
    def load_html(self):
        with open(self.html_file, 'r') as f:
            return json.load(f)
    
    def save_html(self):
        with open(self.html_file, 'w') as f:
            json.dump(self.html, f, indent=4)
    
    def list_html(self):
        return self.html
    
    def add_subscription(self, repo):
        if repo not in self.html:
            self.html.append(repo)
            self.save_html()
    
    def remove_html(self, repo):
        if repo in self.html:
            self.html.remove(repo)
            self.save_html()