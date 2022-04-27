# Paperless-ng

Paperless-ng is accessed via basic auth headers. You have various toggles to determine what you wish to parse when looking for a query match included in the config

## Installation

From the [root](../) of this repo, run the following command:

```shell
make paperless
```

Then open to `~/.local/share/albert/org.albert.extension.python/modules/paperless/config.ini` and fill in the following config.

## Config

- `username`: Login credentials
- `password`: Login credentials
- `base_url`: BAse URl of your paperless instance
- `search_body` (defalt: false): If this is `true` document body will be parsed to check for a query match (may slow down query process)
- `parse_tags` (default: true): If this is `true` document tags will be parsed to check for a query match (may slow down query process)
- `parse_document_type` (default: true): If this is `true` document type will be parsed to check for a query match (may slow down query process)
