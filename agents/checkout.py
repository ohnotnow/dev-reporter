import tempfile
from git import Repo
import shutil
import os

class CheckoutAgent():
    def __init__(self, repo_clone_url: str):
        self.repo_clone_url = repo_clone_url
        self.temp_dir = None

    def run(self) -> str:
        self.temp_dir = tempfile.mkdtemp()
        Repo.clone_from(self.repo_clone_url, self.temp_dir)
        return self.temp_dir

    def cleanup(self):
        if self.temp_dir:
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
        else:
            raise Exception("No temp directory to cleanup")

if __name__ == "__main__":
    agent = CheckoutAgent("https://github.com/openai/openai-python")
    temp_dir = agent.run()
    print(temp_dir)
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            print(os.path.join(root, file))
    agent.cleanup()
