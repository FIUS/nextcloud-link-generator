# nextcloud-link-generator

## Installation

Install dependencies with `pipenv install`.

After installing you have to create a `config.py` file.
This can be done by running `pipenv run login --host=<url of the nextcloud> --base-dir=<directory to search for in nextcloud>`.
See also `config.py.example`.

## Usage

When using the cli the content of the directory is cached in the file `cache.json`.
This should make searches very fast.
The cache is refreshed if the `cache.json` is deleted or if the directory was changed or if the cache is not from the same date as today.
The cache can also be completely bypassed (and will not be updated on disk) by using the `--no-cache` flag.

List all exams:

```bash
pipenv run list-files
# without on disk cache
pipenv run list-files --no-cache
```

Search for exams:

```bash
# for fuzzy search
pipenv run search --lectures="exam1,exam2,exam 3"
# or for more exact matches
pipenv run search --exact --lectures="exam1,exam2,exam 3"
# to search without using the on disk cache
pipenv run search --no-cache --lectures="exam1,exam2,exam 3"
```

Generate links for exams:

```bash
# for fuzzy search
pipenv run links --lectures="exam1,exam2,exam 3"
# or for more exact matches
pipenv run links --exact --lectures="exam1,exam2,exam 3"
# to generate links without using the on disk cache
pipenv run links --no-cache --lectures="exam1,exam2,exam 3"
```

Get help for the commands:

```bash
# list all commands
pipenv run list
# get help for a specific command
pipenv run help <command-name>
# example:
pipenv run help search
```

Note: `pipenv run` can be replaced by `invoke` if inside the python venv.


## Used libraries

  - https://github.com/owncloud/pyocclient at release 0.4
  - python-Levenshtein
  - tabulate
  - clipboard
  - invoke (only for cli)