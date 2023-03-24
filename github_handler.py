import os
import requests
from github import Github
import dotenv

dotenv.load_dotenv()
GITHUB_ACCESS_TOKEN = os.environ["GITHUB_ACCESS_TOKEN"]
GITHUB_USERNAME = os.environ["GITHUB_USERNAME"]

class GithubHandler():

    def __init__(self, repository) -> None:
        g = Github(GITHUB_ACCESS_TOKEN)
        self.repository = repository
        self.repo = g.get_repo(f'{GITHUB_USERNAME}/{repository}')

    def get_git_files(self, path):
        file_names = []

        try:
            contents = self.repo.get_contents(path)
        except Exception as e:
            print(f"{path} not found in the repository")
            return file_names

        for file_content in contents:
            if file_content.type == "file":
                filename = file_content.name
                file_names.append(filename)
        return file_names

    def get_latest_commit_date(self, path):
        try:
            last_commit_date = next(iter(self.repo.get_commits(path=path))).commit.author.date
        except Exception as e:
            return None

        iso_date = last_commit_date.isoformat()
        return iso_date

    def push_images(self, images):
        
        contents = {}
        for image in images:
            # The image path slash is removed because the github api returns the path without the slash
            image_path = image["local_path"].strip("/")
            try:
                contents[image_path] = self.repo.get_contents(image_path, ref="main")
            except Exception as e:
                print(f"{image['local_path']} not found in the repository")

        print("contents", contents)
        # Upload the images to the repository
        for image in images:
            response = requests.get(image["image_url"])
            content = response.content
            image_path = image["local_path"].strip("/")
            image_file_name = image["local_path"].split("/")[-1]
            if image_path in contents:
                # The image file already exists, so update it
                self.repo.update_file(contents[image_path].path, f"Update {image_file_name}", content, contents[image_path].sha, branch="main")
            else:
                # The image file does not exist, so create it
                self.repo.create_file(image_path, f"Add {image_file_name}", content, branch="main")

        print(f"Images uploaded to {self.repository} repository in a single commit")

    def push_md(self, md, slug, path):
        file_path = f"{path}/{slug}.md"
        try:
            contents = self.repo.get_contents(file_path, ref="main")
            self.repo.update_file(contents.path, f"Update {slug}.md", md, contents.sha, branch="main")
        except Exception as e:
            self.repo.create_file(file_path, f"Add {slug}.md", md, branch="main")

        print(f"Markdown file uploaded to {self.repository} repository in a single commit")