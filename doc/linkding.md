# Linkding

You will need your linkding API key to access use this extension. It can be found under Setting → Integrations → Rest API

## Installation

From the [root](../) of this repo, run the following command:

```shell
make linkding
```

Then open to `~/.local/share/albert/org.albert.extension.python/modules/linkding/config.ini` and fill in the following config.

## Config

- `api_token`: See above
- `base_url`: Base URL for your linkding instance
- `per_page` (default: 100): Pagination of queries, increasing this may result in longer queries, but will reduce the number of queries required to refresh articles