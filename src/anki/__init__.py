"""Extension to interact with a paperless-ng instance API.

This extension requires details to be filled into the `config.ini` file located \
in the same location as the __init__.py. Not doing so will result in the \
extension not working correctly.

Synopsis: pl <query>"""

import os
from configparser import ConfigParser
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib import parse

import requests
from albert import *

__title__ = "anki"
__version__ = "0.1.0"
__triggers__ = "anki "
__authors__ = "Pete Hamlin"

iconPath = iconLookup("anki") or os.path.dirname(__file__) + "/anki.png"
user_agent = "org.albert.extension.python.anki"


def initialize():
    global config
    config_file = ConfigParser()
    config_file.read(os.path.dirname(__file__) + "/config.ini")
    config = ApiConfig(config_file)


def handleQuery(query):
    if query.isTriggered:
        debug("{}".format(config.formats))
        results = []
        query.disableSort()
        if query.string.strip().startswith("search"):
            for card in find_cards(query.string.strip()[6:]):
                if "Basic" in card["modelName"]:
                    # Assume all basic types have front/back fields (could be dangerous, but hey)
                    front, back = "Front", "Back"
                else:
                    if not config.use_custom_formats:
                        warn(
                            "Card uses custom format!! Please enable custom formats your config.ini"
                        )
                        continue
                    front, back = derive_format(card["modelName"])
                results.append(
                    Item(
                        id=__title__,
                        icon=iconLookup("gedit") or iconPath,
                        text=card["fields"][back]["value"],
                        subtext="{} - {}".format(
                            card["deckName"], card["fields"][front]["value"]
                        ),
                        actions=[
                            ClipAction(
                                text="Copy answer to clipboard",
                                clipboardText=card["answer"],
                            ),
                            ClipAction(
                                text="Copy question to clipboard",
                                clipboardText=card["question"],
                            ),
                        ],
                    )
                )
        deck, deck_string = find_deck(query.string)
        if deck:
            if deck_string.strip().startswith("add"):
                pass
            else:
                for card in get_cards_for_deck(deck, deck_string):
                    pass
            # return add_new_series(query)
        else:
            for deck_name, deck_id in config.get_decks().items():
                if (
                    not query.string
                    or query.string in deck_name.lower()
                    or query.string in str(deck_id)
                ):
                    results.append(
                        Item(
                            id=__title__,
                            icon=iconPath,
                            text=deck_name,
                            subtext=str(deck_id),
                            completion=f"{__triggers__}{deck_id}",
                        )
                    )
        return results


def derive_format(model: str) -> Tuple[str, str]:
    """
    Takes the provided format and determine which fields serve as the front and back of a given card
    """
    debug("{}".format(config.formats))
    debug(model)
    matched_key = next(
        key for key, value in config.formats.items() if value["model"] == model
    )
    debug(matched_key)
    return config.formats[matched_key]["front"], config.formats[matched_key]["back"]


def anki_request(body: Dict[str, Optional[Dict]]) -> Dict:
    """
    Makes a request to the ankiconnect API with the JSON argument 'body'.

    See here: https://foosoft.net/projects/anki-connect/
    """
    if config.auth_required:
        body["key"] = config.auth_key
    debug("About to POST {}".format(body))
    response = requests.post(config.base_url, json=body)
    debug("Got response {}".format(response.json()))
    if response.ok:
        result = response.json()
        return result


def find_cards(query: str) -> List[Dict]:
    cards = []
    card_ids = anki_request({"action": "findCards", "params": {"query": query}})
    return anki_request({"action": "cardsInfo", "params": {"cards": card_ids}})


def find_cards_for_deck(deck: str, query: str) -> List[Dict]:
    """
    Returns a list of cards for a given deck ID
    """
    card_ids = anki_request(
        {"action": "findCards", "params": {"query": f"deck:{deck} {query}"}}
    )


def find_deck(query_string: str) -> Tuple[str, str]:
    """
    Determine if first argument is a deck and return along with the rest of the query string. Else, return the query string.
    """
    if not query_string:
        return (None, None)
    deck, *query = query_string.split(maxsplit=1)
    for _, id in config.get_decks().items():
        if deck == id:
            return (deck, query)
    return (None, query_string)


class ApiConfig:
    def __init__(self, config) -> None:
        self.base_url = config["anki"]["base_url"]
        self.auth_required = config["anki"].getboolean("auth_required")
        self.use_custom_formats = config["anki"].getboolean("use_custom_formats")
        self.force_custom_formats = config["anki"].getboolean("force_custom_formats")
        self.auth_key = config["anki"]["auth_key"]
        self.decks = {}
        self.deck_expiry = datetime.now()
        if self.use_custom_formats:
            self.formats = {
                key: {
                    "model": config[key]["model"],
                    "front": config[key]["front"],
                    "back": config[key]["back"],
                }
                for key in config
                if (key != "anki" and key != "DEFAULT")
            }

    def get_decks(self) -> Dict:
        if self.deck_expiry < datetime.now():
            self._refresh_decks()
        debug(self.decks)
        return self.decks

    def _refresh_decks(self):
        body = {"action": "deckNamesAndIds"}
        decks = anki_request(body)
        self.decks = decks or {}
        self.deck_expiry = datetime.now() + timedelta(minutes=30)
