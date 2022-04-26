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
__version__ = "0.1.0"
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
        title = article["title"]
        tags = ", ".join([tag for tag in article["tag_names"]])
        if filter_query(query.string, [title, tags, article["url"]]):
            debug(f"Got article: {title} - query string {query.string}")
            subtext = "{}: {}".format(tags, article["url"])
            results.append(
                Item(
                    id=__title__,
                    icon=iconPath,
                    text=title or article["website_title"] or article["url"],
                    subtext=subtext,
                    completion=f"{__triggers__} {query.string}",
                    actions=[
                        UrlAction(text="Open in browser", url=article["url"]),
                        ClipAction(text="Copy URL",
                                   clipboardText=article["url"]),
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
            self._refresh_articles()
        return self.articles

    def _refresh_articles(self):
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
