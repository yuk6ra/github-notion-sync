import logging
import textwrap
from github_handler import GithubHandler
from notion_handler import NotionHandler

class GitNotionSync():
    def __init__(self, git_path, git_md_path, git_assets_path, notion_database_id):
        self.notion = NotionHandler(notion_database_id)

        # Get the repository name from the Notion database
        self.repository = self.notion.get_db_title()
        self.git = GithubHandler(self.repository)

        self.git_path = git_path
        self.git_md_path = git_md_path
        self.git_assets_path = git_assets_path

    def run(self):
        # Get the list of files from the git repository
        git_files = self.git.get_git_files(path=self.git_path)

        # Get the latest commit date from the git repository
        git_latest_commit_date = self.git.get_latest_commit_date(path=self.git_path)
        logging.info(f"Latest={git_latest_commit_date}, Files={git_files}")

        # If there is no commit, set the date to 2020-03-21
        if not git_latest_commit_date:
            git_latest_commit_date = "2020-03-21T00:00:00"
        
        # Get the latest data from Notion
        payload = {
            "filter": {
                "and": [
                    {
                        "property": "visibility",
                        "select": {
                            "equals": "Public"
                        }
                    }, {
                        "timestamp": "last_edited_time",
                        "last_edited_time": {
                            "on_or_after": git_latest_commit_date
                        }
                    }
                ]
            },
            "page_size": 100
        }
        data = self.notion.get_notion_data(payload=payload)

        for page_data in data:
            page_id = page_data["id"]
            slug = page_data["properties"]["slug"]["rich_text"][0]["plain_text"]
            props_md = self._get_props_md(data=page_data)

            md = self.notion.convert_notion_to_md(page_id)

            # if images exist, replace the image url with the local path
            new_md, images = self.notion.replace_image_url(md, slug, self.git_assets_path)

            # Save images to the git repository
            self.git.push_images(images)

            # Add the properties to the top of the md file
            self.git.push_md(props_md + "\n" + new_md, slug, self.git_md_path)

    def _get_props_md(self, data) -> str:

        # Get the emoji
        emoji = ""
        try:
            emoji = data.get("icon", {}).get("emoji", "")
        except Exception:
            pass

        properties = data.get("properties", {})

        # Get the title        
        title = ""
        try:
            title = properties.get("title", {}).get("title", [{}])[0].get("plain_text", "")
        except Exception:
            pass

        # Get the topics
        topics = []
        try:
            topics = [t.get("name", "") for t in properties.get("topics", {}).get("multi_select", [])]
        except Exception:
            pass

        # Get the created_at and last_edited_at
        created_at = properties.get("Created time", {}).get("created_time", "")
        last_edited_at = properties.get("Last edited time", {}).get("last_edited_time", "")

        # Create the properties markdown
        props_md = textwrap.dedent(f"""
            ---
            title: "{title}"
            emoji: "{emoji}"
            topics: {topics}
            created_at: "{created_at}"
            last_edited_at: "{last_edited_at}"
            ---
        """).strip()

        props_md = textwrap.indent(props_md, "")

        return props_md

def main(request):
    
    database_id = request.args.get("database_id", "")

    # Path to the git repository
    # if the repository don't have a subdirectory, set it to ""
    git_path = ""

    # Path to the directory where the markdown files are stored
    git_md_path = request.args.get("git_md_path", "")

    # Path to the directory where the image files are stored
    git_assets_path = request.args.get("git_assets_path", "")

    sync = GitNotionSync(
        git_path=git_path,
        git_md_path=git_md_path,
        git_assets_path=git_assets_path,
        notion_database_id=database_id
    )

    sync.run()
