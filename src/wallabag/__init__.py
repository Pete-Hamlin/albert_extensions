# -*- coding: utf-8 -*-

"""Extension to interact with an existing wallabag instance.

This extension requires details to be filled into the `config.ini` file located \
in the same location as the __init__.py. Not doing so will result in the \
extension not working correctly.

This extension supports searching and retrieving articles from an existing \
wallabag instance. Search supports both title and tags.

Synopsis: <trigger> <query>"""

import os
from configparser import ConfigParser
from datetime import datetime, timedelta
from typing import Dict, List

import requests
from albert import *

__title__ = "Wallabag"
__version__ = "0.2.1"
__triggers__ = "wb "
__authors__ = "Pete Hamlin"
# __py_deps__ = ["requests"]

iconPath = iconLookup("wallabag") or os.path.dirname(
    __file__) + "/wallabag.png"
user_agent = "org.albert.extension.python.wallabag"


def initialize():
    global config
    config_file = ConfigParser()
    config_file.read(os.path.dirname(__file__) + "/config.ini")
    config = Config(config_file["wallabag"])


def handleQuery(query):
    if query.isTriggered:
        return show_articles(query)


def show_articles(query) -> List[Item]:
    results = []
    for article in config.get_articles():
        title = article["title"]
        tags = ", ".join([tag["label"] for tag in article["tags"]])
        if filter_query(query.string, [title, tags, article["url"]]):
            debug(f"Got article: {title} - query string {query.string}")
            subtext = "{}: {}".format(tags, article["url"])
            results.append(
                Item(
                    id=__title__,
                    icon=iconPath,
                    text=title,
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
                    UrlAction(text="Search in Wallabag",
                              url=f"{config.base_url}/search?currentRoute=homepage&search_entry%5Bterm%5D={query}"),
                    UrlAction(text="Open Wallabag", url=config.base_url),
                ])),
    return results


def filter_query(query_string: str, filters: List[str]) -> bool:
    for item in filters:
        if query_string in item.lower():
            return True
    return False


class Config:
    def __init__(self, config):
        self.client_id = config["client_id"]
        self.client_secret = config["client_secret"]
        self.username = config["username"]
        self.password = config["password"]
        self.base_url = config["base_url"]
        self.per_page = config["results_per_page"]
        self.token = None
        self.article_expiry = datetime.now()
        self.refresh_token()

    def get_token(self):
        if not self.token.is_valid():
            self.refresh_token()
        return self.token.access

    def refresh_token(self):
        url = f"{self.base_url}/oauth/v2/token"
        response = requests.post(
            url,
            data={
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.username,
                "password": self.password,
            },
            timeout=5
        )
        if response.ok:
            self.token = Token(response.json())
        else:
            warning(f"Got response {response.content}")

    def get_articles(self) -> List[Dict]:
        if self.article_expiry < datetime.now():
            self._refresh_articles()
        self.sort_articles()
        debug(f"Got {len(self.articles)} articles")
        return self.articles

    def sort_articles(self) -> None:
        existing_articles = set()
        filtered_articles = []
        for article in self.articles:
            if article["url"] not in existing_articles:
                existing_articles.add(article["url"])
                filtered_articles.append(article)
        self.articles = sorted(filtered_articles, key=lambda x: x["title"])

    def _get_response(self, params: str = None):
        url = f"{self.base_url}/api/entries.json?{params}"
        header = {"Authorization": f"Bearer {self.get_token()}",
                  "User_Agent": user_agent}
        debug(f"making GET request to {url}")
        return requests.get(url, headers=header, timeout=5)

    def _refresh_articles(self):
        response = self._get_response(self._get_params())
        if response.ok:
            self.articles = []
            results = response.json()
            pages = int(results["pages"])
            debug(f"Read pages as {pages}")
            self.articles += results["_embedded"]["items"]
            if pages > 1:
                for page in range(2, pages + 1):
                    results = self._get_response(
                        self._get_params(page=page)).json()
                    self.articles += results["_embedded"]["items"]
                    debug(f"Fetched {len(self.articles)}")
            self.article_expiry = datetime.now() + timedelta(minutes=15)
        else:
            debug("Found no results")
            self.articles = []

    def _get_params(self, page: int = 1):
        params = {"page": page, "perPage": self.per_page}
        return "&".join(f"{key}={value}" for key, value in params.items())


class Token:
    def __init__(self, token: Dict):
        self.access = token["access_token"]
        self.refresh = token["refresh_token"]
        self.expiry = datetime.now() + \
            timedelta(seconds=(token["expires_in"]/2))

    def is_valid(self):
        return datetime.now() <= self.expiry
