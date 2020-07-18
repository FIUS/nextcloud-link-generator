from typing import List, Dict, Iterable
from pathlib import Path
from json import load, dump
import re
import pyocclient.owncloud.owncloud as owncloud
from pyocclient.owncloud.owncloud import FileInfo
import Levenshtein as stein
import math
import datetime
import clipboard


# non word characters like - ( or _
WORD_SEPERATORS = re.compile(r'[\W_]+')
# roman numbers up to iii
ROMANS = re.compile(r'(?<=\s)(i+|I+)(?=\s|$)')
'''A regex that matches upper or lowercase i+ not part of a word.'''


def normalize_string_for_search(string: str) -> str:
    '''Replace all WORD_SEPERATORS with a space and all ROMANS with arabic numbers 1-3.'''
    seperators_replaced = WORD_SEPERATORS.sub(' ', string)
    romans_replaced = ROMANS.sub(lambda m: str(len(m.group(0))), seperators_replaced)
    return romans_replaced


def contains_every(search_strings: Iterable[str], compare_string: str):
    '''Return True only if all strings in "search_strings" are a substring of "compare_string".'''
    for search_word in search_strings:
        if search_word not in compare_string:
            return False
    return True


class Nextcloud:

    def __init__(self, domain, username, password, remote_directory):
        self.oc = owncloud.Client(domain)
        #self.oc.login(username, password)
        self.login = False
        def delayed():
            if not self.login:
                self.oc.login(username, password)
                self.login = True
        self.delayed_login = delayed
        self.remote_directory = remote_directory

    def get_files(self) -> List[FileInfo]:
        '''Get a list of directories directly from the nextcloud server.'''
        self.delayed_login()
        files = self.oc.list(self.remote_directory)
        return [f for f in files if f.file_type == 'dir']

    def get_filenames_with_path(self, no_cache=False) -> List[Dict[str, str]]:
        '''Get a list of directory info dicts containing the "filename", the "searchableFilename" and the "path".

        args:
            no_cache: True if the cache should be ignored for this request (default False)
        '''
        cache_path = Path('cache.json')
        if not no_cache and cache_path.exists(): # load cache
            with cache_path.open() as c:
                cache = load(c)
                metadata = cache.get('metadata')
                if metadata: # check if cache is stale or malformed
                    if (
                        metadata.get('date') == datetime.date.today().isoformat()
                        and metadata.get('directory') == self.remote_directory
                    ):
                        return cache.get('files', [])

        # load files from server
        files = self.get_files()
        result = []
        for f in files:
            filename = Path(f.path).name
            searchable_normalized_name = normalize_string_for_search(filename)
            result.append({'filename': filename, 'searchableFilename': searchable_normalized_name, 'path': f.path})

        if not no_cache: # save cache
            with cache_path.open(mode='w') as c:
                cache = {
                    'metadata': {
                        'date': datetime.date.today().isoformat(),
                        'directory': self.remote_directory
                    },
                    'files': result,
                }
                dump(cache, c)
        return result

    def get_files_for_lectures(self, lectures: Iterable[str], accuracy=8, exact_matches=False, no_cache=False) -> List[Dict[str, str]]:
        '''Filters the list from get_filenames_with_path to only include entries that match one of the search strings in lectures.

        args:
            lectures: The list of search strings
            accuracy: The accuracy threshold for the levensthein distance
            exact_matches: if true only exact substring matches are considered (default False)
            no_cache: True if the cache should be ignored for this request (default False)

        returns:
            The list of files matching at least one of the search strings.
        '''
        files = self.get_filenames_with_path(no_cache=no_cache)

        output = {}  # type: Dict[str, Dict[str, str]]
        for lecture in lectures:
            normalized_search = normalize_string_for_search(lecture)
            split_search = [w.lower() for w in normalized_search.split()]
            for f in files:
                filename = f['filename']
                normalized_filename = f['searchableFilename']

                if filename in output:
                    continue
                # exact substring matches
                if contains_every(split_search, normalized_filename.lower()):
                    output[filename] = f
                    continue

                if exact_matches:
                    continue

                # fuzzy levenstein matching
                if stein.distance(normalized_search, normalized_filename) < accuracy:
                    output[filename] = f
                    continue
        return list(output.values())

    def get_links_for_files(self, files: List[Dict[str, str]], link_expire_in_days=7):
        '''Get nextcloud share links for all files.

        args:
            files: The list of files.
                A file is a dict containing at least a str for "path" and one for "filename".
                The list of files can be obtained from get_files_for_lectures.
            link_expire_in_days: the number of days the link should be valid
        '''
        self.delayed_login()
        expiry_date = datetime.datetime.now()+datetime.timedelta(days=link_expire_in_days)
        expiry_date_string = datetime.date.isoformat(expiry_date)
        output = {}
        for f in files:
            normalized_filename = f.get('searchableFilename')
            if normalized_filename is None:
                normalized_filename = f.get('filename')
            path = f.get('path')
            share_info = self.oc.share_file_with_link(path, expire_date=expiry_date_string)
            output[normalized_filename] = share_info.get_link()
        return output

    def get_links(self, lectures: list, link_expire_in_days=7, accuracy=8):
        next_week = datetime.datetime.now()+datetime.timedelta(days=link_expire_in_days)
        next_week_string = str(next_week.year)+"-" + \
            str(next_week.month)+"-"+str(next_week.day)
        print("Getting exams from server...")
        self.delayed_login()
        files = self.oc.list(self.remote_directory)
        print("Done...")
        output = {}
        for lecture in lectures:
            print("Searching for:", lecture)
            for f in files:
                if f.file_type == "dir":
                    split_path = f.path.split("/")

                    lecture_name_server = split_path[-2]

                    modified_lecture_name_server = lecture_name_server.replace(
                        "-", "")
                    modified_lecture = lecture.replace("-", "")

                    distance = stein.distance(
                        modified_lecture, modified_lecture_name_server)
                    if distance < accuracy or modified_lecture.lower() in modified_lecture_name_server.lower():
                        if distance <= 0:
                            distance = 1
                        link_info = self.oc.share_file_with_link(
                            f.path, expire_date=next_week_string)
                        output[lecture_name_server] = (
                            link_info.get_link(), 1/float(math.sqrt(distance)))
        print()
        return output


class Helper:
    @staticmethod
    def toClipboard(text):
        clipboard.copy(text)
