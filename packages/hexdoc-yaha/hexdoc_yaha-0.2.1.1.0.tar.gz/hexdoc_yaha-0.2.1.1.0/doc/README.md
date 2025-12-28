# hexdoc-yaha

Python web book docgen and [hexdoc](https://pypi.org/project/hexdoc) plugin for Yet Another Hex Addon.

A Hexcasting addon that adds an assorted handful of spells, patterns and items!

## Version scheme

We use [hatch-gradle-version](https://pypi.org/project/hatch-gradle-version) to generate the version number based on whichever mod version the docgen was built with.

The version is in this format: `mod-version.python-version.mod-pre.python-dev.python-post`

For example:
* Mod version: `0.11.1-7`
* Python package version: `1.0.dev0`
* Full version: `0.11.1.1.0rc7.dev0`

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```sh
uv sync

.\.venv\Scripts\activate   # Windows
. .venv/bin/activate.fish  # fish
source .venv/bin/activate  # everything else
```

## Usage

For local testing, create a file called `.env` in the repo root following this template:
```sh
GITHUB_REPOSITORY=TheRobbie73/yaha
GITHUB_SHA=master
GITHUB_PAGES_URL=https://therobbie73.github.io/yaha
```

Useful commands:

```sh
# update your Python environment and lockfile if you added new dependencies
uv sync

# show help
hexdoc -h

# render and serve the web book in watch mode
nodemon --config doc/nodemon.json

# render and serve the web book
hexdoc serve

# build and merge the web book
hexdoc build
hexdoc merge

# start the Python interpreter with some extra local variables
hexdoc repl
```
