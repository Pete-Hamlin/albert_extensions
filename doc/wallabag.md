# Wallabag

You will need an API key pair from wallabag to run. [Here](https://doc.wallabag.org/en/developer/api/readme.html) is the official docs on how to generate the necessary credentials.

## Installation

From the [root](../) of this repo, run the following command:

```shell
make wallabag
```

Then open to `~/.local/share/albert/org.albert.extension.python/modules/wallabag/config.ini` and fill in the following config.

## Config

- `client_id`
- `client_secret`
- `username`
- `password`

All of the above are required as part of the wallabag oauth process. After initial token fetch with credentials, future requests are made using the refresh token

- `base_url`: URL for your wallabag instance
- `results_per_page` (default: 20): Pagination of queries, increasing this may result in longer queries, but will reduce the number of queries required to refresh articles