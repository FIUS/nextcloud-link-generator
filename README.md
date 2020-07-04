# nextcloud-link-generator
## Installation
Simply run ```python3 setup.py``` to install all needed libraries and create config.py. If you don't want your nextcloud password saved in config.py just skip the password question by hitting the enter key. 
If you didn't save your passwort during setup you will be asked at running the script.

## Usage
Run ```python3 main.py <exam1> <exam2> <exam n>``` with the exams you want as commandline arguments. If there are spaces in the name, replace them with a minus (```-```)

## Used libraries
  - https://github.com/owncloud/pyocclient at release 0.4
  - python-Levenshtein
  - tabulate
  - clipboard