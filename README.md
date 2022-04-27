# Albert Extensions

Repository of extensions for the popular [albert]() launcher for Linux.

Here is a collection of albert extensions I made for personal use to connect to a number of self hosted solutions that I use. Figured they might be useful to some other people, so have released them to the public! Included extensions for the following services:

- [wallabag](https://github.com/search?utf8=%E2%9C%93&q=wallabag) - Self hostable application for saving web pages: Save and classify articles. Read them later. Freely. 
- [linkding](https://github.com/sissbruecker/linkding) - Self-hosted bookmark service.
- [paperless-ng](https://github.com/jonaswinkler/paperless-ng) - A supercharged version of paperless: scan, index and archive all your physical documents.

Each extension will fetch the necesary info from the respective API and cache it locally (default for 30 mins) to avoid hammering the API with requests. This should allow for much faster follow up queries after the initial fetch has occured.

## Installation

Please note that each extension interacts with a 3rd party servce that needs to be hosted (either self-hosted, or through a 3rd party). You **must** have the service set up and configured for the extension of choice to work (may seem obvious to some - but figured I should probably include that caveat).

I **highly** recommend you follow the official advice and create a clone the [albert python repo locally](https://github.com/albertlauncher/python) to install your extensions into. You can achieve this by running the following:

```shell
git clone https://github.com/albertlauncher/python.git ~/.local/share/albert/org.albert.extension.python/modules
```

From there, you can use the included `Makefile` to quickly copy over the files you need. For example, if you want the `wallabag` extension, simply run from the root of this repo:

```
make wallabag
```

This will copy over the needed `src` files and create an empty `config.ini` in `~/.local/share/albert/org.albert.extension.python/modules/$EXTENSION/`. See below for extension specific config details.

- [linkding](./doc/linkding.md)
- [paperless](./doc/paperless.md)
- [wallabag](./doc/wallabag.md)

## Caveats

I wrote these extensions to solve a problem quickly nd with minimal effort. They work for my personal use case of a fairly small database for each given service. I'm not sure how well they will scale up to a larger fileset, and you may have some serious lag issues if you're trying to process thousands of saved articles/links/documents on your own home server.

I may get around to improving performance should this become an issue for me, but as it stands, they work fine for my use case. If that doesnt work for you, feel free to fork and edit (I encourage you to do so), or even make a Pull Request!
