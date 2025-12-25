import os

from git import Repo
from pydantic import BaseModel


class GitRepoConfig(BaseModel):
    repo_dir: str
    remote_branch: str
    remote_url: str
    username: str
    email: str


class GitRepoNode:
    def __init__(self, repo_config: GitRepoConfig):
        self.repo_config = repo_config
        self.git_repo = GitRepoNode.init_repo(repo_config)

    def config(self) -> GitRepoConfig:
        return self.repo_config

    def repo(self) -> Repo:
        return self.git_repo

    def commit(self, commit_message: str):
        modified_files = [item.a_path for item in self.repo().index.diff(None)]
        changed_files = self.repo().untracked_files + modified_files

        self.repo().index.add(changed_files)

        if len(changed_files) > 0:
            self.repo().index.commit(commit_message)

        return changed_files

    def push(self, close=True):
        origin = self.repo().remote(name="origin")
        origin.push()

        if close:
            self.repo().close()

    def close(self):
        self.repo().close()

    @staticmethod
    def init_repo(repo_config: GitRepoConfig):
        if os.path.exists(repo_config.repo_dir):
            repo = Repo(repo_config.repo_dir)
        else:
            repo = Repo.clone_from(repo_config.remote_url, repo_config.repo_dir)
            repo.git.config("user.name", repo_config.username)
            repo.git.config("user.email", repo_config.email)
            repo.git.checkout("-b", repo_config.remote_branch, f"origin/{repo_config.remote_branch}")

        return repo
