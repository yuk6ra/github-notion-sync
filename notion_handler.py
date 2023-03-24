import requests
import os
import dotenv
import re
from notion2md.exporter.block import StringExporter

dotenv.load_dotenv()

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")

class NotionHandler():

    def __init__(self, database_id) -> None:
        # The daatabase title is the same as the repository name

        self.database_id = database_id
        url = f"https://api.notion.com/v1/databases/{self.database_id}"

        headers = {
            "accept": "application/json",
            'Authorization': 'Bearer ' + NOTION_TOKEN,
            "Notion-Version": "2022-06-28",
        }
        r = requests.get(url, headers=headers)

        self.db_title = r.json()["title"][0]["text"]["content"]

    def get_db_title(self):
        return self.db_title

    def get_notion_data(self, payload):
        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"

        headers = {
            'Authorization': 'Bearer ' + NOTION_TOKEN,
            "Notion-Version": "2022-06-28",
        }
        r = requests.post(url, json=payload ,headers=headers)
        print(r.json())
        data = r.json()["results"]
        return data

    def convert_notion_to_md(self, block_id):
        md = StringExporter(block_id, output_filename="output").export()
        return md

    def replace_image_url(self, md, title, path):
        # Get the image urls from the markdown, and replace the url with the local path

        uuids = []
        pattern = r'!\[(.*?)\]\((https?://.*?)\)'
        print(re.findall(pattern, md))
        images = []

        for match in re.findall(pattern, md):
            _, url = match
            uuid = self.get_uuid_from_url(url)

            if uuid not in uuids:
                _, file_ext = os.path.splitext(url)
                local_path = f"/{path}/{title}/{uuid}{file_ext.split('?')[0]}"            

                uuids.append(uuid)
                images.append({
                    "image_url": url,
                    "local_path": local_path,
                })
                md = re.sub(re.escape(url), f'{local_path}', md)

        return md, images

    def get_uuid_from_url(self, url):
        # Get the uuid from the image url
        uuid = url.split("/")[-2].split("?")[0]
        return uuid