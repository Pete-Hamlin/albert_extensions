"""Extension to interact with a paperless-ng instance API.

This extension requires details to be filled into the `config.ini` file located \
in the same location as the __init__.py. Not doing so will result in the \
extension not working correctly.

Synopsis: pl <query>"""

import os
from configparser import ConfigParser
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from urllib import parse

import requests
from albert import *

__title__ = "paperless"
__version__ = "0.1.0"
__triggers__ = "pl "
__authors__ = "Pete Hamlin"

iconPath = iconLookup("paperless") or os.path.dirname(
    __file__) + "/paperless.png"
user_agent = "org.albert.extension.python.paperless"


def initialize():
    global config
    config_file = ConfigParser()
    config_file.read(os.path.dirname(__file__) + "/config.ini")
    config = ApiConfig(config_file["paperless"])


def handleQuery(query):
    if query.isTriggered:
        return show_documents(query)


def show_documents(query) -> List[Item]:
    results = []
    for document in config.get_documents():
        title = document["title"]
        filters = [title]
        if config.parse_tags:
            tags = ", ".join([config.parse_tag(tag) for tag in document["tags"]])
            if tags:
                filters.append(tags)
        if config.parse_document_type:
            doc_type = config.parse_type(document.get("document_type"))
            if doc_type:
                filters.append(tags)
        if config.search_body and document.get("body"):
            filters.append(document.get("body"))
        debug(f"Got filters: {filters}")
        if filter_query(query.string, filters):
            debug(f"Got document: {title} - query string {query.string}")
            subtext = " - ".join(filters)
            preview_url = url = "{}/api/documents/{}/preview/".format(config.base_url, document["id"])
            download_url = url = "{}/api/documents/{}/download/".format(config.base_url, document["id"])
            results.append(
                Item(
                    id=__title__,
                    icon=iconPath,
                    text=title,
                    subtext=subtext,
                    completion=f"{__triggers__} {query.string}",
                    actions=[
                        UrlAction(text="Preview in browser", url=preview_url),
                        ClipAction(text="Copy Preview URL", clipboardText=preview_url),
                        UrlAction(text="Download Document", url=download_url),
                        ClipAction(text="Copy Download URL", clipboardText=download_url),
                    ],
                )
            )
    if not results:
        results.append(
            Item(
                id=__title__,
                icon=iconPath,
                text="No documents found",
                actions=[
                    UrlAction(text="Open linkding", url=config.base_url)
                ])),
    return results


def filter_query(query_string: str, filters: List[str]) -> bool:
    for item in filters:
        if query_string in item.lower():
            return True
    return False


class ApiConfig:
    def __init__(self, config) -> None:
        self.username = config["username"]
        self.password = config["password"]
        self.base_url = config["base_url"]
        self.search_body = config.getboolean("search_body")
        self.parse_tags = config.getboolean("parse_tags")
        self.parse_document_type = config.getboolean("parse_document_type")
        self.documents = []
        self.doc_expiry = datetime.now()

        if self.parse_tags:
            self.tags = {}
            self.tag_expiry = datetime.now()
            self._refresh_tags()

        if self.parse_document_type:
            self.document_types = {}
            self.type_expiry = datetime.now()
            self._refresh_types()

    def get_documents(self) -> List[Dict]:
        if self.doc_expiry < datetime.now():
            self._refresh_documents()
        return self.documents

    def parse_tag(self, tag: int) -> str:
        if self.tag_expiry < datetime.now():
            self._refresh_tags()
        return self.tags.get(tag)

    def parse_type(self, doc_type: int) -> str:
        if doc_type:
            if self.type_expiry < datetime.now():
                self._refresh_types()
            return self.document_types.get(doc_type)
        return None

    def _refresh_documents(self):
        url = f"{self.base_url}/api/documents/"
        debug("About to GET {}".format(url))
        documents = []
        while url:
            results, url = self._parse_results(url)
            documents += results
        self.documents = documents
        self.doc_expiry = datetime.now() + timedelta(minutes=30)

    def _refresh_tags(self):
        url = f"{self.base_url}/api/tags/"
        debug("About to GET {}".format(url))
        tags = {}
        while url:
            results, url = self._parse_results(url)
            for result in results:
                tags[result['id']] = result['slug']
        self.tags = tags
        self.tag_expiry = datetime.now() + timedelta(minutes=60)

    def _refresh_types(self):
        url = f"{self.base_url}/api/document_types/"
        debug("About to GET {}".format(url))
        doc_types = {}
        while url:
            results, url = self._parse_results(url)
            for result in results:
                doc_types[result['id']] = result['slug']
        self.document_types = doc_types
        self.type_expiry = datetime.now() + timedelta(minutes=60)

    def _parse_results(self, url) -> Tuple[List[Dict], str]:
        response = requests.get(url, timeout=5, auth=(self.username, self.password))
        if response.ok:
            result = response.json()
            return result["results"], result["next"]
        else:
            error('Got response {}'.format(response))
            return [], ""
