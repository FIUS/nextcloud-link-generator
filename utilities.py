import sys
from pathlib import Path
import pyocclient.owncloud.owncloud as owncloud
import Levenshtein as stein
import datetime
import math
import clipboard
import re


# non word characters like - ( or _
WORD_SEPERATORS = re.compile(r'[\W_]+')
# roman numbers up to iii
ROMANS = re.compile(r'(?<=\s)(i+|I+)(?=\s|$)')


def normalize_string_for_search(string: str) -> str:
    seperators_replaced = WORD_SEPERATORS.sub(' ', string)
    romans_replaced = ROMANS.sub(lambda m: str(len(m.group(0))), seperators_replaced)
    return romans_replaced


def contains_every(search_strings, compare_string):
    for search_word in search_strings:
        if search_word not in compare_string:
            return False
    return True


class Nextcloud:

    def __init__(self, domain, username, password, remote_directory):
        self.oc = owncloud.Client(domain)
        self.oc.login(username, password)
        self.remote_directory = remote_directory

    def get_files(self):
        files = self.oc.list(self.remote_directory)
        return [f for f in files if f.file_type == 'dir']

    def get_filenames_with_path(self):
        files = self.get_files()
        result = []
        for f in files:
            filename = Path(f.path).name
            searchable_normalized_name = normalize_string_for_search(filename)
            result.append({'filename': filename, 'searchableFilename': searchable_normalized_name, 'path': f.path})
        return result

    def get_files_for_lectures(self, lectures: list, accuracy=8, exact_matches=False):
        files = self.get_filenames_with_path()
        output = {}
        for lecture in lectures:
            normalized_search = normalize_string_for_search(lecture)
            split_search = [w.lower() for w in normalized_search.split()]
            for f in files:
                filename = f.get('filename')
                normalized_filename = f.get('searchableFilename')

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

    def get_links_for_files(self, files: list, link_expire_in_days=7):
        expiry_date = datetime.datetime.now()+datetime.timedelta(days=link_expire_in_days)
        expiry_date_string = datetime.date.isoformat(expiry_date)
        output = {}
        for f in files:
            normalized_filename = f.get('searchableFilename')
            path = f.get('path')
            share_info = self.oc.share_file_with_link(path, expire_date=expiry_date_string)
            output[normalized_filename] = share_info.get_link()
        return output

    def get_links(self, lectures: list, link_expire_in_days=7, accuracy=8):
        next_week = datetime.datetime.now()+datetime.timedelta(days=link_expire_in_days)
        next_week_string = str(next_week.year)+"-" + \
            str(next_week.month)+"-"+str(next_week.day)
        print("Getting exams from server...")
        files = self.get_filenames_with_path() #self.oc.list(self.remote_directory)
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
