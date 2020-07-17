# nextcloud-link-generator

## Installation

Install dependencies with `pipenv install`.

After installing you have to create a `config.py` file.
This can be done by running `pipenv run login --host=<url of the nextcloud> --base-dir=<directory to search for in nextcloud>`.
See also `config.py.example`.

## Usage

List all exams:

```bash
pipenv run list-files
```

Search for exams:

```bash
# for fuzzy search
pipenv run search --lectures="exam1,exam2,exam 3"
# or for more exact matches
pipenv run search --exact --lectures="exam1,exam2,exam 3"
```

Generate links for exams:

```bash
# for fuzzy search
pipenv run links --lectures="exam1,exam2,exam 3"
# or for more exact matches
pipenv run links --exact --lectures="exam1,exam2,exam 3"
```

Note: `pipenv run` can be replaced by `invoke` if inside the python venv.


## Used libraries

  - https://github.com/owncloud/pyocclient at release 0.4
  - python-Levenshtein
  - tabulate
  - clipboard