from git import Repo
import tempfile

def checkout_repo(repo_clone_url: str) -> str:
    temp_dir = tempfile.mkdtemp()
    Repo.clone_from(repo_clone_url, temp_dir)
    return temp_dir
