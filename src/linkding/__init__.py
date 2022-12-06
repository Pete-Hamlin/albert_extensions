"""Extension to interact with a linkding instance API.

This extension requires details to be filled into the `config.ini` file located \
in the same location as the __init__.py. Not doing so will result in the \
extension not working correctly.

Synopsis: ld <query>"""

import os
from configparser import ConfigParser
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from urllib import parse

import requests
from albert import *

__title__ = "Linkding"
__version__ = "0.1.1"
__triggers__ = "ld "
__authors__ = "Pete Hamlin"

iconPath = iconLookup("linkding") or os.path.dirname(
    __file__) + "/linkding.png"
user_agent = "org.albert.extension.python.linkding"


def initialize():
    global config
    config_file = ConfigParser()
    config_file.read(os.path.dirname(__file__) + "/config.ini")
    config = ApiConfig(config_file["linkding"])


def handleQuery(query):
    if query.isTriggered:
        return show_articles(query)


def show_articles(query) -> List[Item]:
    results = []
    for article in config.get_articles():
        article_id, title, article_url = article["id"], article["title"], article["url"]
        link_id = article["id"]
        tags = ", ".join([tag for tag in article["tag_names"]])
        if filter_query(query.string, [title, tags, article_url]):
            debug(f"Got article: {title} - query string {query.string}")
            subtext = "{}: {}".format(tags, article_url)
            results.append(
                Item(
                    id=__title__,
                    icon=iconPath,
                    text=title or article["website_title"] or article_url,
                    subtext=subtext,
                    completion=f"{__triggers__} {query.string}",
                    actions=[
                        UrlAction(text="Open link in browser", url=article_url),
                        ClipAction(text="Copy link URL",
                                   clipboardText=article_url),
                        FuncAction(text="Archive link", callable=lambda link_id=article_id: archive_link(link_id)),
                        FuncAction(text="Delete link", callable=lambda link_id=article_id: delete_link(link_id)),
                    ],
                )
            )
    if not results:
        results.append(
            Item(
                id=__title__,
                icon=iconPath,
                text="No articles found",
                actions=[
                    UrlAction(text="Open linkding", url=config.base_url),
                    FuncAction(text="Refresh Articles", callable=config.refresh_articles),
                ])),
    return results


def filter_query(query_string: str, filters: List[str]) -> bool:
    for item in filters:
        if query_string in item.lower():
            return True
    return False

def delete_link(link_id: str):
    url = f"{config.base_url}/api/bookmarks/{link_id}"
    debug("About to DELETE {}".format(url))
    response = requests.delete(url, headers=config.headers)
    if response.ok:
        config.refresh_articles()
    else:
        warn("Got response {}".format(response))

def archive_link(link_id: str):
    url = f"{config.base_url}/api/bookmarks/{link_id}/archive/"
    post_request(url)

def post_request(url: str):
    debug("About to POST {}".format(url))
    response = requests.post(url, headers=config.headers)
    if response.ok and response.content:
        return response.json()
    else:
        warn("Got response {}".format(response))

class ApiConfig:
    def __init__(self, config) -> None:
        self.api_token = config["api_token"]
        self.base_url = config["base_url"]
        self.per_page = config["results_per_page"]
        self.headers = {
            "Authorization": "Token {}".format(self.api_token),
        }
        self.params = {
            "limit": self.per_page,
        }
        self.articles = []
        self.article_expiry = datetime.now()

    def get_articles(self) -> List[Dict]:
        if self.article_expiry < datetime.now():
            self.refresh_articles()
        return self.articles

    def refresh_articles(self):
        url = f"{self.base_url}/api/bookmarks/?{self._get_params()}"
        debug("About to GET {}".format(url))
        articles = []
        while url:
            results, url = self._parse_results(url)
            articles += results
        self.articles = articles
        self.article_expiry = datetime.now() + timedelta(minutes=30)

    def _parse_results(self, url) -> Tuple[List[Dict], str]:
        response = requests.get(url, headers=self.headers, timeout=5)
        if response.ok:
            result = response.json()
            return result["results"], result["next"]
        else:
            debug('Got response {}'.format(response))
            return [], ""

    def _get_params(self):
        return "&".join(f"{key}={value}" for key, value in self.params.items())



